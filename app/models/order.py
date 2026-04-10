from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


class OrderItem(BaseModel):
    qty: int
    name: str
    unit_price: float


class TimelineEvent(BaseModel):
    status: str
    ts: datetime
    actor: str


class OrderCreate(BaseModel):
    order_id: int
    customer_id: int
    items_summary: list[OrderItem]
    timeline: list[TimelineEvent] = Field(default_factory=list)
    driver_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None


class OrderResponse(OrderCreate):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
