import asyncio
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.redis import REDIS_URL

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Room manager ──────────────────────────────────────────────────────────────
# dict[order_id, set[asyncio.Queue]]
#
# _broadcast NEVER touches a WebSocket directly.
# It only puts messages into queues — each queue is owned exclusively by
# one _sender coroutine, which is the sole writer on that WebSocket.
# This eliminates the concurrent-send race that was causing delivery failures.

_SENTINEL = object()  # poison-pill: tells _sender to stop

rooms: dict[str, set[asyncio.Queue]] = {}


def _join_room(order_id: str, q: asyncio.Queue) -> None:
    rooms.setdefault(order_id, set()).add(q)


def _leave_room(order_id: str, q: asyncio.Queue) -> None:
    if order_id in rooms:
        rooms[order_id].discard(q)
        if not rooms[order_id]:
            del rooms[order_id]


async def _broadcast(order_id: str, message: str) -> None:
    """Fan-out to all queues in the room. Non-blocking."""
    for q in rooms.get(order_id, set()).copy():
        q.put_nowait(message)


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/delivery/{order_id}")
async def ws_delivery(order_id: str, websocket: WebSocket):
    """
    Flujo al conectar:
    1. Leer order:{order_id}:state → obtener driver_id
    2. Leer driver:{driver_id}:position → seed position
    3. Enviar {type: "seed", ...position} al cliente
    4. Entrar al room con un asyncio.Queue dedicado
    5. _sender: único dueño del WebSocket para writes — lee del queue
    6. _receiver: detecta disconnect leyendo del WS
    7. El primero que termine cancela al otro
    """
    await websocket.accept()

    app = websocket.scope["app"]
    redis = app.state.redis

    # ── Seed: posición actual antes de que Pub/Sub tome el relevo ────────────
    try:
        order_state = await redis.hgetall(f"order:{order_id}:state")
        if order_state and order_state.get("driver_id"):
            position = await redis.hgetall(f"driver:{order_state['driver_id']}:position")
            if position:
                await websocket.send_json({"type": "seed", **position})
    except Exception as e:
        logger.error("Seed error for order %s: %s", order_id, e)

    # ── Room registration ─────────────────────────────────────────────────────
    q: asyncio.Queue = asyncio.Queue()
    _join_room(order_id, q)

    # ── Inner tasks ───────────────────────────────────────────────────────────

    async def _sender() -> None:
        """
        Sole writer on this WebSocket.
        Reads from queue until _SENTINEL or until cancelled.
        """
        while True:
            item = await q.get()
            if item is _SENTINEL:
                break
            try:
                await websocket.send_text(item)
            except Exception as exc:
                logger.debug("send_text failed for order %s: %s", order_id, exc)
                break

    async def _receiver() -> None:
        """
        Sole reader on this WebSocket.
        Exits on WebSocketDisconnect or any error.
        """
        try:
            while True:
                await websocket.receive_text()
        except (WebSocketDisconnect, Exception):
            pass

    try:
        sender_task = asyncio.create_task(_sender())
        receiver_task = asyncio.create_task(_receiver())

        # Wait for whichever finishes first (disconnect or send error)
        done, pending = await asyncio.wait(
            {sender_task, receiver_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        for t in pending:
            t.cancel()
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass

    except Exception as e:
        logger.error("WebSocket error for order %s: %s", order_id, e)
    finally:
        _leave_room(order_id, q)
        # Unblock _sender if it's still waiting on q.get()
        q.put_nowait(_SENTINEL)


# ── Pub/Sub background task ───────────────────────────────────────────────────

async def start_pubsub_listener(app) -> None:
    """
    Background task iniciado en el lifespan.
    Usa una conexión Redis dedicada (Pub/Sub no puede mezclarse con comandos regulares).
    Escucha delivery:* y hace fan-out a los rooms via asyncio.Queue.
    """
    redis_sub = aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = redis_sub.pubsub()
    await pubsub.psubscribe("delivery:*")
    logger.info("Pub/Sub listener active — subscribed to delivery:*")

    try:
        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue
            # channel = "delivery:4502"
            order_id = message["channel"].split(":", 1)[1]
            await _broadcast(order_id, message["data"])

    except asyncio.CancelledError:
        await pubsub.punsubscribe("delivery:*")
        await redis_sub.aclose()
        raise
    except Exception as e:
        logger.error("Pub/Sub listener crashed: %s", e)
        await redis_sub.aclose()
