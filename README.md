# AcmeCorp Platform

AcmeCorp Platform is a production-inspired e-commerce environment I'm building to develop and demonstrate practical Solutions Engineering skills.

My background is in software development, data, APIs, and technical solution design. I wanted a hands-on environment where I could go deeper into distributed systems, observability, cloud infrastructure, security, and production troubleshooting.

Rather than building isolated technology demos, I'm evolving one application incrementally and deliberately introducing problems into it.

The current environment consists of two communicating APIs, PostgreSQL, distributed tracing, structured logging, application metrics, and a local observability stack.

## Architecture

```text
                              Client
                                │
                                ▼
                          Orders API
                         FastAPI :8000
                          │         │
                      SQL │         │ HTTP
                          ▼         ▼
                    PostgreSQL   Payments API
                                  FastAPI :8001
                          │         │
                          └────┬────┘
                               │
                              OTLP
                               │
                               ▼
                     OpenTelemetry Collector
                         │             │
                  Traces │             │ Metrics
                         ▼             ▼
                      Jaeger       Prometheus
                                       │
                                       ▼
                                    Grafana
```

Both application services are instrumented with OpenTelemetry and export telemetry through the OpenTelemetry Collector.

This keeps the application instrumentation separate from the observability backend and gives me a platform where different monitoring and troubleshooting tools can be introduced later.

## Current Capabilities

The platform currently includes:

- Orders API with PostgreSQL persistence
- Payments API with service-to-service communication
- liveness and readiness health checks
- structured JSON logging
- request IDs and cross-service request correlation
- OpenTelemetry distributed tracing
- HTTP and SQLAlchemy instrumentation
- custom application spans
- application metrics with controlled cardinality
- OpenTelemetry Collector
- Jaeger distributed tracing
- Prometheus metrics
- Grafana dashboards
- configurable fault injection
- documented incident investigations

## Troubleshooting Scenarios

Failures are deliberately introduced into the environment so that I can investigate them using the telemetry produced by the system.

### Incident 001 — Slow Inventory Dependency

A simulated inventory dependency introduces additional latency into an Orders API request.

Tracing makes it possible to distinguish time spent in the inventory dependency from time spent querying PostgreSQL and isolate the actual bottleneck.

[Read Incident 001](incidents/001-slow-inventory-check.md)

### Incident 002 — Payment Authorization Failures

The Payments API can be configured to reject a percentage of authorization requests.

A failed checkout produces a failure chain similar to:

```text
Payments API 500
       │
       ▼
Orders API 502
       │
       ▼
Elevated service error rates
```

Metrics identify which services are affected, structured logs provide request-level context, and distributed tracing shows the failed call across the Orders and Payments services.

[Read Incident 002](incidents/002-payment-authorization-failures.md)

## Observability

The environment uses the three main observability signals together:

```text
Metrics  → Is something wrong?
Logs     → What happened?
Traces   → Where did it happen?
```

For example, a payment failure can be investigated by moving from an elevated Grafana error rate to application logs and then using the trace ID to inspect the complete request path in Jaeger.

More detail about the instrumentation and telemetry pipeline is available in [Observability](docs/observability.md).

## Running Locally

The environment requires Docker and Docker Compose.

```bash
git clone <repository-url>
cd acmecorp-platform
docker compose up --build
```

Once running:

| Service | Address |
| --- | --- |
| Orders API | `http://localhost:8000` |
| Payments API | `http://localhost:8001` |
| Orders API docs | `http://localhost:8000/docs` |
| Jaeger | `http://localhost:16686` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |

A more complete setup and testing guide is available in [Running Locally](docs/running-locally.md).

## Technology Stack

| Area | Technology |
| --- | --- |
| Application | Python / FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Containers | Docker / Docker Compose |
| Telemetry | OpenTelemetry |
| Telemetry transport | OTLP / gRPC |
| Tracing | Jaeger |
| Metrics | Prometheus |
| Visualization | Grafana |
| Logging | Structured JSON |

## Documentation

Technical details are kept alongside the code rather than putting everything in this README.

- [Architecture](docs/architecture.md)
- [Observability](docs/observability.md)
- [Running Locally](docs/running-locally.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Incident 001 — Slow Inventory Dependency](incidents/001-slow-inventory-check.md)
- [Incident 002 — Payment Authorization Failures](incidents/002-payment-authorization-failures.md)

## What's Next

The current focus is observability and production-style troubleshooting. The next steps are operational alerting and service-level indicators.

Later phases will expand the same environment with cloud infrastructure, Terraform, networking and security controls rather than replacing it with separate demos.

The longer-term goal is to use the platform for customer-style discovery, architecture design, proofs of concept, troubleshooting, and technical demonstrations.

