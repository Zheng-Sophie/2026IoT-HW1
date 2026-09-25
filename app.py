import streamlit as st
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Taiwan Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from config import CWA_API_KEY
from services.weather_service import WeatherService
from components.weather_cards import render_summary_cards, render_city_cards
from components.charts import (
    render_temperature_trend_chart,
    render_county_comparison_chart,
    render_temperature_difference_chart
)
from components.weather_map import render_taiwan_weather_map

st.set_page_config(layout="wide")

# Initialize Weather Service
@st.cache_resource
def get_service():
    service = WeatherService()
    try:
        service.sync_data()
    except Exception as e:
        st.warning(f"Initial sync warning: {e}")
    return service

weather_service = get_service()

# --- Custom Google Maps Style Full-Screen Layout CSS ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        width: 100vw !important;
    }

    /* 1. 隱藏 Streamlit 原生元件 */
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    div[data-testid="stDecoration"] { display: none !important; }

    /* 2. 強制打破外層容器的所有寬度與內邊距限制 (關鍵修改) */
    .stAppViewContainer, .stMain, .stMainBlockContainer, .block-container {
        padding: 0rem !important;
        margin: 0rem !important;
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* 移除垂直區塊間的預設間距 */
    div[data-testid="stVerticalBlock"] {
        gap: 0rem !important;
    }
    
    /* 3. 強制 st_folium 的 iframe 與包裹元件達到 100% 寬度且無邊框 */
    iframe {
        width: 100% !important;
        border: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* 讓 streamlit-folium 產生的額外 div 容器也不留空隙 */
    div[data-testid="stHtml"] {
        width: 100% !important;
    }

    /* Top Floating Control Bar */
    .top-floating-bar {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 12px 20px;
        border-bottom: 1px solid #e0e0e0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
</style>
""", unsafe_allow_html=True)

# Top Bar with Title, API Status, and Left-Top Location Dropdown
cities = weather_service.get_cities()
if not cities:
    cities = ["臺北市", "新北市", "基隆市", "桃園市", "臺中市", "臺南市", "高雄市"]

# Top Header Layout with Left-Top Location Dropdown Selector
col_nav_left, col_nav_mid, col_nav_right = st.columns([2, 3, 2])

with col_nav_left:
    selected_city = st.selectbox("🎯 選擇縣市位置 (選取自動定位)", cities, index=0)

with col_nav_mid:
    st.markdown("### 🌤️ 全台天氣互動地圖 (Google Map 風格)")
    st.caption("滑鼠移至地圖縣市或地區標籤時，自動顯示當地即時氣溫與天氣！")

with col_nav_right:
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 同步CWA氣象"):
            with st.spinner("更新中..."):
                weather_service.sync_data()
                st.rerun()
    with col_btn2:
        last_updated = weather_service.get_last_updated_time()
        st.caption(f"🕒 更新時間:\n`{last_updated[:16]}`")

# --- Top Nationwide Summary Cards ---
rankings = weather_service.get_county_rankings()
cities_data = rankings.get("cities_data", [])
hottest = rankings.get("hottest")
coolest = rankings.get("coolest")
max_diff = rankings.get("max_diff")

render_summary_cards(hottest, coolest, max_diff, len(cities_data))

# --- GOOGLE MAPS STYLE FULL-SCREEN TAIWAN WEATHER MAP ---
all_stations = weather_service.get_all_map_stations()
render_taiwan_weather_map(all_stations, city_summaries=cities_data, selected_city=selected_city)

st.markdown("---")

# --- Interactive Detailed Data Sections below Fullscreen Map ---
tab1, tab2, tab3 = st.tabs([
    "📊 縣市詳細天氣預報",
    "📈 全台氣象資料分析",
    "🗄️ SQLite 資料庫歷程紀錄"
])

# --- TAB 1: City Weather & Cards ---
with tab1:
    fcst_records = weather_service.get_city_forecast(selected_city)
    obs_records = weather_service.get_city_observations(selected_city)

    render_city_cards(selected_city, fcst_records, obs_records)

    st.markdown("---")

    col_chart, col_table = st.columns([3, 2])

    with col_chart:
        render_temperature_trend_chart(fcst_records, selected_city)

    with col_table:
        st.subheader("📋 預報資料明細表")
        if fcst_records:
            df_fcst = pd.DataFrame(fcst_records)
            df_fcst["降雨等級"] = df_fcst["pop"].apply(WeatherService.classify_pop)

            show_df = df_fcst[[
                "start_time", "weather", "min_temp", "max_temp", "pop", "降雨等級", "comfort"
            ]].rename(columns={
                "start_time": "開始時間",
                "weather": "天氣現象",
                "min_temp": "最低溫(°C)",
                "max_temp": "最高溫(°C)",
                "pop": "降雨機率(%)",
                "comfort": "舒適度"
            })
            st.dataframe(show_df, use_container_width=True, height=350)
        else:
            st.info("尚無該縣市明細資料")

# --- TAB 2: Data Analytics ---
with tab2:
    st.subheader("📊 全台氣象統計與溫差分析")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        render_county_comparison_chart(cities_data)
    with col_c2:
        render_temperature_difference_chart(cities_data)

    st.markdown("---")
    st.subheader("🌧️ 各縣市降雨與極限溫度比較總表")
    if cities_data:
        df_cities = pd.DataFrame(cities_data).rename(columns={
            "city": "縣市",
            "avg_temp": "平均氣溫(°C)",
            "max_temp": "最高溫(°C)",
            "min_temp": "最低溫(°C)",
            "temp_diff": "日夜溫差(°C)",
            "station_count": "觀測站數",
            "avg_rain": "平均降雨(mm)"
        })
        st.dataframe(df_cities, use_container_width=True)

# --- TAB 3: SQLite Database Logs ---
with tab3:
    st.subheader("🗄️ SQLite 資料庫完整紀錄 (forecast_records & observation_records)")
    st.info("本系統依規將 CWA 原始 JSON 轉換並寫入 SQLite 資料庫 (database/weather.db)")

    sub_tab1, sub_tab2 = st.tabs(["預報紀錄 (forecast_records)", "觀測紀錄 (observation_records)"])
    
    with sub_tab1:
        with weather_service.db.get_connection() as conn:
            df_fcst_db = pd.read_sql_query("SELECT * FROM forecast_records ORDER BY id DESC LIMIT 100", conn)
            st.markdown(f"**展示前 100 筆 36小時預報紀錄 (共 {len(df_fcst_db)} 筆範例):**")
            st.dataframe(df_fcst_db, use_container_width=True)

    with sub_tab2:
        with weather_service.db.get_connection() as conn:
            df_obs_db = pd.read_sql_query("SELECT * FROM observation_records ORDER BY id DESC LIMIT 100", conn)
            st.markdown(f"**展示前 100 筆自動氣象站觀測紀錄 (共 {len(df_obs_db)} 筆範例):**")
            st.dataframe(df_obs_db, use_container_width=True)
