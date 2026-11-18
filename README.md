# ApexPulse — AI-Powered Sports Coaching System

Production-grade full-stack **AI-Powered Sports Coaching System** integrating your existing trained `ExtraTreesRegressor` calorie expenditure model (`D:\V3`) with OpenCV video movement tracking, adaptive personalized training programs, workload-based injury prevention, game strategy optimization, real-time WebSocket telemetry, transparent criteria-based skill scoring, gamification, and a voice-enabled Virtual Coaching Assistant.

---

## Key Highlights & Model Integrity

- **Existing Trained Model Preserved 100% Read-Only:**
  - Directly loads `D:\V3\trained_models\calorie_prediction_model.pkl` (2.93 GB, 300-tree `ExtraTreesRegressor`, Test $R^2$ = **91.81%**, MAE = **61.36 kcal**, 5-Fold CV $R^2$ = **91.71%**) and `D:\V3\trained_models\preprocessor.pkl`.
  - Computes real 300-tree ensemble uncertainty bands (10th–90th percentile & std), global feature importances, live counterfactual what-if sensitivity explanations, batch CSV/Excel predictions, and dataset percentile rankings against `D:\V3\preprocessed_workout_dataset.csv` (70,000 rows).
  - Never retrains, overwrites, or replaces your model.
- **Background Non-Blocking Singleton Loader:** Because the trained model is 2.93 GB (~90s cold load), FastAPI starts immediately and loads the model once in a shared background thread, exposing live readiness at `GET /api/ml/status`.
- **Zero Fabricated Outputs:**
  - OpenCV computer vision (Farneback optical flow + MOG2 contour tracking) is strictly separated from the tabular calorie regression model.
  - Injury-risk assessments use transparent sports-science workload heuristics (ACWR, HR load, RPE/fatigue z-score anomalies, sleep & hydration) and are explicitly labeled as **non-medical workload indicators**.
  - Real-time telemetry clearly indicates **"Awaiting Wearable / IoT Sensor Integration"** when no external hardware stream is active.
  - Dashboard KPIs and empty states reflect only real database records.

---

## Project Structure

```text
D:\V3\                              # Existing ML artifacts (READ-ONLY, untouched)
D:\sports-coaching-system\
├── backend\                        # Python 3.14 + FastAPI + SQLAlchemy 2.0 + Alembic + OpenCV
│   ├── app\
│   │   ├── core\                   # Configurable settings (.env), bcrypt, JWT, RBAC
│   │   ├── db\                     # PostgreSQL-compatible ORM models (20 tables) & init_db
│   │   ├── ml\                     # Singleton CalorieModelService integrating D:\V3
│   │   ├── cv\                     # OpenCV VideoAnalyzer (optical flow, tracking, keyframes)
│   │   ├── services\               # Training plans, injury risk, strategy, skills, gamification, assistant, WebSockets
│   │   ├── routers\                # Modular REST & WebSocket API endpoints
│   │   └── schemas\                # Strict Pydantic v2 validation schemas
│   ├── alembic\                    # Database migrations (PostgreSQL & SQLite compatible)
│   ├── tests\                      # Pytest integration & live trained-model tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend\                       # React 19 + TypeScript + Vite + Tailwind CSS v4 + Recharts
│   ├── src\
│   │   ├── context\                # Auth (RBAC), Theme (Dark/Light), ML Model Status
│   │   ├── components\             # Responsive role-aware sidebar, telemetry cards, empty states
│   │   └── pages\                  # All 12 functional modules
│   ├── nginx.conf
│   └── Dockerfile
└── docker-compose.yml              # PostgreSQL 16 + FastAPI Backend + Nginx Frontend
```

---

## Local Setup & Running Instructions

### 1. Backend Setup (FastAPI + Python 3.14)

```powershell
cd D:\sports-coaching-system\backend

# Activate the pre-configured virtual environment (or create via uv venv --python 3.14 .venv)
.\.venv\Scripts\Activate.ps1

# If installing fresh:
# pip install -r requirements.txt

# Configure paths and secrets in .env (already initialized from .env.example)
# MODEL_DIR=D:\V3\trained_models
# DATASET_PATH=D:\V3\preprocessed_workout_dataset.csv

# Run database migrations
alembic upgrade head

# Start backend server (IMPORTANT: keep --workers 1 so the 2.93 GB model is loaded once in RAM)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

- Interactive Swagger API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`
- ML Model Readiness & Metrics: `http://localhost:8000/api/ml/status`

### 2. Frontend Setup (React + TypeScript + Tailwind)

```powershell
cd D:\sports-coaching-system\frontend
npm install
npm run dev
```

- Open `http://localhost:5173` in your browser.
- Register your first account as **Admin**, **Coach / Trainer**, **Sports Analyst**, or **Athlete / Player**.

---

## Database Setup & PostgreSQL Migration

By default for immediate local execution on machines without PostgreSQL installed, `DATABASE_URL` falls back to SQLite (`sqlite:///./sports_coaching.db`). All 20 tables are fully PostgreSQL-compatible via SQLAlchemy 2.0 + `psycopg[binary]` + Alembic.

To switch to **PostgreSQL**:
1. Create a PostgreSQL database (e.g., `CREATE DATABASE sports_coaching;`).
2. Update `backend/.env`:
   ```env
   DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/sports_coaching
   ```
3. Run Alembic migrations:
   ```powershell
   cd D:\sports-coaching-system\backend
   .\.venv\Scripts\alembic.exe upgrade head
   ```

---

## Running Tests

```powershell
cd D:\sports-coaching-system\backend

# Fast full-stack API + OpenCV + RBAC + DB integration suite (~16s)
.\.venv\Scripts\pytest.exe -v tests/test_api.py

# Live end-to-end test loading your actual 2.93 GB ExtraTreesRegressor model (~100s)
.\.venv\Scripts\pytest.exe -v tests/test_real_model_inference.py
```

---

## Wearable / IoT Real-Time Sensor Integration

Push live readings from Garmin/Polar bridges, mobile companion apps, or ESP32/BLE IoT hardware:

```bash
curl -X POST http://localhost:8000/api/telemetry/webhook \
  -H "Content-Type: application/json" \
  -H "X-Sensor-API-Key: apexpulse-sensor-key-local-dev" \
  -d '{
    "athlete_id": 1,
    "source_type": "wearable_webhook",
    "device_name": "Polar H10",
    "heart_rate_bpm": 154,
    "speed_kmh": 13.9,
    "distance_km": 5.2,
    "duration_minutes": 22,
    "calories": 285
  }'
```

Connected browser clients subscribed to `/api/telemetry/ws/{athlete_id}` receive updates instantaneously.

---

## Cloud Deployment (Docker & AWS)

### Docker Compose (Local / Single-Host VM)
```bash
docker compose up --build -d
```

### AWS Production Deployment (Terraform IaC Included)

Full production AWS infrastructure-as-code is provided in `deploy/aws/`:
- **VPC + Public/Private Subnets + Security Groups** (RDS port 5432 locked strictly to the EC2 App SG)
- **Amazon RDS PostgreSQL 16** (private subnet, encrypted, 7-day automated backups)
- **Amazon S3 Bucket** (encrypted, private, versioned for read-only copy of `D:\V3\trained_models` + video uploads)
- **Amazon EC2 (`m6i.xlarge`, 16 GB RAM)** with IAM role (S3 + CloudWatch Logs) and automated cloud-init bootstrap
- **Amazon CloudWatch Log Group & High-CPU Alarm**

```powershell
# 1. Authenticate AWS CLI with valid credentials
aws configure

# 2. Configure variables
Copy-Item D:\sports-coaching-system\deploy\aws\terraform.tfvars.example D:\sports-coaching-system\deploy\aws\terraform.tfvars
# Edit terraform.tfvars to set strong db_password, app_secret_key, and sensor_api_key

# 3. Preview infrastructure plan (dry run)
powershell -ExecutionPolicy Bypass -File D:\sports-coaching-system\deploy\aws\deploy-to-aws.ps1

# 4. Provision AWS stack & upload D:\V3 trained model to S3 (read-only copy)
powershell -ExecutionPolicy Bypass -File D:\sports-coaching-system\deploy\aws\deploy-to-aws.ps1 -Apply
```

### Local MySQL 8 / PostgreSQL 16 Initialization Scripts
- PostgreSQL SQL: `backend/scripts/init_postgres.sql` (`DATABASE_URL=postgresql+psycopg://...`)
- MySQL 8 SQL: `backend/scripts/init_mysql.sql` (`DATABASE_URL=mysql+pymysql://...`)
- Database Verification: `cd backend && .\.venv\Scripts\python.exe -m scripts.verify_db`
