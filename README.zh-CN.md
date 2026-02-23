<div align="center">

  <h2 align="center">Cloudflare - Turnstile Solver</h2>
  <p align="center">
基于 Python 的 Cloudflare Turnstile 验证码解析工具，使用 Camoufox 浏览器引擎。支持多线程并发、RESTful API、自动缓存清理、代理支持，以及多平台 Docker 部署（amd64/arm64）。
    <br />
    <br />
    <a href="./README.md">📖 English</a>
    ·
    <a href="https://github.com/taozhiyu/Turnstile-Solver/issues">⚠️ 反馈 Bug</a>
    ·
    <a href="https://github.com/taozhiyu/Turnstile-Solver/issues">💡 功能请求</a>
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/LICENSE-CC%20BY%20NC%204.0-red?style=for-the-badge"/>
    <img src="https://img.shields.io/github/issues/taozhiyu/Turnstile-Solver?style=for-the-badge&color=red"/>
  </p>
</div>

---

### 🎁 捐赠

- **USDT (Arbitrum One)**: `0x31e16EA02df219562A25636f666fE9038A809105`
- **BTC**: `bc1qh423a705lqlpx5ku2ez8d6c3qvgpwwu5vm004y`

> [!NOTE]
> 以下捐赠地址属于本项目的 **原作者** ([Theyka](https://github.com/Theyka))。如果你觉得这个项目有帮助，请考虑支持他！

- **USDT (TRC20)**: `TWXNQCnJESt6gxNMX5oHKwQzq4gsbdLNRh`
- **USDT (Arbitrum One)**: `0xd8fd1e91c8af318a74a0810505f60ccca4ca0f8c`
- **BTC**: `13iiMaYFpCfNdcyFycSdSVmD2yfQciD7AQ`
- **LTC**: `LSrLQe2dfpDhGgVvDTRwW72fSyC9VsXp9g`

---

### ❗ 免责声明

- 对于使用本项目可能导致的任何后果（如 API 被封锁、IP 被禁止等），作者概不负责。
- 本项目最初为个人兴趣和自用而开发。如果你希望看到更多更新，请给仓库加 Star 并在[此处](https://github.com/taozhiyu/Turnstile-Solver/issues/)提交 Issue。

---

### ⚙️ 安装指南

1. **确保系统已安装 Python 3.8+**。

2. **创建虚拟环境**：

   ```bash
   python -m venv venv
   ```

3. **激活虚拟环境**：
   - **Windows**：
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux**：
     ```bash
     source venv/bin/activate
     ```

4. **安装依赖**：

   ```bash
   pip install -r requirements.txt
   ```

5. **启动求解器**：
   - 运行脚本（查看 [🔧 命令行参数](#-命令行参数) 了解配置项）：
     ```bash
     python api_solver.py
     ```

---

### 🔧 命令行参数

| 参数              | 默认值    | 类型      | 说明                                            |
| ----------------- | --------- | --------- | ----------------------------------------------- |
| `--thread`        | `1`       | `integer` | 并发浏览器线程数。                              |
| `--proxy`         | `False`   | `boolean` | 启用代理支持，从 `proxies.txt` 中随机选择代理。 |
| `--host`          | `0.0.0.0` | `string`  | API 服务监听地址。                              |
| `--port`          | `5000`    | `integer` | API 服务监听端口。                              |
| `--max_cache_age` | `3600`    | `integer` | 任务缓存最大存活时长（秒），超时后自动清理。    |
| `--debug`         | `False`   | `boolean` | 启用调试模式，输出详细日志。                    |

---

### 🐳 Docker 部署

#### 本地构建

```bash
docker build -t turnstile-solver .
docker run -d -p 5000:5000 --name turnstile_solver turnstile-solver
```


#### 使用 GitHub Container Registry

尚未实现（发布），请优先自行构建或安装

多平台镜像（amd64 和 arm64）通过 GitHub Actions 自动构建并发布。

```bash
docker pull ghcr.io/taozhiyu/turnstile-solver:latest
```

#### 启动容器

```bash
docker run -d \
  -p 5000:5000 \
  -e TZ=Asia/Shanghai \
  --name turnstile_solver \
  ghcr.io/taozhiyu/turnstile-solver:latest
```

可以在镜像名称后追加[命令行参数](#-命令行参数)：

```bash
docker run -d \
  -p 5000:5000 \
  -e TZ=Asia/Shanghai \
  --name turnstile_solver \
  ghcr.io/taozhiyu/turnstile-solver:latest \
  --host 0.0.0.0 --port 5000 --thread 2 --max_cache_age 7200
```

---

### 📡 API 文档

#### 创建求解任务

```http
POST /turnstile
Content-Type: application/json
```

**请求体**：

```json
{
  "url": "https://example.com",
  "sitekey": "0x4AAAAAAA",
  "action": "login",
  "cdata": "optional-custom-data"
}
```

| 参数          | 类型   | 说明                                                    | 必填 |
| ------------- | ------ | ------------------------------------------------------- | ---- |
| `url`         | string | 包含 CAPTCHA 的目标页面 URL（如 `https://example.com`） | 是   |
| `sitekey`     | string | CAPTCHA 的站点密钥（如 `0x4AAAAAAA`）                   | 是   |
| `action`      | string | 求解过程中触发的操作，如 `login`                        | 否   |
| `cdata`       | string | 自定义数据，用于附加 CAPTCHA 参数                       | 否   |
| `cf_selector` | string | Turnstile 组件的 CSS 选择器（默认：`.cf-turnstile`）    | 否   |

**响应**（`202 Created`）：

```json
{
  "status": "created",
  "task_id": "d2cbb257-9c37-4f9c-9bc7-1eaee72d96a8"
}
```

---

#### 查询结果

```http
GET /result?id=<task_id>
```

| 参数 | 类型   | 说明                                    | 必填 |
| ---- | ------ | --------------------------------------- | ---- |
| `id` | string | 由 `/turnstile` 接口返回的唯一任务 ID。 | 是   |

**响应 — 处理中**（`202`）：

```json
{
  "status": "pending"
}
```

**响应 — 成功**（`200`）：

```json
{
  "status": "success",
  "data": {
    "token": "0.KBtT-r...",
    "elapsed_time": 7.625
  }
}
```

**响应 — 失败**（`500`）：

```json
{
  "status": "error",
  "error": "CAPTCHA_FAIL",
  "elapsed_time": 30.123
}
```

---

### 📜 致谢

灵感来源于 [Turnaround](https://github.com/Body-Alhoha/turnaround)
原始代码作者 [Theyka](https://github.com/Theyka/Turnstile-Solver)
修改者 [Sexfrance](https://github.com/sexfrance)
优化重构 [taozhiyu](https://github.com/taozhiyu)