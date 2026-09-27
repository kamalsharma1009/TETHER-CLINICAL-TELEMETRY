"""
Standardized Plotly Chart Component for TETHER Dashboard
Renders dark healthcare IoT heart rate trend with baseline and stress thresholds.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Any
from utils.constants import HR_STRESS_MULTIPLIER


def render_hr_trend_chart(
    readings: List[Dict[str, Any]],
    baseline_hr: float = 72.0
):
    """
    Renders standardized rolling Heart Rate line chart inside a telemetry panel box.
    """
    st.markdown(
        """
        <div class="panel-header-row">
            <span class="panel-title">💓 REAL-TIME HEART RATE & STRESS TELEMETRY</span>
            <span class="panel-datastream-badge">STREAM: V0 (ROLLING 60s)</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not readings:
        st.markdown(
            """
            <div class="empty-chart-box">
                <span style="font-size: 24px;">📈</span>
                <span class="map-warning-title">WAITING FOR SENSOR DATA</span>
                <span class="map-warning-desc">Establishing rolling heart rate telemetry trend window...</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Extract timestamps and HR
    data = []
    for r in readings:
        hr = r.get("heart_rate")
        ts = r.get("timestamp", "")
        if " " in ts:
            time_part = ts.split(" ")[1]
        elif "T" in ts:
            time_part = ts.split("T")[1].split(".")[0]
        else:
            time_part = ts
        if hr is not None and hr > 0:
            data.append({"time": time_part, "heart_rate": hr})

    if not data:
        st.markdown(
            """
            <div class="empty-chart-box">
                <span style="font-size: 24px;">📈</span>
                <span class="map-warning-title">NO VALID HR SAMPLES</span>
                <span class="map-warning-desc">Wearable optical heart rate sensor signal pending.</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    df = pd.DataFrame(data)
    threshold = round(baseline_hr * HR_STRESS_MULTIPLIER, 1)

    fig = go.Figure()

    # Elevated threshold reference line
    fig.add_hline(
        y=threshold,
        line_dash="dot",
        line_color="#EF4444",
        line_width=1.5,
        annotation_text=f"Stress ≥{threshold} BPM (+25%)",
        annotation_position="top right",
        annotation_font_color="#EF4444",
        annotation_font_size=10
    )

    # Baseline HR reference line
    fig.add_hline(
        y=baseline_hr,
        line_dash="dash",
        line_color="#10B981",
        line_width=1.2,
        annotation_text=f"Baseline: {int(baseline_hr)} BPM",
        annotation_position="bottom right",
        annotation_font_color="#10B981",
        annotation_font_size=10
    )

    # Main Heart Rate line
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["heart_rate"],
            mode="lines+markers",
            name="Heart Rate",
            line=dict(color="#00F2FE", width=2.5, shape="spline"),
            marker=dict(
                size=6,
                color=["#EF4444" if val >= threshold else "#00F2FE" for val in df["heart_rate"]],
                line=dict(width=1, color="#ffffff")
            ),
            fill="tozeroy",
            fillcolor="rgba(0, 242, 254, 0.08)",
            hovertemplate="Time: %{x}<br>Heart Rate: <b>%{y} BPM</b><extra></extra>"
        )
    )

    # Layout styling for modern dark UI
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0F1626",
        margin=dict(l=10, r=10, t=20, b=10),
        height=280,
        showlegend=False,
        xaxis=dict(
            showgrid=True,
            gridcolor="#192338",
            gridwidth=1,
            color="#8E9EB5",
            tickfont=dict(size=9, color="#8E9EB5"),
            showline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#192338",
            gridwidth=1,
            color="#8E9EB5",
            tickfont=dict(size=9, color="#8E9EB5"),
            range=[max(40, df["heart_rate"].min() - 10), max(130, df["heart_rate"].max() + 15)],
            showline=False
        )
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
