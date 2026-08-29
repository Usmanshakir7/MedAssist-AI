import streamlit as st
import pandas as pd
import json
from datetime import datetime

from database.user_model import update_password, update_full_name
from database.report_model import get_reports_for_user, get_test_results
from theme import page_header


def settings_page():
    page_header("⚙️ Settings", "Manage your profile and data.")

    user = st.session_state["user"]

    # ---------- Profile card ----------
    st.markdown("#### Profile")
    st.markdown(
        f"""
        <div class="card">
            <div style="color:var(--text-muted); font-size:0.8rem;">Name</div>
            <div style="margin-bottom:10px;">{user.get('full_name', '—')}</div>
            <div style="color:var(--text-muted); font-size:0.8rem;">Email</div>
            <div>{user.get('email', '—')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- Change name ----------
    st.markdown("#### Change name")
    with st.form("change_name_form"):
        new_name = st.text_input("Full name", value=user.get("full_name", ""))
        name_submitted = st.form_submit_button("Save name", type="primary")

        if name_submitted:
            ok, msg = update_full_name(user["id"], new_name)
            if ok:
                # Refresh session so header/welcome show the new name
                st.session_state.user = dict(st.session_state.user)
                st.session_state.user["full_name"] = new_name.strip()
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    # ---------- Change password ----------
    st.markdown("#### Change password")
    with st.form("change_password_form"):
        current_pw = st.text_input("Current password", type="password")
        new_pw = st.text_input("New password", type="password")
        confirm_pw = st.text_input("Confirm new password", type="password")
        pw_submitted = st.form_submit_button("Update password", type="primary")

        if pw_submitted:
            if not current_pw or not new_pw or not confirm_pw:
                st.error("Please fill all password fields.")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match.")
            else:
                ok, msg = update_password(user["id"], current_pw, new_pw)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    # ---------- Export all data ----------
    st.markdown("#### Export my data")
    st.caption("Download all your reports and test results as CSV or JSON.")

    reports = get_reports_for_user(user["id"])

    if not reports:
        st.info("No reports to export yet.")
        return

    # Build flat rows for CSV
    all_rows = []
    full_export = []

    for r in reports:
        results = get_test_results(r["report_id"])
        report_block = {
            "report_id": r["report_id"],
            "report_type": r["report_type"],
            "hospital_name": r["hospital_name"],
            "report_date": r["report_date"],
            "uploaded_at": r["uploaded_at"] if "uploaded_at" in r.keys() else None,
            "tests": [dict(t) for t in results],
        }
        full_export.append(report_block)

        for t in results:
            all_rows.append({
                "report_id": r["report_id"],
                "report_type": r["report_type"],
                "hospital": r["hospital_name"],
                "report_date": r["report_date"],
                "test_name": t["test_name"],
                "value": t["value"],
                "unit": t["unit"],
                "reference_low": t["reference_low"],
                "reference_high": t["reference_high"],
                "status": t["status"],
            })

    df = pd.DataFrame(all_rows)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    json_bytes = json.dumps(full_export, indent=2, default=str).encode("utf-8")

    stamp = datetime.now().strftime("%Y%m%d")
    c1, c2 = st.columns(2)

    with c1:
        st.download_button(
            "⬇️ Download CSV",
            data=csv_bytes,
            file_name=f"medassist_export_{stamp}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with c2:
        st.download_button(
            "⬇️ Download JSON",
            data=json_bytes,
            file_name=f"medassist_export_{stamp}.json",
            mime="application/json",
            use_container_width=True,
        )