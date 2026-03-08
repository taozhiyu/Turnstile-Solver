<div align="center">

  <h2 align="center">Cloudflare - Turnstile Solver</h2>
  <p align="center">
A Python-based Turnstile CAPTCHA solver powered by the Camoufox browser engine. Features multi-threaded execution, RESTful API, automatic cache cleanup, proxy support, and multi-platform Docker deployment (amd64/arm64).
    <br />
    <br />
    <a href="./README.zh-CN.md"> 📖 中文文档</a>
    ·
    <a href="https://github.com/taozhiyu/Turnstile-Solver/issues">⚠️ Report Bug</a>
    ·
    <a href="https://github.com/taozhiyu/Turnstile-Solver/issues">💡 Request Feature</a>
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/LICENSE-CC%20BY%20NC%204.0-red?style=for-the-badge"/>
    <img src="https://img.shields.io/github/issues/taozhiyu/Turnstile-Solver?style=for-the-badge&color=red"/>
  </p>
</div>

---

### 🎁 Donation
- **USDT (Arbitrum One)**: `0x31e16EA02df219562A25636f666fE9038A809105`
- **BTC**: `bc1qh423a705lqlpx5ku2ez8d6c3qvgpwwu5vm004y`

> [!NOTE]
> The donation addresses below belong to the **original author** of this project ([Theyka](https://github.com/Theyka)). If you find this project useful, please consider supporting them!
> 
> - **USDT (TRC20)**: `TWXNQCnJESt6gxNMX5oHKwQzq4gsbdLNRh`
> - **USDT (Arbitrum One)**: `0xd8fd1e91c8af318a74a0810505f60ccca4ca0f8c`
> - **BTC**: `13iiMaYFpCfNdcyFycSdSVmD2yfQciD7AQ`
> - **LTC**: `LSrLQe2dfpDhGgVvDTRwW72fSyC9VsXp9g`

---

### ❗ Disclaimers

- I am not responsible for anything that may happen, such as API Blocking, IP ban, etc.
- This was a quick project that was made for fun and personal use if you want to see further updates, star the repo & create an "issue" [here](https://github.com/taozhiyu/Turnstile-Solver/issues/)

---

### ⚙️ Installation Instructions

1. **Ensure Python 3.8+ is installed** on your system.

2. **Create a Python virtual environment**:

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - On **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - On **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

4. **Install required dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

5. **Start the solver**:
   - Run the script (Check [🔧 Command line arguments](#-command-line-arguments) for configuration):
     ```bash
     python api_solver.py
     ```

---

### 🔧 Command line arguments

| Parameter         | Default   | Type      | Description                                                           |
|-------------------|-----------|-----------|-----------------------------------------------------------------------|
| `--thread`        | `1`       | `integer` | Number of concurrent browser threads for solving CAPTCHAs.            |
| `--proxy`         | `False`   | `boolean` | Enable proxy support, randomly selects a proxy from `proxies.txt`.    |
| `--host`          | `0.0.0.0` | `string`  | IP address the API server listens on.                                 |
| `--port`          | `5000`    | `integer` | Port the API server listens on.                                       |
| `--max_cache_age` | `3600`    | `integer` | Maximum age (in seconds) for cached task results before auto-cleanup. |
| `--debug`         | `False`   | `boolean` | Enable debug mode for verbose logging.                                |

---

### 🐳 Docker

#### Using GitHub Container Registry

Multi-platform images (amd64 & arm64) are automatically built and published via GitHub Actions.

```bash
docker pull ghcr.io/taozhiyu/turnstile-solver:latest
```

#### Running the Container

```bash
docker run -d \
  -p 5000:5000 \
  -e TZ=Asia/Shanghai \
  --name turnstile_solver \
  ghcr.io/taozhiyu/turnstile-solver:latest
```

You can append any [command line arguments](#-command-line-arguments) after the image name:

```bash
docker run -d \
  -p 5000:5000 \
  -e TZ=Asia/Shanghai \
  --name turnstile_solver \
  ghcr.io/taozhiyu/turnstile-solver:latest \
  --host 0.0.0.0 --port 5000 --thread 2 --max_cache_age 7200
```


#### Building Locally

```bash
docker build -t turnstile-solver .
docker run -d -p 5000:5000 --name turnstile_solver turnstile-solver
```

---

### 📡 API Documentation

#### Create a Solve Task

```http
POST /turnstile
Content-Type: application/json
```

**Request Body**:

```json
{
  "url": "https://example.com",
  "sitekey": "0x4AAAAAAA",
  "action": "login",
  "cdata": "optional-custom-data"
}
```

| Parameter     | Type   | Description                                                             | Required |
|---------------|--------|-------------------------------------------------------------------------|----------|
| `url`         | string | The target URL containing the CAPTCHA. (e.g., `https://example.com`)    | Yes      |
| `sitekey`     | string | The site key for the CAPTCHA to be solved. (e.g., `0x4AAAAAAA`)         | Yes      |
| `action`      | string | Action to trigger during CAPTCHA solving, e.g., `login`                 | No       |
| `cdata`       | string | Custom data for additional CAPTCHA parameters.                          | No       |
| `cf_selector` | string | Custom CSS selector for the Turnstile widget (default: `.cf-turnstile`) | No       |

**Response** (`202 Created`):

```json
{
  "status": "created",
  "task_id": "d2cbb257-9c37-4f9c-9bc7-1eaee72d96a8"
}
```

---

#### Get Result

```http
GET /result?id=<task_id>
```

| Parameter | Type   | Description                                                | Required |
|-----------|--------|------------------------------------------------------------|----------|
| `id`      | string | The unique task ID returned from the `/turnstile` request. | Yes      |

**Response — Pending** (`202`):

```json
{
  "status": "pending"
}
```

**Response — Success** (`200`):

```json
{
  "status": "success",
  "data": {
    "token": "0.KBtT-r...",
    "elapsed_time": 7.625
  }
}
```

**Response — Failed** (`500`):

```json
{
  "status": "error",
  "error": "CAPTCHA_FAIL",
  "elapsed_time": 30.123
}
```

---

### 📜 Credits

Inspired by [Turnaround](https://github.com/Body-Alhoha/turnaround)
Original code by [Theyka](https://github.com/Theyka/Turnstile-Solver)
Changes by [Sexfrance](https://github.com/sexfrance)
Re-built by [taozhiyu](https://github.com/taozhiyu)