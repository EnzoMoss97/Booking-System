from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

from .models import BookingStatus, BookingType, FlightStatus, PaymentStatus, Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    role: Role

    class Config:
        from_attributes = True


class FlightCreate(BaseModel):
    aircraft_id: int
    route_id: int
    departure_time: datetime
    pilot_name: str


class FlightPatch(BaseModel):
    status: FlightStatus | None = None
    aircraft_id: int | None = None
    route_id: int | None = None
    departure_time: datetime | None = None
    pilot_name: str | None = None


class FlightOut(BaseModel):
    id: int
    aircraft_id: int
    route_id: int
    departure_time: datetime
    pilot_name: str
    status: FlightStatus

    class Config:
        from_attributes = True


class BookingCreate(BaseModel):
    type: BookingType
    status: BookingStatus = BookingStatus.RESERVED
    payment_status: PaymentStatus = PaymentStatus.PENDING
    total_price: float
    flight_id: int


class BookingOut(BaseModel):
    id: int
    type: BookingType
    status: BookingStatus
    payment_status: PaymentStatus
    total_price: float
    flight_id: int | None

    class Config:
        from_attributes = True


class PassengerCreate(BaseModel):
    name: str
    contact: str
    booking_id: int
    flight_id: int


class PassengerCheckIn(BaseModel):
    passenger_id: int


class CargoCreate(BaseModel):
    booking_id: int
    flight_id: int
    shipper: str
    receiver: str
    cargo_type: str
    weight: float = Field(gt=0)
    price: float


class CargoOut(BaseModel):
    id: int
    awb_number: str
    shipper: str
    receiver: str
    cargo_type: str
    weight: float
    price: float
    flight_id: int

    class Config:
        from_attributes = True


class CostCreate(BaseModel):
    flight_id: int
    fuel_cost: float = 0
    pilot_cost: float = 0
    maintenance_cost: float = 0


class RevenueReport(BaseModel):
    period: Literal["daily", "monthly"]
    total_revenue: float
    pax_revenue: float
    cargo_revenue: float
    total_cost: float
    profit: float


class SyncPushItem(BaseModel):
    entity_name: str
    entity_id: str
    operation: str
    payload: str
    device_id: str
    updated_at: datetime
