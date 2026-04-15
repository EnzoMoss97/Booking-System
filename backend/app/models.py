import enum
import uuid
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base, utcnow


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    DISPATCHER = "DISPATCHER"
    AGENT = "AGENT"
    ACCOUNTANT = "ACCOUNTANT"


class FlightStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    BOARDING = "boarding"
    DEPARTED = "departed"
    LANDED = "landed"
    CANCELLED = "cancelled"


class BookingType(str, enum.Enum):
    PAX = "PAX"
    CARGO = "CARGO"


class BookingStatus(str, enum.Enum):
    RESERVED = "reserved"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked-in"
    NO_SHOW = "no-show"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Aircraft(Base):
    __tablename__ = "aircraft"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    max_passengers: Mapped[int] = mapped_column(Integer)
    max_cargo_weight: Mapped[float] = mapped_column(Float)
    max_total_weight: Mapped[float] = mapped_column(Float, default=0)


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    origin: Mapped[str] = mapped_column(String(60), index=True)
    destination: Mapped[str] = mapped_column(String(60), index=True)


class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aircraft_id: Mapped[int] = mapped_column(ForeignKey("aircraft.id"), nullable=False)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), nullable=False)
    departure_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    pilot_name: Mapped[str] = mapped_column(String(120), default="TBD")
    status: Mapped[FlightStatus] = mapped_column(Enum(FlightStatus), default=FlightStatus.SCHEDULED)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    aircraft: Mapped[Aircraft] = relationship()
    route: Mapped[Route] = relationship()


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), index=True)
    type: Mapped[BookingType] = mapped_column(Enum(BookingType), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.RESERVED)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    flight_id: Mapped[int | None] = mapped_column(ForeignKey("flights.id"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Passenger(Base):
    __tablename__ = "passengers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    contact: Mapped[str] = mapped_column(String(120))
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flights.id"), nullable=False)
    checked_in: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=utcnow)


class Cargo(Base):
    __tablename__ = "cargo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    awb_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    shipper: Mapped[str] = mapped_column(String(120))
    receiver: Mapped[str] = mapped_column(String(120))
    weight: Mapped[float] = mapped_column(Float)
    cargo_type: Mapped[str] = mapped_column(String(80))
    price: Mapped[float] = mapped_column(Numeric(12, 2))
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flights.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(40))
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    timestamp: Mapped[DateTime] = mapped_column(DateTime, default=utcnow)


class Cost(Base):
    __tablename__ = "costs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flights.id"), nullable=False, unique=True)
    fuel_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    pilot_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    maintenance_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)


class SyncEvent(Base):
    __tablename__ = "sync_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(60), index=True)
    entity_id: Mapped[str] = mapped_column(String(60), index=True)
    operation: Mapped[str] = mapped_column(String(20))
    payload: Mapped[str] = mapped_column(Text)
    device_id: Mapped[str] = mapped_column(String(80), index=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=utcnow, index=True)
