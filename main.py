from fastapi import FastAPI

from app.database import lifespan
from app.routes import drivers, orders

app = FastAPI(title="Mathews Coffee Delivery API", lifespan=lifespan)

app.include_router(drivers.router, prefix="/drivers", tags=["drivers"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])


@app.get("/")
def read_root():
    return {"status": "ok", "service": "Mathews Coffee Delivery API"}
