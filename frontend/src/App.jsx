import React, { useEffect, useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  const [rows, setRows] = useState([]);
  const [revenue, setRevenue] = useState(null);

  useEffect(() => {
    fetch(`${API}/dashboard/dispatch`).then(r => r.json()).then(setRows).catch(() => setRows([]));
    fetch(`${API}/reports/revenue?period=daily`).then(r => r.json()).then(setRevenue).catch(() => setRevenue(null));
  }, []);

  return (
    <div className="container">
      <h1>Aviation Dispatch Dashboard</h1>
      <section className="cards">
        <div className="card">
          <h3>Today's Flights</h3>
          <p>{rows.length}</p>
        </div>
        <div className="card">
          <h3>Revenue (Daily)</h3>
          <p>${revenue?.total_revenue ?? 0}</p>
        </div>
        <div className="card">
          <h3>Profit (Daily)</h3>
          <p>${revenue?.profit ?? 0}</p>
        </div>
      </section>

      <h2>Load Control</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Flight</th>
              <th>Aircraft</th>
              <th>PAX</th>
              <th>Cargo kg</th>
              <th>Load Factor</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.flight_id}>
                <td>{r.flight_id}</td>
                <td>{r.aircraft}</td>
                <td>{r.passengers}</td>
                <td>{r.cargo_weight}</td>
                <td>{Math.round(r.load_factor * 100)}%</td>
                <td><span className={`badge ${r.indicator.toLowerCase()}`}>{r.indicator}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
