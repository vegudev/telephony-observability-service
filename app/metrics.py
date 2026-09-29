from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Prometheus Metrics Definitions
TELEPHONY_EVENTS_TOTAL = Counter(
    "telephony_events_total",
    "Total count of telephony events ingested",
    ["event_type", "status"]
)

CALL_LATENCY_HISTOGRAM = Histogram(
    "telephony_call_latency_seconds",
    "Call event processing and transmission latency in seconds",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

ACTIVE_CALLS_GAUGE = Gauge(
    "telephony_active_calls_count",
    "Number of active in-progress telephony calls"
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"]
)

def get_metrics_payload():
    return generate_latest(), CONTENT_TYPE_LATEST
