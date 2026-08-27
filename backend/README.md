# PrintPulse Backend

FastAPI + PostgreSQL backend for the PrintPulse FDM 3D Printer Predictive Maintenance System.

## Stack
- **FastAPI** — REST API + WebSocket server
- **PostgreSQL** + **SQLAlchemy (async)** + **asyncpg** — database
- **Alembic** — schema migrations
- **aiomqtt** — MQTT subscriber (receives ESP32 classifications)
- **JWT (python-jose + passlib)** — authentication
- **aiosmtplib + httpx/Twilio** — email and SMS alerts

---

## Project Structure

```
app/
├── main.py          # FastAPI app, lifespan startup/shutdown, routers
├── config.py        # Settings from .env (pydantic-settings)
├── database.py      # Async SQLAlchemy engine + session factory
├── models.py        # ORM table definitions (User, FaultEvent)
├── schemas.py       # Pydantic request/response schemas
├── auth.py          # JWT creation, password hashing, current_user dependency
├── mqtt.py          # Background task: subscribes to ESP32 MQTT topic
├── websocket.py     # WebSocket connection manager (broadcasts to dashboard)
├── alerts.py        # Email (SMTP) and SMS (Twilio) alert dispatching
└── routers/
    ├── auth.py      # POST /auth/register, /auth/login, GET/PATCH /auth/me
    ├── faults.py    # GET /faults, /faults/stats, /faults/trend, POST /{id}/acknowledge
    └── dashboard.py # GET /dashboard/live, WS /dashboard/ws/live
```

---

## Setup

### 1. Clone and create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your PostgreSQL URL, MQTT broker, SMTP, and Twilio credentials
```

### 3. Create the PostgreSQL database
```sql
CREATE DATABASE printpulse_db;
CREATE USER printpulse WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE printpulse_db TO printpulse;
```

### 4. Run database migrations
```bash
alembic upgrade head
```

### 5. Start the server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API docs: http://localhost:8000/docs

---

## API Reference

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create a new user account |
| POST | `/auth/login` | Login — returns JWT access token |
| GET | `/auth/me` | Get current user profile |
| PATCH | `/auth/me` | Update alert email/phone/enabled |

### Fault Events
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/faults` | Paginated fault history (filters: class, acknowledged, date range) |
| GET | `/faults/stats` | Aggregated counts for dashboard stats panel |
| GET | `/faults/trend?minutes=60` | Time-series readings for trend chart |
| GET | `/faults/{id}` | Single event detail |
| POST | `/faults/{id}/acknowledge` | Mark event acknowledged + add notes |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/live` | Latest reading (REST fallback for page load) |
| WS | `/dashboard/ws/live?token=<JWT>` | WebSocket — streams live classifications |

---

## WebSocket Message Format

The server sends JSON messages over the WebSocket connection:

```json
{
  "type": "live_reading",
  "fault_class": "NORMAL",
  "confidence": 0.982,
  "accel_rms_z": 0.031,
  "current_rms": 0.94,
  "temperature": 207.5,
  "received_at": "2025-07-15T14:32:01.123456+00:00",
  "event_id": 1042
}
```

The React dashboard connects with:
```js
const ws = new WebSocket(`ws://localhost:8000/dashboard/ws/live?token=${accessToken}`);
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.type === "live_reading") { /* update state */ }
};
```

---

## ESP32 MQTT Payload Format

The ESP32 publishes to `printpulse/status` (configurable via `MQTT_TOPIC`):

```json
{
  "fault_class": "NORMAL",
  "confidence": 0.96,
  "accel_rms_z": 0.028,
  "current_rms": 0.91,
  "temperature": 205.3,
  "timestamp": 1720000000000
}
```

---

## Running in Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

For production, use a process manager (systemd, supervisor) and put Nginx in front as a reverse proxy with SSL termination.
