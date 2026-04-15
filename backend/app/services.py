import json
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import Booking, BookingStatus, BookingType, Cargo, Cost, Flight, FlightStatus, Passenger

AVG_PASSENGER_WEIGHT_KG = 90


def compute_flight_load(db: Session, flight_id: int) -> dict:
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise ValueError("Flight not found")

    pax_count = db.query(Passenger).filter(Passenger.flight_id == flight_id).count()
    cargo_weight = db.query(func.coalesce(func.sum(Cargo.weight), 0.0)).filter(Cargo.flight_id == flight_id).scalar() or 0.0

    total_weight = pax_count * AVG_PASSENGER_WEIGHT_KG + float(cargo_weight)
    seat_capacity = flight.aircraft.max_passengers
    cargo_capacity = float(flight.aircraft.max_cargo_weight)
    total_capacity = float(flight.aircraft.max_total_weight or (seat_capacity * AVG_PASSENGER_WEIGHT_KG + cargo_capacity))

    overloaded = pax_count > seat_capacity or cargo_weight > cargo_capacity or total_weight > total_capacity
    warning = (
        pax_count >= seat_capacity * 0.9
        or cargo_weight >= cargo_capacity * 0.9
        or total_weight >= total_capacity * 0.9
    )

    status = "OVERLOAD" if overloaded else ("WARNING" if warning else "SAFE")

    return {
        "flight_id": flight_id,
        "pax_count": pax_count,
        "cargo_weight": float(cargo_weight),
        "total_weight": float(total_weight),
        "seat_capacity": seat_capacity,
        "cargo_capacity": cargo_capacity,
        "total_capacity": total_capacity,
        "load_factor": round(total_weight / total_capacity, 3) if total_capacity else 0,
        "indicator": status,
    }


def assert_booking_capacity(db: Session, flight_id: int, booking_type: BookingType, add_weight: float = 0):
    load = compute_flight_load(db, flight_id)
    if booking_type == BookingType.PAX and load["pax_count"] >= load["seat_capacity"]:
        raise ValueError("Passenger capacity exceeded")
    if booking_type == BookingType.CARGO and load["cargo_weight"] + add_weight > load["cargo_capacity"]:
        raise ValueError("Cargo capacity exceeded")


def can_depart(db: Session, flight_id: int) -> tuple[bool, str]:
    load = compute_flight_load(db, flight_id)
    if load["indicator"] == "OVERLOAD":
        return False, "Flight overloaded"

    manifest_count = db.query(Passenger).filter(Passenger.flight_id == flight_id).count()
    if manifest_count == 0:
        return False, "Passenger manifest missing"

    return True, "OK"


def create_awb(cargo_id: int, flight_id: int) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d")
    return f"AWB-{ts}-{flight_id:03d}-{cargo_id:05d}"


def revenue_report(db: Session, monthly: bool = False) -> dict:
    pax_revenue = float(
        db.query(func.coalesce(func.sum(Booking.total_price), 0))
        .filter(Booking.type == BookingType.PAX, Booking.payment_status == "PAID")
        .scalar()
        or 0
    )
    cargo_revenue = float(
        db.query(func.coalesce(func.sum(Booking.total_price), 0))
        .filter(Booking.type == BookingType.CARGO, Booking.payment_status == "PAID")
        .scalar()
        or 0
    )
    total_cost = float(
        db.query(func.coalesce(func.sum(Cost.fuel_cost + Cost.pilot_cost + Cost.maintenance_cost), 0)).scalar() or 0
    )

    total_revenue = pax_revenue + cargo_revenue
    return {
        "period": "monthly" if monthly else "daily",
        "total_revenue": total_revenue,
        "pax_revenue": pax_revenue,
        "cargo_revenue": cargo_revenue,
        "total_cost": total_cost,
        "profit": total_revenue - total_cost,
    }


def serialize_model(model) -> str:
    data = {}
    for k, v in model.__dict__.items():
        if k.startswith("_"):
            continue
        data[k] = str(v) if isinstance(v, datetime) else v
    return json.dumps(data)
