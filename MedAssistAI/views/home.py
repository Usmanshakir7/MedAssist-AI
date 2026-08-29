import html
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from database.report_model import (
    get_reports_for_user, get_test_results, count_abnormal_results_for_user,
    get_status_breakdown_for_user, get_distinct_test_names, get_test_history, delete_report,
)
from theme import stat_card_html, page_header
from views.upload import upload_section
from views.Settings import settings_page
from ai.insights import generate_insights, generate_urdu_recipe


def anchor(name):
    st.markdown(f'<div id="{name}" class="anchor-offset"></div>', unsafe_allow_html=True)


def fmt(v):
    if v is None:
        return "—"
    try:
        return f"{float(v):g}"
    except Exception:
        return str(v)


def fmt_range(lo, hi):
    if lo is None and hi is None:
        return "—"
    if lo is None:
        return f"< {fmt(hi)}"
    if hi is None:
        return f"> {fmt(lo)}"
    return f"{fmt(lo)} – {fmt(hi)}"


def result_table(results):
    rows = []
    for r in results:
        rows.append({
            "Test": r["test_name"],
            "Value": fmt(r["value"]),
            "Unit": r["unit"] or "",
            "Reference": fmt_range(r["reference_low"], r["reference_high"]),
            "Status": r["status"] or "Unknown",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def reports_section(user_id):
    reports = get_reports_for_user(user_id)
    if not reports:
        st.markdown('<div class="empty-card"><b>No reports yet.</b><br>Your saved reports will appear here.</div>', unsafe_allow_html=True)
        return

    for r in reports:
        results = get_test_results(r["report_id"])
        abnormal = sum(1 for x in results if x["status"] in ("Low", "High"))
        with st.container(border=True):
            c1, c2, c3 = st.columns([2.5, 1, 1])
            with c1:
                st.markdown(
                    f'**{html.escape(r["report_type"] or "Other")}** · {html.escape(r["report_date"] or "Unknown date")}<br><span class="muted">{html.escape(r["hospital_name"] or "Unknown lab")}</span>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.metric("Results", len(results))
            with c3:
                st.metric("Outside range", abnormal)

            if results:
                with st.expander("View outcome report", expanded=(r["report_id"] == st.session_state.get("last_uploaded_report_id"))):
                    result_table(results)
                    csv = pd.DataFrame([dict(x) for x in results]).to_csv(index=False).encode("utf-8")
                    st.download_button("⬇️ Download CSV", csv, f"report_{r['report_id']}.csv", "text/csv", key=f"csv_{r['report_id']}")
            else:
                st.warning("No recognizable test results were extracted from this report.")

            if st.button("🗑️ Delete", key=f"delete_{r['report_id']}"):
                if delete_report(r["report_id"], user_id):
                    st.rerun()


def dashboard_section(user_id):
    reports = get_reports_for_user(user_id)
    breakdown = get_status_breakdown_for_user(user_id)
    cols = st.columns(4)
    stats = [
        ("Reports", len(reports), "accent"),
        ("Outside range", breakdown.get("Low", 0) + breakdown.get("High", 0), "warn"),
        ("Normal", breakdown.get("Normal", 0), "accent"),
        ("Tracked tests", len(get_distinct_test_names(user_id)), "accent"),
    ]
    for col, (label, value, accent) in zip(cols, stats):
        with col:
            st.markdown(stat_card_html(label, str(value), accent), unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        vals = [v for v in breakdown.values() if v]
        labs = [k for k, v in breakdown.items() if v]
        if vals:
            fig = go.Figure(go.Pie(labels=labs, values=vals, hole=.62, textinfo="value"))
            fig.update_layout(height=320, margin=dict(l=10,r=10,t=30,b=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#EAF6F4", legend_orientation="h")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("The status chart will appear after results are extracted.")

    with right:
        names = get_distinct_test_names(user_id)
        if not names:
            st.info("Upload reports with numeric results to build trends.")
            return
        selected = st.selectbox("Track a test", names, key="dashboard_test")
        history = get_test_history(user_id, selected)
        df = pd.DataFrame([dict(x) for x in history])
        if df.empty:
            st.info("No numeric history available for this test.")
            return
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        if df.empty:
            st.info("No numeric history available for this test.")
            return
        fig = px.line(df, x="report_date", y="value", markers=True, labels={"value": selected, "report_date": "Report date"})
        fig.update_layout(height=320, margin=dict(l=10,r=10,t=30,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#EAF6F4")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def insights_section(user_id):
    reports = get_reports_for_user(user_id)
    if not reports:
        st.info("AI Insights will appear after you upload a report with extracted results.")
        return

    labels = [f'{r["report_type"]} — {r["report_date"]} (ID {r["report_id"]})' for r in reports]
    selected = st.selectbox("Choose report", labels, key="onepage_insight_report")
    report = reports[labels.index(selected)]
    results = get_test_results(report["report_id"])
    if not results:
        st.warning("No extracted test values are available for this report.")
        return

    language = st.radio(
        "AI summary language",
        ["🇬🇧 English", "🇵🇰 اردو"],
        horizontal=True,
        key=f"ai_language_{report['report_id']}",
    )
    lang = "Urdu" if language.endswith("اردو") else "English"
    cache_key = f"{report['report_id']}::{lang}"

    if cache_key in st.session_state.ai_cache:
        summary, recommendation = st.session_state.ai_cache[cache_key]
        st.markdown(f'<div class="insight-card"><div class="eyebrow">AI SUMMARY</div><h3>What your report shows</h3><p>{html.escape(summary)}</p></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="recommend-card"><div class="eyebrow">GENERAL GUIDANCE</div><h3>What you can do next</h3><p>{html.escape(recommendation)}</p></div>', unsafe_allow_html=True)
        if st.button("↻ Regenerate summary", key=f"regen_{cache_key}"):
            del st.session_state.ai_cache[cache_key]
            st.rerun()
    else:
        if st.button("✨ Generate AI Summary", type="primary", key=f"generate_{cache_key}"):
            try:
                with st.spinner("Generating your explanation…"):
                    st.session_state.ai_cache[cache_key] = generate_insights(results, lang)
                st.rerun()
            except Exception as exc:
                st.error(f"Could not generate AI summary: {exc}")

    if lang == "Urdu":
        st.markdown("### 🥗 اردو غذائی رہنمائی اور گھریلو ترکیب")
        recipe_key = f"{report['report_id']}::recipe"
        if recipe_key not in st.session_state.recipe_cache:
            if st.button("🍲 Generate Urdu dietary guidance", key=f"recipe_{report['report_id']}"):
                try:
                    with st.spinner("اردو غذائی رہنمائی تیار کی جا رہی ہے…"):
                        st.session_state.recipe_cache[recipe_key] = generate_urdu_recipe(results)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Recipe generation failed: {exc}")
        else:
            data = st.session_state.recipe_cache[recipe_key]
            st.markdown("#### غذائی تجاویز")
            for item in data.get("dietary_suggestions", []):
                st.markdown(f"• {item}")
            st.markdown(f"#### 🍲 {data.get('recipe_name', 'آسان گھریلو ترکیب')}")
            st.markdown("**اجزاء**")
            for item in data.get("ingredients", []):
                st.markdown(f"• {item}")
            st.markdown("**طریقہ تیاری**")
            for i, item in enumerate(data.get("preparation", []), 1):
                st.markdown(f"**{i}.** {item}")
            st.warning(data.get("important_note", "یہ عمومی غذائی معلومات ہیں، طبی علاج کا متبادل نہیں۔"))

    st.caption("AI output is general educational information, not a diagnosis or medical advice.")


def home_page():
    user = st.session_state["user"]
    reports = get_reports_for_user(user["id"])
    first = (user.get("full_name") or "User").split()[0]
    abnormal = count_abnormal_results_for_user(user["id"])

    anchor("home-section")
    st.markdown(
        f'<div class="hero"><div><div class="eyebrow">MEDASSIST AI</div><h1>Welcome back, {html.escape(first)}.</h1><p>Your reports, extracted results, trends and AI explanations in one continuous workspace.</p></div><div class="hero-orbit">🩺</div></div>',
        unsafe_allow_html=True,
    )
    if not reports:
        st.markdown(
            '<div class="guide-card"><b>01</b><div><h3>Start with a report</h3><p>Scroll down and upload a clear image or PDF. The app will save the report and show the extracted outcome automatically.</p></div></div>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="scroll-cue">↓ Scroll to upload</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="stat-grid">'
        + stat_card_html("Reports", str(len(reports)), "accent")
        + stat_card_html("Outside range", str(abnormal), "warn")
        + stat_card_html("Latest report", str(reports[0]["report_date"]) if reports else "—")
        + '</div>',
        unsafe_allow_html=True,
    )

    anchor("upload-section")
    page_header("＋ Upload Report", "Different laboratory report types can be uploaded; Gemini reads the actual image instead of relying on fixed CBC columns.")
    upload_section()
    st.markdown('<div class="scroll-cue">↓ Saved outcome report</div>', unsafe_allow_html=True)

    anchor("reports-section")
    page_header("📄 Outcome Reports", "Your extracted values are saved to your account and shown below.")
    reports_section(user["id"])

    anchor("dashboard-section")
    page_header("📊 Dashboard", "Interactive graphs based on the results you have uploaded over time.")
    dashboard_section(user["id"])
    st.markdown('<div class="scroll-cue">↓ Continue to AI Insights</div>', unsafe_allow_html=True)

    anchor("insights-section")
    page_header("🤖 AI Insights", "Choose English or Urdu for the explanation. Urdu also includes a separate general dietary section.")
    insights_section(user["id"])

    anchor("settings-section")
    settings_page()
