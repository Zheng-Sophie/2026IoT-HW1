import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

def render_temperature_trend_chart(forecast_records: List[Dict[str, Any]], city_name: str):
    """Render temperature trend line chart for selected city."""
    if not forecast_records:
        st.info("尚無趨勢圖表資料")
        return

    df = pd.DataFrame(forecast_records)
    
    # Format time labels
    df["time_label"] = df["start_time"].apply(lambda x: x.split(" ")[-1] if " " in str(x) else str(x)[11:16])
    
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["time_label"],
        y=df["max_temp"],
        mode="lines+markers+text",
        name="最高溫 (MaxT)",
        text=[f"{v}°C" for v in df["max_temp"]],
        textposition="top center",
        line=dict(color="#FF4B4B", width=3),
        marker=dict(size=8)
    ))

    fig.add_trace(go.Scatter(
        x=df["time_label"],
        y=df["min_temp"],
        mode="lines+markers+text",
        name="最低溫 (MinT)",
        text=[f"{v}°C" for v in df["min_temp"]],
        textposition="bottom center",
        line=dict(color="#1E88E5", width=3),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title=f"🌡️ {city_name} 36小時溫度趨勢圖 (°C)",
        xaxis_title="預報時段",
        yaxis_title="溫度 (°C)",
        template="plotly_white",
        hovermode="x unified",
        height=380,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

def render_county_comparison_chart(cities_data: List[Dict[str, Any]]):
    """Render county temperature comparison bar chart."""
    if not cities_data:
        st.info("尚無全台縣市比較資料")
        return

    df = pd.DataFrame(cities_data)
    
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["city"],
        y=df["max_temp"],
        name="最高溫 MaxT",
        marker_color="#FF6B6B"
    ))

    fig.add_trace(go.Bar(
        x=df["city"],
        y=df["min_temp"],
        name="最低溫 MinT",
        marker_color="#4D96FF"
    ))

    fig.update_layout(
        title="🏙️ 全台各縣市最高溫與最低溫比較圖 (°C)",
        xaxis_title="縣市",
        yaxis_title="溫度 (°C)",
        barmode="group",
        template="plotly_white",
        height=400,
        margin=dict(l=20, r=20, t=50, b=50)
    )

    st.plotly_chart(fig, use_container_width=True)

def render_temperature_difference_chart(cities_data: List[Dict[str, Any]]):
    """Render diurnal temperature variation chart (Step 4 Requirement: 溫差 = 最高溫 - 最低溫)."""
    if not cities_data:
        return

    df = pd.DataFrame(cities_data).sort_values(by="temp_diff", ascending=False)

    fig = px.bar(
        df,
        x="city",
        y="temp_diff",
        title="📊 全台各縣市日夜溫差分析 (溫差 = 最高溫 - 最低溫)",
        labels={"city": "縣市", "temp_diff": "日夜溫差 (°C)"},
        color="temp_diff",
        color_continuous_scale="Viridis",
        template="plotly_white"
    )

    fig.update_layout(height=380, margin=dict(l=20, r=20, t=50, b=50))
    st.plotly_chart(fig, use_container_width=True)
