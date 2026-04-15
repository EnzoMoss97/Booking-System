CREATE TABLE IF NOT EXISTS aircraft (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL,
    max_passengers INT NOT NULL,
    max_cargo_weight NUMERIC(12,2) NOT NULL,
    max_total_weight NUMERIC(12,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS routes (
    id SERIAL PRIMARY KEY,
    origin VARCHAR(60) NOT NULL,
    destination VARCHAR(60) NOT NULL
);

CREATE TABLE IF NOT EXISTS flights (
    id SERIAL PRIMARY KEY,
    aircraft_id INT NOT NULL REFERENCES aircraft(id),
    route_id INT NOT NULL REFERENCES routes(id),
    departure_time TIMESTAMP NOT NULL,
    pilot_name VARCHAR(120) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled'
);

CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    type VARCHAR(10) NOT NULL CHECK (type IN ('PAX', 'CARGO')),
    status VARCHAR(20) NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    total_price NUMERIC(12,2) NOT NULL,
    flight_id INT REFERENCES flights(id)
);

CREATE TABLE IF NOT EXISTS passengers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    contact VARCHAR(120) NOT NULL,
    booking_id INT NOT NULL REFERENCES bookings(id),
    flight_id INT NOT NULL REFERENCES flights(id),
    checked_in BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS cargo (
    id SERIAL PRIMARY KEY,
    weight NUMERIC(10,2) NOT NULL,
    cargo_type VARCHAR(80) NOT NULL,
    shipper VARCHAR(120) NOT NULL,
    receiver VARCHAR(120) NOT NULL,
    price NUMERIC(12,2) NOT NULL,
    awb_number VARCHAR(30) UNIQUE NOT NULL,
    booking_id INT NOT NULL REFERENCES bookings(id),
    flight_id INT NOT NULL REFERENCES flights(id)
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    booking_id INT NOT NULL REFERENCES bookings(id),
    amount NUMERIC(12,2) NOT NULL,
    method VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS costs (
    id SERIAL PRIMARY KEY,
    flight_id INT NOT NULL UNIQUE REFERENCES flights(id),
    fuel_cost NUMERIC(12,2) DEFAULT 0,
    pilot_cost NUMERIC(12,2) DEFAULT 0,
    maintenance_cost NUMERIC(12,2) DEFAULT 0
);
