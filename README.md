# OG Miner API

The backend service for **OG Miner**, a high-performance URL metadata extraction API.
Built with **FastAPI**, **Playwright**, and **Redis**.

## 🚀 Features

-   **Metadata Extraction**: Retrieves OpenGraph, Twitter Cards, JSON-LD, and oEmbed data.
-   **Headless Browser**: Integrated Playwright support to render JavaScript-heavy websites (SPAs).
-   **High Performance**:
    -   **Redis Caching**: Caches results to serve repeat requests in <10ms.
    -   **Async I/O**: Fully asynchronous architecture using `httpx` and `uvicorn`.
-   **Security**:
    -   **SSRF Protection**: Validators to prevent internal network scanning.
    -   **Rate Limiting**: Built-in rate limiting using `slowapi`.
    -   **API Key Auth**: Validates requests via `X-RapidAPI-Proxy-Secret`.

## 🛠️ Tech Stack

-   **Language**: Python 3.10+
-   **Framework**: FastAPI
-   **Browser**: Playwright (Chromium)
-   **Cache**: Redis
-   **Task Runner**: Uvicorn

## 📦 Getting Started

### Prerequisites

-   Python 3.10+
-   Redis (running locally or via Docker)
-   Google Chrome (for Playwright)

### Local Development

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/og-miner.git
    cd og-miner/og-miner-api
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

4.  **Configure Environment**:
    Create a `.env` file based on `.env.example`:
    ```ini
    PROJECT_NAME="og-miner"
    VERSION="1.0.0"
    REDIS_URL="redis://localhost:6379/0"
    SECRET_KEY="your-secret-key"
    X_RAPIDAPI_PROXY_SECRET="your-rapidapi-secret"
    LOG_LEVEL="INFO"
    ```

5.  **Run the Server**:
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be available at `http://localhost:8000`.

### Docker Development

Run the entire stack (API + Redis) with Docker Compose:

```bash
docker-compose up --build
```

## 🟣 Deployment

### Heroku (Recommended)

1.  **Login**:
    ```bash
    heroku login
    heroku container:login
    ```

2.  **Create App & Add Redis**:
    ```bash
    heroku create og-miner-api
    heroku addons:create heroku-redis:mini -a og-miner-api
    ```

3.  **Set Secrets**:
    ```bash
    heroku config:set SECRET_KEY="your-secret" X_RAPIDAPI_PROXY_SECRET="your-key" -a og-miner-api
    ```

4.  **Deploy**:
    ```bash
    heroku container:push web -a og-miner-api
    heroku container:release web -a og-miner-api
    ```

## 📚 API Reference

**POST** `/v1/extract`

**Body**:
```json
{
  "url": "https://example.com",
  "enable_javascript": false,
  "force_refresh": false
}
```

**Response**:
```json
{
  "meta": { "url": "...", "latency_ms": 120 },
  "data": { "title": "Example", "image": "..." }
}
```

## 🧪 Testing

Run strict tests using `pytest`:

```bash
pytest
```

---

&copy; 2026 OG Miner Backend.
