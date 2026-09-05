import hashlib
import os
import uuid
from datetime import date
import streamlit as st

from database.report_model import create_report, save_test_results
from ocr.gemini_extractor import extract_report
from ocr.validator import validate_and_normalize

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def detect_report_type(tests):
    names = " ".join((x.get("test_name") or "").lower() for x in tests)
    if any(k in names for k in ["hemoglobin", "rbc", "mch", "mchc", "platelet", "wbc", "neutrophil"]):
        return "CBC"
    if any(k in names for k in ["glucose", "blood sugar", "fasting sugar", "random sugar", "hba1c"]):
        return "Blood Sugar"
    if any(k in names for k in ["cholesterol", "triglyceride", "ldl", "hdl"]):
        return "Lipid Profile"
    if any(k in names for k in ["alt", "ast", "bilirubin", "alkaline phosphatase", "alp"]):
        return "Liver Function Test"
    if any(k in names for k in ["creatinine", "urea", "egfr", "uric acid"]):
        return "Kidney Function Test"
    if any(k in names for k in ["tsh", "t3", "t4", "thyroxine"]):
        return "Thyroid Profile"
    return "Other"


def upload_section():
    st.markdown(
        """<div class="guide-card"><b>📷</b><div><h3 style="margin:0">Upload a clear report</h3>
        <p style="margin:6px 0 0">JPG, PNG and PDF are supported. A clear, straight image gives the AI the best chance of reading every row.</p>
        </div></div>""",
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Choose your laboratory report",
        type=["png", "jpg", "jpeg", "pdf"],
        help="Maximum 10 MB. Clear images work best.",
        key="onepage_upload",
    )
    if not uploaded:
        return

    if uploaded.size > 10 * 1024 * 1024:
        st.error("Maximum file size is 10 MB.")
        return

    raw = uploaded.getvalue()
    signature = hashlib.sha256(raw).hexdigest()
    if st.session_state.get("processed_upload_signature") == signature:
        st.success("This report has already been processed in this session.")
        return

    ext = os.path.splitext(uploaded.name)[1].lower()
    path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}{ext}")

    try:
        with open(path, "wb") as f:
            f.write(raw)

        with st.status("Analyzing your report…", expanded=True) as status:
            st.write("Reading the report with MedAssist Vision…")
            extracted = extract_report(path)
            tests = validate_and_normalize(extracted.get("tests", []))
            report_type = detect_report_type(tests)
            hospital = (extracted.get("hospital_name") or "").strip()
            report_date = extracted.get("report_date") or str(date.today())

            user = st.session_state["user"]
            report_id = create_report(
                user["id"], report_type, hospital, report_date, path
            )
            save_test_results(report_id, tests)

            st.write(f"Detected {len(tests)} result row(s).")
            if tests:
                status.update(label="Report saved successfully", state="complete")
            else:
                status.update(label="Report saved, but no numeric test rows were recognized", state="complete")

        st.session_state["processed_upload_signature"] = signature
        st.session_state["last_uploaded_report_id"] = report_id
        st.success(f"Report uploaded successfully. Report ID: {report_id}")
        if not tests:
            st.warning("No recognizable test results were found. The image was saved, but the report needs a clearer image or a supported layout.")
        st.rerun()

    except Exception as exc:
        try:
            os.remove(path)
        except OSError:
            pass
        st.error(f"Extraction failed: {exc}")
