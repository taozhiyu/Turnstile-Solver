import os
import sys
import time
import uuid
import json
import random
import logging
import asyncio
import argparse
from quart import Quart, request, jsonify
from camoufox.async_api import AsyncCamoufox

COLORS = {
    'MAGENTA': '\033[35m',
    'BLUE': '\033[34m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'RED': '\033[31m',
    'RESET': '\033[0m',
}


class CustomLogger(logging.Logger):
    @staticmethod
    def format_message(level, color, message):
        timestamp = time.strftime('%H:%M:%S')
        return f"[{timestamp}] [{COLORS.get(color)}{level}{COLORS.get('RESET')}] -> {message}"

    def debug(self, message, *args, **kwargs):
        super().debug(self.format_message('DEBUG', 'MAGENTA', message), *args, **kwargs)

    def info(self, message, *args, **kwargs):
        super().info(self.format_message('INFO', 'BLUE', message), *args, **kwargs)

    def success(self, message, *args, **kwargs):
        super().info(self.format_message('SUCCESS', 'GREEN', message), *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        super().warning(self.format_message('WARNING', 'YELLOW', message), *args, **kwargs)

    def error(self, message, *args, **kwargs):
        super().error(self.format_message('ERROR', 'RED', message), *args, **kwargs)


logging.setLoggerClass(CustomLogger)
# noinspection PyTypeChecker
logger: CustomLogger = logging.getLogger("TurnstileAPIServer")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

# NOTE: 缓存清理默认间隔（秒），每隔此时间执行一次过期任务扫描
CLEANUP_INTERVAL_SECONDS = 60


class TurnstileAPIServer:

    def __init__(self, thread: int, proxy_support: bool, max_cache_age: int, debug: bool):
        self.app = Quart(__name__)
        self.debug = debug
        self.results = self._load_results()
        self.thread_count = thread
        self.proxy_support = proxy_support
        self.max_cache_age = max_cache_age
        self.browser_pool = asyncio.Queue()

        self._setup_routes()

    @staticmethod
    def _load_results():
        """从 results.json 加载历史结果。"""
        try:
            if os.path.exists("results.json"):
                with open("results.json", "r") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading results: {str(e)}. Starting with an empty results dictionary.")
        return {}

    def _save_results(self):
        """将结果持久化到 results.json。"""
        try:
            with open("results.json", "w") as result_file:
                json.dump(self.results, result_file, indent=4)
        except IOError as e:
            logger.error(f"Error saving results to file: {str(e)}")

    def _cleanup_expired_tasks(self):
        """删除超过 max_cache_age 的过期任务，返回被清理的数量。"""
        now = time.time()
        expired_keys = [
            task_id for task_id, data in self.results.items()
            if isinstance(data, dict) and now - data.get("created_at", now) > self.max_cache_age
        ]
        for key in expired_keys:
            del self.results[key]
        if expired_keys:
            self._save_results()
            logger.info(f"Cleaned up {len(expired_keys)} expired task(s)")
        return len(expired_keys)

    async def _periodic_cleanup(self):
        """后台协程：定期执行过期任务清理。"""
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            try:
                self._cleanup_expired_tasks()
            except Exception as e:
                logger.error(f"Error during periodic cleanup: {str(e)}")

    def _setup_routes(self) -> None:
        """注册路由和启动钩子。"""
        self.app.before_serving(self._startup)
        self.app.route('/turnstile', methods=['POST'])(self.process_turnstile)
        self.app.route('/result', methods=['GET'])(self.get_result)
        self.app.route('/')(self.index)

    async def _startup(self) -> None:
        """服务启动时初始化浏览器池并注册后台清理任务。"""
        logger.info("Starting browser initialization")
        try:
            await self._initialize_browser()
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise

        # NOTE: 启动时先清理一次历史过期数据，再启动定期清理协程
        self._cleanup_expired_tasks()
        asyncio.create_task(self._periodic_cleanup())
        logger.info(f"Periodic cache cleanup enabled (max_cache_age={self.max_cache_age}s)")

    async def _initialize_browser(self) -> None:
        """初始化 camoufox 浏览器池（headless 模式）。"""
        camoufox = AsyncCamoufox(headless=True)

        for i in range(self.thread_count):
            browser = await camoufox.start()
            await self.browser_pool.put((i + 1, browser))

            if self.debug:
                logger.success(f"Browser {i + 1} initialized successfully")

        logger.success(f"Browser pool initialized with {self.browser_pool.qsize()} browsers")

    async def _solve_turnstile(self, cf_selector: str, task_id: str, url: str, sitekey: str, action: str = None,
                               cdata: str = None):
        """执行 Turnstile 验证码求解。"""
        index, browser = await self.browser_pool.get()

        # NOTE: 根据 proxy_support 配置决定是否使用代理
        if self.proxy_support:
            proxy_file_path = os.path.join(os.getcwd(), "proxies.txt")

            with open(proxy_file_path) as proxy_file:
                proxies = [line.strip() for line in proxy_file if line.strip()]

            proxy = random.choice(proxies) if proxies else None

            if proxy:
                parts = proxy.split(':')
                if len(parts) == 3:
                    context = await browser.new_context(proxy={"server": f"{proxy}"})
                elif len(parts) == 5:
                    proxy_scheme, proxy_ip, proxy_port, proxy_user, proxy_pass = parts
                    context = await browser.new_context(
                        proxy={"server": f"{proxy_scheme}://{proxy_ip}:{proxy_port}", "username": proxy_user,
                               "password": proxy_pass})
                else:
                    raise ValueError("Invalid proxy format")
            else:
                context = await browser.new_context()
        else:
            context = await browser.new_context()

        page = await context.new_page()

        start_time = time.time()

        # ── 构造注入页面 ──────────────────────────────────────────────────────────
        # data-* 属性按需拼接，避免空值污染
        extra_attrs = ""
        if action:
            extra_attrs += f' data-action="{action}"'
        if cdata:
            extra_attrs += f' data-cdata="{cdata}"'

        injected_html = f"""<!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <!--
            仅保留 Turnstile api.js。
            浏览器仍处于目标 URL 的 Origin，满足 Cloudflare 域名校验。
          -->
          <script src="https://challenges.cloudflare.com/turnstile/v0/api.js"
                  async defer></script>
        </head>
        <body>
          <div class="cf-turnstile"
               data-sitekey="{sitekey}"{extra_attrs}
               style="width:70px">
          </div>
        </body>
        </html>"""

        # ── 路由拦截：只替换第一个主文档，其余请求（api.js 等）正常放行 ──────────
        intercepted = {"done": False}

        async def _intercept(route, req):
            # NOTE: 仅拦截一次主文档导航，其余资源（Cloudflare js、字体等）全部放行
            if not intercepted["done"] and req.resource_type == "document":
                intercepted["done"] = True
                if self.debug:
                    logger.debug(
                        f"Browser {index}: Intercepted document request → "
                        f"injecting Turnstile-only page | url={req.url}"
                    )
                await route.fulfill(
                    status=200,
                    content_type="text/html; charset=utf-8",
                    body=injected_html,
                )
            else:
                await route.continue_()

        await page.route("**/*", _intercept)

        try:

            if self.debug:
                logger.debug(
                    f"Browser {index}: Navigating to {url} "
                    f"(response will be replaced by injected HTML)"
                )

            # wait_until="commit" 表示拿到响应头即可，不等待页面资源全部加载完毕。
            # 配合路由拦截，浏览器几乎立即拿到我们的自定义 HTML。
            await page.goto(url, wait_until="commit")

            if self.debug:
                logger.debug(f"Browser {index}: Setting up Turnstile widget dimensions")

            await page.wait_for_selector('[name=cf-turnstile-response]', state="attached", timeout=30000)
            await page.eval_on_selector(f"{cf_selector}", "el => el.style.width = '70px'")

            if self.debug:
                logger.debug(f"Browser {index}: Starting Turnstile response retrieval loop")

            for attempt in range(30):
                try:
                    turnstile_check = await page.input_value("[name=cf-turnstile-response]", timeout=2000)
                    if turnstile_check == "":
                        if self.debug:
                            logger.debug(f"Browser {index}: Attempt {attempt} - No Turnstile response yet")
                        # 使用注入页面里固定的 .cf-turnstile，也兼容外部传入的 cf_selector
                        target = cf_selector if cf_selector else ".cf-turnstile"
                        await page.locator(target).click(timeout=5000)
                        await asyncio.sleep(0.5)
                    else:
                        elapsed_time = round(time.time() - start_time, 3)

                        logger.success(
                            f"Browser {index}: Successfully solved captcha - {COLORS.get('MAGENTA')}{turnstile_check[:10]}{COLORS.get('RESET')} in {COLORS.get('GREEN')}{elapsed_time}{COLORS.get('RESET')} Seconds")

                        self.results[task_id] = {
                            "status": "success",
                            "token": turnstile_check,
                            "elapsed_time": elapsed_time,
                            "created_at": self.results[task_id].get("created_at", time.time()),
                        }
                        self._save_results()
                        break
                except Exception as e:
                    logger.info(f"Exception occurred while trying to solve {e}")
                    pass

            # 循环结束仍未写入成功结果 → 标记失败
            result = self.results.get(task_id, {})
            if not isinstance(result, dict) or result.get("status") != "success":
                elapsed_time = round(time.time() - start_time, 3)
                self.results[task_id] = {
                    "status": "failed",
                    "error": "CAPTCHA_FAIL",
                    "elapsed_time": elapsed_time,
                    "created_at": result.get("created_at", time.time()) if isinstance(result, dict) else time.time(),
                }
                self._save_results()
                if self.debug:
                    logger.error(
                        f"Browser {index}: Error solving Turnstile in {COLORS.get('RED')}{elapsed_time}{COLORS.get('RESET')} Seconds")
        except Exception as e:
            elapsed_time = round(time.time() - start_time, 3)
            created_at = time.time()
            existing = self.results.get(task_id)
            if isinstance(existing, dict):
                created_at = existing.get("created_at", created_at)
            self.results[task_id] = {
                "status": "failed",
                "error": "CAPTCHA_FAIL",
                "elapsed_time": elapsed_time,
                "created_at": created_at,
            }
            self._save_results()
            if self.debug:
                logger.error(f"Browser {index}: Error solving Turnstile: {str(e)}")
        finally:
            if self.debug:
                logger.debug(f"Browser {index}: Clearing page state")

            await page.unroute("**/*", _intercept)  # 清理路由，防止内存泄漏

            await context.close()
            await self.browser_pool.put((index, browser))

    async def process_turnstile(self):
        """处理 /turnstile 端点请求，创建验证码求解任务。"""

        data = await request.get_json()
        url = data.get("url")
        cf_selector = data.get("cf_selector") or ".cf-turnstile"
        sitekey = data.get("sitekey")
        action = data.get("action")
        cdata = data.get("cdata")

        if not url or not sitekey:
            return jsonify({
                "status": "error",
                "error": "Both 'url' and 'sitekey' are required"
            }), 400

        task_id = str(uuid.uuid4())
        # NOTE: 初始化时记录 created_at，供过期清理使用
        self.results[task_id] = {"status": "pending", "created_at": time.time()}

        try:
            asyncio.create_task(
                self._solve_turnstile(cf_selector=cf_selector, task_id=task_id, url=url, sitekey=sitekey, action=action,
                                      cdata=cdata))

            if self.debug:
                logger.debug(f"Request completed with taskid {task_id}.")
            return jsonify({"status": "created", "task_id": task_id}), 202
        except Exception as e:
            logger.error(f"Unexpected error processing request: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    async def get_result(self):
        """查询任务结果，所有状态均返回统一 JSON 格式。"""
        task_id = request.args.get('id')

        if not task_id or task_id not in self.results:
            return jsonify({"status": "error", "error": "Invalid task ID"}), 404

        result = self.results[task_id]

        # NOTE: 兼容旧格式数据（非 dict 的历史遗留数据视为 pending）
        if not isinstance(result, dict):
            return jsonify({"status": "pending"}), 202

        status = result.get("status", "pending")

        if status == "pending":
            return jsonify({"status": "pending"}), 202
        elif status == "success":
            return jsonify({
                "status": "success",
                "data": {
                    "token": result.get("token"),
                    "elapsed_time": result.get("elapsed_time"),
                }
            }), 200
        else:
            # status == "failed"
            return jsonify({
                "status": "error",
                "error": result.get("error", "CAPTCHA_FAIL"),
                "elapsed_time": result.get("elapsed_time"),
            }), 500

    @staticmethod
    async def index():
        """提供 API 文档首页（读取 index.html）。"""
        html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="Turnstile API Server")

    parser.add_argument('--thread', type=int, default=1,
                        help='浏览器并发线程数（默认: 1）')
    parser.add_argument('--proxy', type=bool, default=False,
                        help='是否启用代理支持，从 proxies.txt 随机选择代理（默认: False）')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='API 监听地址（默认: 0.0.0.0）')
    parser.add_argument('--port', type=str, default='5000',
                        help='API 监听端口（默认: 5000）')
    parser.add_argument('--max_cache_age', type=int, default=3600,
                        help='任务缓存最大存活时长，单位秒（默认: 3600）')
    parser.add_argument('--debug', type=bool, default=False,
                        help='启用调试日志（默认: False）')
    return parser.parse_args()


def create_app(thread: int, proxy_support: bool, max_cache_age: int, debug: bool) -> Quart:
    """创建并返回 Quart 应用实例。"""
    server = TurnstileAPIServer(thread=thread, proxy_support=proxy_support, max_cache_age=max_cache_age, debug=debug)
    return server.app


if __name__ == '__main__':
    args = parse_args()
    app = create_app(thread=args.thread, proxy_support=args.proxy, max_cache_age=args.max_cache_age, debug=args.debug)
    app.run(host=args.host, port=int(args.port))
