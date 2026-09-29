import time
import json
import logging
from typing import Set
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, WebSocket
from app.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION

logger = logging.getLogger("telephony_observability")
logger.setLevel(logging.INFO)

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        endpoint = request.url.path
        method = request.method

        response = await call_next(request)
        duration = time.time() - start_time

        # Update Prometheus metrics
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        HTTP_REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)

        # Output structured JSON log
        log_entry = {
            "timestamp": time.time(),
            "method": method,
            "path": endpoint,
            "status_code": response.status_code,
            "latency_ms": round(duration * 1000, 2),
            "client_ip": request.client.host if request.client else "unknown"
        }
        logger.info(json.dumps(log_entry))
        return response

class WebSocketTelemetryHub:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, event_data: dict):
        dead_connections = set()
        for conn in self.active_connections:
            try:
                await conn.send_json(event_data)
            except Exception:
                dead_connections.add(conn)
        self.active_connections.difference_update(dead_connections)

telemetry_hub = WebSocketTelemetryHub()
