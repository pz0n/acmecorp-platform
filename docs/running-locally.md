# Running AcmeCorp Platform Locally

The complete AcmeCorp environment runs locally using Docker Compose.

This guide covers starting the platform, verifying the services, generating application traffic, and accessing the observability tools.

## Requirements

Install:

- Docker
- Docker Compose
- Git

Verify Docker is available:

```powershell
docker --version
docker compose version
```

## Start the Environment

From the repository root:

```powershell
docker compose up --build -d
```

Check the containers:

```powershell
docker compose ps
```

The main services should include:

```text
orders-api
payments-api
postgres
otel-collector
jaeger
prometheus
grafana
```

## Service URLs

| Service | URL |
| --- | --- |
| Orders API | `http://localhost:8000` |
| Orders API docs | `http://localhost:8000/docs` |
| Payments API | `http://localhost:8001` |
| Payments API docs | `http://localhost:8001/docs` |
| Jaeger | `http://localhost:16686` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |

## Verify Service Health

Check the Orders API:

```powershell
curl.exe http://localhost:8000/health/live
curl.exe http://localhost:8000/health/ready
```

Check the Payments API:

```powershell
curl.exe http://localhost:8001/health/live
curl.exe http://localhost:8001/health/ready
```

Liveness confirms that the application process is running.

Readiness confirms that the service is ready to handle requests. The Orders API readiness check also verifies PostgreSQL connectivity.

## Create an Order

The Orders API accepts new orders through:

```text
POST /orders
```

The exact request schema can be inspected through the FastAPI documentation:

```text
http://localhost:8000/docs
```

After creating an order, retrieve it using:

```powershell
curl.exe http://localhost:8000/orders/1
```

Replace `1` with the ID of the created order if necessary.

## Test Checkout

Checkout exercises communication between the Orders and Payments services.

```powershell
curl.exe -i `
    -X POST `
    http://localhost:8000/orders/1/checkout
```

With the Payments API in its healthy state, the request should return successfully.

The request path is:

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

This request also produces a distributed trace spanning both services.

## Inspect Distributed Traces

Open Jaeger:

```text
http://localhost:16686
```

Select `orders-api` and search for recent traces.

Generate another checkout if necessary:

```powershell
curl.exe -X POST http://localhost:8000/orders/1/checkout
```

A checkout trace should show the request crossing from the Orders API to the Payments API.

## Inspect Metrics

Open Prometheus:

```text
http://localhost:9090
```

A useful starting query is:

```promql
acmecorp_http_requests_total
```

The resulting series should contain metrics for both:

```text
orders-api
payments-api
```

depending on which requests have been generated.

Request rate can be queried with:

```promql
sum(rate(acmecorp_http_requests_total[1m]))
```

## View Grafana Dashboards

Open Grafana:

```text
http://localhost:3000
```

The dashboard visualizes operational measurements such as:

- request rate
- HTTP 5xx error rate
- p95 request latency
- service-specific failure behavior

Generate application traffic if the dashboard does not yet contain data.

## Generate Test Traffic

The following PowerShell loop sends repeated checkout requests:

```powershell
1..40 | ForEach-Object {
    curl.exe `
        -s `
        -o $null `
        -w "%{http_code}`n" `
        -X POST `
        http://localhost:8000/orders/1/checkout

    Start-Sleep -Milliseconds 150
}
```

In a healthy environment these requests should normally succeed.

The traffic is also useful for producing enough telemetry to inspect in Grafana, Prometheus, and Jaeger.

## Incident 001 — Inventory Latency

The Orders API includes a controlled latency scenario:

```text
GET /debug/slow-order/{order_id}
```

Generate it with:

```powershell
curl.exe http://localhost:8000/debug/slow-order/1
```

The delay is controlled through:

```text
INVENTORY_DELAY_SECONDS
```

For example:

```yaml
INVENTORY_DELAY_SECONDS: "1.5"
```

introduces approximately 1.5 seconds of simulated dependency latency.

The resulting trace contains an:

```text
inventory.check
```

span that can be inspected in Jaeger.

See:

```text
incidents/001-slow-inventory-check.md
```

for the full investigation.

## Incident 002 — Payment Failures

Payment failures are controlled through:

```text
PAYMENT_FAILURE_RATE
```

A healthy configuration uses:

```yaml
PAYMENT_FAILURE_RATE: "0"
```

For incident testing, the value can temporarily be changed to:

```yaml
PAYMENT_FAILURE_RATE: "0.4"
```

This causes approximately 40% of payment authorization attempts to fail.

Recreate the Payments API after changing the configuration:

```powershell
docker compose up -d --force-recreate payments-api
```

Then generate checkout traffic:

```powershell
1..40 | ForEach-Object {
    curl.exe `
        -s `
        -o $null `
        -w "%{http_code}`n" `
        -X POST `
        http://localhost:8000/orders/1/checkout

    Start-Sleep -Milliseconds 150
}
```

The expected failure chain is:

```text
Payments API 500
       │
       ▼
Orders API 502
       │
       ▼
Checkout failure
```

Use Grafana, application logs, and Jaeger to investigate the incident.

See:

```text
incidents/002-payment-authorization-failures.md
```

for the full investigation.

### Restore Healthy Behavior

After testing the incident, restore:

```yaml
PAYMENT_FAILURE_RATE: "0"
```

and recreate the service:

```powershell
docker compose up -d --force-recreate payments-api
```

Verify checkout succeeds again:

```powershell
curl.exe -i `
    -X POST `
    http://localhost:8000/orders/1/checkout
```

## Application Logs

View Orders API logs:

```powershell
docker compose logs orders-api --tail 100
```

View Payments API logs:

```powershell
docker compose logs payments-api --tail 100
```

Follow logs in real time:

```powershell
docker compose logs -f orders-api payments-api
```

Application logs are structured JSON and contain correlation fields including:

```text
request_id
trace_id
span_id
```

These can be used to follow a request across services and connect log events with distributed traces.

## Stop the Environment

Stop the containers:

```powershell
docker compose down
```

To also remove persistent Compose volumes:

```powershell
docker compose down -v
```

The `-v` option removes persisted data such as the local PostgreSQL volume, so use it only when a clean environment is intended.

## Rebuild After Code Changes

If application dependencies or Docker images change:

```powershell
docker compose up --build -d
```

To rebuild only one service:

```powershell
docker compose build payments-api
docker compose up -d payments-api
```

The same pattern can be used for the Orders API.