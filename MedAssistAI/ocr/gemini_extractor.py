"""
Gemini Vision based extractor.

Replaces: image -> EasyOCR -> regex parser
With:     image -> Gemini Vision -> structured JSON (validated with Pydantic)

Uses the Gemini API free tier (an API key from https://aistudio.google.com/apikey),
via Google's current `google-genai` SDK.
"""

import os
import io
from typing import List, Optional, Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

try:
    import pymupdf as fitz  # PyMuPDF, only needed for PDF uploads
except ImportError:
    fitz = None


GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


# --------------------------------------------------------------------
# STRUCTURED OUTPUT SCHEMA
#
# This is what forces Gemini to return clean JSON instead of free text
# that would need to be regex-parsed like the old EasyOCR pipeline.
# --------------------------------------------------------------------

class ExtractedTest(BaseModel):
    test_name: str = Field(description="Name of the lab test, e.g. 'Hemoglobin', 'WBC'")
    value: Optional[float] = Field(default=None, description="Numeric result value")
    unit: Optional[str] = Field(default="", description="Unit of the result, e.g. 'g/dL', 'fL', '%'")
    reference_low: Optional[float] = Field(default=None, description="Lower bound of normal reference range")
    reference_high: Optional[float] = Field(default=None, description="Upper bound of normal reference range")
    status: Literal["Low", "Normal", "High", "Unknown"] = Field(
        default="Unknown",
        description="Whether the value is Low, Normal or High compared to the reference range"
    )


class ExtractedReport(BaseModel):
    hospital_name: Optional[str] = Field(default=None, description="Lab / hospital name printed on the report, if visible")
    report_date: Optional[str] = Field(default=None, description="Date printed on the report, if visible (YYYY-MM-DD if possible)")
    tests: List[ExtractedTest] = Field(default_factory=list)


EXTRACTION_PROMPT = """
You are reading a scanned medical laboratory report (e.g. CBC, blood sugar,
lipid profile, LFT, KFT, thyroid profile).

Carefully read every row of the results table in the image and extract:
- test_name: the test/parameter name (keep it close to what's printed)
- value: the patient's numeric result for that row
- unit: the unit shown next to the result (e.g. g/dL, fL, pg, %, mg/dL)
- reference_low / reference_high: the lower and upper bounds of the normal
  reference range shown for that row (if the report only gives a single
  cutoff like "< 200", set reference_low to null and reference_high to 200;
  if it's a single "normal below X" style range, use your best judgement)
- status: "Low" if value is below reference_low, "High" if above
  reference_high, "Normal" if within range, "Unknown" if you cannot
  determine it

Also extract the hospital/laboratory name and the report date if visible
anywhere on the page.

Do not invent rows that are not present in the image. Do not include
headers, patient demographic fields, or footer text as test rows. Only
include rows that represent an actual lab test with a numeric result.
"""


def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            api_key = None

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found. Set it as an environment variable "
            "or in .streamlit/secrets.toml. Get a free key at "
            "https://aistudio.google.com/apikey"
        )

    return genai.Client(api_key=api_key)


def _load_image_bytes(file_path: str) -> tuple[bytes, str]:
    """
    Returns (bytes, mime_type) for the given upload.
    PDFs are rendered to a PNG of the first page.
    """

    ext = file_path.lower().split(".")[-1]

    if ext == "pdf":
        if fitz is None:
            raise RuntimeError(
                "PyMuPDF is required to read PDF uploads. Install it with "
                "'pip install pymupdf'."
            )

        doc = fitz.open(file_path)
        page = doc.load_page(0)
        # Render at higher resolution so small table text stays legible.
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        image_bytes = pix.tobytes("png")
        doc.close()
        return image_bytes, "image/png"

    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }

    with open(file_path, "rb") as f:
        return f.read(), mime_map.get(ext, "image/png")


def extract_report(file_path: str) -> dict:
    """
    Sends the report image/PDF to Gemini and returns a validated dict:

    {
        "hospital_name": str | None,
        "report_date": str | None,
        "tests": [
            {
                "test_name": str,
                "value": float | None,
                "unit": str,
                "reference_low": float | None,
                "reference_high": float | None,
                "status": "Low" | "Normal" | "High" | "Unknown"
            },
            ...
        ]
    }

    Raises RuntimeError if Gemini's output doesn't match the expected schema.
    """

    client = get_client()
    image_bytes, mime_type = _load_image_bytes(file_path)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            EXTRACTION_PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractedReport,
            temperature=0,
        ),
    )

    # response.parsed is already an ExtractedReport instance when the SDK
    # can validate it against the schema. Fall back to manual validation
    # against response.text if .parsed is unavailable for any reason.
    parsed: Optional[ExtractedReport] = getattr(response, "parsed", None)

    if parsed is None:
        parsed = ExtractedReport.model_validate_json(response.text)

    return parsed.model_dump()
