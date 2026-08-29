"""Gemini Vision laboratory-report extractor."""

import os
from typing import List, Optional, Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    import pymupdf as fitz
except ImportError:
    fitz = None

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")


class ExtractedTest(BaseModel):
    test_name: str = Field(description="Exact or near-exact laboratory test name")
    value: Optional[float] = Field(default=None, description="Patient result as a number")
    unit: Optional[str] = Field(default="", description="Unit printed with the result")
    reference_low: Optional[float] = Field(default=None, description="Lower reference limit, if printed")
    reference_high: Optional[float] = Field(default=None, description="Upper reference limit, if printed")
    status: Literal["Low", "Normal", "High", "Unknown"] = Field(default="Unknown")


class ExtractedReport(BaseModel):
    hospital_name: Optional[str] = None
    report_date: Optional[str] = None
    tests: List[ExtractedTest] = Field(default_factory=list)


PROMPT = """
Read this medical laboratory report image/PDF page carefully. Extract only actual laboratory result rows.

For each result row return:
- test_name
- patient's numeric value
- unit
- reference_low and reference_high when the report prints a range
- status based ONLY on the printed reference range

Rules:
1. Do not invent values, reference ranges, or test rows.
2. Do not treat patient demographics, accession numbers, dates, headings, or footer text as test rows.
3. Preserve decimal values exactly as read.
4. If a result value cannot be read confidently, use null instead of guessing.
5. If a reference range is missing, use null bounds and status Unknown.
6. Extract the lab/hospital name and report date only when visible.
7. This is extraction, not diagnosis.
"""


def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()
    try:
        import streamlit as st
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return None


def get_client():
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY not found. Add it to .env or .streamlit/secrets.toml. "
            "Create a key at https://aistudio.google.com/apikey"
        )
    return genai.Client(api_key=key)


def _load_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        if fitz is None:
            raise RuntimeError("PyMuPDF is required for PDF uploads. Run: pip install pymupdf")
        doc = fitz.open(file_path)
        if len(doc) == 0:
            doc.close()
            raise RuntimeError("The PDF contains no pages.")
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        data = pix.tobytes("png")
        doc.close()
        return data, "image/png"

    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext)
    if not mime:
        raise RuntimeError("Unsupported file type. Use PNG, JPG, JPEG, or PDF.")
    with open(file_path, "rb") as f:
        return f.read(), mime


def extract_report(file_path):
    client = get_client()
    image_bytes, mime_type = _load_file(file_path)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractedReport,
        ),
    )

    parsed = getattr(response, "parsed", None)
    if parsed is None:
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned an empty extraction response.")
        parsed = ExtractedReport.model_validate_json(text)

    return parsed.model_dump()
