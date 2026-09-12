# AcmeCorp Platform

A production-inspired distributed e-commerce environment built to demonstrate **solution architecture, observability, troubleshooting, distributed systems, and technical problem-solving**.

The project is designed as a hands-on Solutions Engineering portfolio project. Rather than focusing only on application development, it demonstrates how modern services can be integrated, observed, diagnosed, and explained from both an engineering and customer-facing perspective.

The environment currently uses **Python, FastAPI, PostgreSQL, Docker, OpenTelemetry, Prometheus, Grafana, and Jaeger**, with cloud infrastructure, security capabilities, additional incidents, and customer-facing Solutions Engineering material being added incrementally.

---

## Why This Project Exists

I am building this project as part of my transition toward Solutions Engineering.

It provides an environment where I can learn, experiment with, and demonstrate technical skills involved in the role while building on my existing background in software development, data, APIs, databases, technical discovery, and solution design.

The project focuses on capabilities such as:

- understanding application and customer architectures
- identifying technical requirements and dependencies
- designing service integrations
- working with APIs, databases, containers, and infrastructure
- implementing observability
- troubleshooting production-style problems
- correlating logs, metrics, and distributed traces
- explaining technical findings clearly
- designing and demonstrating proofs of concept

Rather than creating isolated technology demos, AcmeCorp Platform is one evolving fictional production environment.

New services, integrations, infrastructure, observability capabilities, security controls, failure scenarios, and troubleshooting challenges are introduced incrementally.

The goal is not simply to build a microservices application. The platform acts as a **Solutions Engineering playground** for understanding how systems fit together, diagnosing problems, designing solutions, and communicating the technical reasoning behind them.

---

## Current Architecture

The current platform consists of an Orders API backed by PostgreSQL and a downstream Payments API.

Both application services are instrumented with OpenTelemetry.

```text
                              Client
                                │
                                │ HTTP
                                ▼
                         ┌─────────────┐
                         │ Orders API  │
                         │   FastAPI   │
                         └──────┬──────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    │ SQL                   │ HTTP
                    ▼                       ▼
             ┌────────────┐          ┌──────────────┐
             │ PostgreSQL │          │ Payments API │
             └────────────┘          │   FastAPI    │
                                     └──────────────┘
                    │                       │
                    │                       │
                    └───────────┬───────────┘
                                │
                                │ OTLP
                                ▼
                      ┌────────────────────┐
                      │   OpenTelemetry    │
                      │     Collector      │
                      └─────────┬──────────┘
                                │
                     ┌──────────┴──────────┐
                     │                     │
                     ▼                     ▼
              ┌────────────┐        ┌────────────┐
              │   Jaeger   │        │ Prometheus │
              │   Traces   │        │  Metrics   │
              └────────────┘        └──────┬─────┘
                                           │
                                           ▼
                                    ┌────────────┐
                                    │  Grafana   │
                                    │ Dashboards │
                                    └────────────┘
```

The OpenTelemetry Collector acts as a telemetry routing layer between the applications and observability backends.

This keeps application instrumentation vendor-neutral and provides a central place from which telemetry can be routed to different platforms.

---

## Current Services

The complete environment runs using Docker Compose.

Current services are:

```text
orders-api
payments-api
postgres
otel-collector
jaeger
prometheus
grafana
```

The application layer currently contains two independently containerized FastAPI services.

### Orders API

Responsible for:

- creating orders
- retrieving orders
- PostgreSQL persistence
- initiating checkout
- communicating with the Payments API
- handling downstream payment failures

Example endpoints:

```text
POST /orders
GET  /orders/{order_id}
POST /orders/{order_id}/checkout
```

### Payments API

Represents a downstream payment authorization service.

Example endpoint:

```text
POST /payments/authorize
```

A checkout therefore creates a real service-to-service request:

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

This provides the foundation for distributed tracing and future downstream dependency incidents.

---

## Health Monitoring

Services expose separate liveness and readiness endpoints.

Orders:

```text
GET /health/live
GET /health/ready
```

Payments:

```text
GET /health/live
GET /health/ready
```

Liveness answers:

> Is the service process alive?

Readiness answers:

> Is the service capable of accepting traffic?

The Orders readiness check includes a PostgreSQL dependency check.

This models health-check patterns commonly used by container orchestrators and load balancers.

---

# Observability

The platform implements the three primary observability signals:

```text
Logs     → What happened?

Metrics  → How is the system behaving?

Traces   → Where did the request spend its time?
```

These signals provide different levels of information and can be combined during an investigation.

---

## Structured Logging

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

Structured logging makes application events easier to search, aggregate, correlate, and eventually ingest into observability or SIEM platforms.

---

## Cross-Service Request Correlation

Each incoming request receives a request ID.

Clients can also provide one through:

```text
X-Request-ID
```

During checkout, Orders propagates this request ID to Payments:

```text
Client
   │
   │ X-Request-ID
   ▼
Orders API
   │
   │ X-Request-ID
   ▼
Payments API
```

The same identifier can therefore appear in structured logs from both services.

This provides application-level correlation across the distributed transaction.

---

## Distributed Tracing

Both Orders and Payments are instrumented using OpenTelemetry.

Instrumentation currently includes:

- FastAPI server requests
- HTTPX outgoing HTTP requests
- SQLAlchemy database operations
- manually instrumented business operations

Telemetry is exported using OTLP over gRPC.

```text
Orders API ──────┐
                 │
Payments API ────┼── OTLP ──► OpenTelemetry Collector ──► Jaeger
                 │
                 │
PostgreSQL spans ┘
```

Jaeger provides visualization of complete request execution paths.

---

## Distributed Context Propagation

A checkout request creates a distributed trace spanning multiple services.

Conceptually:

```text
POST /orders/{order_id}/checkout
│
├── PostgreSQL SELECT
│
└── HTTP POST → Payments API
      │
      └── POST /payments/authorize
            │
            └── payment.authorize
```

OpenTelemetry propagates trace context across the HTTP boundary between Orders and Payments.

As a result, spans generated by both services share the same trace ID.

This allows an individual customer request to be followed across service boundaries.

---

## Trace and Log Correlation

Structured application logs include:

```text
trace_id
span_id
request_id
```

This provides two complementary correlation mechanisms.

```text
request_id
    │
    └── application-level request correlation

trace_id
    │
    └── distributed telemetry correlation
```

A troubleshooting workflow can therefore move from:

```text
Grafana
   │
   │ detect abnormal behavior
   ▼
Structured logs
   │
   │ identify affected request
   ▼
trace_id
   │
   ▼
Jaeger
   │
   │ inspect distributed execution
   ▼
Slow or failing dependency
```

---

## Application Metrics

The Orders API records OpenTelemetry application metrics including:

```text
acmecorp.http.requests
acmecorp.http.request.duration
```

These are exported through:

```text
Orders API
    │
    │ OTLP
    ▼
OpenTelemetry Collector
    │
    │ Prometheus exposition
    ▼
Prometheus
    │
    │ PromQL
    ▼
Grafana
```

The request counter measures HTTP traffic.

The request-duration histogram allows latency distributions and percentiles to be analyzed.

Metric attributes include:

```text
http.request.method
http.route
http.response.status_code
```

---

## Metric Cardinality

HTTP metrics use normalized route templates rather than individual resource paths.

For example:

```text
/orders/1
/orders/2
/orders/999
```

are represented in metrics as:

```text
/orders/{order_id}
```

instead of creating a separate metric dimension for every order ID.

This avoids unbounded metric cardinality as the number of resources increases.

Exact request paths remain available in structured logs where request-level detail is appropriate.

---

# Prometheus and Grafana

Prometheus stores the application's time-series metrics and provides PromQL for querying them.

Grafana provides operational visualization on top of Prometheus.

The current Orders API dashboard includes:

```text
Request Rate
5xx Error Rate
p95 Request Latency
```

These panels help answer different operational questions.

```text
Request Rate
    → How much traffic is the service receiving?

5xx Error Rate
    → Are requests failing?

p95 Request Latency
    → Are users experiencing degraded performance?
```

The dashboard and Prometheus datasource are provisioned from files in the repository so the observability environment can be recreated automatically.

---

# Incident Simulation

The platform contains intentionally introduced failure and degradation scenarios.

The goal is not simply to demonstrate that telemetry exists.

The goal is to use telemetry to answer questions such as:

```text
What is happening?

Which requests are affected?

Where is time being spent?

Which dependency is responsible?

Is the problem latency, availability, or errors?

What evidence supports the root-cause hypothesis?
```

Incident scenarios are documented under:

```text
/incidents
```

---

## Incident 001 — Slow Inventory Dependency

The first incident simulates elevated latency caused by a legacy inventory dependency.

Affected endpoint:

```text
GET /debug/slow-order/{order_id}
```

The dependency creates a custom OpenTelemetry span:

```text
inventory.check
```

and introduces configurable latency using:

```text
INVENTORY_DELAY_SECONDS
```

For example:

```text
INVENTORY_DELAY_SECONDS=1.5
```

adds approximately 1.5 seconds of downstream latency.

### Observed Symptom

A normal request can complete in a few milliseconds:

```text
GET /orders/1
```

while the degraded request takes approximately:

```text
GET /debug/slow-order/1

~1.5 seconds
```

### Investigation

Grafana exposes elevated p95 request latency.

Structured logs identify individual slow requests.

Jaeger then reveals where the request spent its time:

```text
GET /debug/slow-order/{order_id}       ~1500 ms
│
├── inventory.check                    ~1500 ms
│
└── PostgreSQL query                      few ms
```

The trace isolates the inventory dependency as the primary latency contributor.

At the same time, SQLAlchemy tracing shows that PostgreSQL remains responsive.

The database can therefore be eliminated as the likely root cause.

### Troubleshooting Workflow

```text
Customer reports slow requests
            │
            ▼
Grafana shows elevated latency
            │
            ▼
Inspect structured logs
            │
            ▼
Identify affected request
            │
            ▼
Use trace_id
            │
            ▼
Inspect distributed trace
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

The full investigation is documented in:

```text
incidents/001-slow-inventory-check.md
```

---

# Downstream Failure Handling

Orders acts as a consumer of the Payments service and handles downstream failures explicitly.

Examples include:

```text
Payments unavailable
    → 502 Bad Gateway

Payments returns an error
    → 502 Bad Gateway

Payments timeout
    → 504 Gateway Timeout
```

This allows the API to distinguish between internal application failures and problems originating from downstream dependencies.

It also provides the foundation for future payment-service failure scenarios.

---

# Fault Injection

Incident behavior is intentionally configurable.

For Incident 001:

```yaml
INVENTORY_DELAY_SECONDS: "1.5"
```

introduces latency.

Changing it to:

```yaml
INVENTORY_DELAY_SECONDS: "0"
```

restores normal behavior.

This allows healthy and degraded states to be compared while keeping the application architecture constant.

Future scenarios will introduce additional failure modes such as:

```text
downstream latency
timeouts
application errors
database contention
authentication failures
dependency outages
security events
```

---

# Running the Environment

## Requirements

You need:

- Docker
- Docker Compose
- Git

Clone the repository:

```bash
git clone <repository-url>
cd acmecorp-platform
```

Start the environment:

```bash
docker compose up --build
```

Docker Compose starts the application and observability stack.

---

## Local Services

After startup:

| Service | Address |
|---|---|
| Orders API | `http://localhost:8000` |
| Orders Swagger UI | `http://localhost:8000/docs` |
| Payments API | `http://localhost:8001` |
| Payments Swagger UI | `http://localhost:8001/docs` |
| Grafana | `http://localhost:3000` |
| Prometheus | `http://localhost:9090` |
| Jaeger | `http://localhost:16686` |

The default Grafana credentials for the local lab are:

```text
username: admin
password: admin
```

These credentials are intended only for the local development environment.

---

# Testing the Platform

Check Orders:

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

Check Payments:

```bash
curl http://localhost:8001/health/live
curl http://localhost:8001/health/ready
```

Create an order:

```bash
curl -X POST \
  http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 100,
    "product": "Cloud Widget",
    "quantity": 2
  }'
```

Retrieve it:

```bash
curl http://localhost:8000/orders/1
```

Perform checkout:

```bash
curl -X POST \
  http://localhost:8000/orders/1/checkout \
  -H "X-Request-ID: checkout-demo-001"
```

The checkout request crosses the Orders and Payments service boundary and produces a distributed trace.

---

# Viewing Distributed Traces

Open Jaeger:

```text
http://localhost:16686
```

Select:

```text
orders-api
```

Perform a checkout:

```bash
curl -X POST \
  http://localhost:8000/orders/1/checkout \
  -H "X-Request-ID: checkout-demo-001"
```

The resulting trace should include spans from both:

```text
orders-api
payments-api
```

Conceptually:

```text
Orders checkout
│
├── PostgreSQL
│
└── Payments HTTP request
      │
      └── Payments authorization
```

---

# Viewing Metrics

Open Grafana:

```text
http://localhost:3000
```

The provisioned Orders API dashboard exposes:

```text
Request Rate
5xx Error Rate
p95 Request Latency
```

Prometheus is available at:

```text
http://localhost:9090
```

for direct PromQL exploration.

---

# Repository Structure

```text
acmecorp-platform/
│
├── application/
│   ├── orders-api/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── logging_config.py
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   └── telemetry.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── payments-api/
│       ├── app/
│       │   ├── __init__.py
│       │   ├── logging_config.py
│       │   ├── main.py
│       │   └── telemetry.py
│       ├── Dockerfile
│       └── requirements.txt
│
├── architecture/
│   └── architecture.md
│
├── infrastructure/
│
├── observability/
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── provisioning/
│   ├── otel-collector/
│   │   └── config.yaml
│   └── prometheus/
│       └── prometheus.yml
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

---

# Technology Stack

| Area | Technology |
|---|---|
| Language | Python |
| APIs | FastAPI |
| HTTP client | HTTPX |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Containers | Docker / Docker Compose |
| Telemetry | OpenTelemetry |
| Telemetry transport | OTLP / gRPC |
| Distributed tracing | Jaeger |
| Metrics | OpenTelemetry Metrics / Prometheus |
| Dashboards | Grafana |
| Logging | Structured JSON |

---

# Roadmap

## Application

- [x] Orders API
- [x] Payments API
- [x] PostgreSQL persistence
- [x] API validation
- [x] Health endpoints
- [x] Service-to-service HTTP integration
- [x] Downstream error handling

## Observability

- [x] Structured JSON logging
- [x] Request IDs
- [x] Cross-service request correlation
- [x] Trace/log correlation
- [x] OpenTelemetry instrumentation
- [x] HTTP server tracing
- [x] HTTP client tracing
- [x] Database tracing
- [x] Custom application spans
- [x] Application metrics
- [x] Metric cardinality controls
- [x] OpenTelemetry Collector
- [x] Jaeger
- [x] Prometheus
- [x] Grafana dashboards
- [x] Inter-service distributed tracing
- [ ] Operational alerting
- [ ] Service-level indicators and objectives

## Architecture

- [x] Docker Compose environment
- [x] Multiple application services
- [x] Inter-service communication
- [x] Distributed context propagation
- [ ] Reverse proxy / load balancer
- [ ] Cloud deployment
- [ ] Terraform infrastructure
- [ ] AWS networking

## Reliability & Incident Simulation

- [x] Configurable latency injection
- [x] Latency incident investigation
- [x] Downstream dependency error handling
- [ ] Payment dependency incident
- [ ] Timeout incident
- [ ] Database contention incident
- [ ] Service-level alerting

## Security

- [ ] Authentication and authorization
- [ ] Edge security controls
- [ ] WAF integration
- [ ] Security event generation
- [ ] SIEM integration
- [ ] Security incident scenarios

## Solutions Engineering

- [ ] Customer discovery scenario
- [ ] Requirements mapping
- [ ] Solution architecture
- [ ] Proof-of-concept success criteria
- [ ] Demo script
- [ ] Technical objection handling
- [ ] Vendor-specific solution variants

---

# Planned Architecture

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
                  ┌──────────────┴──────────────┐
                  │                             │
                  ▼                             ▼
              Frontend                     Orders API
                                               │
                                  ┌────────────┴────────────┐
                                  │                         │
                                  ▼                         ▼
                             PostgreSQL                Payments API


                       Observability Pipeline

                    Applications / Infrastructure
                                │
                                ▼
                        OpenTelemetry
                                │
                                ▼
                      OpenTelemetry Collector
                         │              │
                         ▼              ▼
                       Jaeger       Prometheus
                                      │
                                      ▼
                                   Grafana
```

The same environment will be used to explore multiple Solutions Engineering domains, including:

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

# Solutions Engineering Focus

This repository is not intended to represent a finished commercial application.

It is a **production-inspired technical lab and portfolio environment** designed to demonstrate the ability to connect application behavior, infrastructure, telemetry, reliability, and customer-facing troubleshooting.

The emphasis is not only:

```text
Can the application run?
```

but also:

```text
Can the architecture be explained?

Can service dependencies be identified?

Can telemetry be designed correctly?

Can context be propagated across services?

Can a production symptom be detected?

Can an affected request be identified?

Can a distributed trace isolate the responsible dependency?

Can competing root-cause hypotheses be eliminated using evidence?

Can the findings be communicated clearly?

Can a proposed solution be mapped to customer requirements?
```

Those questions drive the continued development of the project.

---

# Project Status

**Active development**

The current platform has established its core distributed application and observability foundation:

```text
FastAPI services
      +
PostgreSQL
      +
Docker Compose
      +
OpenTelemetry
      +
structured logging
      +
distributed tracing
      +
Prometheus
      +
Grafana
      +
incident simulation
```

The next development phase will expand the platform into additional reliability incidents, cloud infrastructure, security scenarios, and customer-facing Solutions Engineering exercises.