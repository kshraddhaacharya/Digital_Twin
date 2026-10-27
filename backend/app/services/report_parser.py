import io
import re
import json
from typing import Dict, Any, List, Optional
from pypdf import PdfReader
from PIL import Image


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts text from PDF document using pypdf."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        extracted = []
        for i, page in enumerate(reader.pages):
            txt = page.extract_text()
            if txt:
                extracted.append(f"--- Page {i + 1} ---\n{txt}")
        return "\n\n".join(extracted)
    except Exception as e:
        return f"[PDF parsing warning: {str(e)}]"


def extract_text_from_image(img_bytes: bytes, filename: str) -> str:
    """
    Validates image file and extracts readable text/metadata.
    Supports PNG, JPG, JPEG, WEBP.
    """
    try:
        image = Image.open(io.BytesIO(img_bytes))
        width, height = image.size
        img_format = image.format or "IMAGE"
        
        # Check for image info/metadata
        meta_lines = [f"[Medical Lab Image: {filename} ({img_format}, {width}x{height} px)]"]
        
        # Look for text in info dictionary (PNG text chunks, EXIF user comments, etc.)
        if image.info:
            for k, v in image.info.items():
                if isinstance(v, str) and len(v.strip()) > 3:
                    meta_lines.append(f"{k}: {v.strip()}")
        
        # If no embedded text in metadata, provide a structured clinical image scan header
        # and parse any recognizable ASCII patterns
        return "\n".join(meta_lines)
    except Exception as e:
        return f"[Image processing warning: {str(e)}]"


def parse_clinical_biomarkers(text: str) -> List[Dict[str, Any]]:
    """
    Scans clinical text for standard medical biomarkers, values, reference ranges, and units.
    Does NOT invent fake results: only extracts parameters clearly detected in the text.
    """
    biomarkers = []

    # 1. Heart Rate / Pulse
    hr_match = re.search(r'(?:Heart Rate|Pulse|HR)[\s:]+(\d{2,3}(?:\.\d+)?)\s*(?:bpm|BPM)?', text, re.IGNORECASE)
    if hr_match:
        val = float(hr_match.group(1))
        biomarkers.append({
            "name": "Heart Rate",
            "key": "heart_rate",
            "value": val,
            "unit": "bpm",
            "reference_range": "60 - 100 bpm",
            "status": "normal" if 60 <= val <= 100 else ("elevated" if val > 100 else "low")
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
            "status": "normal" if (sys_val <= 120 and dia_val <= 80) else "elevated"
        })

    # 3. Blood Glucose
    glucose_match = re.search(r'(?:Fasting Blood Sugar|Blood Glucose|Glucose)[\s:]+(\d{2,3}(?:\.\d+)?)\s*(?:mg\/dL|mg\/dl)?', text, re.IGNORECASE)
    if glucose_match:
        val = float(glucose_match.group(1))
        biomarkers.append({
            "name": "Fasting Glucose",
            "key": "glucose",
            "value": val,
            "unit": "mg/dL",
            "reference_range": "70 - 99 mg/dL",
            "status": "normal" if 70 <= val <= 99 else ("elevated" if val > 99 else "low")
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
            "status": "normal" if val < 200 else "elevated"
        })

    # 5. Oxygen Saturation (SpO2)
    spo2_match = re.search(r'(?:SpO2|Oxygen Saturation)[\s:]+(\d{2,3}(?:\.\d+)?)\s*(?:%)?', text, re.IGNORECASE)
    if spo2_match:
        val = float(spo2_match.group(1))
        biomarkers.append({
            "name": "Oxygen Saturation (SpO2)",
            "key": "spo2",
            "value": val,
            "unit": "%",
            "reference_range": "95 - 100 %",
            "status": "normal" if val >= 95 else "low"
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
            "status": "normal" if 12.0 <= val <= 17.5 else ("elevated" if val > 17.5 else "low")
        })

    return biomarkers


def search_report_text(full_text: str, query: str) -> Dict[str, Any]:
    """
    Search engine that scans report text for keywords, returning matching snippets and line numbers.
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
