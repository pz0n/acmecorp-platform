from fastapi import FastAPI

app = FastAPI(
    title="AcmeCorp Orders API",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "service": "orders-api",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    return {
        "order_id": order_id,
        "customer_id": 42,
        "product": "Acme Cloud Mug",
        "quantity": 2,
        "status": "confirmed"
    }