import json
import logging
import time

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/driver/{driver_id}")
async def ws_driver(driver_id: str, websocket: WebSocket):
    """
    Conexión persistente del conductor.

    Ciclo de vida:
    - onconnect  → valida que el driver existe, lo marca available en Redis
    - onmessage  → procesa cada ping GPS: HSET position, PUBLISH Pub/Sub, XADD Stream
    - ondisconnect → lo marca offline y limpia sus keys de Redis

    Mensaje esperado del driver (JSON):
        { "order_id": 4502, "lat": -0.18, "lng": -78.48, "heading": 90, "speed": 32.5 }

    Respuesta por mensaje exitoso:
        { "status": "ok", "ts": 1714601234 }
    """
    await websocket.accept()

    app = websocket.scope["app"]
    redis = app.state.redis
    db = app.state.db

    # ── Validar driver ────────────────────────────────────────────────────────
    try:
        oid = ObjectId(driver_id)
    except InvalidId:
        await websocket.close(code=4400, reason="Invalid driver_id format")
        return

    driver = await db.drivers.find_one({"_id": oid})
    if not driver:
        await websocket.close(code=4404, reason="Driver not found")
        return

    # ── onconnect: marcar disponible ──────────────────────────────────────────
    ts = int(time.time())
    await redis.hset(f"driver:{driver_id}:state", mapping={
        "status": "available",
        "last_seen": ts,
    })
    await redis.sadd("available_drivers", driver_id)
    logger.info("Driver %s connected — marked available", driver_id)

    try:
        async for raw in websocket.iter_text():
            # ── Parsear mensaje ───────────────────────────────────────────────
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "invalid JSON"})
                continue

            required = {"order_id", "lat", "lng", "heading", "speed"}
            missing = required - data.keys()
            if missing:
                await websocket.send_json({"error": f"missing fields: {sorted(missing)}"})
                continue

            ts = int(time.time())

            # ── HSET: posición actual (sobrescribe) ───────────────────────────
            await redis.hset(f"driver:{driver_id}:position", mapping={
                "lat":      data["lat"],
                "lng":      data["lng"],
                "heading":  data["heading"],
                "speed":    data["speed"],
                "order_id": data["order_id"],
                "ts":       ts,
            })

            # ── PUBLISH: fan-out a clientes WebSocket via Pub/Sub ─────────────
            await redis.publish(
                f"delivery:{data['order_id']}",
                json.dumps({
                    "lat":     data["lat"],
                    "lng":     data["lng"],
                    "heading": data["heading"],
                    "speed":   data["speed"],
                    "ts":      ts,
                }),
            )

            # ── XADD: acumular en Stream para flush a Cassandra ───────────────
            await redis.xadd(
                f"driver:{driver_id}:breadcrumbs",
                {
                    "lat":      str(data["lat"]),
                    "lng":      str(data["lng"]),
                    "heading":  str(data["heading"]),
                    "speed":    str(data["speed"]),
                    "ts":       str(ts),
                    "order_id": str(data["order_id"]),
                },
            )

            await websocket.send_json({"status": "ok", "ts": ts})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("Driver WS error for %s: %s", driver_id, e)
    finally:
        # ── ondisconnect: marcar offline y limpiar Redis ──────────────────────
        await redis.srem("available_drivers", driver_id)
        await redis.delete(f"driver:{driver_id}:state")
        await redis.delete(f"driver:{driver_id}:position")
        logger.info("Driver %s disconnected — marked offline", driver_id)
