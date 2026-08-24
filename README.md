# PrintPulse — Faultline Command Center

**IoT-enabled predictive maintenance system for FDM 3D printers.**

Group 16 · Department of Computer Engineering · University of Ghana, Legon · 2025/2026

---

## What is PrintPulse?

PrintPulse is a real-time fault detection system that monitors a desktop FDM 3D printer using
three sensors (MPU-6050 vibration, ACS712 current, DS18B20 temperature) connected to an ESP32
microcontroller. The ESP32 runs a trained Random Forest classifier (96.8% test accuracy) on-device,
classifies the printer state every ~5 seconds, and publishes the result over MQTT. The Faultline
Command Center (this dashboard) receives those results and displays them live.

**Four fault classes detected:** Normal · Nozzle Clog · Motor Fault · Thermal Runaway

---

## Project Structure

```
printpulse/
├── frontend/          React 18 + Vite + TypeScript dashboard
├── backend/           Python FastAPI + PostgreSQL backend
└── README.md          This file
```

---

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in your DB, MQTT, SMTP, Twilio credentials
alembic upgrade head          # create PostgreSQL tables
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                   # starts on http://localhost:5173
```

The Vite dev server proxies `/api/*` → `http://localhost:8000` automatically.

---

## Architecture

```
FDM Printer
  └── Sensors (MPU-6050 · ACS712 · DS18B20)
        └── ESP32 (edge inference + MQTT publish)
              └── MQTT Broker (Mosquitto)
                    ├── FastAPI backend (stores to PostgreSQL, dispatches alerts)
                    │     └── WebSocket → Faultline Command Center (React dashboard)
                    └── [direct MQTT] → useMQTT hook (optional bypass)
```

