import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.database.connection import engine, Base, SessionLocal
from backend.app.models import *  # noqa: F401, F403
from backend.app.api import api_router
from backend.app.data.synthetic import generate_synthetic_patient_data
from backend.app.models.patient import Patient
from backend.app.models.measurement import Measurement
from backend.app.digital_twin.engine import DigitalTwinEngine
from backend.app.services.ingestion import parse_iso_datetime


def seed_default_demo_patient():
    """Seeds a default demo patient upon initial database startup if none exist."""
    db = SessionLocal()
    try:
        count = db.query(Patient).count()
        if count == 0:
            print("[INFO] No patients found in database. Seeding demo patient PT-DEMO-001...")
            bundle = generate_synthetic_patient_data(
                patient_id="PT-DEMO-001",
                name="Alice M. Taylor",
                age=56,
                gender="Female",
                baseline_hr=72.0,
                duration_hours=24,
                interval_minutes=15,
                noise_level=1.2,
                include_exercise=True
            )
            pt_data = bundle["patient"]
            patient = Patient(
                id=pt_data["id"],
                name=pt_data["name"],
                age=pt_data["age"],
                gender=pt_data["gender"],
                baseline_heart_rate=pt_data["baseline_heart_rate"],
                medical_notes=pt_data["medical_notes"],
                is_synthetic=True
            )
            db.add(patient)
            db.flush()

            meas_objs = []
            for m in bundle["measurements"]:
                meas_objs.append(Measurement(
                    patient_id=pt_data["id"],
                    timestamp=parse_iso_datetime(m["timestamp"]),
                    measurement_type=m["measurement_type"],
                    value=m["value"],
                    unit=m["unit"],
                    source=m["source"],
                    is_late_arrival=False
                ))
            db.add_all(meas_objs)
            db.commit()

            # Initialize twin at version 1
            DigitalTwinEngine.initialize_twin("PT-DEMO-001", db)
            print("[INFO] Seeded demo patient PT-DEMO-001 with Digital Twin State Version 1.")
    except Exception as e:
        print(f"[WARN] Auto-seeding skipped or encountered error: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize all database tables
    Base.metadata.create_all(bind=engine)
    seed_default_demo_patient()
    yield


app = FastAPI(
    title="Hackloop 2026 — Digital Twin of a Patient API",
    description=(
        "Core Digital Twin Engine for patient physiological state tracking, "
        "short-term autoregressive forecasting, and counterfactual scenario simulation.\n\n"
        "**EDUCATIONAL & RESEARCH PROTOTYPE ONLY**: Not for medical diagnosis or clinical use."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for local development and Docker deployment
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*"  # research prototype permissive default
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "project": "Hackloop 2026 — Digital Twin of a Patient",
        "docs_url": "/docs",
        "api_prefix": "/api",
        "health": "/api/health"
    }
