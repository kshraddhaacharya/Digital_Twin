import os
import json
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.models.user import User
from backend.app.models.report import MedicalReport
from backend.app.models.measurement import Measurement
from backend.app.models.twin_state import TwinState
from backend.app.digital_twin.engine import DigitalTwinEngine
from backend.app.services.auth import get_current_user, get_optional_current_user, verify_patient_authorization
from backend.app.services.report_parser import (
    extract_text_from_pdf,
    extract_text_from_image,
    parse_clinical_biomarkers,
    search_report_text,
    generate_report_summary
)
from backend.app.utils.datetime_utils import to_utc_iso

router = APIRouter(prefix="/reports", tags=["Medical Report Upload & Search Engine"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "reports")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


class ConfirmBiomarkerPayload(BaseModel):
    key: str = Field(..., description="e.g. 'heart_rate'")
    value: float = Field(..., description="Confirmed numeric value")
    unit: str = Field("bpm", description="e.g. 'bpm'")
    context: str = Field("resting", description="'resting', 'active', 'clinical', etc.")
    observation_timestamp: Optional[datetime] = None
    notes: Optional[str] = None


def validate_file_content(file_bytes: bytes, ext: str) -> str:
    """Verifies file magic signature bytes so extensions alone cannot be spoofed."""
    if ext == ".pdf":
        if not file_bytes.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed file: File extension is .pdf but content does not match a valid PDF header."
            )
        return "pdf"
    elif ext == ".png":
        if not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed file: File extension is .png but content does not match a valid PNG header."
            )
        return "png"
    elif ext in [".jpg", ".jpeg"]:
        if not file_bytes.startswith(b"\xff\xd8\xff"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed file: File extension is JPEG/JPG but content does not match a valid JPEG header."
            )
        return "jpeg" if ext == ".jpeg" else "jpg"
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported format '{ext}'.")


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_medical_report(
    title: str = Form(..., min_length=1, max_length=256),
    report_date: str = Form(...),
    description: Optional[str] = Form(None),
    patient_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Uploads a medical report (PDF or Image), performs content magic-byte validation,
    extracts readable clinical text without fabricating unreadable documents,
    computes factual summary and candidate biomarkers, and links to target patient.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats are: PDF, PNG, JPG, JPEG."
        )

    file_bytes = await file.read()
    file_size = len(file_bytes)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 25 MB limit."
        )

    # Magic byte validation
    file_type = validate_file_content(file_bytes, ext)

    # Resolve target patient and user
    target_patient_id = patient_id or (current_user.patient_id if current_user else "PT-DEMO-001")
    target_user_id = current_user.id if current_user else "USR-DEMO"

    # Enforce authorization
    verify_patient_authorization(target_patient_id, current_user, db)

    # Sanitize and create unique file path
    safe_name = f"{target_user_id}_{int(datetime.now().timestamp())}_{os.path.basename(file.filename)}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Extract text based on file format
    if ext == ".pdf":
        extracted_text = extract_text_from_pdf(file_bytes)
    else:
        extracted_text = extract_text_from_image(file_bytes, file.filename)

    # Parse candidate biomarkers
    biomarkers = parse_clinical_biomarkers(extracted_text)

    # Generate factual readable summary
    summary = generate_report_summary(
        title=title.strip(),
        report_date=report_date.strip(),
        extracted_text=extracted_text,
        biomarkers=biomarkers,
        file_type=file_type
    )

    is_scanned = bool(
        not extracted_text
        or "no digital text layer was found" in extracted_text
        or "Automated OCR is not enabled" in extracted_text
        or "Could not read text" in extracted_text
    )

    # Save metadata in database
    report = MedicalReport(
        user_id=target_user_id,
        patient_id=target_patient_id,
        title=title.strip(),
        report_date=report_date.strip(),
        file_name=file.filename,
        file_path=file_path,
        file_type=file_type,
        file_size_bytes=file_size,
        description=description.strip() if description else None,
        extracted_text=extracted_text,
        extracted_vitals=json.dumps(biomarkers)
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "success": True,
        "message": "Medical report uploaded and analyzed successfully.",
        "report": {
            "id": report.id,
            "patient_id": report.patient_id,
            "title": report.title,
            "report_date": report.report_date,
            "file_name": report.file_name,
            "file_type": report.file_type,
            "file_size_bytes": report.file_size_bytes,
            "description": report.description,
            "summary": summary,
            "extracted_text": extracted_text,
            "is_scanned": is_scanned,
            "biomarkers": biomarkers,
            "requires_review": len(biomarkers) > 0,
            "created_at": to_utc_iso(report.created_at)
        }
    }


@router.get("/")
def list_user_reports(
    patient_id: Optional[str] = Query(None, description="Filter reports for specific patient"),
    search: Optional[str] = Query(None, description="Search keyword across titles, descriptions, and extracted text"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Lists medical reports for the selected patient or authenticated user with search and date filtering."""
    if patient_id:
        verify_patient_authorization(patient_id, current_user, db)
        query = db.query(MedicalReport).filter(MedicalReport.patient_id == patient_id)
    elif current_user:
        query = db.query(MedicalReport).filter(MedicalReport.user_id == current_user.id)
    else:
        # Default demo patient
        query = db.query(MedicalReport).filter(MedicalReport.patient_id == "PT-DEMO-001")

    if start_date:
        query = query.filter(MedicalReport.report_date >= start_date)
    if end_date:
        query = query.filter(MedicalReport.report_date <= end_date)

    reports = query.order_by(MedicalReport.report_date.desc(), MedicalReport.created_at.desc()).all()

    results = []
    for r in reports:
        biomarkers = json.loads(r.extracted_vitals) if r.extracted_vitals else []
        search_matches = None

        if search and search.strip():
            q = search.strip().lower()
            in_meta = (q in r.title.lower()) or (r.description and q in r.description.lower())
            text_search = search_report_text(r.extracted_text or "", search.strip())

            if not in_meta and text_search["matches_found"] == 0:
                continue
            search_matches = text_search

        text_content = r.extracted_text or ""
        summary = generate_report_summary(
            title=r.title,
            report_date=r.report_date,
            extracted_text=text_content,
            biomarkers=biomarkers,
            file_type=r.file_type
        )
        is_scanned = bool(
            not text_content
            or "no digital text layer was found" in text_content
            or "Automated OCR is not enabled" in text_content
            or "Could not read text" in text_content
        )

        results.append({
            "id": r.id,
            "patient_id": r.patient_id,
            "title": r.title,
            "report_date": r.report_date,
            "file_name": r.file_name,
            "file_type": r.file_type,
            "file_size_bytes": r.file_size_bytes,
            "description": r.description,
            "summary": summary,
            "extracted_text": text_content,
            "is_scanned": is_scanned,
            "biomarkers": biomarkers,
            "search_matches": search_matches,
            "created_at": to_utc_iso(r.created_at)
        })

    return results


@router.get("/{report_id}")
def get_report_details(
    report_id: int,
    search: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves full details, extracted text, and search matches for a specific report."""
    report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    verify_patient_authorization(report.patient_id, current_user, db)

    biomarkers = json.loads(report.extracted_vitals) if report.extracted_vitals else []
    search_result = search_report_text(report.extracted_text or "", search) if search else None

    text_content = report.extracted_text or ""
    summary = generate_report_summary(
        title=report.title,
        report_date=report.report_date,
        extracted_text=text_content,
        biomarkers=biomarkers,
        file_type=report.file_type
    )
    is_scanned = bool(
        not text_content
        or "no digital text layer was found" in text_content
        or "Automated OCR is not enabled" in text_content
        or "Could not read text" in text_content
    )

    return {
        "id": report.id,
        "patient_id": report.patient_id,
        "title": report.title,
        "report_date": report.report_date,
        "file_name": report.file_name,
        "file_type": report.file_type,
        "file_size_bytes": report.file_size_bytes,
        "description": report.description,
        "summary": summary,
        "extracted_text": text_content,
        "is_scanned": is_scanned,
        "biomarkers": biomarkers,
        "search_result": search_result,
        "created_at": to_utc_iso(report.created_at)
    }


@router.get("/{report_id}/download")
def download_report_file(
    report_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Securely serves the authorized patient's original uploaded document."""
    report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found.")

    verify_patient_authorization(report.patient_id, current_user, db)

    media_type = "application/pdf" if report.file_type == "pdf" else f"image/{report.file_type}"
    return FileResponse(
        path=report.file_path,
        media_type=media_type,
        filename=report.file_name
    )


@router.delete("/{report_id}")
def delete_medical_report(
    report_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a medical report record and removes its physical file from storage."""
    report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    verify_patient_authorization(report.patient_id, current_user, db)

    if os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except Exception:
            pass

    db.delete(report)
    db.commit()
    return {"success": True, "message": "Report deleted successfully."}


@router.post("/{report_id}/confirm-biomarkers")
def confirm_report_biomarkers_to_twin(
    report_id: int,
    payload: ConfirmBiomarkerPayload,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Patient Review-and-Confirm step:
    Allows user to review, confirm, or adjust extracted biomarker values before
    they are formally ingested into their canonical health state and digital twin.
    """
    report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    verify_patient_authorization(report.patient_id, current_user, db)

    if payload.key != "heart_rate":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Biomarker '{payload.key}' confirmation is not currently supported in the physiological twin model. Supported: 'heart_rate'."
        )

    if not (30.0 <= payload.value <= 250.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Heart rate value {payload.value} bpm is outside physiological plausibility (30 - 250 bpm)."
        )

    obs_ts = payload.observation_timestamp or datetime.now(timezone.utc)
    if obs_ts.tzinfo is None:
        obs_ts = obs_ts.replace(tzinfo=timezone.utc)

    # Ingest measurement into report.patient_id
    meas = Measurement(
        patient_id=report.patient_id,
        timestamp=obs_ts,
        measurement_type="heart_rate",
        value=float(payload.value),
        unit=payload.unit or "bpm",
        source=f"report_confirmed:{report.id}:{report.file_name}",
        context=payload.context or "resting",
        data_quality="valid",
        is_late_arrival=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(meas)
    db.commit()
    db.refresh(meas)

    # Advance digital twin state
    active_state = db.query(TwinState).filter(
        TwinState.patient_id == report.patient_id,
        TwinState.is_active_version == True
    ).first()

    if not active_state:
        updated_state = DigitalTwinEngine.initialize_twin(patient_id=report.patient_id, db=db)
        stale_count = 0
    else:
        updated_state, stale_count = DigitalTwinEngine.update_twin_with_measurement(
            patient_id=report.patient_id,
            measurement=meas,
            db=db
        )

    return {
        "success": True,
        "message": f"Biomarker confirmed. Digital Twin updated to State Version {updated_state.state_version}.",
        "measurement": {
            "id": meas.id,
            "value": meas.value,
            "unit": meas.unit,
            "timestamp": to_utc_iso(meas.timestamp),
            "context": meas.context
        },
        "digital_twin_update": {
            "current_state_version": updated_state.state_version,
            "latest_heart_rate": updated_state.latest_heart_rate,
            "vital_status": updated_state.vital_status,
            "attestation_status": updated_state.attestation_status,
            "on_chain_tx_hash": updated_state.on_chain_tx_hash,
            "stale_forecasts_invalidated": stale_count
        }
    }


@router.post("/{report_id}/sync-twin")
def sync_report_vitals_to_twin(
    report_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Direct sync of recognized biomarkers to twin (auto-confirm fallback).
    """
    report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    verify_patient_authorization(report.patient_id, current_user, db)

    biomarkers = json.loads(report.extracted_vitals) if report.extracted_vitals else []
    hr_biomarker = next((b for b in biomarkers if b.get("key") == "heart_rate"), None)

    if not hr_biomarker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No heart rate biomarker detected in this document to sync."
        )

    payload = ConfirmBiomarkerPayload(
        key="heart_rate",
        value=float(hr_biomarker["value"]),
        unit=hr_biomarker.get("unit", "bpm"),
        context="resting"
    )
    return confirm_report_biomarkers_to_twin(report_id, payload, current_user, db)
