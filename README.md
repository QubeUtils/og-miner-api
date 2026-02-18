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
-   **Anti-Blocking**:
    -   **Proxy Rotation**: Automatically rotates free proxies (or uses your paid proxy) to avoid IP bans.
    -   **Geo-Targeting (Beta)**: Supports `country` parameter for region-specific scraping (requires `PROXY_URL` to be set).
    -   **BYOP (Pro)**: Bring Your Own Proxy. Pass a `proxy` URL per request to use your own premium proxies.
    -   **Cookies**: Supports passing session cookies for authenticated scraping.
-   **Developer Experience**:
    -   **Batch Processing**: Process up to 50 URLs in parallel.
    -   **Image Proxy**: Securely resize and cache external images (WebP format).
    -   **Screenshots**: Capture full-page or viewport screenshots.

## 🛠️ Tech Stack

### Core
-   **Language**: Python 3.10+
-   **Framework**: FastAPI (High-performance web framework)
-   **Server**: Uvicorn (ASGI server)

### Extraction Engine
-   **Headless Browser**: Playwright (Chromium) for SPA/JS rendering.
-   **HTTP Client**: HTTPX (Async HTTP client).
-   **Parsers**:
    -   `extruct`: For Schema.org (JSON-LD, Microdata) & OpenGraph.
    -   `beautifulsoup4`: For fallback meta tag parsing.

### Infrastructure & Data
-   **Caching**: Redis (Key-value store for <10ms response times).
-   **Rate Limiting**: `slowapi` (In-memory or Redis-backed).
-   **Task Queue**: `BackgroundTasks` (FastAPI native) for async batch processing.

## 📂 Project Structure

```text
og-miner-api/
├── app/
│   ├── api/
│   │   ├── v1/             # Route handlers (Extract, Batch, Image, Screenshot)
│   │   └── dependencies.py # Auth & Rate Limiting dependencies
│   ├── core/
│   │   ├── config.py       # Environment configuration
│   │   └── security.py     # SSRF protection & validation
│   ├── schemas/            # Pydantic models (Request/Response schemas)
│   ├── services/           # Core Business Logic
│   │   ├── extract.py      # Main extraction orchestrator
│   │   ├── fetcher.py      # Async HTTP fetcher
│   │   ├── headless.py     # Playwright manager
│   │   ├── image_proxy.py  # Image resizing & proxying
│   │   └── parser.py       # HTML parsing logic
│   └── main.py             # App entrypoint
├── tests/                  # Unit tests (Pytest)
├── Dockerfile              # Docker build
└── requirements.txt        # Python dependencies
```

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
    PROXY_URL="" # Optional: "http://user:pass@host:port" (Leave empty for free proxy rotation)
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

### 1. Extract Metadata
**POST** `/v1/extract`

Extracts metadata from a single URL.

**Body**:
```json
{
  "url": "https://netflix.com/title/80057281",
  "enable_javascript": false,
  "force_refresh": false,
  "country": "US",          // Optional: Geo-target (Beta, requires paid PROXY_URL)
  "proxy": "http://user:pass@host:port", // Optional: BYOP (Pro)
  "cookies": {              // Optional: Authenticated scraping
    "netflixId": "v=2&ct=..."
  }
}
```

### 2. Batch Extraction
**POST** `/v1/batch/extract`

Process up to 50 URLs in parallel.

**Body**:
```json
{
  "urls": ["https://google.com", "https://apple.com"],
  "enable_javascript": false
}
```

### 3. Image Proxy
**GET** `/v1/image`

Securely proxies, resizes, and caches images.

**Query Parameters**:
- `url`: The image URL (required).
- `width`: Target width (optional, e.g., `200`).
- `height`: Target height (optional).

**Headers**:
- `X-RapidAPI-Proxy-Secret`: Your secret key (required).

**Example**:
`GET /v1/image?url=https://example.com/logo.png&width=300`

### 4. Take Screenshot
**POST** `/v1/screenshot`

Captures a screenshot of the page.

**Body**:
```json
{
  "url": "https://example.com",
  "full_page": false,
  "dark_mode": true,
  "delay": 2000
}
```

## 🧪 Testing

The project maintains a strict test suite using `pytest`, covering:
-   **Unit Tests**: Individual service logic (Extract, Batch, Image Proxy).
-   **Security**: Verification of SSRF protection and Proxy validation.
-   **Integration**: Mocked integration with Playwright and Redis.

Run the full suite:

```bash
pytest
```

---

&copy; 2026 OG Miner Backend.
