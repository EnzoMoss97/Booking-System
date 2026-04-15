from datetime import datetime, timedelta

from app.auth import get_password_hash
from app.database import Base, SessionLocal, engine
from app.models import Aircraft, Booking, BookingStatus, BookingType, Cost, Flight, PaymentStatus, Role, Route, User


Base.metadata.create_all(bind=engine)
db = SessionLocal()

if not db.query(User).first():
    users = [
        User(username="admin", hashed_password=get_password_hash("admin123"), role=Role.ADMIN),
        User(username="dispatch", hashed_password=get_password_hash("dispatch123"), role=Role.DISPATCHER),
        User(username="agent", hashed_password=get_password_hash("agent123"), role=Role.AGENT),
        User(username="acct", hashed_password=get_password_hash("acct123"), role=Role.ACCOUNTANT),
    ]
    db.add_all(users)

if not db.query(Aircraft).first():
    db.add_all(
        [
            Aircraft(name="Cessna Caravan 208", max_passengers=12, max_cargo_weight=1200, max_total_weight=2100),
            Aircraft(name="Twin Otter DHC-6", max_passengers=19, max_cargo_weight=1800, max_total_weight=3200),
        ]
    )

if not db.query(Route).first():
    db.add_all([Route(origin="Juba", destination="Wau"), Route(origin="Wau", destination="Malakal")])

db.commit()

if not db.query(Flight).first():
    flight = Flight(aircraft_id=1, route_id=1, departure_time=datetime.utcnow() + timedelta(hours=4), pilot_name="Capt. Deng")
    db.add(flight)
    db.commit()

if not db.query(Booking).first():
    db.add_all(
        [
            Booking(type=BookingType.PAX, status=BookingStatus.CONFIRMED, payment_status=PaymentStatus.PAID, total_price=220, flight_id=1),
            Booking(type=BookingType.CARGO, status=BookingStatus.CONFIRMED, payment_status=PaymentStatus.PAID, total_price=580, flight_id=1),
        ]
    )
    db.add(Cost(flight_id=1, fuel_cost=150, pilot_cost=120, maintenance_cost=60))


db.commit()
db.close()
print("Seed complete")
