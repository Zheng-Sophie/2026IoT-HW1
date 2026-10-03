import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config import CWA_API_KEY
from services.weather_service import WeatherService
from components.weather_cards import render_city_cards
from components.charts import (
    render_temperature_trend_chart,
    render_county_comparison_chart,
    render_temperature_difference_chart
)
from components.weather_map import render_taiwan_weather_map, CITY_GOV_LOCATIONS
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

st.set_page_config(
    page_title="台灣即時天氣地圖",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Weather Service
api_sync_error = None
@st.cache_resource
def get_service():
    return WeatherService()

weather_service = get_service()

# ============================================================
# 10 分鐘自動更新
# ============================================================

if st_autorefresh is not None:
    st_autorefresh(
        interval=10 * 60 * 1000,
        limit=None,
        key="weather_auto_refresh"
    )
# ============================================================
# 初次啟動 / 每 5 分鐘同步一次 CWA
# ============================================================

if "last_sync_timestamp" not in st.session_state:
    st.session_state.last_sync_timestamp = None

should_sync = False

if st.session_state.last_sync_timestamp is None:
    should_sync = True
else:
    elapsed = (
        datetime.now() - st.session_state.last_sync_timestamp
    ).total_seconds()

    if elapsed >= 300:
        should_sync = True

if should_sync:
    try:
        with st.spinner("正在同步中央氣象署最新資料..."):
            weather_service.sync_data()

        st.session_state.last_sync_timestamp = datetime.now()

    except Exception as e:
        api_sync_error = str(e)

# --- Custom Windy / Taiwan Weather Map Dark GIS Aesthetic CSS ---
st.markdown("""
<style>
    /* Global Background & Dark Theme */
    html, body, [data-testid="stAppViewContainer"], .stApp, .stMain, .stMainBlockContainer, .block-container {
        background-color: #030712 !important;
        color: #f3f4f6 !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans TC', sans-serif;
        margin: 0 !important;
        padding: 0 !important;
        width: 100vw !important;
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }
    
    /* Remove default Streamlit header & top margins */
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    div[data-testid="stDecoration"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    
    .stAppViewContainer, .stMain, .stMainBlockContainer, .block-container {
        padding: 0rem !important;
        margin: 0rem !important;
        max-width: 100vw !important;
        width: 100% !important;
    }

    .main .block-container {
        padding: 0rem !important;
        max-width: 100vw !important;
    }

    /* Map Iframe Styling - Force Fullscreen Width and Height */
    iframe {
        width: 100vw !important;
        max-width: 100vw !important;
        height: 100vh !important;
        min-height: 840px !important;
        border: none !important;
        border-radius: 0px !important;
        display: block !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    div[data-testid="stCustomComponentV1"],
    div[data-testid="element-container"]:has(iframe) {
        width: 100vw !important;
        max-width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* --- Floating Panels General Glassmorphism --- */
    .floating-panel-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding-bottom: 8px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    }
    .floating-panel-title {
        font-size: 15px;
        font-weight: 800;
        color: #f8fafc;
        letter-spacing: -0.3px;
    }
    .floating-panel-subtitle {
        font-size: 10px;
        color: #94a3b8;
    }

    /* =========================================================================
       FLOATING PANELS (Direct Container Key Targeting)
       ========================================================================= */

    /* 1. Left-Top Map Controls Panel */
    .st-key-floating_ctrl_panel {
        position: fixed !important;
        top: 18px !important;
        left: 18px !important;
        width: 320px !important;
        max-width: calc(100vw - 36px) !important;
        max-height: calc(100vh - 120px) !important;
        overflow-y: auto !important;
        z-index: 1000 !important;
        background: rgba(15, 23, 42, 0.88) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        border-radius: 16px !important;
        padding: 14px 16px !important;
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6) !important;
        pointer-events: auto !important;
        /* 避免 fixed panel 產生不必要的高度 */
        margin: 0 !important;
    }

    /* 2. Right-Top Information Panel */
    .st-key-floating_info_panel {
        position: fixed !important;
        top: 18px !important;
        right: 18px !important;
        width: 315px !important;
        max-width: calc(100vw - 36px) !important;
        height: auto !important;
        max-height: none !important;
        overflow: hidden !important;
        z-index: 1000 !important;
        background: rgba(15, 23, 42, 0.88) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        border-radius: 16px !important;
        padding: 12px 14px !important;
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6) !important;
        pointer-events: auto !important;
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
        margin: 0 !important;
    }

    .st-key-floating_info_panel::-webkit-scrollbar {
        display: none !important;
        width: 0px !important;
        height: 0px !important;
    }

    /* 3. Left-Bottom Status Panel */
    .st-key-floating_status_panel {
        position: fixed !important;
        bottom: 18px !important;
        left: 18px !important;
        width: 320px !important;
        max-width: calc(100vw - 36px) !important;
        z-index: 1000 !important;
        background: rgba(15, 23, 42, 0.88) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        border-radius: 16px !important;
        padding: 12px 14px !important;
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6) !important;
        pointer-events: auto !important;
    }

    /* Scrollbars for Floating Control Panel */
    .st-key-floating_ctrl_panel::-webkit-scrollbar {
        width: 4px;
    }
    .st-key-floating_ctrl_panel::-webkit-scrollbar-thumb,
    .st-key-floating_info_panel::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
    }

    .mobile-expand-hint {
        display: none;
        font-size: 11px;
        font-weight: 600;
        color: #38bdf8;
        margin-left: auto;
        background: rgba(56, 189, 248, 0.12);
        padding: 2px 7px;
        border-radius: 6px;
        border: 1px solid rgba(56, 189, 248, 0.25);
    }

    /* =========================================================================
       RESPONSIVE DESIGN (RWD) BREAKPOINTS
       ========================================================================= */

    /* 1. Medium Desktop / Laptop (901px ~ 1200px) */
    @media (max-width: 1200px) and (min-width: 901px) {
        .st-key-floating_ctrl_panel {
            width: 280px !important;
            padding: 12px 14px !important;
            top: 14px !important;
            left: 14px !important;
        }
        .st-key-floating_info_panel {
            width: 290px !important;
            padding: 10px 12px !important;
            top: 14px !important;
            right: 14px !important;
            height: auto !important;
            overflow: hidden !important;
        }
        .st-key-floating_status_panel {
            width: 280px !important;
            padding: 10px 12px !important;
            bottom: 14px !important;
            left: 14px !important;
        }
        .stat-chip-val {
            font-size: 13px !important;
        }
    }

    /* 2. Tablet / Small Viewport (701px ~ 900px) */
    @media (max-width: 900px) and (min-width: 701px) {
        .st-key-floating_ctrl_panel {
            width: 250px !important;
            padding: 10px 12px !important;
            top: 12px !important;
            left: 12px !important;
        }
        .st-key-floating_info_panel {
            width: 260px !important;
            padding: 8px 10px !important;
            top: 12px !important;
            right: 12px !important;
            height: auto !important;
            overflow: hidden !important;
        }
        .st-key-floating_status_panel {
            width: 250px !important;
            padding: 9px 12px !important;
            bottom: 12px !important;
            left: 12px !important;
        }
        .floating-panel-title {
            font-size: 13px !important;
        }
        .stat-chip {
            padding: 5px 6px !important;
        }
        .stat-chip-val {
            font-size: 12px !important;
        }
    }

    /* Streamlit Selectbox & Input Clean Design */
    div[data-baseweb="select"] > div {
        background-color: rgba(30, 41, 59, 0.8) !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
        color: #f8fafc !important;
        border-radius: 10px !important;
        font-size: 13px !important;
        min-height: 38px !important;
    }

    /* Radio / Pills Pill-button Styling */
    div[data-testid="stRadio"] > div {
        gap: 5px !important;
        display: flex !important;
        flex-wrap: wrap !important;
    }
    div[data-testid="stRadio"] label {
        background: rgba(30, 41, 59, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 8px !important;
        padding: 4px 9px !important;
        font-size: 12px !important;
        color: #cbd5e1 !important;
        margin: 0 !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stRadio"] label:hover {
        background: rgba(2, 132, 199, 0.3) !important;
        border-color: #38bdf8 !important;
        color: #ffffff !important;
    }
    
    /* Streamlit Checkbox Compact */
    div[data-testid="stCheckbox"] {
        margin-bottom: -6px !important;
    }
    div[data-testid="stCheckbox"] label span {
        font-size: 12px !important;
        color: #cbd5e1 !important;
    }

    /* Streamlit Button */
    .stButton>button {
        background: linear-gradient(135deg, #0284c7, #0369a1) !important;
        color: white !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        border-radius: 8px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        padding: 6px 12px !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0369a1, #075985) !important;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.5) !important;
    }

    /* Stat Cards within Info Panel */
    .stat-chip {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 8px 10px;
        text-align: center;
    }
    .stat-chip-label {
        font-size: 10px;
        color: #94a3b8;
        margin-bottom: 2px;
    }
    .stat-chip-val {
        font-size: 14px;
        font-weight: 800;
        font-family: monospace;
    }

    /* Bottom Expander Styling */
    div[data-testid="stExpander"] {
        margin: 20px 24px !important;
        background: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 16px !important;
    }
    div[data-testid="stExpander"] summary {
        font-size: 14px !important;
        font-weight: 700 !important;
        color: #38bdf8 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Fetch Data & Compute Nationwide Analytics ---
all_stations = weather_service.get_all_map_stations()
rankings = weather_service.get_county_rankings()
cities_data = rankings.get("cities_data", [])
hottest = rankings.get("hottest")
coolest = rankings.get("coolest")
max_diff = rankings.get("max_diff")
total_cities = len(cities_data)
total_stations = len(all_stations)

# Compute Average Temperature across Taiwan
valid_temps = [s.get("temp") for s in all_stations if s.get("temp") is not None and s.get("temp") > -50]
if valid_temps:
    avg_taiwan_temp = round(sum(valid_temps) / len(valid_temps), 1)
elif cities_data:
    avg_taiwan_temp = round(sum([c["avg_temp"] for c in cities_data]) / len(cities_data), 1)
else:
    avg_taiwan_temp = 25.0

# Compute City with Max Rainfall
rain_cities = [c for c in cities_data if c.get("avg_rain", 0) > 0]
if rain_cities:
    rain_cities.sort(key=lambda x: x.get("avg_rain", 0), reverse=True)
    top_rain = rain_cities[0]
    rain_info_str = f"{top_rain['city']} ({top_rain['avg_rain']} mm)"
else:
    rain_info_str = "全台晴朗無顯著降雨"

last_updated = weather_service.get_last_updated_time()
time_str = last_updated[11:16] if len(last_updated) >= 16 else (last_updated if last_updated else "即時")

# ============================================================
# 初始化狀態
# ============================================================

if "selected_city" not in st.session_state:
    st.session_state.selected_city = "全台灣"

if "active_layer" not in st.session_state:
    st.session_state.active_layer = "temperature"

if "show_county_badges" not in st.session_state:
    st.session_state.show_county_badges = True

if "show_value_labels" not in st.session_state:
    st.session_state.show_value_labels = True

if "basemap_style" not in st.session_state:
    st.session_state.basemap_style = "街道地圖 (OSM)"

# ==============================================================================
# 1. 左上角：地圖控制浮動面板 (🗺️ 地圖控制)
# ==============================================================================
if "show_map_control" not in st.session_state:
    st.session_state.show_map_control = True

with st.container(key="floating_ctrl_panel"):

    ctrl_toggle_col, ctrl_title_col = st.columns([1, 5])

    with ctrl_toggle_col:
        if st.button(
            "◀" if st.session_state.show_map_control else "▶",
            key="toggle_map_control"
        ):
            st.session_state.show_map_control = not st.session_state.show_map_control
            st.rerun()

    with ctrl_title_col:
        st.markdown(
            """
            <div class="floating-panel-title">
                🗺️ 地圖控制
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.session_state.show_map_control:
        st.markdown("""
        <div class="floating-panel-header" tabindex="0">
            <span style="font-size: 20px;">🗺️</span>
            <div>
                <div class="floating-panel-title">地圖控制</div>
                <div class="floating-panel-subtitle">即時天氣圖層與視角切換</div>
            </div>
            <span class="mobile-expand-hint">點擊展開 ▼</span>
        </div>
        """, unsafe_allow_html=True)

        # 1. 縣市定位選擇
        city_list = ["全台灣"] + [k for k in CITY_GOV_LOCATIONS.keys() if k != "全台灣"]
        selected_city = st.selectbox("🎯 縣市選擇", city_list, index=0)

        # 2. 氣象圖層選擇 (氣溫 / 雨量 / 風速 / 濕度 / 天氣 / 測站)
        layer_options = {
            "🌡️ 氣溫": "temperature",
            "🌧️ 雨量": "rain",
            "💨 風速": "wind",
            "💧 濕度": "humidity",
            "⛅ 天氣": "weather",
            "📍 測站": "stations"
        }
        selected_layer_label = st.radio(
            "切換氣象圖層",
            options=list(layer_options.keys()),
            horizontal=True,
            index=0
        )
        active_layer = layer_options[selected_layer_label]

        # 3. 顯示開關 (顯示縣市資訊 / 顯示測站數值)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            show_county_badges = st.checkbox("🏛️ 縣市資訊", value=True)
        with col_c2:
            show_value_labels = st.checkbox("🏷️ 測站數值", value=True)

        # 4. 地圖底圖選擇
        basemap_options = [
            #"深色模式 (CartoDB)",
            "街道地圖 (OSM)",
            #"淺色模式 (CartoDB)",
            "衛星影像 (Esri)"
        ]
        basemap_style = st.selectbox("🗺️ 地圖底圖", basemap_options, index=0)

# ==============================================================================
# 2. 右上角：全台即時資訊浮動面板 (📊 全台即時資訊)
# ==============================================================================
with st.container(key="floating_info_panel"):
    hottest_city = hottest['city'] if hottest else "無"
    hottest_temp = f"{hottest['max_temp']}°C" if hottest else "--"
    coolest_city = coolest['city'] if coolest else "無"
    coolest_temp = f"{coolest['min_temp']}°C" if coolest else "--"

    st.markdown(f"""
    <div class="floating-panel-header" tabindex="0" style="padding-bottom: 6px; margin-bottom: 8px;">
        <span style="font-size: 20px;">📊</span>
        <div>
            <div class="floating-panel-title">全台即時資訊</div>
            <div class="floating-panel-subtitle">即時觀測統計摘要</div>
        </div>
        <span class="mobile-expand-hint">點擊展開 ▼</span>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 7px;">
        <div class="stat-chip">
            <div class="stat-chip-label">觀測縣市</div>
            <div class="stat-chip-val" style="color: #38bdf8;">{total_cities} 縣市</div>
        </div>
        <div class="stat-chip">
            <div class="stat-chip-label">觀測測站數</div>
            <div class="stat-chip-val" style="color: #60a5fa;">{total_stations} 站</div>
        </div>
        <div class="stat-chip">
            <div class="stat-chip-label">平均氣溫</div>
            <div class="stat-chip-val" style="color: #34d399;">{avg_taiwan_temp}°C</div>
        </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 7px;">
        <div class="stat-chip" style="border-color: rgba(248, 113, 113, 0.3); text-align: left; padding: 6px 8px;">
            <div class="stat-chip-label" style="color: #f87171;">🔥 全台最高溫縣市</div>
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 2px;">
                <span style="font-size: 13px; font-weight: 700; color: #f8fafc;">{hottest_city}</span>
                <span class="stat-chip-val" style="color: #f87171;">{hottest_temp}</span>
            </div>
        </div>
        <div class="stat-chip" style="border-color: rgba(96, 165, 250, 0.3); text-align: left; padding: 6px 8px;">
            <div class="stat-chip-label" style="color: #60a5fa;">❄️ 全台最低溫縣市</div>
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 2px;">
                <span style="font-size: 13px; font-weight: 700; color: #f8fafc;">{coolest_city}</span>
                <span class="stat-chip-val" style="color: #60a5fa;">{coolest_temp}</span>
            </div>
        </div>
    </div>

    <div class="stat-chip" style="border-color: rgba(168, 85, 247, 0.3); text-align: left; padding: 6px 8px;">
        <div class="stat-chip-label" style="color: #c084fc;">🌧️ 目前雨量較大縣市</div>
        <div style="font-size: 12px; font-weight: 700; color: #e2e8f0; margin-top: 2px;">{rain_info_str}</div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. 左下角：資料來源 / 系統狀態浮動面板 (📡 中央氣象署資料)
# ==============================================================================
with st.container(key="floating_status_panel"):
    status_badge = "🟢 連線正常" if not api_sync_error else "⚠️ 連線異常"
    status_badge_color = "#34d399" if not api_sync_error else "#fbbf24"
    
    st.markdown(f"""
    <div class="floating-panel-header" tabindex="0" style="padding-bottom: 2px; margin-bottom: 6px;">
        <span style="font-size: 16px;">📡</span>
        <div>
            <div class="floating-panel-title" style="font-size: 13px;">中央氣象署資料</div>
        </div>
        <span style="font-size: 11px; font-weight: 700; color: {status_badge_color}; background: rgba(255,255,255,0.06); padding: 2px 8px; border-radius: 9999px; margin-left: 6px;">
            {status_badge}
        </span>
        <span class="mobile-expand-hint">點擊展開 ▼</span>
    </div>
    <div style="font-size: 11px; color: #94a3b8; line-height: 1.6; margin-bottom: 8px;">
        <div>• 資料來源：CWA Open Data API (O-A0003-001)</div>
        <div>• 最後觀測時間：<b style="color: #38bdf8;">🕒 {time_str}</b></div>
    </div>
    """, unsafe_allow_html=True)

    if api_sync_error:
        st.caption(f"⚠️ 連線備註: {api_sync_error[:60]}")

    if st.button("🔄 立即同步資料", width="stretch"):
        with st.spinner("同步 CWA 資料中..."):
            weather_service.sync_data()
            st.rerun()

# ==============================================================================
# 4. 全台主體互動天氣地圖 (Folium Fullscreen Centerpiece)
# ==============================================================================
render_taiwan_weather_map(
    stations=all_stations,
    city_summaries=cities_data,
    selected_city=selected_city,
    active_layer=active_layer,
    show_county_badges=show_county_badges,
    show_value_labels=show_value_labels,
    basemap_style=basemap_style,
    height=860
)

# ==============================================================================
# 5. 底部詳細氣象分析與資料庫歷程 (可收合展開抽屜)
# ==============================================================================
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

with st.expander("📊 查看更多：36小時預報、全台氣象統計分析與 SQLite 資料庫歷程", expanded=False):
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
                st.dataframe(show_df, width="stretch", height=350)
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
            st.dataframe(df_cities, width="stretch")

    # --- TAB 3: SQLite Database Logs ---
    with tab3:
        st.markdown("### 🗄️ SQLite 氣象資料庫歷程紀錄 (database/weather.db)")
        st.caption("系統將 CWA Open Data API (O-A0003-001 & F-C0032-001) 經結構化解析後儲存於本機 SQLite 資料表")

        sub_t1, sub_t2 = st.tabs(["36小時預報紀錄 (forecast_records)", "即時觀測紀錄 (observation_records)"])
        
        with sub_t1:
            with weather_service.db.get_connection() as conn:
                df_fcst_db = pd.read_sql_query("SELECT * FROM forecast_records ORDER BY id DESC LIMIT 100", conn)
                st.markdown(f"**展示前 100 筆預報紀錄 (目前共 {len(df_fcst_db)} 筆範例):**")
                st.dataframe(df_fcst_db, width="stretch")

        with sub_t2:
            with weather_service.db.get_connection() as conn:
                df_obs_db = pd.read_sql_query("SELECT * FROM observation_records ORDER BY id DESC LIMIT 100", conn)
                st.markdown(f"**展示前 100 筆觀測紀錄 (目前共 {len(df_obs_db)} 筆範例):**")
                st.dataframe(df_obs_db, width="stretch")
