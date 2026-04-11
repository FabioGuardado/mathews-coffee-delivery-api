from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.database import get_db
from app.models.driver import DriverCreate, DriverResponse

router = APIRouter()


def parse_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id format")

@router.get("/")
async def list_drivers(
    name: str | None = Query(None),
    active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):
    query = {}

    # Filtro 1: nombre (búsqueda parcial)
    if name:
        query["name"] = {"$regex": name, "$options": "i"}

    # Filtro 2: activo
    if active is not None:
        query["active"] = active

    # Paginación
    skip = (page - 1) * limit

    # Consulta con filtros y paginación
    cursor = db.drivers.find(query).skip(skip).limit(limit)
    drivers = await cursor.to_list(length=limit)
    total = await db.drivers.count_documents(query)

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": drivers
    }

"""@router.get("/", response_model=list[DriverResponse])
async def list_drivers(db=Depends(get_db)):
    drivers = await db.drivers.find().to_list(length=None)
    return drivers"""

@router.get("/{id}", response_model=DriverResponse)
async def get_driver(id: str, db=Depends(get_db)):
    driver = await db.drivers.find_one({"_id": parse_object_id(id)})
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver


@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(payload: DriverCreate, db=Depends(get_db)):
    doc = payload.model_dump()
    result = await db.drivers.insert_one(doc)
    created = await db.drivers.find_one({"_id": result.inserted_id})
    return created


@router.patch("/{id}/active", response_model=DriverResponse)
async def toggle_active(id: str, active: bool, db=Depends(get_db)):
    oid = parse_object_id(id)
    result = await db.drivers.update_one({"_id": oid}, {"$set": {"active": active}})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    updated = await db.drivers.find_one({"_id": oid})
    return updated


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(id: str, db=Depends(get_db)):
    result = await db.drivers.delete_one({"_id": parse_object_id(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
