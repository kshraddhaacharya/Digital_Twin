import io
import re
import json
from typing import Dict, Any, List, Optional
from pypdf import PdfReader
from PIL import Image


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts text from PDF document using pypdf.
    Clearly reports when a document has no readable digital text layer (scanned).
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        extracted = []
        for i, page in enumerate(reader.pages):
            txt = page.extract_text()
            if txt and txt.strip():
                extracted.append(f"--- Page {i + 1} ---\n{txt.strip()}")

        if not extracted:
            return (
                "[PDF uploaded successfully, but no digital text layer was found. "
                "This appears to be a scanned image-based document. "
                "Please enter vitals manually or review the document directly.]"
            )

        return "\n\n".join(extracted)
    except Exception as e:
        return f"[PDF parsing warning: Could not read text: {str(e)}]"


def extract_text_from_image(img_bytes: bytes, filename: str) -> str:
    """
    Validates image file and extracts metadata and header context.
    Does NOT invent simulated lab results if no text layer exists.
    """
    try:
        image = Image.open(io.BytesIO(img_bytes))
        width, height = image.size
        img_format = image.format or "IMAGE"
        
        meta_lines = [
            f"[Medical Document Image: {filename} ({img_format}, {width}x{height} px)]",
            "Notice: Automated OCR is not enabled for image files. Values must be verified by the user before inclusion in health records."
        ]
        
        if image.info:
            for k, v in image.info.items():
                if isinstance(v, str) and len(v.strip()) > 3:
                    meta_lines.append(f"{k}: {v.strip()}")
        
        return "\n".join(meta_lines)
    except Exception as e:
        return f"[Image processing warning: {str(e)}]"


def parse_clinical_biomarkers(text: str) -> List[Dict[str, Any]]:
    """
    Scans clinical text for standard medical biomarkers, values, reference ranges, and units.
    Does NOT fabricate results for unreadable text: only extracts clearly detected parameters.
    Labels every item with requires_confirmation=True for patient safety.
    """
    biomarkers = []

    # 1. Heart Rate / Pulse
    hr_match = re.search(r'(?:Heart Rate|Pulse Rate|Pulse|HR)[\s:]+(\d{2,3}(?:\.\d+)?)\s*(?:bpm|BPM|beats\/min)?', text, re.IGNORECASE)
    if hr_match:
        val = float(hr_match.group(1))
        if 30.0 <= val <= 250.0:
            biomarkers.append({
                "name": "Heart Rate",
                "key": "heart_rate",
                "value": val,
                "unit": "bpm",
                "reference_range": "60 - 100 bpm",
                "status": "normal" if 60 <= val <= 100 else ("elevated" if val > 100 else "low"),
                "confidence": "high",
                "requires_confirmation": True
            })

    # 2. Blood Pressure (Systolic / Diastolic)
    bp_match = re.search(r'(?:Blood Pressure|BP)[\s:]+(\d{2,3})\s*[\/|\\]\s*(\d{2,3})\s*(?:mmHg)?', text, re.IGNORECASE)
    if bp_match:
        sys_val = int(bp_match.group(1))
        dia_val = int(bp_match.group(2))
        biomarkers.append({
            "name": "Blood Pressure",
            "key": "blood_pressure",
            "value": f"{sys_val}/{dia_val}",
            "unit": "mmHg",
            "reference_range": "< 120/80 mmHg",
            "status": "normal" if (sys_val <= 120 and dia_val <= 80) else "elevated",
            "confidence": "high",
            "requires_confirmation": True
        })

    # 3. Blood Glucose
    glucose_match = re.search(r'(?:Fasting Blood Sugar|Blood Glucose|Fasting Glucose|Glucose)[\s:]+(\d{2,3}(?:\.\d+)?)\s*(?:mg\/dL|mg\/dl)?', text, re.IGNORECASE)
    if glucose_match:
        val = float(glucose_match.group(1))
        biomarkers.append({
            "name": "Fasting Glucose",
            "key": "glucose",
            "value": val,
            "unit": "mg/dL",
            "reference_range": "70 - 99 mg/dL",
            "status": "normal" if 70 <= val <= 99 else ("elevated" if val > 99 else "low"),
            "confidence": "high",
            "requires_confirmation": True
        })

    # 4. Total Cholesterol
    chol_match = re.search(r'(?:Total Cholesterol|Cholesterol)[\s:]+(\d{2,3}(?:\.\d+)?)\s*(?:mg\/dL|mg\/dl)?', text, re.IGNORECASE)
    if chol_match:
        val = float(chol_match.group(1))
        biomarkers.append({
            "name": "Total Cholesterol",
            "key": "total_cholesterol",
            "value": val,
            "unit": "mg/dL",
            "reference_range": "< 200 mg/dL",
            "status": "normal" if val < 200 else "elevated",
            "confidence": "moderate",
            "requires_confirmation": True
        })

    # 5. Oxygen Saturation (SpO2)
    spo2_match = re.search(r'(?:SpO2|Oxygen Saturation|O2 Sat)[\s:]+(\d{2,3}(?:\.\d+)?)\s*(?:%)?', text, re.IGNORECASE)
    if spo2_match:
        val = float(spo2_match.group(1))
        if val <= 100.0:
            biomarkers.append({
                "name": "Oxygen Saturation (SpO2)",
                "key": "spo2",
                "value": val,
                "unit": "%",
                "reference_range": "95 - 100 %",
                "status": "normal" if val >= 95 else "low",
                "confidence": "high",
                "requires_confirmation": True
            })

    # 6. Hemoglobin
    hgb_match = re.search(r'(?:Hemoglobin|Hgb)[\s:]+(\d{1,2}(?:\.\d+)?)\s*(?:g\/dL|g\/dl)?', text, re.IGNORECASE)
    if hgb_match:
        val = float(hgb_match.group(1))
        biomarkers.append({
            "name": "Hemoglobin",
            "key": "hemoglobin",
            "value": val,
            "unit": "g/dL",
            "reference_range": "12.0 - 17.5 g/dL",
            "status": "normal" if 12.0 <= val <= 17.5 else ("elevated" if val > 17.5 else "low"),
            "confidence": "moderate",
            "requires_confirmation": True
        })

    return biomarkers


def generate_report_summary(
    title: str,
    report_date: str,
    extracted_text: str,
    biomarkers: List[Dict[str, Any]],
    file_type: str = "pdf"
) -> str:
    """
    Constructs a factual, transparent clinical summary from parsed document text
    and recognized biomarkers without fabricating clinical diagnoses.
    """
    text_clean = (extracted_text or "").strip()
    is_scanned = (
        not text_clean
        or "no digital text layer was found" in text_clean
        or "Automated OCR is not enabled" in text_clean
        or "Could not read text" in text_clean
    )

    if is_scanned:
        return (
            f"Document '{title}' ({report_date}) was uploaded as an image or scanned document. "
            "Automated text extraction was unsuccessful because no digital character layer was found. "
            "Automated OCR is not configured; clinical biomarkers cannot be automatically parsed. "
            "Please review the original file directly or record vital signs manually."
        )

    # Word and line metrics
    lines = [line.strip() for line in text_clean.splitlines() if line.strip() and not line.startswith("--- Page")]
    word_count = len(text_clean.split())

    if biomarkers:
        param_strings = []
        for b in biomarkers:
            status_desc = b.get("status", "normal")
            param_strings.append(f"{b['name']}: {b['value']} {b.get('unit', '')} ({status_desc}, ref: {b.get('reference_range', 'standard')})")
        
        abnormal_count = sum(1 for b in biomarkers if b.get("status") in ["elevated", "low"])
        findings_note = f" All {len(biomarkers)} parameters are within normal reference ranges." if abnormal_count == 0 else f" Note: {abnormal_count} parameter(s) are outside standard resting ranges."

        return (
            f"Successfully processed '{title}' ({report_date}). Parsed {len(lines)} content lines ({word_count} words). "
            f"Extracted {len(biomarkers)} clinical parameter(s): {'; '.join(param_strings)}.{findings_note} "
            "Please review each parameter before confirming ingestion into your physiological twin."
        )
    else:
        return (
            f"Successfully processed '{title}' ({report_date}). Parsed {len(lines)} content lines ({word_count} words). "
            "The document contains readable digital text, but no recognized cardiovascular or metabolic vital signs "
            "(such as Heart Rate, Blood Pressure, Fasting Glucose, SpO2, or Hemoglobin) matched standard laboratory formats."
        )


def search_report_text(full_text: str, query: str) -> Dict[str, Any]:
    """
    Search engine scanning report text for keywords, returning matching snippets and line numbers.
    """
    if not full_text or not query:
        return {"query": query, "matches_found": 0, "snippets": []}

    q = query.strip().lower()
    lines = full_text.splitlines()
    matches = []

    for idx, line in enumerate(lines):
        if q in line.lower():
            start_ctx = max(0, idx - 1)
            end_ctx = min(len(lines), idx + 2)
            snippet = "\n".join(lines[start_ctx:end_ctx])
            matches.append({
                "line_number": idx + 1,
                "matched_line": line.strip(),
                "snippet": snippet
            })

    return {
        "query": query,
        "matches_found": len(matches),
        "snippets": matches
    }
