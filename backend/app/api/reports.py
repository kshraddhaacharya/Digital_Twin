import os
import json
import shutil
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.models.user import User
from backend.app.models.report import MedicalReport
from backend.app.models.measurement import Measurement
from backend.app.digital_twin.engine import DigitalTwinEngine
from backend.app.services.auth import get_current_user
from backend.app.services.report_parser import (
    extract_text_from_pdf,
    extract_text_from_image,
    parse_clinical_biomarkers,
    search_report_text
)

router = APIRouter(prefix="/reports", tags=["Medical Report Upload & Search Engine"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "reports")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_medical_report(
    title: str = Form(..., min_length=1, max_length=256),
    report_date: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Uploads a medical report (PDF or Image), extracts readable clinical text,
    identifies health biomarkers, and securely saves the record.
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

    # Sanitize and create unique file path
    safe_name = f"{current_user.id}_{int(datetime.now().timestamp())}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Extract text based on file format
    if ext == ".pdf":
        extracted_text = extract_text_from_pdf(file_bytes)
        file_type = "pdf"
    else:
        extracted_text = extract_text_from_image(file_bytes, file.filename)
        file_type = ext.replace(".", "")

    # Parse biomarkers from text
    biomarkers = parse_clinical_biomarkers(extracted_text)

    # Save metadata in database
    report = MedicalReport(
        user_id=current_user.id,
        patient_id=current_user.patient_id,
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
            "title": report.title,
            "report_date": report.report_date,
            "file_name": report.file_name,
            "file_type": report.file_type,
            "file_size_bytes": report.file_size_bytes,
            "description": report.description,
            "biomarkers": biomarkers,
            "created_at": report.created_at.isoformat()
        }
    }


@router.get("/")
def list_user_reports(
    search: Optional[str] = Query(None, description="Search keyword across titles, descriptions, and extracted text"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all medical reports for the current user with optional search and date filtering."""
    query = db.query(MedicalReport).filter(MedicalReport.user_id == current_user.id)

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
            # Check title, description, or search through extracted text
            q = search.strip().lower()
            in_meta = (q in r.title.lower()) or (r.description and q in r.description.lower())
            text_search = search_report_text(r.extracted_text or "", search.strip())

            if not in_meta and text_search["matches_found"] == 0:
                continue  # Skip report if search query doesn't match
            search_matches = text_search

        results.append({
            "id": r.id,
            "title": r.title,
            "report_date": r.report_date,
            "file_name": r.file_name,
            "file_type": r.file_type,
            "file_size_bytes": r.file_size_bytes,
            "description": r.description,
            "biomarkers": biomarkers,
            "search_matches": search_matches,
            "created_at": r.created_at.isoformat()
        })

    return results


@router.get("/{report_id}")
def get_report_details(
    report_id: int,
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves full details, extracted text, and search matches for a specific report."""
    report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.user_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    biomarkers = json.loads(report.extracted_vitals) if report.extracted_vitals else []
    search_result = search_report_text(report.extracted_text or "", search) if search else None

    return {
        "id": report.id,
        "title": report.title,
        "report_date": report.report_date,
        "file_name": report.file_name,
        "file_type": report.file_type,
        "file_size_bytes": report.file_size_bytes,
        "description": report.description,
        "extracted_text": report.extracted_text,
        "biomarkers": biomarkers,
        "search_result": search_result,
        "created_at": report.created_at.isoformat()
    }


@router.get("/{report_id}/download")
def download_report_file(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Securely serves the user's original uploaded document."""
    report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.user_id == current_user.id
    ).first()
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found.")

    media_type = "application/pdf" if report.file_type == "pdf" else f"image/{report.file_type}"
    return FileResponse(
        path=report.file_path,
        media_type=media_type,
        filename=report.file_name
    )


@router.delete("/{report_id}")
def delete_medical_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a medical report record and removes its physical file from storage."""
    report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.user_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except Exception:
            pass

    db.delete(report)
    db.commit()
    return {"success": True, "message": "Report deleted successfully."}


@router.post("/{report_id}/sync-twin")
def sync_report_vitals_to_twin(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Takes extracted physiological biomarkers (e.g. Heart Rate) from the report
    and automatically feeds them into the user's Digital Twin with on-chain Web3 verification.
    """
    report = db.query(MedicalReport).filter(
        MedicalReport.id == report_id,
        MedicalReport.user_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    biomarkers = json.loads(report.extracted_vitals) if report.extracted_vitals else []
    hr_biomarker = next((b for b in biomarkers if b.get("key") == "heart_rate"), None)

    if not hr_biomarker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No heart rate vital was detected in this report to synchronize with the Digital Twin."
        )

    # Ingest measurement
    meas = Measurement(
        patient_id=current_user.patient_id,
        timestamp=datetime.now(timezone.utc),
        measurement_type="heart_rate",
        value=float(hr_biomarker["value"]),
        unit="bpm",
        source=f"report_sync:{report.title}",
        is_late_arrival=False
    )
    db.add(meas)
    db.commit()

    # Evolve digital twin state & anchor on blockchain
    updated_state = DigitalTwinEngine.ingest_measurement_and_update(
        patient_id=current_user.patient_id,
        new_measurement_id=meas.id,
        db=db
    )

    return {
        "success": True,
        "message": f"Successfully synchronized {hr_biomarker['value']} bpm from report into Digital Twin.",
        "twin_state_version": updated_state.state_version,
        "latest_heart_rate": updated_state.latest_heart_rate,
        "on_chain_tx_hash": updated_state.on_chain_tx_hash,
        "ipfs_cid": updated_state.ipfs_cid
    }
