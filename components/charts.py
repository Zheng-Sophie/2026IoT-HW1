import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

def render_temperature_trend_chart(forecast_records: List[Dict[str, Any]], city_name: str):
    """Render temperature trend line chart for selected city with dark neon styling."""
    if not forecast_records:
        st.info("尚無趨勢圖表資料")
        return

    df = pd.DataFrame(forecast_records)
    
    # Format time labels
    df["time_label"] = df["start_time"].apply(lambda x: x.split(" ")[-1] if " " in str(x) else str(x)[11:16])
    
    fig = go.Figure()

    # Min Temp line
    fig.add_trace(go.Scatter(
        x=df["time_label"],
        y=df["min_temp"],
        mode="lines+markers+text",
        name="最低溫 (MinT)",
        text=[f"{v}°C" for v in df["min_temp"]],
        textposition="bottom center",
        line=dict(color="#38bdf8", width=3),
        marker=dict(size=9, color="#0284c7")
    ))

    # Max Temp line with area fill
    fig.add_trace(go.Scatter(
        x=df["time_label"],
        y=df["max_temp"],
        mode="lines+markers+text",
        name="最高溫 (MaxT)",
        text=[f"{v}°C" for v in df["max_temp"]],
        textposition="top center",
        line=dict(color="#f87171", width=3),
        marker=dict(size=9, color="#ef4444"),
        fill='tonexty',
        fillcolor='rgba(56, 189, 248, 0.12)'
    ))

    fig.update_layout(
        title=f"📈 {city_name} 36 小時溫度變化趨勢 (°C)",
        xaxis_title="預報時段",
        yaxis_title="溫度 (°C)",
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0.6)",
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        hovermode="x unified",
        height=380,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

def render_county_comparison_chart(cities_data: List[Dict[str, Any]]):
    """Render county temperature comparison bar chart in dark theme."""
    if not cities_data:
        st.info("尚無全台縣市比較資料")
        return

    df = pd.DataFrame(cities_data)
    
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["city"],
        y=df["max_temp"],
        name="最高溫 MaxT",
        marker_color="#f87171"
    ))

    fig.add_trace(go.Bar(
        x=df["city"],
        y=df["min_temp"],
        name="最低溫 MinT",
        marker_color="#38bdf8"
    ))

    fig.update_layout(
        title="🏙️ 全台各縣市最高溫與最低溫比較圖 (°C)",
        xaxis_title="縣市",
        yaxis_title="溫度 (°C)",
        barmode="group",
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0.6)",
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        height=400,
        margin=dict(l=20, r=20, t=50, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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
        color_continuous_scale="Plasma",
        template="plotly_dark"
    )

    fig.update_layout(
        paper_bgcolor="rgba(15, 23, 42, 0.6)",
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        height=380,
        margin=dict(l=20, r=20, t=50, b=50)
    )
    st.plotly_chart(fig, use_container_width=True)
