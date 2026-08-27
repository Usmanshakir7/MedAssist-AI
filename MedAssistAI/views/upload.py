import streamlit as st
import os
import uuid

from database.report_model import create_report
from ocr.extractor import extract_text
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def upload_page():

    st.title("📤 Upload Medical Report")

    report_type = st.selectbox(
        "Report Type",
        [
            "CBC",
            "Blood Sugar",
            "Lipid Profile",
            "Liver Function Test",
            "Kidney Function Test",
            "Thyroid Profile",
            "Other"
        ]
    )

    hospital = st.text_input("Hospital / Laboratory")

    report_date = st.date_input("Report Date")

    uploaded_file = st.file_uploader(
        "Upload Report",
        type=["pdf", "png", "jpg", "jpeg"]
    )

    if st.button("Upload Report"):

        if uploaded_file is None:
            st.error("Please select a report.")
            return

        # File size limit (10 MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("Maximum file size is 10 MB.")
            return

        extension = uploaded_file.name.split(".")[-1]

        filename = f"{uuid.uuid4()}.{extension}"

        save_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        user = st.session_state["user"]

        report_id = create_report(
            user["id"],
            report_type,
            hospital,
            str(report_date),
            save_path
        )

        st.success("Report uploaded successfully!")

        st.info(f"Report ID: {report_id}")
        text = extract_text(save_path)

st.subheader("📄 Extracted Text")

st.text_area(
    "OCR Output",
    st.text,
    height=300
)