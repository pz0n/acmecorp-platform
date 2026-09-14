# Architecture

AcmeCorp Platform is a production-inspired e-commerce environment built around a small distributed application and an observability stack.

The architecture is intentionally simple enough to understand end to end, while still including the kinds of service boundaries, dependencies, telemetry flows, and failure modes that appear in production systems.

## Current Architecture

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