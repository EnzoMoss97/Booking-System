from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from .auth import create_access_token, verify_password
from .database import Base, engine
from .deps import get_db, require_roles
from .models import (
    Aircraft,
    Booking,
    BookingStatus,
    BookingType,
    Cargo,
    Cost,
    Flight,
    FlightStatus,
    Passenger,
    PaymentStatus,
    Role,
    Route,
    SyncEvent,
    User,
)
from .schemas import (
    BookingCreate,
    BookingOut,
    CargoCreate,
    CargoOut,
    CostCreate,
    FlightCreate,
    FlightOut,
    FlightPatch,
    LoginRequest,
    PassengerCheckIn,
    PassengerCreate,
    RevenueReport,
    SyncPushItem,
    Token,
)
from .services import assert_booking_capacity, can_depart, compute_flight_load, create_awb, revenue_report, serialize_model

app = FastAPI(title="Aviation Booking & Operations API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.post("/auth/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username, "role": user.role.value})
    return Token(access_token=token)


@app.get("/flights", response_model=list[FlightOut])
def get_flights(db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.DISPATCHER, Role.AGENT, Role.ACCOUNTANT))):
    return db.query(Flight).order_by(Flight.departure_time.asc()).all()


@app.post("/flights", response_model=FlightOut)
def create_flight(payload: FlightCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.DISPATCHER))):
    flight = Flight(**payload.model_dump())
    db.add(flight)
    db.commit()
    db.refresh(flight)
    return flight


@app.patch("/flights/{flight_id}", response_model=FlightOut)
def patch_flight(flight_id: int, payload: FlightPatch, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.DISPATCHER))):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(flight, k, v)

    if payload.status == FlightStatus.DEPARTED:
        ok, message = can_depart(db, flight_id)
        if not ok:
            raise HTTPException(status_code=400, detail=f"Cannot depart: {message}")

    db.commit()
    db.refresh(flight)
    return flight


@app.post("/bookings", response_model=BookingOut)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.AGENT))):
    assert_booking_capacity(db, payload.flight_id, payload.type)
    booking = Booking(**payload.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@app.get("/bookings", response_model=list[BookingOut])
def get_bookings(db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.AGENT, Role.ACCOUNTANT))):
    return db.query(Booking).order_by(Booking.id.desc()).all()


@app.post("/passengers")
def create_passenger(payload: PassengerCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.AGENT))):
    booking = db.query(Booking).filter(Booking.id == payload.booking_id, Booking.type == BookingType.PAX).first()
    if not booking:
        raise HTTPException(status_code=404, detail="PAX booking not found")
    p = Passenger(**payload.model_dump())
    db.add(p)
    booking.status = BookingStatus.CONFIRMED
    db.commit()
    db.refresh(p)
    return p


@app.post("/passengers/checkin")
def passenger_checkin(payload: PassengerCheckIn, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.AGENT, Role.DISPATCHER))):
    pax = db.query(Passenger).filter(Passenger.id == payload.passenger_id).first()
    if not pax:
        raise HTTPException(status_code=404, detail="Passenger not found")
    pax.checked_in = True
    booking = db.query(Booking).filter(Booking.id == pax.booking_id).first()
    if booking:
        booking.status = BookingStatus.CHECKED_IN
    db.commit()
    return {"message": "Passenger checked in"}


@app.post("/cargo", response_model=CargoOut)
def create_cargo(payload: CargoCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.AGENT))):
    booking = db.query(Booking).filter(Booking.id == payload.booking_id, Booking.type == BookingType.CARGO).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Cargo booking not found")

    assert_booking_capacity(db, payload.flight_id, BookingType.CARGO, payload.weight)
    c = Cargo(
        **payload.model_dump(),
        awb_number=f"TEMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )
    db.add(c)
    db.flush()
    c.awb_number = create_awb(c.id, c.flight_id)
    booking.status = BookingStatus.CONFIRMED
    db.commit()
    db.refresh(c)
    return c


@app.get("/cargo", response_model=list[CargoOut])
def get_cargo(db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.AGENT, Role.DISPATCHER, Role.ACCOUNTANT))):
    return db.query(Cargo).order_by(Cargo.id.desc()).all()


@app.post("/costs")
def create_cost(payload: CostCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.ACCOUNTANT))):
    cost = db.query(Cost).filter(Cost.flight_id == payload.flight_id).first()
    if not cost:
        cost = Cost(**payload.model_dump())
        db.add(cost)
    else:
        for k, v in payload.model_dump().items():
            setattr(cost, k, v)
    db.commit()
    return {"message": "Cost saved"}


@app.get("/reports/revenue", response_model=RevenueReport)
def report_revenue(period: str = "daily", db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.ACCOUNTANT))):
    return revenue_report(db, monthly=period == "monthly")


@app.get("/reports/flights")
def report_flights(date: str | None = None, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.DISPATCHER, Role.ACCOUNTANT))):
    query = db.query(Flight)
    if date:
        query = query.filter(func.date(Flight.departure_time) == date)
    flights = query.all()

    rows = []
    for f in flights:
        load = compute_flight_load(db, f.id)
        rows.append({
            "flight_id": f.id,
            "departure_time": f.departure_time,
            "aircraft": f.aircraft.name,
            "route": f"{f.route.origin}-{f.route.destination}",
            "status": f.status,
            **load,
        })
    return rows


@app.get("/dashboard/dispatch")
def dispatch_dashboard(db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.DISPATCHER, Role.ACCOUNTANT))):
    today = datetime.utcnow().date()
    flights = db.query(Flight).filter(func.date(Flight.departure_time) == today).all()
    data = []
    for f in flights:
        load = compute_flight_load(db, f.id)
        data.append(
            {
                "flight_id": f.id,
                "departure_time": f.departure_time,
                "aircraft": f.aircraft.name,
                "status": f.status,
                "passengers": load["pax_count"],
                "cargo_weight": load["cargo_weight"],
                "load_factor": load["load_factor"],
                "indicator": load["indicator"],
            }
        )
    return data


@app.get("/sync/pull")
def sync_pull(since: datetime, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.AGENT, Role.DISPATCHER))):
    events = db.query(SyncEvent).filter(SyncEvent.updated_at > since).order_by(SyncEvent.updated_at.asc()).all()
    return events


@app.post("/sync/push")
def sync_push(items: list[SyncPushItem], db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN, Role.AGENT, Role.DISPATCHER))):
    applied = []
    for item in items:
        existing = (
            db.query(SyncEvent)
            .filter(SyncEvent.entity_name == item.entity_name, SyncEvent.entity_id == item.entity_id)
            .order_by(SyncEvent.updated_at.desc())
            .first()
        )
        if existing and existing.updated_at > item.updated_at:
            continue  # Last-write-wins conflict resolution

        ev = SyncEvent(**item.model_dump())
        db.add(ev)
        applied.append({"entity": item.entity_name, "entity_id": item.entity_id})
    db.commit()
    return {"applied": applied, "strategy": "last-write-wins with audit trail"}


@app.post("/sync/record/{entity}/{entity_id}")
def sync_record(entity: str, entity_id: str, device_id: str, db: Session = Depends(get_db)):
    ev = SyncEvent(entity_name=entity, entity_id=entity_id, operation="UPSERT", payload="{}", device_id=device_id)
    db.add(ev)
    db.commit()
    return {"ok": True}


@app.get("/health")
def health():
    return {"status": "ok"}
