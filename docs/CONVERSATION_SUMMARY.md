# PrintPulse — Full Conversation Summary

Group 16 · Department of Computer Engineering · University of Ghana, Legon · 2025/2026

---

## 1. Project Overview

**PrintPulse** is a real-time IoT-enabled predictive maintenance system for desktop FDM 3D printers.
It classifies printer operational state into four fault classes using embedded sensing and machine
learning, then streams results to a live web dashboard called the **Faultline Command Center**.

- **Sensors:** MPU-6050 GY-521 (vibration, I2C) · ACS712 5A (current, ADC) · DS18B20 (temperature, 1-Wire)
- **Edge node:** ESP32 dual-core 240 MHz
- **Classifier:** Random Forest — 50 trees, 34 features, 96.8% test accuracy
- **Dashboard:** React 18 + Vite 5 + TypeScript 5
- **Backend:** Python + FastAPI + PostgreSQL

---

## 2. Sensor Discussion

### SW-1801P (rejected)
The SW-1801P vibration switch was evaluated and rejected. It outputs a binary HIGH/LOW signal only —
no waveform, no frequency content, no amplitude data. It cannot feed the feature extraction pipeline
the Random Forest model expects. It could serve as a supplementary motion-detect trigger alongside
the MPU-6050, but not as a primary fault sensor.

### MPU-6050 GY-521 (selected)
The GY-521 is the correct module — the standard breakout board for the MPU-6050 chip. Key configuration:
- Full-scale range: ±2g (AFS_SEL = 0)
- Sample rate: 100 Hz (SMPLRT_DIV = 79)
- Low-pass filter: DLPF_CFG = 3 (44 Hz bandwidth)
- I2C address: 0x68 (AD0 grounded)
- I2C clock: 400 kHz Fast Mode
- Power: GY-521 has onboard AMS1117 regulator — safe on 5V rail
- Startup calibration: 1000-sample static baseline, per-axis offset stored in NVS

---

## 3. Report Documents Produced

| File | Contents |
|------|----------|
| PrintPulse_System_Design_Methodology.docx | Early system design and methodology draft |
| PrintPulse_Chapter3_System_Design.docx | Chapter 3 only, no stakeholder section |
| PrintPulse_Full_Report_Ch1_Ch2_Ch3.docx | Combined Chapters 1+2+3 |
| PrintPulse_Full_Report_With_Figures.docx | Same with Figures 3.1, 3.2, 3.3 embedded |

All documents follow the reference progress report format:
Times New Roman 12pt · justified · bold numbered headings · italic figure captions · grey-header
bordered tables · footer: "Department of Computer Engineering, University of Ghana  2025/2026"

Note: The Stakeholder Engagement and Interviews section was removed on request. All subsequent
section numbers were renumbered accordingly (3.3 → 3.2, 3.4 → 3.3, etc.).

---

## 4. Chapter 1 — Introduction

- **1.1 Background:** FDM printing landscape, Industry 4.0 and CPS, IoT in manufacturing, ML-based
  predictive maintenance, multimodal sensing, digital twins, edge computing. 29 inline citations.
- **1.2 Statement of the Problem:** reactive detection gap in consumer FDM printers; no integrated
  multimodal IoT PdM framework for desktop-grade systems.
- **1.3 Objectives:** 6 numbered specific objectives (hardware, IoT arch, ML, evaluation, benchmarking).
- **1.4 Research Questions:** 5 numbered questions.
- **1.5 Scope:** ESP32-based, 3-sensor, lab-validated, 4 fault classes, MQTT/local Wi-Fi.
- **1.6 Significance:** theoretical (multimodal desktop FDM PdM) + practical (low-cost retrofit) +
  Industry 4.0 democratisation argument.
- **1.7 Organisation:** maps each of the 5 chapters to its content.
- **References:** 33 IEEE-formatted references (Jafar 2024 → Szydlo 2021).

---

## 5. Chapter 2 — Literature Review (33 papers, 8 sections)

| Section | Theme | Key Papers |
|---------|-------|------------|
| 2.1 | ML in Additive Manufacturing | Inayathullah 2025; Zhang 2024; Aktepe & Ergün 2025; Soori 2025 |
| 2.2 | Predictive Maintenance Frameworks | Mallioris 2023; Tamir 2023; Ryalat 2025 |
| 2.3 | Sensing Modalities | Isiani 2023 (vibration); Kumar 2024 (multi-sensor); Kim 2023 (vision); Hu 2023 (fusion) |
| 2.4 | Digital Twins & Autonomous Systems | Rachmawati 2023; Xu 2025; Lee & Park 2025 |
| 2.5 | Low-Cost Empirical Studies | Kumar 2022 (Arduino CNN, 94%); Yoon 2014 (PHM acoustic); Szydlo 2021 (open dataset) |
| 2.6 | Statistical Signal Processing | Dorian 2023 (anticipation); Bhattacharya 2024 (temporal); Zhang 2024 (unsupervised) |
| 2.7 | Quality & Materials | Seifert 2025; Rojek 2025; Ukwaththa 2024 (XAI); Kadam 2021 |
| 2.8 | Systems Integration | Wang 2024 (deep learning + vision); Wang 2025 (PCSV); Chen 2024 |

**Gap (Section 2.9):** No published framework integrates multimodal sensor fusion, edge ML inference,
MQTT IoT communication, and a live operator dashboard within a unified low-cost CPS for desktop FDM
printers. PrintPulse directly addresses this gap.

---

## 6. Chapter 3 — System Design and Development

| Section | Content |
|---------|---------|
| 3.0 | Introduction |
| 3.1 | System Overview — 6 major components (numbered list) |
| 3.2 | Theoretical Framework — PdM Theory · Signal Processing Theory · Ensemble Learning Theory |
| 3.2.1 | Functional Requirements (10 bullets) |
| 3.2.2 | Non-Functional Requirements (8 bullets) |
| 3.2.3 | Frameworks re Dashboard — MVVM · Alert Design Principles |
| 3.3 | System Design and Development Process — phase table (6 phases + validation gates) |
| 3.3.1 | Model Training — synthetic dataset, hyperparameter tuning, per-class metrics table |
| 3.3.2 | Hardware Development — component table (ESP32, MPU-6050, ACS712, DS18B20) |
| 3.3.3 | Software Development — ESP32 firmware + Faultline Command Center |
| 3.3.4 | Software Modelling — Python reference pipeline, feature equivalence validation |
| 3.3.5 | System Modelling — Dashboard state machine (5 states) |
| 3.3.6 | Development Tools — tools table (17 rows) |

---

## 7. Figures Generated

All three figures are high-resolution PNGs (2× for print quality), embedded in the Word document.

### Figure 3.1 — System Architecture Diagram
Three-layer block diagram with colour-coded layers:
- Layer 1 (blue): MPU-6050 GY-521 · ACS712 5A · DS18B20 with specs in each box
- Layer 2 (purple): ESP32 — Data Acquisition → Feature Extraction → Random Forest → MQTT Publish
- Layer 3 (red): Faultline Command Center — Live Feed · Trend Charts · Fault Log · Alerts
- Arrows labelled: I2C/ADC/1-Wire (L1→L2), MQTT/Wi-Fi (L2→L3)

### Figure 3.2 — Pictorial Flow Diagram
Left-to-right flow: FDM Printer + Sensors → ESP32 (4 processing steps) → MQTT Broker → Dashboard mockup
Includes fault class colour legend (green/amber/orange/red)

### Figure 3.3 — System Flow Chart
START → ESP32 Init → 100 Hz polling loop → 512-sample window? (No → loop back) →
Feature extraction → Random Forest inference → 4-way fault branch →
MQTT Publish → Dashboard Update → Print complete? → END

---

## 8. Frontend — Faultline Command Center

**Stack:** React 18 · Vite 5 · TypeScript 5 · Chart.js · MQTT.js · Plain CSS (design tokens)

### File Map

```
frontend/
├── index.html                      HTML entry — loads Plus Jakarta Sans + JetBrains Mono
├── package.json                    npm dependencies
├── tsconfig.json                   TypeScript strict config
├── vite.config.ts                  Proxies /api/* → localhost:8000
└── src/
    ├── main.tsx                    React root
    ├── App.tsx                     Auth gate: LoginPage or Dashboard
    ├── styles.css                  All styles — design tokens, light/dark, every component
    ├── types/index.ts              TS interfaces: LiveReading · FaultEvent · FaultStats · User · AlertConfig
    ├── utils/faultUtils.ts         FAULT_LABELS · FAULT_COLORS · FAULT_BG · SEVERITY · formatters
    ├── hooks/
    │   ├── useAuth.ts              Login/logout, JWT persistence in localStorage
    │   ├── useWebSocket.ts         WebSocket → backend /dashboard/ws/live (primary live data)
    │   ├── useMQTT.ts              Direct MQTT.js connection (alternative / testing bypass)
    │   ├── useApi.ts               fetch() wrappers for all REST endpoints
    │   └── useAlerts.ts            Alert config, Web Audio API tones, threshold evaluation
    ├── pages/
    │   ├── LoginPage.tsx           Username + password form
    │   └── Dashboard.tsx           Full layout: header, tabs, alert banner, stats bar, content
    └── components/
        ├── LiveFeed.tsx            Fault badge + confidence + 3 sensor cards
        ├── TrendCharts.tsx         3 Chart.js line charts (vibration, current, temperature)
        ├── FaultLog.tsx            Table of events with acknowledge + CSV export
        ├── StatsBar.tsx            7-column aggregated counts bar
        ├── AlertBanner.tsx         Dismissable flash alert banner
        └── AlertSettings.tsx       Checkboxes + confidence slider, persisted to localStorage
```

### Key Design Decisions

**CSS design tokens:** All colours, surfaces, radii defined as CSS custom properties. Light/dark
switching is one `data-theme` attribute on `<html>` — no per-component style duplication.

**Two live data hooks:** `useWebSocket` (primary) connects to the FastAPI backend WebSocket endpoint
with JWT auth. `useMQTT` (alternative) connects directly to the MQTT broker over WebSocket port 9001 —
useful for testing when the backend is not running.

**Rolling buffer:** Both hooks maintain a 60-reading history array (sliding window). This feeds the
trend charts without unbounded memory growth (~5 minutes of data at 5s intervals).

**Audio alerts via Web Audio API:** No external sound library. Three tone frequencies by severity:
- Nozzle Clog: 440 Hz single tone
- Motor Fault: 660 Hz single tone
- Thermal Runaway: 880 Hz double-pulse

**Fault colour system:**
- Normal: #27AE60 (green)
- Nozzle Clog: #F39C12 (amber)
- Motor Fault: #E67E22 (orange)
- Thermal Runaway: #C0392B (red)

---

## 9. Backend — FastAPI + PostgreSQL

**Stack:** Python · FastAPI · SQLAlchemy async · asyncpg · PostgreSQL · aiomqtt · JWT (python-jose) · passlib/bcrypt

### File Map

```
backend/
├── requirements.txt                All pinned dependencies (bcrypt==4.0.1 for passlib compat)
├── .env.example                    Template for all env vars
├── alembic.ini                     Migration config
├── alembic/
│   ├── env.py                      Async-compatible Alembic env
│   ├── script.py.mako              Migration template
│   └── versions/
│       └── 0001_initial_schema.py  Creates users + fault_events tables + fault_class_enum
└── app/
    ├── main.py                     FastAPI app · CORS · lifespan (starts MQTT task, creates tables)
    ├── config.py                   Pydantic Settings — reads .env, all vars with defaults
    ├── database.py                 Async engine (pool_size=10) · session factory · get_db dependency
    ├── models.py                   User + FaultEvent ORM models with all columns
    ├── schemas.py                  Pydantic: MQTTPayload · FaultEventOut · FaultStats · TrendData · Token
    ├── auth.py                     bcrypt hash/verify · JWT create/decode · get_current_user dependency
    ├── mqtt.py                     Background task: subscribe → validate → DB insert → WS broadcast → alerts
    ├── websocket.py                ConnectionManager — broadcasts dict to all open WS connections
    ├── alerts.py                   Email via aiosmtplib/SMTP · SMS via Twilio REST · threshold check
    └── routers/
        ├── auth.py                 /auth/register · /auth/login · /auth/me (GET + PATCH)
        ├── faults.py               /faults (paginated+filtered) · /stats · /trend · /{id} · /{id}/acknowledge
        └── dashboard.py            /dashboard/live (REST) · /dashboard/ws/live (WebSocket)
```

### API Endpoints (12 total)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | — | Create user account |
| POST | /auth/login | — | Returns JWT access token |
| GET | /auth/me | JWT | Current user profile |
| PATCH | /auth/me | JWT | Update alert email/phone/enabled |
| GET | /faults | JWT | Paginated history (filters: class, ack, date range) |
| GET | /faults/stats | JWT | Aggregated counts for stats bar |
| GET | /faults/trend | JWT | Time-series points (?minutes=60) |
| GET | /faults/{id} | JWT | Single event detail |
| POST | /faults/{id}/acknowledge | JWT | Acknowledge + optional notes |
| GET | /dashboard/live | JWT | Latest reading (REST fallback on page load) |
| WS | /dashboard/ws/live?token= | JWT | Live WebSocket stream |
| GET | /health | — | Health check |

### Data Flow

1. ESP32 publishes JSON → `printpulse/status` (MQTT)
2. `mqtt.py` background task receives, validates with Pydantic, inserts into `fault_events`
3. Broadcasts to all open WebSocket connections via `ConnectionManager`
4. Checks confidence threshold + fault class config → sends email (aiosmtplib) and/or SMS (Twilio)

### Database Schema

**users:** id · email · username · hashed_password · is_active · created_at · alert_email · alert_phone · alerts_enabled

**fault_events:** id · fault_class (ENUM) · confidence · accel_rms_z · current_rms · temperature · esp32_timestamp · received_at · alert_sent · acknowledged · acknowledged_at · acknowledged_by (FK→users) · notes

---

## 10. Why This Stack?

**React + Vite + CSS:**
React's component model handles real-time partial UI updates cleanly. Vite is near-instant during
development (HMR). Plain CSS with custom properties gives a full design token system without adding
a framework dependency or fighting pre-built component defaults.

**Python + FastAPI:**
Python keeps the ML pipeline (scikit-learn, NumPy, SciPy) in the same language as the backend —
no language boundary if server-side retraining is added later. FastAPI is async-native (asyncio),
handling MQTT subscriber + WebSocket connections + HTTP requests concurrently. Flask would need
threading workarounds. Automatic OpenAPI docs at `/docs` are free.

---

## 11. Running the Full Stack

```bash
# 1. PostgreSQL — create database
psql -U postgres -c "CREATE DATABASE printpulse_db;"
psql -U postgres -c "CREATE USER printpulse WITH PASSWORD 'password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE printpulse_db TO printpulse;"

# 2. MQTT Broker
mosquitto -v

# 3. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in credentials
alembic upgrade head
uvicorn app.main:app --reload --port 8000
# API docs: http://localhost:8000/docs

# 4. Frontend
cd frontend
npm install
npm run dev
# Dashboard: http://localhost:5173

# 5. Test without ESP32 hardware
mosquitto_pub -t printpulse/status -m \
  '{"fault_class":"NOZZLE_CLOG","confidence":0.94,"accel_rms_z":0.12,"current_rms":1.4,"temperature":208.0,"timestamp":1720000000000}'
```

---

## 12. Next Steps

- Wire the ESP32 firmware MQTT publish to the local Mosquitto broker
- Collect real sensor data for model retraining and validation
- Add `/auth/register` UI to the frontend Settings panel
- Production: Nginx reverse proxy + SSL + systemd service files
- Multi-printer support: per-device MQTT topic namespacing + dashboard multi-stream view
