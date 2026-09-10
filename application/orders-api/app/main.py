from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Order
from .schemas import OrderCreate, OrderResponse

app = FastAPI(
    title="AcmeCorp Orders API",
    version="0.3.0",
)


Base.metadata.create_all(bind=engine)


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