import time
from typing import Optional
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import SessionLocal, init_db, TelemetryLog
from app.metrics import (
    TELEPHONY_EVENTS_TOTAL,
    CALL_LATENCY_HISTOGRAM,
    ACTIVE_CALLS_GAUGE,
    get_metrics_payload
)
from app.middleware import StructuredLoggingMiddleware, telemetry_hub

init_db()

app = FastAPI(
    title="High-Performance Telephony & Event Observability Service",
    version="1.0.0",
    description="Real-time call telemetry monitoring, Prometheus metrics exporter, and event stream observability pipeline."
)

app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TelemetryPayload(BaseModel):
    call_sid: str
    sip_status: Optional[str] = "200 OK"
    event_type: str  # CALL_START, MEDIA_STREAMING, SIP_BYE, PACKET_DROP
    latency_ms: float = 0.0
    jitter_ms: float = 0.0
    packet_loss_pct: float = 0.0
    extra_data: Optional[dict] = None

@app.get("/metrics")
def metrics():
    data, content_type = get_metrics_payload()
    return Response(content=data, media_type=content_type)

@app.get("/health")
def health():
    return {"status": "UP", "timestamp": time.time()}

@app.post("/api/v1/telemetry")
async def ingest_telemetry(payload: TelemetryPayload, db: Session = Depends(get_db)):
    # 1. Update Prometheus metrics
    TELEPHONY_EVENTS_TOTAL.labels(
        event_type=payload.event_type,
        status=payload.sip_status or "unknown"
    ).inc()

    CALL_LATENCY_HISTOGRAM.observe(payload.latency_ms / 1000.0)

    if payload.event_type == "CALL_START":
        ACTIVE_CALLS_GAUGE.inc()
    elif payload.event_type in ["CALL_END", "SIP_BYE"]:
        ACTIVE_CALLS_GAUGE.dec()

    # 2. Persist in database
    log = TelemetryLog(
        call_sid=payload.call_sid,
        sip_status=payload.sip_status,
        event_type=payload.event_type,
        latency_ms=payload.latency_ms,
        jitter_ms=payload.jitter_ms,
        packet_loss_pct=payload.packet_loss_pct,
        extra_data=payload.extra_data
    )
    db.add(log)
    db.commit()

    # 3. Broadcast to live dashboard via WebSocket
    event_dict = {
        "call_sid": payload.call_sid,
        "event_type": payload.event_type,
        "latency_ms": payload.latency_ms,
        "jitter_ms": payload.jitter_ms,
        "timestamp": time.time()
    }
    await telemetry_hub.broadcast(event_dict)

    return {"status": "recorded", "id": log.id}

@app.get("/api/v1/telemetry/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(TelemetryLog.id)).scalar() or 0
    avg_latency = db.query(func.avg(TelemetryLog.latency_ms)).scalar() or 0.0
    avg_jitter = db.query(func.avg(TelemetryLog.jitter_ms)).scalar() or 0.0

    return {
        "total_telemetry_events": total,
        "avg_latency_ms": round(float(avg_latency), 2),
        "avg_jitter_ms": round(float(avg_jitter), 2)
    }

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await telemetry_hub.connect(websocket)
    try:
        while True:
            # Keep-alive loop
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        telemetry_hub.disconnect(websocket)

@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Live Telephony Observability Dashboard</title>
  <style>
    body { background: #0b1120; color: #f8fafc; font-family: monospace; padding: 20px; }
    h1 { color: #38bdf8; font-size: 20px; }
    .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }
    .card { background: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; }
    .card h3 { font-size: 12px; color: #94a3b8; text-transform: uppercase; margin: 0 0 5px 0; }
    .card .val { font-size: 28px; font-weight: bold; color: #38bdf8; }
    table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; }
    th, td { padding: 10px 14px; text-align: left; font-size: 13px; border-bottom: 1px solid #334155; }
    th { background: #0f172a; color: #94a3b8; }
    tr:nth-child(even) { background: #182234; }
    .badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; background: #0369a1; color: #fff; }
  </style>
</head>
<body>
  <h1>📡 Live Telephony & Event Observability Monitor</h1>
  <p>Streaming metrics from WebSocket: <code>/ws/telemetry</code> | Scrape URL: <code>/metrics</code></p>
  <div class="grid">
    <div class="card">
      <h3>Active Event Stream</h3>
      <div class="val" id="eventCount">0</div>
    </div>
    <div class="card">
      <h3>Latest Latency</h3>
      <div class="val" id="lastLatency">0 ms</div>
    </div>
    <div class="card">
      <h3>System Status</h3>
      <div class="val" style="color:#10b981;">OPTIMAL</div>
    </div>
  </div>

  <h2>Real-Time Telephony Event Stream</h2>
  <table>
    <thead>
      <tr>
        <th>Call SID</th>
        <th>Event Type</th>
        <th>Latency (ms)</th>
        <th>Jitter (ms)</th>
        <th>Timestamp</th>
      </tr>
    </thead>
    <tbody id="eventRows">
    </tbody>
  </table>

  <script>
    let count = 0;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/telemetry`);
    
    ws.onmessage = (event) => {
      const d = JSON.parse(event.data);
      count++;
      document.getElementById('eventCount').innerText = count;
      document.getElementById('lastLatency').innerText = d.latency_ms + ' ms';
      
      const tbody = document.getElementById('eventRows');
      const row = document.createElement('tr');
      row.innerHTML = `
        <td><code>${d.call_sid}</code></td>
        <td><span class="badge">${d.event_type}</span></td>
        <td>${d.latency_ms}</td>
        <td>${d.jitter_ms}</td>
        <td>${new Date(d.timestamp * 1000).toLocaleTimeString()}</td>
      `;
      tbody.prepend(row);
      if (tbody.children.length > 15) tbody.removeChild(tbody.lastChild);
    };
  </script>
</body>
</html>"""
