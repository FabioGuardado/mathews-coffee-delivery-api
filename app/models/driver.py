from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


class Vehicle(BaseModel):
    type: str
    plate: str


class DriverCreate(BaseModel):
    name: str
    lastname: str
    phone: str
    vehicle: Vehicle
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DriverResponse(DriverCreate):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
