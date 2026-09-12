# AcmeCorp Platform

A production-inspired e-commerce environment built to demonstrate **solution architecture, observability, troubleshooting, and technical problem-solving** in a realistic distributed application.

The project is designed as a hands-on Solutions Engineering portfolio project. Rather than focusing only on application development, it demonstrates how a modern service can be deployed, observed, diagnosed, and explained from both an engineering and customer-facing perspective.

The environment currently uses **Python, FastAPI, PostgreSQL, Docker, OpenTelemetry, and Jaeger**, with additional infrastructure, observability, cloud, and security capabilities being added incrementally.

---

## Why This Project Exists

Modern Solutions Engineers need to understand more than a single product or programming language.

They need to be able to:

- understand customer architectures
- identify technical requirements
- design integrations
- work with APIs and infrastructure
- troubleshoot production problems
- understand application telemetry
- communicate technical findings clearly
- demonstrate solutions through proofs of concept

AcmeCorp Platform provides a realistic environment for practicing and demonstrating those skills.

Instead of building isolated technology demos, the project uses one evolving fictional production environment where infrastructure, observability, security, and troubleshooting scenarios can be introduced over time.

---

## Architecture

The current environment consists of a containerized Orders API backed by PostgreSQL and instrumented with OpenTelemetry.

```text
                         AcmeCorp Platform

                              Client
                                │
                                │ HTTP
                                ▼
                         ┌─────────────┐
                         │ Orders API  │
                         │   FastAPI   │
                         └──────┬──────┘
                                │
                  ┌─────────────┴─────────────┐
                  │                           │
                  │ SQL                       │ OTLP
                  ▼                           ▼
           ┌────────────┐              ┌───────────────┐
           │ PostgreSQL │              │ OpenTelemetry │
           │            │              │   Collector   │
           └────────────┘              └───────┬───────┘
                                              │
                                              │ Traces
                                              ▼
                                       ┌─────────────┐
                                       │   Jaeger    │
                                       │             │
                                       └─────────────┘
```

The OpenTelemetry Collector acts as the telemetry routing layer between the application and observability backends.

This keeps application instrumentation vendor-neutral and allows additional platforms to be introduced without redesigning the application.

---

## Current Capabilities

### Application

The platform currently includes a FastAPI-based Orders API with:

- order creation
- order retrieval
- PostgreSQL persistence
- SQLAlchemy ORM
- API validation
- HTTP error handling

Example endpoint:

```text
GET /orders/{order_id}
```

---

### Containerization

The environment runs locally using Docker Compose.

Current services include:

```text
orders-api
postgres
otel-collector
jaeger
```

This provides a reproducible environment where application and infrastructure behavior can be tested consistently.

---

### Health Monitoring

The Orders API exposes separate liveness and readiness endpoints.

```text
GET /health/live
GET /health/ready
```

The liveness endpoint answers:

> Is the application process running?

The readiness endpoint answers:

> Is the application capable of serving traffic?

Readiness includes a PostgreSQL dependency check using a lightweight database query.

This models the health-check patterns commonly used by container orchestrators and load balancers.

---

## Observability

The application implements the three primary observability signals:

```text
Logs     → What happened?

Metrics  → How is the system behaving?

Traces   → Where did the request spend its time?
```

Together these signals provide different perspectives on application behavior and can be correlated during troubleshooting.

---

### Structured Logging

Application requests are logged as structured JSON rather than unstructured text.

Example:

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

Structured logging makes application events easier to search, aggregate, and ingest into observability or SIEM platforms.

---

### Request Correlation

Each HTTP request receives a unique request ID.

Clients can also provide their own ID through:

```text
X-Request-ID
```

The request ID is included in:

- application logs
- HTTP response headers
- error events

This makes it possible to follow an individual request during troubleshooting.

---

### Trace and Log Correlation

Structured logs also include OpenTelemetry:

```text
trace_id
span_id
```

This allows an engineer to move from a specific application log directly to the corresponding distributed trace.

A typical investigation can therefore follow:

```text
Error log
    │
    ▼
trace_id
    │
    ▼
Distributed trace
    │
    ▼
Slow or failing operation
```

---

### Distributed Tracing

The Orders API is instrumented using OpenTelemetry.

Instrumentation currently covers:

- FastAPI HTTP requests
- SQLAlchemy database operations
- manually instrumented application operations

Telemetry is exported using OTLP over gRPC:

```text
Orders API
     │
     │ OTLP :4317
     ▼
OpenTelemetry Collector
     │
     ▼
Jaeger
```

Jaeger provides trace visualization and allows individual request execution paths to be inspected.

---

### Application Metrics

The Orders API records application-level OpenTelemetry metrics including:

```text
acmecorp.http.requests
acmecorp.http.request.duration
```

The request counter measures HTTP request volume.

The request duration histogram records latency distributions and will later support operational measurements such as:

- request rate
- error rate
- p50 latency
- p95 latency
- p99 latency

Metric attributes include information such as:

```text
http.request.method
http.route
http.response.status_code
```

---

### Metric Cardinality

HTTP metrics use normalized route templates rather than individual request paths.

For example, requests to:

```text
/orders/1
/orders/2
/orders/999
```

are represented as:

```text
/orders/{order_id}
```

rather than creating separate metric dimensions for every order ID.

This prevents unbounded metric cardinality as the number of unique resources increases.

Exact paths remain available in structured logs where request-level detail is useful.

---

## Incident Simulation

The platform contains intentionally introduced failure and degradation scenarios.

The purpose is not simply to demonstrate that telemetry exists, but to use telemetry to investigate realistic production problems.

Incident scenarios are documented under:

```text
/incidents
```

---

## Incident 001 — Slow Inventory Dependency

The first incident simulates elevated latency caused by a legacy inventory dependency.

The affected test endpoint is:

```text
GET /debug/slow-order/{order_id}
```

The simulated dependency creates an OpenTelemetry span:

```text
inventory.check
```

and introduces configurable latency through:

```text
INVENTORY_DELAY_SECONDS
```

For example:

```text
INVENTORY_DELAY_SECONDS=1.5
```

introduces approximately 1.5 seconds of downstream latency.

### Observed Symptom

A normal request may complete in a few milliseconds:

```text
GET /orders/1
```

while the degraded endpoint takes approximately:

```text
GET /debug/slow-order/1

~1.5 seconds
```

### Investigation

Structured logs identify the affected requests and show elevated request duration.

Distributed tracing then reveals where that time was spent.

Conceptually:

```text
GET /debug/slow-order/{order_id}       ~1500 ms
│
├── inventory.check                    ~1500 ms
│
└── PostgreSQL query                      few ms
```

The trace therefore isolates the inventory dependency as the primary latency contributor.

At the same time, SQLAlchemy tracing shows that PostgreSQL remains responsive.

This allows the database to be eliminated as the likely root cause.

### Troubleshooting Workflow

```text
Customer reports slow requests
            │
            ▼
Inspect service health
            │
            ▼
Inspect latency / request telemetry
            │
            ▼
Identify affected requests
            │
            ▼
Use trace_id to inspect execution
            │
            ▼
Compare span durations
            │
            ▼
inventory.check dominates trace
            │
            ▼
PostgreSQL eliminated as bottleneck
            │
            ▼
Root cause isolated
```

This demonstrates how logs, metrics, and traces provide complementary information during an investigation.

The full incident analysis is available at:

```text
incidents/001-slow-inventory-check.md
```

---

## Fault Injection

Incident behavior is intentionally configurable.

For example:

```yaml
INVENTORY_DELAY_SECONDS: "1.5"
```

can be changed to:

```yaml
INVENTORY_DELAY_SECONDS: "0"
```

to return the simulated dependency to healthy behavior.

This allows the same application and infrastructure to demonstrate both healthy and degraded conditions without modifying application logic.

Future scenarios will introduce additional failure modes such as:

```text
latency
timeouts
application errors
database contention
authentication failures
dependency failures
security events
```

---

## Running the Environment

### Requirements

You need:

- Docker
- Docker Compose
- Git

Clone the repository and start the environment:

```bash
git clone <repository-url>
cd acmecorp-platform
docker compose up --build
```

Docker Compose starts the application and its supporting infrastructure.

---

## Testing the API

Check application liveness:

```bash
curl http://localhost:8000/health/live
```

Check readiness:

```bash
curl http://localhost:8000/health/ready
```

Retrieve an order:

```bash
curl http://localhost:8000/orders/1
```

The interactive FastAPI documentation is available at:

```text
http://localhost:8000/docs
```

---

## Viewing Distributed Traces

Jaeger is exposed locally at:

```text
http://localhost:16686
```

Select:

```text
orders-api
```

as the service to inspect application traces.

Generate a normal request:

```bash
curl http://localhost:8000/orders/1
```

or generate the controlled latency incident:

```bash
curl http://localhost:8000/debug/slow-order/1
```

The resulting traces can then be compared in Jaeger.

---

## Repository Structure

```text
acmecorp-platform/
│
├── application/
│   └── orders-api/
│       ├── app/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   ├── logging_config.py
│       │   ├── main.py
│       │   ├── models.py
│       │   ├── schemas.py
│       │   └── telemetry.py
│       │
│       ├── Dockerfile
│       └── requirements.txt
│
├── architecture/
│   └── architecture.md
│
├── infrastructure/
│
├── observability/
│   └── otel-collector/
│       └── config.yaml
│
├── security/
│
├── incidents/
│   └── 001-slow-inventory-check.md
│
├── presales/
│   └── customer-requirements.md
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

The repository is intentionally organized beyond application source code.

Separate areas exist for:

```text
architecture     → system design documentation
infrastructure   → infrastructure-as-code and cloud resources
observability    → telemetry and monitoring configuration
security         → security controls and scenarios
incidents        → troubleshooting exercises and root-cause analysis
presales         → discovery, requirements, PoCs, and demo material
```

This structure allows the project to evolve into a broader Solutions Engineering environment rather than remaining only an application-development exercise.

---

## Technology Stack

| Area | Technology |
|---|---|
| Application | Python |
| API | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Containers | Docker / Docker Compose |
| Telemetry | OpenTelemetry |
| Telemetry Protocol | OTLP / gRPC |
| Distributed Tracing | Jaeger |
| Logging | Structured JSON |
| Metrics | OpenTelemetry Metrics |

---

## Roadmap

### Application

- [x] Orders API
- [x] PostgreSQL persistence
- [x] API validation
- [x] Error handling
- [x] Health endpoints

### Observability

- [x] Structured JSON logging
- [x] Request IDs
- [x] Trace/log correlation
- [x] OpenTelemetry instrumentation
- [x] HTTP tracing
- [x] Database tracing
- [x] Custom application spans
- [x] Application metrics
- [x] Metric cardinality controls
- [x] OpenTelemetry Collector
- [x] Jaeger
- [x] Prometheus
- [x] Grafana dashboards
- [ ] Operational alerting
- [ ] Service-level indicators

### Architecture

- [x] Docker Compose environment
- [ ] Additional microservices
- [ ] Inter-service distributed tracing
- [ ] Reverse proxy / load balancer
- [ ] Cloud deployment
- [ ] Terraform infrastructure
- [ ] AWS networking

### Security

- [ ] Authentication and authorization
- [ ] Edge security controls
- [ ] WAF integration
- [ ] Security event generation
- [ ] SIEM integration
- [ ] Security incident scenarios

### Solutions Engineering

- [ ] Customer discovery scenario
- [ ] Requirements mapping
- [ ] Solution architecture
- [ ] Proof-of-concept success criteria
- [ ] Demo script
- [ ] Technical objection handling
- [ ] Vendor-specific solution variants

---

## Planned Architecture

The long-term environment will evolve toward a broader production-inspired architecture:

```text
                            Internet
                               │
                               ▼
                      Edge / Security Layer
                               │
                    DNS / CDN / WAF / Zero Trust
                               │
                               ▼
                         Load Balancer
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
          Frontend         Orders API      Payments API
                               │                │
                               └───────┬────────┘
                                       │
                                       ▼
                                  PostgreSQL


                     Observability Pipeline

                  Applications / Infrastructure
                              │
                              ▼
                      OpenTelemetry
                              │
                              ▼
                    OpenTelemetry Collector
                         │           │
                         │           │
                         ▼           ▼
                       Traces      Metrics / Logs
```

The goal is to use the same environment to explore multiple Solutions Engineering domains, including:

- cloud infrastructure
- application performance monitoring
- distributed tracing
- security
- networking
- SIEM
- edge services
- infrastructure as code
- incident investigation
- technical discovery
- proof-of-concept design

---

## Solutions Engineering Focus

This repository is not intended to represent a finished commercial application.

It is a **production-inspired technical lab and portfolio environment** designed to demonstrate the ability to connect application behavior, infrastructure, telemetry, and customer-facing troubleshooting.

The emphasis is therefore not only on:

```text
Can the application run?
```

but also:

```text
Can the architecture be explained?

Can dependencies be identified?

Can telemetry be designed correctly?

Can a production symptom be investigated?

Can the root cause be isolated using evidence?

Can the findings be communicated clearly?

Can the solution be mapped to customer requirements?
```

Those questions drive the continued development of the project.

---

## Project Status

**Active development**

The current phase focuses on building the core application and observability foundation.

Upcoming work will add a Prometheus and Grafana metrics stack, additional distributed services, cloud infrastructure, security scenarios, and customer-facing Solutions Engineering material.