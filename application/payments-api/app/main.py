import logging
import time
import uuid
import os 
import random

from fastapi import FastAPI, HTTPException, Request
from opentelemetry import (
    trace,
    metrics,
)
from opentelemetry.instrumentation.fastapi import (
    FastAPIInstrumentor,
)
from pydantic import BaseModel

from .telemetry import (
    configure_tracing,
    configure_metrics,
)
from .logging_config import configure_logging


PAYMENT_FAILURE_RATE = float(
    os.getenv(
        "PAYMENT_FAILURE_RATE",
        "0",
    )
)

PAYMENT_DELAY_SECONDS = float(
    os.getenv(
        "PAYMENT_DELAY_SECONDS",
        "0",
    )
)


configure_logging()
configure_tracing()
configure_metrics()

logger = logging.getLogger(
    "acmecorp"
)

meter = metrics.get_meter(
    "payments-api"
)

request_counter = meter.create_counter(
    name="acmecorp.http.requests",
    description="Total number of HTTP requests",
    unit="1",
)

request_duration = meter.create_histogram(
    name="acmecorp.http.request.duration",
    description="HTTP request duration",
    unit="ms",
)

app = FastAPI(
    title="AcmeCorp Payments API",
    version="0.1.0",
)

FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer(
    "payments-api"
)


class PaymentRequest(BaseModel):
    order_id: int
    customer_id: int
    amount_cents: int


class PaymentResponse(BaseModel):
    order_id: int
    status: str
    authorization_code: str


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    request_id = request.headers.get(
        "X-Request-ID",
        str(uuid.uuid4()),
    )

    start_time = time.perf_counter()

    try:
        response = await call_next(
            request
        )

        duration_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        response.headers[
            "X-Request-ID"
        ] = request_id


        route = request.scope.get("route")
        route_path = getattr(
            route,
            "path",
            request.url.path,
        )

        attributes = {
            "http.request.method": request.method,
            "http.route": route_path,
            "http.response.status_code":
                response.status_code,
        }

        request_counter.add(
            1,
            attributes=attributes,
        )

        request_duration.record(
            duration_ms,
            attributes=attributes,
        )

        logger.info(
            "HTTP request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code":
                    response.status_code,
                "duration_ms": round(
                    duration_ms,
                    2,
                ),
            },
        )

        return response

    except Exception:
        duration_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        route = request.scope.get("route")
        route_path = getattr(
            route,
            "path",
            request.url.path,
        )

        attributes = {
            "http.request.method": request.method,
            "http.route": route_path,
            "http.response.status_code": 500,
        }

        request_counter.add(
            1,
            attributes=attributes,
        )

        request_duration.record(
            duration_ms,
            attributes=attributes,
        )

        logger.exception(
            "Unhandled exception during HTTP request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "duration_ms": round(
                    duration_ms,
                    2,
                ),
            },
        )

        raise

@app.get("/health/live")
def liveness():
    return {
        "status": "alive",
    }

@app.get("/health/ready")
def readiness():    
    return {
        "status": "ready",
    }


@app.post(
    "/payments/authorize",
    response_model=PaymentResponse,
)

def authorize_payment(
    payment: PaymentRequest,
):
    with tracer.start_as_current_span(
        "payment.authorize",
    ) as span:
        span.set_attribute(
            "payment.order_id",
            payment.order_id,
        )

        span.set_attribute(
            "payment.amount_cents",
            payment.amount_cents,
        )

        span.set_attribute(
            "payment.failure_rate",
            PAYMENT_FAILURE_RATE,
        )

        span.set_attribute(
            "payment.delay_seconds",
            PAYMENT_DELAY_SECONDS,
        )

        if PAYMENT_DELAY_SECONDS > 0:
            time.sleep(
                PAYMENT_DELAY_SECONDS
            )

        if random.random() < PAYMENT_FAILURE_RATE:
            span.set_attribute(
                "payment.authorized",
                False,
            )

            logger.error(
                "Payment authorization failed",
                extra={
                    "order_id":
                        payment.order_id,
                },
            )

            raise HTTPException(
                status_code=500,
                detail="Simulated payment authorization failure",
            )

        span.set_attribute(
            "payment.authorized",
            True,
        )

        logger.info(
            "Payment authorized",
            extra={
                "order_id":
                    payment.order_id,
            },
        )

        return PaymentResponse(
            order_id=payment.order_id,
            status="authorized",
            authorization_code=(
                f"AUTH-{payment.order_id}"
            ),
        )