import streamlit as st
import plotly.graph_objects as go

from database.report_model import (
    get_reports_for_user,
    get_status_breakdown_for_user,
    get_distinct_test_names,
    get_test_history,
)

VITAL = "#2DD4BF"
HIGH = "#FF6B6B"
LOW = "#FFB84D"
OK = "#34D399"
UNK = "#7FA8A3"

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#EAF6F4"),
    margin=dict(l=10, r=10, t=30, b=10),
)


def _status_donut(breakdown: dict):
    labels = [k for k, v in breakdown.items() if v > 0]
    values = [v for v in breakdown.values() if v > 0]
    colors = {"Normal": OK, "High": HIGH, "Low": LOW, "Unknown": UNK}

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker=dict(colors=[colors[l] for l in labels]),
                textinfo="value",
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        **PLOT_LAYOUT,
        showlegend=True,
        legend=dict(orientation="h", y=-0.1),
        height=280,
    )
    return fig


def _trend_chart(history):
    dates = [h["report_date"] for h in history]
    values = [h["value"] for h in history]
    low = [h["reference_low"] for h in history]
    high = [h["reference_high"] for h in history]
    unit = history[0]["unit"] if history else ""

    fig = go.Figure()

    # Shaded normal-range band, when every point shares the same range
    if all(l is not None for l in low) and all(h is not None for h in high):
        fig.add_trace(go.Scatter(
            x=dates + dates[::-1],
            y=high + low[::-1],
            fill="toself",
            fillcolor="rgba(45, 212, 191, 0.10)",
            line=dict(color="rgba(0,0,0,0)"),
            hoverinfo="skip",
            name="Normal range",
            showlegend=True,
        ))

    point_colors = []
    for h in history:
        if h["status"] == "High":
            point_colors.append(HIGH)
        elif h["status"] == "Low":
            point_colors.append(LOW)
        elif h["status"] == "Normal":
            point_colors.append(OK)
        else:
            point_colors.append(UNK)

    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode="lines+markers",
        line=dict(color=VITAL, width=2.5),
        marker=dict(size=9, color=point_colors, line=dict(width=1, color="#0B1F26")),
        name=f"Value ({unit})" if unit else "Value",
    ))

    fig.update_layout(**PLOT_LAYOUT, height=340, hovermode="x unified")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)")

    return fig


def dashboard_page():

    from theme import page_header
    page_header("📊 Dashboard", "Trends across everything you've uploaded so far.")

    user = st.session_state["user"]
    reports = get_reports_for_user(user["id"])

    if not reports:
        st.markdown(
            """
            <div class="card">
                <b>Nothing to show yet.</b>
                <p style="color:var(--text-muted); margin-bottom:0;">
                    Upload a couple of reports and this page will start
                    charting how your values move over time.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Track a test over time")

        test_names = get_distinct_test_names(user["id"])
        selected_test = st.selectbox("Test", test_names)

        history = get_test_history(user["id"], selected_test)

        if len(history) < 2:
            st.info(
                "Only one data point so far for this test — upload another "
                "report with the same test to see a trend line."
            )
        else:
            st.plotly_chart(_trend_chart(history), use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Overall status breakdown")

        breakdown = get_status_breakdown_for_user(user["id"])
        st.plotly_chart(_status_donut(breakdown), use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
