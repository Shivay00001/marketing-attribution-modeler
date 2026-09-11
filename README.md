# Marketing Attribution Modeler

An enterprise-grade solution engineered for high performance.

![Language](https://img.shields.io/badge/Language-Python-blue)
![Framework](https://img.shields.io/badge/Framework-FastAPI-009688)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-Custom%20Commercial-orange)

## 🚀 Overview

Welcome to the **Marketing Attribution Modeler** repository. This project is built to deliver a robust and scalable solution tailored to modern development standards.

At its core, the service is a **FastAPI-based inference API** designed to serve marketing attribution predictions over HTTP. It exposes a lightweight, containerized REST interface that accepts feature payloads and returns attribution class predictions with confidence scores — intended to be the serving layer for multi-touch attribution models (e.g., classifying which marketing channel/touchpoint receives credit for a conversion).

## ✨ Features

- **High Performance:** Optimized for speed and efficiency.
- **Scalable Architecture:** Designed to grow with your needs.
- **Clean Codebase:** Follows best practices and industry standards.
- **Secure by Default:** Engineered with security in mind.
- **RESTful Inference API:** FastAPI-powered endpoints with automatic interactive docs (`/docs`).
- **Container-Ready:** Ships with a `Dockerfile` for one-command deployment anywhere.
- **ML-Ready Dependency Stack:** Includes `numpy`, `pandas`, `scikit-learn`, and `torch` for building and serving attribution models.

## 🏗️ Architecture / How It Works

The current implementation (`main.py`) is a minimal FastAPI application acting as the serving scaffold for the attribution model:

```
┌─────────────┐      HTTP POST /predict      ┌──────────────────────────┐
│   Client    │ ───────────────────────────▶ │  FastAPI App (uvicorn)   │
│ (dashboard, │                              │                          │
│  CRM, etc.) │ ◀─────────────────────────── │  /predict endpoint:      │
└─────────────┘   {"class_id", "confidence"} │  - accepts JSON payload  │
                                             │  - runs inference        │
       │                                     │  - returns class + score │
       │ GET /                               └──────────────────────────┘
       ▼                                       Model version: v2.4.1
 {"status": "operational"}
```

**Endpoints:**

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| `GET` | `/` | Health check | `{"status": "operational", "model_version": "v2.4.1"}` |
| `POST` | `/predict` | Attribution inference | `{"class_id": <int>, "confidence": <float>}` |

**Request flow:**
1. Client sends a JSON payload of marketing touchpoint features to `/predict`.
2. The endpoint generates a 128-dimensional inference vector (`numpy`) and selects the argmax as the predicted attribution class (e.g., channel index).
3. The predicted `class_id` and its `confidence` score are returned as JSON.

> ⚠️ **Note:** The current `/predict` implementation uses a *simulated* inference stub (`np.random.rand(128)`). A trained attribution model (sklearn/PyTorch — both already in `requirements.txt`) is intended to be loaded and swapped in here.

## 🛠️ Prerequisites

Ensure you have the following installed in your environment before proceeding:
- **Python 3.9+**
- **pip** (Python package manager)
- **Docker** (optional, for containerized deployment)
- Standard development tools

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Shivay00001/marketing-attribution-modeler.git
   ```
2. Navigate to the project directory:
   ```bash
   cd marketing-attribution-modeler
   ```
3. (Recommended) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Usage

### Local (without Docker)

Start the API server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then test it:

```bash
# Health check
curl http://localhost:8000/

# Prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"touchpoints": ["paid_search", "email", "organic_social"], "days_to_conversion": 4}'
```

Interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs`.

## 🐳 Running with Docker

The repository includes a `Dockerfile` (Python 3.9-slim base) so the service runs identically on any laptop or server.

### Option 1: Docker CLI

```bash
# Build the image
docker build -t marketing-attribution-modeler .

# Run the container (exposes the API on port 8000)
docker run -p 8000:8000 marketing-attribution-modeler
```

The API will be available at `http://localhost:8000` (docs at `http://localhost:8000/docs`).

### Option 2: Docker Compose

If you prefer `docker-compose`, create a `docker-compose.yml` (not currently included in the repo):

```yaml
version: "3.9"
services:
  api:
    build: .
    ports:
      - "8000:8000"
```

Then run:

```bash
docker-compose up --build
```

> Note: The `Dockerfile` does not specify an `--port`, so uvicorn defaults to port `8000` inside the container — make sure your port mapping (`-p 8000:8000`) matches.

## 🔍 Workability Assessment

An honest evaluation of the repository's current state:

**What works:**
- ✅ The FastAPI app starts and runs correctly; both endpoints (`/` and `/predict`) are functional.
- ✅ The Dockerfile is valid and will build/run the service as-is.
- ✅ The dependency set (`fastapi`, `uvicorn`, `numpy`, `pandas`, `scikit-learn`, `torch`) is appropriate for a real ML attribution service.
- ✅ Security hygiene is good — `.gitignore` properly excludes secrets, credentials, and environment files.

**What is missing / not production-ready:**
- ❌ **No actual trained model.** `/predict` returns random numbers (`np.random.rand(128)`), not real attribution predictions. It is a placeholder stub.
- ❌ **No model training code, datasets, or serialized model artifacts** (e.g., `.pkl`/`.pt` files) are present.
- ❌ **No input validation** — the payload is an untyped `dict`; malformed requests are not handled (Pydantic schemas should be added).
- ❌ **No tests, CI/CD, or logging/monitoring** configuration.
- ❌ **No `docker-compose.yml`** (instructions above provide one you can add).
- ⚠️ **License badge mismatch** — the original badge said MIT, but the actual `LICENSE` is a custom commercial license with revenue-sharing terms (corrected above).
- ⚠️ **Heavy dependencies** — `torch` makes the Docker image large (~several GB) despite not being used yet; consider pinning versions and trimming until a real model requires it.

**Verdict:** This is a **well-structured skeleton/scaffold** — a solid foundation for an attribution inference API — but it is **not production-ready** in its current form. To make it production-viable: integrate a trained attribution model (e.g., Markov chains, Shapley values, or an ML classifier), add Pydantic request/response schemas, write tests, pin dependency versions, and add observability.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page. Please note the licensing terms below before contributing or using the code commercially.

## 📝 License

This project is licensed under the **VisionQuantech Custom Commercial License** (see `LICENSE`):

- **Non-financial / non-earning use:** Free for personal and educational purposes.
- **Personal earning use:** Requires a 15–30% revenue share on earnings generated from the Software.
- **Business / enterprise use:** Requires a separate commercial license — contact **visionquantech@proton.me**.

Copyright © 2026 Shivay00001 / VisionQuantech. All rights reserved.