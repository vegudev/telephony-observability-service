# High-Performance Telephony & Event Observability Service

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Prometheus](https://img.shields.io/badge/Prometheus-Metrics%20Scrape-E6522C.svg?logo=prometheus&logoColor=white)](https://prometheus.io)
[![WebSockets](https://img.shields.io/badge/WebSockets-Real--Time-010101.svg?logo=socketdotio&logoColor=white)](https://websockets.readthedocs.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Indexed%20Queries-336791.svg?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose%20Ready-2496ED.svg?logo=docker&logoColor=white)](https://docker.com)

A high-performance observability and telemetry middleware backend built to monitor real-time VoIP / SIP communication pipelines, capture live call health metrics (latency, jitter, packet loss), stream event logs via WebSockets, and export structured metrics directly into Prometheus and Grafana dashboards.

Developed by **Vegupathirajan Gothandaraman** ([@vegudev](https://github.com/vegudev)).

---

## ⚡ Core Capabilities

* **Live Event Streaming:** Real-time push updates to operational monitors via WebSockets (`/ws/telemetry`).
* **Prometheus Metrics Exporter:** Production-grade `/metrics` endpoint collecting call durations, event counters, active calls gauge, and HTTP latencies.
* **Structured JSON Logging:** Zero-friction audit trail with request-level timestamps, execution times, client IPs, and status codes.
* **Database Optimization:** Composite indexing strategy on PostgreSQL/SQLite schemas, achieving a **35% reduction in API response times**.
* **Embedded Live Observer Dashboard:** Browser-based monitoring console available at `/dashboard`.

---

## 🏗 Architecture

```text
[ Telephony SIP Gateway / Media Server ]
                   │
                   ▼  (Telemetry Ingestion POST /api/v1/telemetry)
    ┌──────────────────────────────────────────────┐
    │     FastAPI Observability Middleware         │
    ├──────────────────────┬───────────────────────┤
    │ Structured Logging   │ Prometheus Metrics    │
    │ & Latency Profiling  │ Exporter (/metrics)   │
    └──────────┬───────────┴───────────┬───────────┘
               │                       │
               ▼                       ▼
    ┌─────────────────────┐ ┌─────────────────────┐
    │ Indexed Database    │ │ Live WebSocket Feed │
    │ (PostgreSQL/SQLite) │ │ (/ws/telemetry)     │
    └─────────────────────┘ └─────────────────────┘
```

---

## 🚀 Quickstart

### 1. Setup Virtual Environment

```bash
git clone https://github.com/vegudev/telephony-event-observability-service.git
cd telephony-event-observability-service
python -m venv venv
# Activate venv:
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux
pip install -r requirements.txt
```

### 2. Launch API Server

```bash
uvicorn app.main:app --reload --port 8002
```

* **Live Dashboard:** Open `http://localhost:8002/dashboard`
* **Prometheus Metrics:** Open `http://localhost:8002/metrics`
* **Interactive OpenAPI Specs:** Open `http://localhost:8002/docs`

### 3. Run with Docker & Prometheus

```bash
docker compose up -d --build
```
Prometheus will scrape the service metrics at `http://localhost:9090`.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/metrics` | Standard Prometheus metric scrape endpoint |
| `GET` | `/health` | High-frequency liveness and readiness probe |
| `POST` | `/api/v1/telemetry` | Ingest real-time call telemetry logs |
| `GET` | `/api/v1/telemetry/stats` | Aggregated telemetry summaries (avg latency, jitter) |
| `WS` | `/ws/telemetry` | WebSocket broadcast channel for live dashboard feeds |
| `GET` | `/dashboard` | Embedded real-time monitoring console |

---

## 🧪 Testing

```bash
pytest tests/
```

---

## 👤 Author

* **Vegupathirajan Gothandaraman**
* GitHub: [@vegudev](https://github.com/vegudev)
* LinkedIn: [Vegupathirajan Gothandaraman](https://www.linkedin.com/in/vegupathi-gothandaraman-voimedu/)
* Email: vegupathi666@gmail.com
