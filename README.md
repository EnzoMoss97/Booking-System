# Aviation Booking & Operations System

Production-style reference implementation for small-aircraft interior operations handling PAX + Cargo.

## Features
- Flight operations lifecycle (scheduled → boarding → departed → landed/cancelled)
- Passenger and cargo bookings
- Load control with overload prevention
- Dispatch dashboard (SAFE / WARNING / OVERLOAD)
- Revenue + cost + profit reporting
- JWT auth and role-based access (Admin, Dispatcher, Agent, Accountant)
- Offline sync design for low-connectivity outstations (SQLite mode)

## Quick start
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

Open Swagger: `http://localhost:8000/docs`

## Frontend
```bash
cd frontend
npm install
npm run dev
```

Set API URL via `VITE_API_URL` (default `http://localhost:8000`).

## Docker deploy
1. Place TLS certs in `ssl/server.crt` and `ssl/server.key`
2. Run:
```bash
docker compose up --build
```

## API endpoints (minimum)
- `GET /flights`
- `POST /flights`
- `PATCH /flights/{id}`
- `POST /bookings`
- `GET /bookings`
- `POST /passengers/checkin`
- `POST /cargo`
- `GET /cargo`
- `GET /reports/revenue`
- `GET /reports/flights`

## Default seeded users
- `admin / admin123`
- `dispatch / dispatch123`
- `agent / agent123`
- `acct / acct123`
