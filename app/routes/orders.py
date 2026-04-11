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

@router.get("/")
async def list_orders(
    status: str | None = Query(None),
    customer_id: str | None = Query(None),
    min_total: float | None = Query(None),
    max_total: float | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):
    query = {}

    # FILTRO 1: status
    if status:
        query["status"] = status

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

    # Consulta con filtros y paginación
    cursor = db.orders.find(query).skip(skip).limit(limit)
    orders = await cursor.to_list(length=limit)
    total = await db.orders.count_documents(query)

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": orders
    }

"""@router.get("/", response_model=list[OrderResponse])
async def list_orders(db=Depends(get_db)):
    orders = await db.orders.find().to_list(length=None)
    return orders"""


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


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(id: str, db=Depends(get_db)):
    result = await db.orders.delete_one({"_id": parse_object_id(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
