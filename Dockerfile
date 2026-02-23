FROM python:3.12-slim

# NOTE: 设置非交互式安装 + 时区可通过环境变量 TZ 配置
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    TZ=UTC

WORKDIR /app

# NOTE: camoufox 运行时依赖的系统库（GTK3、音视频编解码、字体渲染等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxss1 \
    libxcursor1 \
    libxi6 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# NOTE: 预下载 camoufox 浏览器二进制，避免运行时下载
RUN python -m camoufox fetch

COPY api_solver.py .
COPY proxies.txt .

EXPOSE 5000

# NOTE: 默认参数可通过 docker run 的 CMD 追加参数覆盖
ENTRYPOINT ["python", "api_solver.py"]
CMD ["--host", "0.0.0.0", "--port", "5000"]
