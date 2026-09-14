# Observability

AcmeCorp Platform uses logs, metrics, and distributed traces together to investigate application behavior across service boundaries.

Both the Orders API and Payments API are instrumented with OpenTelemetry and send telemetry through an OpenTelemetry Collector.

The current observability stack is:

```text
Orders API ────┐
               │
Payments API ──┼──► OpenTelemetry Collector
               │           │
               │           ├──► Jaeger
               │           │     Traces
               │           │
               │           └──► Prometheus
               │                    │
               │                    ▼
               │                 Grafana
               │                 Metrics
               │
               └──► Structured JSON logs
```

## Signals

The environment uses the three main observability signals for different questions:

| Signal | Question |
| --- | --- |
| Metrics | Is something wrong? |
| Logs | What happened? |
| Traces | Where did it happen? |

The goal is not to treat these signals independently. They are designed to be used together during an investigation.

For example:

```text
Grafana shows elevated error rate
              │
              ▼
Identify affected service
              │
              ▼
Inspect application logs
              │
              ▼
Find trace_id
              │
              ▼
Inspect distributed trace
              │
              ▼
Identify failing dependency
```

## Structured Logging

The application services produce structured JSON logs.

A request log contains fields such as:

```json
{
  "timestamp": "2026-09-11T18:00:11.494599+00:00",
  "level": "INFO",
  "service": "orders-api",
  "message": "HTTP request completed",
  "trace_id": "002c193dd5de5b0b0e8857be238a1d1d",
  "span_id": "43ed561f9f1a90ad",
  "request_id": "b7320602-ca50-40e3-bfe3-6b9e504fada4",
  "method": "GET",
  "path": "/orders/1",
  "status_code": 200,
  "duration_ms": 8.42
}
```

Structured fields make it possible to search and aggregate events without parsing information from free-form log messages.

Important fields include:

```text
service
request_id
trace_id
span_id
method
path
status_code
duration_ms
```

## Request Correlation

Each incoming request receives a request ID.

Clients can provide their own using:

```text
X-Request-ID
```

If one is not provided, the application generates an ID.

For service-to-service requests, the Orders API forwards the request ID to the Payments API.

A checkout can therefore produce logs similar to:

```text
orders-api
request_id = abc-123
        │
        │ HTTP
        ▼
payments-api
request_id = abc-123
```

This provides a simple application-level correlation mechanism across the two services.

## Trace and Log Correlation

Application logs also contain the active OpenTelemetry:

```text
trace_id
span_id
```

This makes it possible to move from a specific log event to the distributed trace for the same request.

Conceptually:

```text
Application error
      │
      ▼
Structured log
      │
      │ trace_id
      ▼
Jaeger trace
      │
      ▼
Individual spans
```

Request IDs and trace IDs serve different purposes.

The request ID is an application-level identifier that can also be supplied by a client.

The trace ID is part of the distributed tracing context and identifies the complete trace across instrumented services.

Both are useful during troubleshooting.

## Distributed Tracing

OpenTelemetry tracing is enabled for both application services.

Instrumentation currently covers:

- FastAPI HTTP requests
- outgoing HTTP requests
- SQLAlchemy database operations
- custom application operations

Trace data is exported using OTLP over gRPC to the OpenTelemetry Collector and then forwarded to Jaeger.

```text
Application
    │
    │ OTLP/gRPC
    ▼
OpenTelemetry Collector
    │
    ▼
Jaeger
```

### Cross-Service Tracing

Checkout introduces a distributed request path:

```text
Client
  │
  ▼
Orders API
  │
  │ HTTP
  ▼
Payments API
```

OpenTelemetry HTTP instrumentation propagates trace context with the outgoing request.

As a result, Jaeger can display the Orders and Payments operations as part of the same distributed trace.

A simplified trace looks like:

```text
POST /orders/{order_id}/checkout
│
├── Orders API processing
│
└── POST payments-api/payments/authorize
       │
       └── payment.authorize
```

This is particularly useful when the customer-facing service is not the service responsible for the underlying failure.

## Application Metrics

Both APIs produce OpenTelemetry application metrics.

The primary metrics are:

```text
acmecorp.http.requests
acmecorp.http.request.duration
```

After export to Prometheus these are exposed using Prometheus-compatible metric names such as:

```text
acmecorp_http_requests_total
acmecorp_http_request_duration_milliseconds_bucket
```

### Request Counter

The request counter records HTTP request volume and includes attributes such as:

```text
http.request.method
http.route
http.response.status_code
```

Resource attributes are also exposed to Prometheus so that metrics can be separated by service.

This allows queries to distinguish:

```text
orders-api
payments-api
```

### Request Duration

Request duration is recorded as a histogram.

Histograms make it possible to calculate latency percentiles rather than relying only on average response time.

For example, the Grafana dashboard currently uses a Prometheus query to calculate p95 request latency.

## Metric Cardinality

HTTP metrics use normalized route templates instead of individual resource paths.

For example:

```text
/orders/1
/orders/2
/orders/999
```

are represented as:

```text
/orders/{order_id}
```

Using the individual order ID as a metric attribute would continuously create new metric label combinations as new orders are created.

Normalized routes keep metric cardinality bounded.

Request-specific information remains available in logs and traces, where high-detail investigation is more appropriate.

## OpenTelemetry Collector

The OpenTelemetry Collector sits between the applications and the observability backends.

```text
Orders API ────┐
               │
Payments API ──┴──► Collector ──► observability backends
```

The applications therefore send telemetry to one common OTLP endpoint rather than being configured directly for every backend.

The current Collector pipelines handle:

```text
traces  → Jaeger
metrics → Prometheus exporter
```

This also keeps the application instrumentation relatively vendor-neutral.

A different observability backend can later be introduced at the Collector layer without replacing the instrumentation throughout the application.

## Prometheus

Prometheus scrapes metrics exposed by the OpenTelemetry Collector.

The local Prometheus UI is available at:

```text
http://localhost:9090
```

A basic request-rate query is:

```promql
sum(rate(acmecorp_http_requests_total[1m]))
```

Metrics can also be filtered by service, HTTP route, and response status.

This is important in a distributed application because an overall error rate does not necessarily identify which service originated the failure.

## Grafana

Grafana is used to visualize Prometheus metrics.

The local Grafana instance is available at:

```text
http://localhost:3000
```

The Orders API overview includes operational measurements such as:

- request rate
- HTTP 5xx error rate
- p95 request latency

The payment failure scenario also demonstrates service-specific error rates.

A Payments API failure can produce:

```text
payments-api
HTTP 500
    │
    ▼
orders-api
HTTP 502
```

Separate service metrics make both sides of this failure visible.

## Example: Payment Failure Investigation

The payment failure incident demonstrates how the signals work together.

A configurable failure is introduced in the Payments API:

```text
PAYMENT_FAILURE_RATE=0.4
```

Some authorization requests then return HTTP 500.

Because Orders depends on Payments, the corresponding checkout request returns HTTP 502.

```text
Client
  │
  ▼
Orders API ─────────────► Payments API
   502                       500
```

### 1. Metrics

Grafana shows an elevated Payments API 5xx rate together with an elevated Orders API 5xx rate.

This establishes that the problem affects both services and provides a starting point for investigation.

### 2. Logs

Structured logs show the failed payment authorization and the resulting upstream error.

The request ID can be used to correlate application events across both services.

### 3. Trace

The trace ID identifies the distributed trace in Jaeger.

The trace shows the request crossing from Orders to Payments and identifies the failed payment authorization operation.

The combined evidence provides a causal chain:

```text
Payments authorization failure
            │
            ▼
Payments HTTP 500
            │
            ▼
Orders downstream request fails
            │
            ▼
Orders HTTP 502
            │
            ▼
Checkout failure
```

The complete incident analysis is documented in:

```text
incidents/002-payment-authorization-failures.md
```

## Current Limitations

The observability environment is intentionally still evolving.

Current gaps include:

- operational alerting
- formal service-level indicators
- centralized log backend
- infrastructure telemetry
- cloud telemetry
- security event monitoring

These will be introduced incrementally as the platform expands.