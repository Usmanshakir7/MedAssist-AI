import streamlit as st
import pandas as pd

from database.report_model import (
    get_reports_for_user,
    get_test_results,
    delete_report,
)
from theme import page_header, status_badge_html, range_bar_html


def _format_range(low, high):
    if low is None and high is None:
        return "—"
    if low is None:
        return f"< {high}"
    if high is None:
        return f"> {low}"
    return f"{low} – {high}"


def reports_page():
    page_header("📄 Reports", "Browse and review your uploaded lab reports.")

    user = st.session_state["user"]
    reports = get_reports_for_user(user["id"])

    # ---------- Empty state ----------
    if not reports:
        st.markdown(
            """
            <div class="card" style="text-align:center; padding:28px 20px;">
                <b>No reports yet</b>
                <p style="color:var(--text-muted); margin:8px 0 0 0;">
                    Upload your first lab report and it will appear here.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ---------- Select report ----------
    labels = [
        f"{r['report_type']} — {r['hospital_name'] or 'Unknown'} — {r['report_date']} (ID {r['report_id']})"
        for r in reports
    ]

    selected = st.selectbox(
        "Select a report",
        labels,
        key="reports_report_select",
    )
    report = reports[labels.index(selected)]
    report_id = report["report_id"]

    results = get_test_results(report_id)
    abnormal = [r for r in results if r["status"] in ("Low", "High")]

    # ---------- Report header card ----------
    st.markdown(
        f"""
        <div class="card" style="border-top-color: var(--vital);">
            <h3 style="margin:0;">{report['report_type']} · {report['report_date']}</h3>
            <p style="color:var(--text-muted); margin:4px 0 0 0;">
                Hospital/Lab: {report['hospital_name'] or 'Not specified'}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- Actions: CSV + Delete ----------
    col_a, col_b, col_c = st.columns([1, 1, 2])

    with col_a:
        if results:
            df_export = pd.DataFrame([dict(r) for r in results])
            # Keep only useful columns
            cols = [c for c in ["test_name", "value", "unit", "reference_low", "reference_high", "status"] if c in df_export.columns]
            df_export = df_export[cols]
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Export CSV",
                data=csv,
                file_name=f"report_{report_id}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with col_b:
        if st.button("🗑️ Delete report", use_container_width=True):
            st.session_state["confirm_delete_id"] = report_id

    # Confirm delete
    if st.session_state.get("confirm_delete_id") == report_id:
        st.warning("Are you sure you want to permanently delete this report?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes, delete it", type="primary", key="confirm_delete_yes"):
                ok = delete_report(report_id, user["id"])
                st.session_state.pop("confirm_delete_id", None)
                if ok:
                    st.success("Report deleted.")
                    st.rerun()
                else:
                    st.error("Could not delete report.")
        with c2:
            if st.button("Cancel", key="confirm_delete_no"):
                st.session_state.pop("confirm_delete_id", None)
                st.rerun()

    if not results:
        st.warning("No extracted test results found for this report.")
        return

    # ---------- Abnormal warning ----------
    if abnormal:
        st.markdown(
            f"""
            <div class="card" style="border-top-color: var(--status-high);">
                ⚠️ <b>{len(abnormal)}</b> value(s) outside the normal range.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------- Results table (reliable version) ----------
    st.markdown("#### Test results")

    # Build a clean dataframe for display
    rows = []
    for r in results:
        rows.append({
            "Test": r["test_name"],
            "Value": r["value"] if r["value"] is not None else "—",
            "Unit": r["unit"] or "",
            "Normal range": _format_range(r["reference_low"], r["reference_high"]),
            "Status": r["status"] or "Unknown",
        })

    df = pd.DataFrame(rows)

    # Color the Status column lightly via pandas Styler
    def color_status(val):
        if val == "High":
            return "color: #FF6B6B; font-weight: 600"
        if val == "Low":
            return "color: #FFB84D; font-weight: 600"
        if val == "Normal":
            return "color: #34D399; font-weight: 600"
        return "color: #7FA8A3"

    styled = df.style.map(color_status, subset=["Status"])

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
    )