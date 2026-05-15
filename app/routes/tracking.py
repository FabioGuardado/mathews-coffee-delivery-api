import json
import time
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.cassandra import cassandra_execute, get_cassandra
from app.redis import get_redis

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class GPSPing(BaseModel):
    driver_id: str
    order_id: int
    lat: float
    lng: float
    heading: int
    speed: float


# ── GPS history queries ───────────────────────────────────────────────────────

@router.get("/drivers/{driver_id}/gps-history")
async def gps_history_by_driver(
    driver_id: str,
    date: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    cassandra=Depends(get_cassandra),
):
    """
    Retorna el historial GPS de un driver para un día específico.
    Consulta la tabla gps_by_driver particionada por (driver_id, day).
    """
    day = datetime.strptime(date, "%Y-%m-%d").date()
    rows = await cassandra_execute(
        cassandra,
        "SELECT ts, lat, lng, heading, speed, order_id FROM gps_by_driver "
        "WHERE driver_id = %s AND day = %s",
        (driver_id, day),
    )
    points = [
        {
            "ts": row.ts.isoformat(),
            "lat": row.lat,
            "lng": row.lng,
            "heading": row.heading,
            "speed": row.speed,
            "order_id": row.order_id,
        }
        for row in rows
    ]
    return {"driver_id": driver_id, "date": date, "points": points}


@router.get("/orders/{order_id}/gps-trail")
async def gps_trail_by_order(
    order_id: int,
    cassandra=Depends(get_cassandra),
):
    """
    Retorna el trail GPS completo de una orden.
    Consulta la tabla gps_by_order particionada por order_id.
    """
    rows = await cassandra_execute(
        cassandra,
        "SELECT ts, lat, lng, heading, speed, driver_id FROM gps_by_order "
        "WHERE order_id = %s",
        (order_id,),
    )
    points = [
        {
            "ts": row.ts.isoformat(),
            "lat": row.lat,
            "lng": row.lng,
            "heading": row.heading,
            "speed": row.speed,
            "driver_id": row.driver_id,
        }
        for row in rows
    ]
    return {"order_id": order_id, "points": points}
