import time

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.database import get_db
from app.models.order import OrderCreate, OrderResponse, TimelineEvent
from app.redis import get_redis

router = APIRouter()


def parse_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id format")


def serialize_order(doc: dict) -> dict:
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


@router.get("/")
async def list_orders(
    status: str | None = Query(None),
    customer_id: int | None = Query(None),
    min_total: float | None = Query(None),
    max_total: float | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):
    skip = (page - 1) * limit

    pipeline = []

    pipeline.append({
        "$addFields": {
            "total": {
                "$sum": {
                    "$map": {
                        "input": "$items_summary",
                        "as": "item",
                        "in": {
                            "$multiply": ["$$item.qty", "$$item.unit_price"]
                        }
                    }
                }
            }
        }
    })

    pipeline.append({
        "$addFields": {
            "last_status": {
                "$arrayElemAt": ["$timeline.status", -1]
            }
        }
    })

    match_stage = {}

    if status:
        match_stage["last_status"] = status

    if customer_id:
        match_stage["customer_id"] = customer_id

    if min_total is not None or max_total is not None:
        match_stage["total"] = {}
        if min_total is not None:
            match_stage["total"]["$gte"] = min_total
        if max_total is not None:
            match_stage["total"]["$lte"] = max_total

    if match_stage:
        pipeline.append({"$match": match_stage})

    pipeline.extend([
        {"$skip": skip},
        {"$limit": limit}
    ])

    cursor = db.orders.aggregate(pipeline)
    orders = await cursor.to_list(length=limit)

    count_pipeline = pipeline[:-2] + [{"$count": "total"}]
    count_result = await db.orders.aggregate(count_pipeline).to_list(length=1)
    total = count_result[0]["total"] if count_result else 0

    serialized_orders = [serialize_order(order) for order in orders]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": serialized_orders
    }

@router.get("/by-driver")
async def list_orders_by_driver(
    driver_name: str = Query(...),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):
    skip = (page - 1) * limit
    pipeline = [
        {"$addFields": {"driver_oid": {"$toObjectId": "$driver_id"}}},
        {
            "$lookup": {
                "from": "drivers",
                "localField": "driver_oid",
                "foreignField": "_id",
                "as": "driver"
            }
        },
        {"$unwind": {"path": "$driver", "preserveNullAndEmptyArrays": True}},
        {
            "$match": {
                "$or": [
                    {"driver.name": {"$regex": driver_name, "$options": "i"}},
                    {"driver.lastname": {"$regex": driver_name, "$options": "i"}},
                ]
            }
        },
    ]

    count_result = await db.orders.aggregate(
        pipeline + [{"$count": "total"}]
    ).to_list(length=1)
    total = count_result[0]["total"] if count_result else 0

    cursor = db.orders.aggregate(
        pipeline + [{"$skip": skip}, {"$limit": limit}, {"$unset": ["driver", "driver_oid"]}]
    )
    orders = await cursor.to_list(length=limit)
    serialized_orders = [serialize_order(order) for order in orders]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": serialized_orders
    }

@router.get("/{id}", response_model=OrderResponse)
async def get_order(id: str, db=Depends(get_db)):
    order = await db.orders.find_one({"_id": parse_object_id(id)})
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderCreate, db=Depends(get_db)):
    doc = payload.model_dump()
    result = await db.orders.insert_one(doc)
    created = await db.orders.find_one({"_id": result.inserted_id})
    return created


@router.put("/{id}", response_model=OrderResponse)
async def update_order(id: str, payload: OrderCreate, db=Depends(get_db)):
    oid = parse_object_id(id)
    result = await db.orders.replace_one({"_id": oid}, payload.model_dump())
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    updated = await db.orders.find_one({"_id": oid})
    return updated


@router.post("/{id}/timeline", response_model=OrderResponse)
async def append_timeline_event(
    id: str,
    event: TimelineEvent,
    db=Depends(get_db),
    redis=Depends(get_redis),
):
    oid = parse_object_id(id)
    update: dict = {"$push": {"timeline": event.model_dump()}}
    if event.status == "delivered":
        update["$set"] = {"delivered_at": event.ts}

    result = await db.orders.update_one({"_id": oid}, update)
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    updated = await db.orders.find_one({"_id": oid})

    # ── Redis: sync live order state ──────────────────────────────────────────
    order_id = updated["order_id"]  # int
    ts = int(time.time())

    if event.status == "delivered":
        # Limpieza completa: eliminar estado de la orden
        await redis.delete(f"order:{order_id}:state")

        # Devolver al driver al pool de disponibles
        if updated.get("driver_id"):
            driver_id = updated["driver_id"]
            await redis.hset(f"driver:{driver_id}:state", mapping={
                "status": "available",
                "last_seen": ts,
            })
            await redis.sadd("available_drivers", driver_id)
    else:
        # Transición normal: actualizar estado
        await redis.hset(f"order:{order_id}:state", mapping={
            "status": event.status,
            "updated_at": ts,
        })

    return updated


# ── Order assignment ──────────────────────────────────────────────────────────

class AssignPayload(BaseModel):
    driver_id: str


@router.post("/{id}/assign", response_model=OrderResponse)
async def assign_driver(
    id: str,
    payload: AssignPayload,
    db=Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Asigna un driver a una orden.
    - Actualiza driver_id en MongoDB
    - Remueve al driver del pool de disponibles
    - Inicializa el estado live de la orden en Redis
    """
    oid = parse_object_id(id)
    order = await db.orders.find_one({"_id": oid})
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Verificar que el driver está disponible
    is_available = await redis.sismember("available_drivers", payload.driver_id)
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Driver is not available",
        )

    # Actualizar MongoDB
    await db.orders.update_one({"_id": oid}, {"$set": {"driver_id": payload.driver_id}})
    updated = await db.orders.find_one({"_id": oid})

    # ── Redis ─────────────────────────────────────────────────────────────────
    ts = int(time.time())
    order_id = updated["order_id"]  # int

    # Sacar al driver del pool
    await redis.srem("available_drivers", payload.driver_id)

    # Marcar driver como ocupado
    await redis.hset(f"driver:{payload.driver_id}:state", mapping={
        "status": "busy",
        "last_seen": ts,
    })

    # Inicializar estado live de la orden
    await redis.hset(f"order:{order_id}:state", mapping={
        "status": "pending",
        "driver_id": payload.driver_id,
        "updated_at": ts,
    })

    return updated
