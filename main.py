from fastapi import FastAPI

from app.database import lifespan
from app.routes import drivers, orders
from app.routes import tracking, ws, driver_ws

app = FastAPI(title="Mathews Coffee Delivery API", lifespan=lifespan)

app.include_router(drivers.router, prefix="/drivers", tags=["drivers"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(tracking.router, tags=["tracking"])
app.include_router(ws.router, prefix="/ws", tags=["websocket"])
app.include_router(driver_ws.router, prefix="/ws", tags=["websocket"])


@app.get("/")
def read_root():
    return {"status": "ok", "service": "Mathews Coffee Delivery API"}
