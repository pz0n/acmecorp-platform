import logging
import time
import uuid

from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import (
    FastAPIInstrumentor,
)
from pydantic import BaseModel

from .telemetry import configure_tracing
from .logging_config import configure_logging

configure_logging()
configure_tracing()

logger = logging.getLogger(
    "acmecorp"
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

        time.sleep(0.15)

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
            authorization_code=f"AUTH-{payment.order_id}",
        )