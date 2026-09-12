import logging
import time
from urllib import request
import uuid
import os
import httpx    

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry import (
    metrics,
    trace,
)
from opentelemetry.instrumentation.httpx import (
    HTTPXClientInstrumentor,
)

from .telemetry import (
    configure_tracing,
    configure_metrics,
)

from .database import Base, engine, get_db
from .models import Order
from .schemas import OrderCreate, OrderResponse
from .logging_config import configure_logging


PAYMENTS_API_URL = os.getenv(
    "PAYMENTS_API_URL",
    "http://payments-api:8001",
)

configure_logging()
configure_tracing()
configure_metrics()


logger = logging.getLogger("acmecorp")

meter = metrics.get_meter("orders-api")
tracer = trace.get_tracer("orders-api")

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
    title="AcmeCorp Orders API",
    version="0.4.0",
)


Base.metadata.create_all(bind=engine)


FastAPIInstrumentor.instrument_app(app)

SQLAlchemyInstrumentor().instrument(
    engine=engine,
)

HTTPXClientInstrumentor().instrument()

@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    request_id = request.headers.get(
        "X-Request-ID",
        str(uuid.uuid4()),
    )

    request.state.request_id = request_id

    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        response.headers["X-Request-ID"] = request_id

        route = request.scope.get("route")
        route_path = getattr(
            route,
            "path",
            request.url.path,
        )

        attributes = {
            "http.request.method": request.method,
            "http.route": route_path,
            "http.response.status_code": response.status_code,
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
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

        return response

    except Exception:
        duration_ms = (
            time.perf_counter() - start_time
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
                "duration_ms": round(duration_ms, 2),
            },
        )

        raise


def simulate_inventory_check() -> None:
    delay_seconds = float(
        os.getenv(
            "INVENTORY_DELAY_SECONDS",
            "0",
        )
    )

    with tracer.start_as_current_span(
        "inventory.check",
    ) as span:
        span.set_attribute(
            "inventory.provider",
            "legacy-inventory-system",
        )
        span.set_attribute(
            "inventory.delay_seconds",
            delay_seconds,
        )
        span.set_attribute(
            "incident.simulated",
            True,
        )

        time.sleep(delay_seconds)

@app.get("/")
def root():
    return {
        "service": "orders-api",
        "status": "running",
    }


@app.get("/health/live")
def liveness():
    return {
        "status": "alive",
    }


@app.get("/health/ready")
def readiness(
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "database": "reachable",
        }

    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return {
            "status": "not_ready",
            "database": "unreachable",
        }


@app.post(
    "/orders",
    response_model=OrderResponse,
    status_code=201,
)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
):
    order = Order(
        customer_id=order_data.customer_id,
        product=order_data.product,
        quantity=order_data.quantity,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


@app.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order

@app.post("/orders/{order_id}/checkout")
def checkout_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    order = db.get(
        Order,
        order_id,
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    payment_request = {
        "order_id": order.id,
        "customer_id": order.customer_id,
        "amount_cents": order.quantity * 1000,
    }

    try:
        with httpx.Client(
            timeout=3.0,
        ) as client:
            payment_response = client.post(
                (
                    f"{PAYMENTS_API_URL}"
                    "/payments/authorize"
                ),
                json=payment_request,
                headers={
                    "X-Request-ID":
                        request.state.request_id,
                },
            )

            payment_response.raise_for_status()

    # we use 504 when the Orders successfully sent the request to the Payments API, but the Payments API did not respond in time
    except httpx.TimeoutException:
        logger.error(
            "Payments API request timed out",
            extra={
                "request_id":
                    request.state.request_id,
            },
        )

        raise HTTPException(
            status_code=504,
            detail="Payments service timed out",
        )

    # we use 502 when the downstream dependecy (Payments API) returned an error, or when the Payments API is unavailable
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Payments API returned an error",
            extra={
                "request_id":
                    request.state.request_id,
                "status_code":
                    exc.response.status_code,
            },
        )

        raise HTTPException(
            status_code=502,
            detail="Payments service returned an error",
        )

    except httpx.RequestError:
        logger.exception(
            "Payments API unavailable",
            extra={
                "request_id":
                    request.state.request_id,
            },
        )

        raise HTTPException(
            status_code=502,
            detail="Payments service unavailable",
        )

    return {
        "order_id": order.id,
        "order_status": order.status,
        "payment": payment_response.json(),
    }

@app.get("/debug/error")
def debug_error():
    raise RuntimeError("Simulated application failure")


@app.get("/debug/slow-order/{order_id}")
def slow_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    simulate_inventory_check()

    order = db.get(Order, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order

