# Troubleshooting

AcmeCorp Platform includes controlled failure scenarios for practicing production-style troubleshooting.

The goal is not only to generate failures, but to use evidence from the system to determine:

- what is affected
- where the failure originates
- which dependencies are involved
- whether the suspected root cause is supported by telemetry
- whether the system returns to normal after remediation

## Investigation Approach

A typical investigation follows this path:

```text
Reported symptom
      │
      ▼
Verify service health
      │
      ▼
Inspect metrics
      │
      ▼
Identify affected service
      │
      ▼
Inspect structured logs
      │
      ▼
Correlate request / trace
      │
      ▼
Inspect distributed trace
      │
      ▼
Compare dependencies and spans
      │
      ▼
Form root-cause hypothesis
      │
      ▼
Apply remediation
      │
      ▼
Verify recovery
```

The order is not a strict rule. Different incidents may require starting from a log, trace, or customer-reported request.

The important principle is to use telemetry to test a hypothesis rather than assuming the first visible error is the root cause.

## 1. Start With the Symptom

First determine what the user or monitoring system is actually reporting.

Examples include:

```text
Checkout requests are failing
Requests are slower than normal
A service is returning HTTP 5xx
A dependency appears unavailable
```

A symptom describes what is visible. It does not necessarily identify the root cause.

For example:

```text
Orders API returns 502
```

does not automatically mean the Orders API itself is malfunctioning.

The status may represent a failure in a downstream service.

## 2. Check Service Health

Verify that the relevant processes and dependencies are running.

```powershell
docker compose ps
```

Application health endpoints provide another quick check:

```powershell
curl.exe http://localhost:8000/health/live
curl.exe http://localhost:8000/health/ready

curl.exe http://localhost:8001/health/live
curl.exe http://localhost:8001/health/ready
```

Liveness and readiness answer different questions.

A process may be alive while still being unable to serve traffic because one of its required dependencies is unavailable.

## 3. Use Metrics to Determine Scope

Metrics provide a high-level view of system behavior.

Useful questions include:

```text
Did request latency increase?

Did the error rate increase?

Which service is producing errors?

Did the problem begin at a specific time?

Are multiple services affected?
```

The current Grafana dashboards expose measurements including:

```text
request rate
5xx error rate
p95 request latency
```

Service-level filtering is particularly important.

For example, during a payment failure:

```text
payments-api → HTTP 500
orders-api   → HTTP 502
```

Both services show errors, but they represent different points in the same failure path.

## 4. Inspect Structured Logs

Once the affected service or time window is known, inspect its logs.

Orders API:

```powershell
docker compose logs orders-api --tail 100
```

Payments API:

```powershell
docker compose logs payments-api --tail 100
```

Or follow both:

```powershell
docker compose logs -f orders-api payments-api
```

Application logs contain structured fields including:

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

These fields make it possible to narrow an investigation from a service-level symptom to an individual request.

## 5. Correlate Across Services

For requests crossing service boundaries, compare correlation identifiers.

A checkout may appear as:

```text
orders-api
request_id = abc-123
trace_id   = 123456...
        │
        ▼
payments-api
request_id = abc-123
trace_id   = 123456...
```

The shared identifiers provide evidence that the events belong to the same transaction.

The request ID provides application-level correlation.

The trace ID connects the request to its OpenTelemetry distributed trace.

## 6. Inspect the Distributed Trace

Use the trace ID to inspect the request in Jaeger:

```text
http://localhost:16686
```

A trace provides the execution path and timing of individual operations.

For a checkout, this can include:

```text
Orders API request
│
├── application processing
│
└── HTTP request to Payments API
       │
       └── payment.authorize
```

For the inventory latency scenario:

```text
Orders API request
│
├── inventory.check
│
└── PostgreSQL query
```

Comparing span durations and status information helps identify where time was spent or where a failure originated.

## 7. Separate Symptom From Root Cause

Distributed systems often expose failures through an upstream service even when the underlying problem exists downstream.

Incident 002 demonstrates this:

```text
Customer sees checkout failure
            │
            ▼
Orders API returns 502
            │
            ▼
Orders called Payments
            │
            ▼
Payments returned 500
            │
            ▼
Payment authorization failed
```

The Orders API error is therefore an important symptom, but the Payments API is the source of the simulated failure.

Incident 001 demonstrates the same reasoning for latency.

The overall Orders request is slow, but tracing shows:

```text
inventory.check  → slow
PostgreSQL       → responsive
```

This allows PostgreSQL to be eliminated as the likely bottleneck.

## 8. Form a Hypothesis

At this stage, the evidence should support a specific explanation.

A useful root-cause statement identifies both the failing component and the mechanism.

For example:

```text
Checkout failures are caused by the Payments API returning HTTP 500
during authorization. Orders converts the downstream failure into an
HTTP 502 response for the checkout request.
```

This is more useful than:

```text
The Orders API has errors.
```

Similarly:

```text
Request latency is dominated by the inventory.check operation while
database spans remain responsive.
```

is more useful than:

```text
The application is slow.
```

## 9. Remediate

Controlled incidents in AcmeCorp are configured through environment variables.

For example:

```text
INVENTORY_DELAY_SECONDS
PAYMENT_FAILURE_RATE
PAYMENT_DELAY_SECONDS
```

Returning these values to their healthy configuration removes the injected failure.

The remediation depends on the incident being investigated and is documented in the corresponding incident report.

## 10. Verify Recovery

Remediation is not complete until recovery has been verified.

Repeat the same checks used to identify the incident.

For example:

```text
Service health      → healthy
Checkout request    → HTTP 200
5xx rate            → returns to baseline
Request latency     → returns to baseline
New traces          → no failing dependency
Application logs    → no corresponding errors
```

This closes the investigation with evidence that the system has recovered.

## Troubleshooting the Platform Itself

Not every problem is an intentional incident.

The local environment can also experience configuration or application startup problems.

Start with container state:

```powershell
docker compose ps -a
```

If a service is stopped or restarting, inspect its logs:

```powershell
docker compose logs <service> --tail 200
```

For example:

```powershell
docker compose logs payments-api --tail 200
```

If necessary, rebuild and start a single service in the foreground:

```powershell
docker compose build payments-api
docker compose up payments-api
```

Running it in the foreground makes startup exceptions immediately visible.

This is useful for distinguishing:

```text
application problem
configuration problem
container problem
telemetry problem
visualization problem
```

before debugging a downstream tool unnecessarily.

## Example: Observability Pipeline Checks

If traces or metrics are missing, verify the pipeline from the producer outward rather than starting at the visualization layer.

For metrics:

```text
Application
    │
    ▼
OpenTelemetry SDK
    │
    ▼
OpenTelemetry Collector
    │
    ▼
Prometheus
    │
    ▼
Grafana
```

For traces:

```text
Application
    │
    ▼
OpenTelemetry SDK
    │
    ▼
OpenTelemetry Collector
    │
    ▼
Jaeger
```

If Grafana does not show a Payments API metric, for example, first verify that the Payments API is actually running and producing traffic before assuming the dashboard is incorrect.

This helps isolate which stage of the telemetry pipeline is failing.

## Incident Reports

Detailed investigations are documented separately:

- [Incident 001 — Slow Inventory Dependency](../incidents/001-slow-inventory-check.md)
- [Incident 002 — Payment Authorization Failures](../incidents/002-payment-authorization-failures.md)

These reports document the symptom, investigation, evidence, root cause, remediation, and verification for each scenario.