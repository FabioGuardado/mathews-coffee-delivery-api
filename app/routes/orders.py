from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.database import get_db
from app.models.order import OrderCreate, OrderResponse, TimelineEvent

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
    query = {}

    # FILTRO 1: status
    if status:
        query["$expr"] = {"$eq": [{"$last": "$timeline.status"}, status]}

    # FILTRO 2: customer_id
    if customer_id:
        query["customer_id"] = customer_id

    # FILTRO 3: rango de total
    if min_total is not None or max_total is not None:
        query["total"] = {}
        if min_total is not None:
            query["total"]["$gte"] = min_total
        if max_total is not None:
            query["total"]["$lte"] = max_total

    # Paginación
    skip = (page - 1) * limit

    cursor = db.orders.find(query).skip(skip).limit(limit)
    orders = await cursor.to_list(length=limit)
    total = await db.orders.count_documents(query)

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
async def append_timeline_event(id: str, event: TimelineEvent, db=Depends(get_db)):
    oid = parse_object_id(id)
    update: dict = {"$push": {"timeline": event.model_dump()}}
    if event.status == "delivered":
        update["$set"] = {"delivered_at": event.ts}
    result = await db.orders.update_one({"_id": oid}, update)
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    updated = await db.orders.find_one({"_id": oid})
    return updated
