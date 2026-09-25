import streamlit as st
import pandas as pd
from datetime import datetime
from config import CWA_API_KEY
from services.weather_service import WeatherService
from components.weather_cards import render_summary_cards, render_city_cards
from components.charts import (
    render_temperature_trend_chart,
    render_county_comparison_chart,
    render_temperature_difference_chart
)
from components.weather_map import render_taiwan_weather_map, CITY_GOV_LOCATIONS

# Initialize Weather Service
@st.cache_resource
def get_service():
    service = WeatherService()
    try:
        service.sync_data()
    except Exception as e:
        st.warning(f"資料初始化同步警示: {e}")
    return service

weather_service = get_service()

st.set_page_config(layout="wide") #寬版
# --- Custom Windy / Taiwan Weather Map Dark GIS Aesthetic CSS ---
st.markdown("""
<style>
    /* Global Background & Dark Theme */
    .stApp {
        background-color: #030712 !important;
        color: #f3f4f6 !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans TC', sans-serif;
    }
    
    /* Remove default Streamlit header & top margins */
    header[data-testid="stHeader"] { 
        display: none !important; 
    }
    footer { 
        display: none !important; 
    }
    
    .main .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 100% !important;
    }
    
    /* Sleek Top Floating Control Bar */
    .windy-topbar {
        background: rgba(15, 23, 42, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 12px 20px;
        margin-bottom: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    /* Map Iframe Styling */
    iframe {
        width: 100% !important;
        height: 740px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 12px 35px rgba(0,0,0,0.6) !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94a3b8;
        padding: 8px 16px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }

    /* Streamlit Selectbox and Button Styling */
    div[data-baseweb="select"] > div {
        background-color: rgba(15, 23, 42, 0.9) !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
        color: #f8fafc !important;
        border-radius: 10px !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #0284c7, #0369a1) !important;
        color: white !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0369a1, #075985) !important;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.5) !important;
    }

    /* Metrics Styling */
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 10px 14px;
    }
</style>
""", unsafe_allow_html=True)

# --- Top Header & Floating Bar ---
top_left, top_mid, top_right = st.columns([3, 4, 3])

with top_left:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-size: 28px;">🌤️</span>
        <div>
            <div style="font-size: 20px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;">台灣即時氣象地圖</div>
            <div style="font-size: 11px; color: #38bdf8; font-weight: 500;">中央氣象署開放資料 · 類 Windy 風格視覺化</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with top_mid:
    # Layer Switcher buttons
    layer_options = {
        "🌡️ 氣溫": "temperature",
        "🌧️ 雨量": "rain",
        "💨 風速": "wind",
        "💧 濕度": "humidity",
        "⛅ 天氣": "weather",
        "📍 測站": "stations"
    }
    
    selected_layer_label = st.radio(
        "圖層切換",
        options=list(layer_options.keys()),
        horizontal=True,
        index=0,
        label_visibility="collapsed"
    )
    active_layer = layer_options[selected_layer_label]

with top_right:
    c_btn1, c_btn2, c_btn3 = st.columns([1.2, 1, 1])
    with c_btn1:
        # Location Selector
        city_list = ["全台灣"] + [k for k in CITY_GOV_LOCATIONS.keys() if k != "全台灣"]
        selected_city = st.selectbox("🎯 定位縣市", city_list, index=0, label_visibility="collapsed")
    
    with c_btn2:
        if st.button("🔄 同步資料", use_container_width=True):
            with st.spinner("同步 CWA 資料中..."):
                weather_service.sync_data()
                st.rerun()

    with c_btn3:
        last_updated = weather_service.get_last_updated_time()
        time_str = last_updated[11:16] if len(last_updated) >= 16 else "即時"
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 6px; text-align: center;">
            <div style="font-size: 9px; color: #94a3b8;">觀測時間</div>
            <div style="font-size: 12px; font-weight: bold; color: #34d399;">🕒 {time_str}</div>
        </div>
        """, unsafe_allow_html=True)

# --- Map Options & Quick Controls Bar ---
ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 1.5, 1.5, 3])

with ctrl_col1:
    basemap_choice = st.radio(
        "底圖風格",
        ["深色 (Dark Matter)", "淺色 (Positron)", "街道圖 (OSM)"],
        horizontal=True,
        index=0,
        label_visibility="collapsed"
    )
    basemap_map = {
        "深色 (Dark Matter)": "dark",
        "淺色 (Positron)": "light",
        "街道圖 (OSM)": "osm"
    }
    basemap_style = basemap_map[basemap_choice]

with ctrl_col2:
    show_county_badges = st.checkbox("🏛️ 顯示縣市總覽標籤", value=True)

with ctrl_col3:
    show_value_labels = st.checkbox("🏷️ 顯示數值膠囊標籤", value=True)

with ctrl_col4:
    st.markdown("""
    <div style="text-align: right; font-size: 12px; color: #94a3b8; padding-top: 4px;">
        💡 提示：點擊地圖任意測站或縣市標籤，可展開即時溫濕度、風速雨量與極值卡片
    </div>
    """, unsafe_allow_html=True)

# --- Top Nationwide Summary Analytics Cards ---
rankings = weather_service.get_county_rankings()
cities_data = rankings.get("cities_data", [])
hottest = rankings.get("hottest")
coolest = rankings.get("coolest")
max_diff = rankings.get("max_diff")

render_summary_cards(hottest, coolest, max_diff, len(cities_data))

# --- CENTERPIECE: FULLSCREEN WINDY-STYLE FOLIUM WEATHER MAP ---
all_stations = weather_service.get_all_map_stations()

render_taiwan_weather_map(
    stations=all_stations,
    city_summaries=cities_data,
    selected_city=selected_city,
    active_layer=active_layer,
    show_county_badges=show_county_badges,
    show_value_labels=show_value_labels,
    basemap_style=basemap_style
)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# --- Detailed Analytics & Database Inspection Sections ---
tab1, tab2, tab3 = st.tabs([
    "📊 縣市詳細天氣預報 (36小時)",
    "📈 全台氣象資料統計分析",
    "🗄️ SQLite 氣象資料庫歷程"
])

# --- TAB 1: City Detailed Forecast & Trends ---
with tab1:
    target_city = selected_city if selected_city != "全台灣" else "臺北市"
    fcst_records = weather_service.get_city_forecast(target_city)
    obs_records = weather_service.get_city_observations(target_city)

    render_city_cards(target_city, fcst_records, obs_records)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    c_chart, c_table = st.columns([3, 2])
    with c_chart:
        render_temperature_trend_chart(fcst_records, target_city)

    with c_table:
        st.markdown(f"#### 📋 {target_city} 預報資料明細")
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
            st.info("尚無該縣市預報明細資料")

# --- TAB 2: All Taiwan Analytics ---
with tab2:
    st.markdown("### 📊 全台 22 縣市溫度與日夜溫差分析")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        render_county_comparison_chart(cities_data)
    with col_c2:
        render_temperature_difference_chart(cities_data)

    st.markdown("---")
    st.markdown("#### 🌧️ 各縣市即時降雨與溫度統計表")
    if cities_data:
        df_cities = pd.DataFrame(cities_data).rename(columns={
            "city": "縣市",
            "avg_temp": "平均氣溫(°C)",
            "max_temp": "轄區最高溫(°C)",
            "min_temp": "轄區最低溫(°C)",
            "temp_diff": "日夜溫差(°C)",
            "station_count": "觀測站數",
            "avg_rain": "平均降雨(mm)"
        })
        st.dataframe(df_cities, use_container_width=True)

# --- TAB 3: SQLite Database Logs ---
with tab3:
    st.markdown("### 🗄️ SQLite 氣象資料庫歷程紀錄 (database/weather.db)")
    st.caption("系統將 CWA Open Data API (O-A0003-001 & F-C0032-001) 經結構化解析後儲存於本機 SQLite 資料表")

    sub_t1, sub_t2 = st.tabs(["36小時預報紀錄 (forecast_records)", "即時觀測紀錄 (observation_records)"])
    
    with sub_t1:
        with weather_service.db.get_connection() as conn:
            df_fcst_db = pd.read_sql_query("SELECT * FROM forecast_records ORDER BY id DESC LIMIT 100", conn)
            st.markdown(f"**展示前 100 筆預報紀錄 (目前共 {len(df_fcst_db)} 筆範例):**")
            st.dataframe(df_fcst_db, use_container_width=True)

    with sub_t2:
        with weather_service.db.get_connection() as conn:
            df_obs_db = pd.read_sql_query("SELECT * FROM observation_records ORDER BY id DESC LIMIT 100", conn)
            st.markdown(f"**展示前 100 筆觀測紀錄 (目前共 {len(df_obs_db)} 筆範例):**")
            st.dataframe(df_obs_db, use_container_width=True)
