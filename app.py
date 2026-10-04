import logging
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)
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

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_map_stations():
    return weather_service.get_all_map_stations()

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_rankings():
    return weather_service.get_county_rankings()


# ============================================================
# 5 分鐘自動更新
# ============================================================

if st_autorefresh is not None:
    st_autorefresh(
        interval=5 * 60 * 1000,
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

    /* Map Iframe: only control the actual map component.
       DO NOT use height:100vh here; it creates an extra layout area in Streamlit. */
    div[data-testid="stCustomComponentV1"],
    div[data-testid="element-container"]:has(iframe) {
        width: 100vw !important;
        max-width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
        min-height: 0 !important;
    }

    div[data-testid="element-container"]:has(iframe) iframe {
        width: 100vw !important;
        max-width: 100vw !important;
        height: 860px !important;
        min-height: 860px !important;
        border: none !important;
        border-radius: 0 !important;
        display: block !important;
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
       FLOATING PANELS
       IMPORTANT: the keyed Streamlit containers are fixed AND their nearest
       layout wrappers are collapsed to zero height. This is what prevents the
       old black block from pushing the map down.
       ========================================================================= */

    .st-key-floating_ctrl_panel,
    .st-key-floating_info_panel,
    .st-key-floating_status_panel,
    .st-key-floating_forecast_panel {
        position: fixed !important;
        z-index: 2000 !important;
        box-sizing: border-box !important;
        margin: 0 !important;
    }

    /* Collapse the Streamlit layout block that contains each fixed panel. */
    div[data-testid="stVerticalBlock"]:has(> .st-key-floating_ctrl_panel),
    div[data-testid="stVerticalBlock"]:has(> .st-key-floating_info_panel),
    div[data-testid="stVerticalBlock"]:has(> .st-key-floating_status_panel),
    div[data-testid="stVerticalBlock"]:has(> .st-key-floating_forecast_panel) {
        min-height: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: visible !important;
    }

    /* Also collapse one additional Streamlit element wrapper when present. */
    div[data-testid="element-container"]:has(.st-key-floating_ctrl_panel),
    div[data-testid="element-container"]:has(.st-key-floating_info_panel),
    div[data-testid="element-container"]:has(.st-key-floating_status_panel),
    div[data-testid="element-container"]:has(.st-key-floating_forecast_panel) {
        min-height: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: visible !important;
    }

    /* Left panel */
    .st-key-floating_ctrl_panel {
        top: 18px !important;
        left: 18px !important;
        width: 320px !important;
        max-width: calc(100vw - 36px) !important;
        max-height: calc(100vh - 120px) !important;
        overflow-y: auto !important;
        background: rgba(15, 23, 42, 0.90) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        border-radius: 16px !important;
        padding: 10px 12px !important;
        box-shadow: 0 16px 36px rgba(0,0,0,0.60) !important;
    }

    /* Right panel */
    .st-key-floating_info_panel {
        top: 18px !important;
        right: 18px !important;
        width: 315px !important;
        max-width: calc(100vw - 36px) !important;
        max-height: calc(100vh - 120px) !important;
        overflow-y: auto !important;
        background: rgba(15, 23, 42, 0.90) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        border-radius: 16px !important;
        padding: 10px 12px !important;
        box-shadow: 0 16px 36px rgba(0,0,0,0.60) !important;
    }

    /* Bottom-left status */
    .st-key-floating_status_panel {
        bottom: 18px !important;
        left: 18px !important;
        width: 320px !important;
        max-width: calc(100vw - 36px) !important;
        background: rgba(15, 23, 42, 0.90) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        border-radius: 16px !important;
        padding: 10px 12px !important;
        box-shadow: 0 16px 36px rgba(0,0,0,0.60) !important;
    }

    /* Bottom-right forecast drawer */
    .st-key-floating_forecast_panel {
        right: 18px !important;
        bottom: 18px !important;
        width: min(620px, calc(100vw - 36px)) !important;
        max-height: min(650px, calc(100vh - 36px)) !important;
        overflow-y: auto !important;
        background: rgba(15, 23, 42, 0.96) !important;
        backdrop-filter: blur(18px) !important;
        -webkit-backdrop-filter: blur(18px) !important;
        border: 1px solid rgba(255,255,255,0.16) !important;
        border-radius: 16px !important;
        padding: 12px 14px !important;
        box-shadow: 0 18px 45px rgba(0,0,0,0.68) !important;
    }

    .floating-panel-toggle-row {
        display: flex;
        align-items: center;
        gap: 8px;
        min-height: 30px;
        margin-bottom: 4px;
    }

    .floating-panel-toggle-label {
        font-size: 14px;
        font-weight: 800;
        color: #f8fafc;
    }
    .panel-title-small {
        font-size: 20px !important;
        font-weight: 700 !important;
        line-height: 1.4 !important;
        color: #f8fafc !important;
        margin: 2px 0 6px 0 !important;
        white-space: nowrap !important;
    }

    .st-key-floating_ctrl_panel .stButton>button,
    .st-key-floating_info_panel .stButton>button,
    .st-key-floating_status_panel .stButton>button,
    .st-key-floating_forecast_panel .stButton>button {
        min-height: 30px !important;
        padding: 4px 8px !important;
    }

    @media (max-width: 900px) {
        .st-key-floating_ctrl_panel {
            width: 270px !important;
            left: 10px !important;
            top: 10px !important;
        }

        .st-key-floating_info_panel {
            width: 270px !important;
            right: 10px !important;
            top: 10px !important;
        }

        .st-key-floating_status_panel {
            width: 270px !important;
            left: 10px !important;
            bottom: 10px !important;
        }

        .st-key-floating_forecast_panel {
            right: 10px !important;
            bottom: 10px !important;
            width: calc(100vw - 20px) !important;
            max-height: calc(100vh - 20px) !important;
        }
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
        transition: none !important;
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
        transition: none !important;
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
all_stations = get_cached_map_stations()
rankings = get_cached_rankings()
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
if last_updated:
    try:
        dt = datetime.fromisoformat(last_updated)

        # 如果資料沒有時區資訊，視為台灣時間
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("Asia/Taipei"))

        # 統一轉成台灣時間
        dt = dt.astimezone(ZoneInfo("Asia/Taipei"))

        time_str = dt.strftime("%H:%M")

    except (ValueError, TypeError):
        time_str = last_updated[:16]
else:
    time_str = "即時"

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
    st.session_state.show_value_labels = False

if "basemap_style" not in st.session_state:
    st.session_state.basemap_style = "街道地圖 (OSM)"

# ==============================================================================
# 1. 初始化地圖控制狀態
# ==============================================================================

if "show_map_control" not in st.session_state:
    st.session_state.show_map_control = True

if "show_info_panel" not in st.session_state:
    st.session_state.show_info_panel = True

if "show_status_panel" not in st.session_state:
    st.session_state.show_status_panel = True

if "forecast_panel_open" not in st.session_state:
    st.session_state.forecast_panel_open = False

if "handled_canvas_click" not in st.session_state:
    st.session_state.handled_canvas_click = None

if "handled_object_click_count" not in st.session_state:
    st.session_state.handled_object_click_count = 0

city_list = ["全台灣"] + [
    k for k in CITY_GOV_LOCATIONS.keys()
    if k != "全台灣"
]

layer_options = {
    "🌡️ 氣溫": "temperature",
    "🌧️ 雨量": "rain",
    "💨 風速": "wind",
    "💧 濕度": "humidity",
    "⛅ 天氣": "weather",
    "📍 測站": "stations"
}

basemap_options = [
    "街道地圖 (OSM)",
    "衛星影像 (Esri)"
]

# ==============================================================================
# 2. 主體地圖：先 render 地圖，再建立 floating panels
#    這是避免原本「上方黑色大區塊」的關鍵。
# ==============================================================================

selected_city = st.session_state.selected_city
active_layer = st.session_state.active_layer
show_county_badges = st.session_state.show_county_badges
show_value_labels = st.session_state.show_value_labels
basemap_style = st.session_state.basemap_style

map_result = render_taiwan_weather_map(
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
# 3. 地圖點擊 → 自動辨識最近縣市
# ==============================================================================

def _nearest_city_from_click(click_data):
    if not click_data:
        return None

    point = click_data.get("lat") if isinstance(click_data, dict) else None
    lon = click_data.get("lng") if isinstance(click_data, dict) else None

    if point is None or lon is None:
        return None

    best_city = None
    best_distance = float("inf")

    for city_name, info in CITY_GOV_LOCATIONS.items():
        if city_name == "全台灣":
            continue

        city_lat, city_lon = info["coords"]
        distance = (float(point) - city_lat) ** 2 + (float(lon) - city_lon) ** 2

        if distance < best_distance:
            best_distance = distance
            best_city = city_name

    # Only accept clicks reasonably close to a county/city center.
    # This prevents a click far offshore from unexpectedly opening a county.
    return best_city if best_distance <= 1.5 ** 2 else None

newly_clicked_city = None

if isinstance(map_result, dict):
    # 1. 處理點擊地圖上的物件（縣市標籤 country_badge 或測站標記）
    object_click = map_result.get("last_object_clicked")
    object_click_count = map_result.get("last_object_clicked_count")
    object_tooltip = map_result.get("last_object_clicked_tooltip")

    last_handled_count = st.session_state.get("handled_object_click_count", 0)

    if object_click and object_click_count is not None and object_click_count > last_handled_count:
        st.session_state.handled_object_click_count = object_click_count

        # 從 Tooltip 或經緯度辨識縣市
        target = None
        if object_tooltip and isinstance(object_tooltip, str):
            for c_name in CITY_GOV_LOCATIONS:
                if c_name != "全台灣" and c_name in object_tooltip:
                    target = c_name
                    break

        if not target:
            target = _nearest_city_from_click(object_click)

        if target:
            newly_clicked_city = target

    # 2. 處理點擊地圖背景畫布（Canvas Click）
    if not newly_clicked_city:
        last_clicked = map_result.get("last_clicked")
        if last_clicked and isinstance(last_clicked, dict):
            click_lat = last_clicked.get("lat")
            click_lng = last_clicked.get("lng")

            if click_lat is not None and click_lng is not None:
                current_click = (
                    round(float(click_lat), 5),
                    round(float(click_lng), 5)
                )
                previous_click = st.session_state.get("handled_canvas_click")

                if current_click != previous_click:
                    st.session_state.handled_canvas_click = current_click
                    canvas_city = _nearest_city_from_click(last_clicked)
                    if canvas_city:
                        newly_clicked_city = canvas_city

# 若有新點擊的縣市，更新選取縣市並打開預報抽屜
if newly_clicked_city:
    st.session_state.selected_city = newly_clicked_city
    st.session_state.forecast_panel_open = True
    if "city_selector" in st.session_state:
        st.session_state["city_selector"] = newly_clicked_city

# 本次執行真正要顯示的縣市
display_city = st.session_state.selected_city
# ==============================================================================
# 4. 左上角：地圖控制
# ==============================================================================

def _render_map_control_panel():
    with st.container(key="floating_ctrl_panel"):
        ctrl_toggle_col, ctrl_title_col = st.columns([1, 6])
        with ctrl_toggle_col:
            if st.button("◀" if st.session_state.show_map_control else "▶", key="toggle_map_control"):
                st.session_state.show_map_control = not st.session_state.show_map_control
                if hasattr(st, "fragment"):
                    st.rerun(scope="fragment")
                else:
                    st.rerun()
        with ctrl_title_col:
            st.markdown(
                '<div class="panel-title-small">🗺️ 地圖控制</div>',
                unsafe_allow_html=True
            )

        if not st.session_state.show_map_control:
            return

        if "city_selector" in st.session_state and st.session_state.city_selector != st.session_state.selected_city:
            st.session_state.city_selector = st.session_state.selected_city

        city_index = city_list.index(st.session_state.selected_city) if st.session_state.selected_city in city_list else 0
        selected_city_ui = st.selectbox("🎯 縣市選擇", city_list, index=city_index, key="city_selector")
        if selected_city_ui != st.session_state.selected_city:
            st.session_state.selected_city = selected_city_ui
            st.session_state.forecast_panel_open = (selected_city_ui != "全台灣")
            st.rerun()

        current_layer_index = list(layer_options.values()).index(st.session_state.active_layer) if st.session_state.active_layer in layer_options.values() else 0
        selected_layer_label = st.radio("切換氣象圖層", list(layer_options.keys()), index=current_layer_index, horizontal=True, key="weather_layer_selector")
        new_active_layer = layer_options[selected_layer_label]
        if new_active_layer != st.session_state.active_layer:
            st.session_state.active_layer = new_active_layer
            st.rerun()

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            new_badges = st.checkbox("🏛️ 縣市資訊", value=st.session_state.show_county_badges, key="county_badges_checkbox")
        with col_c2:
            new_labels = st.checkbox("🏷️ 測站數值", value=st.session_state.show_value_labels, key="value_labels_checkbox")
        if new_badges != st.session_state.show_county_badges or new_labels != st.session_state.show_value_labels:
            st.session_state.show_county_badges = new_badges
            st.session_state.show_value_labels = new_labels
            st.rerun()
        st.session_state.show_county_badges = new_badges
        st.session_state.show_value_labels = new_labels

        base_index = basemap_options.index(st.session_state.basemap_style) if st.session_state.basemap_style in basemap_options else 0
        new_basemap = st.selectbox("🗺️ 地圖底圖", basemap_options, index=base_index, key="basemap_selector")
        if new_basemap != st.session_state.basemap_style:
            st.session_state.basemap_style = new_basemap
            st.rerun()

if hasattr(st, "fragment"):
    _render_map_control_panel = st.fragment(_render_map_control_panel)
_render_map_control_panel()

# ==============================================================================
# 5. 右上角：全台即時資訊
# ==============================================================================

def _render_info_panel():
    with st.container(key="floating_info_panel"):
        info_toggle_col, info_title_col = st.columns([1, 6])
        with info_toggle_col:
            if st.button("▶" if not st.session_state.show_info_panel else "◀", key="toggle_info_panel"):
                st.session_state.show_info_panel = not st.session_state.show_info_panel
                if hasattr(st, "fragment"):
                    st.rerun(scope="fragment")
                else:
                    st.rerun()
        with info_title_col:
            st.markdown(
                '<div class="panel-title-small">📊 全台即時資訊</div>',
                unsafe_allow_html=True
            )

        if not st.session_state.show_info_panel:
            return

        hottest_city = hottest["city"] if hottest else "無"
        hottest_temp = f"{hottest['max_temp']}°C" if hottest else "--"
        coolest_city = coolest["city"] if coolest else "無"
        coolest_temp = f"{coolest['min_temp']}°C" if coolest else "--"

        #c1, c2 = st.columns(2)
        #c1.metric("觀測縣市", f"{total_cities} 縣市")
        #c2.metric("觀測站台數", f"{total_stations} 站")
        c1, c2 = st.columns(2)
        c1.metric("全台最高溫縣市", hottest_city, hottest_temp)
        c2.metric("全台最低溫縣市", coolest_city, coolest_temp)
        st.caption(f"平均氣溫：{avg_taiwan_temp}°C")
        st.caption(f"目前雨量較大縣市：{rain_info_str}")

if hasattr(st, "fragment"):
    _render_info_panel = st.fragment(_render_info_panel)
_render_info_panel()

# ==============================================================================
# 6. 左下角：資料來源 / 系統狀態
# ==============================================================================

with st.container(key="floating_status_panel"):
    status_badge = "🟢 連線正常" if not api_sync_error else "⚠️ 連線異常"
    st.markdown(
        '<div class="panel-title-small">📡 中央氣象署資料</div>',
        unsafe_allow_html=True
    )
    st.caption(f"{status_badge}　｜　最後同步時間：{time_str}")
    if api_sync_error:
        st.warning(f"連線備註：{api_sync_error[:60]}")
    if st.button("🔄 立即同步資料", width="stretch", key="manual_sync"):
        with st.spinner("同步 CWA 資料中..."):
            weather_service.sync_data()
            st.session_state.last_sync_timestamp = datetime.now()
            get_cached_map_stations.clear()
            get_cached_rankings.clear()
            st.rerun()

# ==============================================================================
# 7. 右下角：縣市詳細天氣預報
# ==============================================================================

if st.session_state.forecast_panel_open:

    target_city = display_city

    if target_city == "全台灣":
        target_city = "臺北市"

    fcst_records = weather_service.get_city_forecast(target_city)
    obs_records = weather_service.get_city_observations(target_city)

    with st.container(key="floating_forecast_panel"):

        forecast_toggle_col, forecast_title_col = st.columns([1, 8])

        with forecast_toggle_col:
            if st.button("✕", key="close_forecast_panel"):
                st.session_state.forecast_panel_open = False
                st.rerun()

        with forecast_title_col:
            st.markdown(
                f"""
                <div class="floating-panel-title">
                    📍 {target_city} 詳細天氣預報
                </div>
                <div class="floating-panel-subtitle">
                    今明36小時天氣預報
                </div>
                """,
                unsafe_allow_html=True
            )

        # 頂部 36 小時卡片
        render_city_cards(target_city, fcst_records, obs_records)

        # 底部兩個分頁：一週趨勢 + 一週表格
        week_tab_chart, week_tab_table = st.tabs([
            "📈 一週溫度趨勢",
            "📋 一週溫度表"
        ])

        # ------------------------------------------------------------------
        # 一週資料：優先使用 weekly_forecast_records。
        # 若資料表尚未建立，會顯示提示，不把 36 小時資料冒充一週資料。
        # ------------------------------------------------------------------
        def load_weekly_forecast(city_name):
            try:
                records = weather_service.get_city_weekly_forecast(city_name)
                return pd.DataFrame(records) if records else pd.DataFrame(
                    columns=["forecast_date", "max_temp", "min_temp"]
                )
            except Exception as e:
                logger.exception(
                    f"Error loading weekly forecast for {city_name}: {e}"
                )
                return pd.DataFrame(
                    columns=["forecast_date", "max_temp", "min_temp"]
                )

        weekly_df = load_weekly_forecast(target_city)
        with week_tab_chart:
            st.markdown("#### 📈 未來一週最高 / 最低溫")

            if not weekly_df.empty:
                chart_df = weekly_df.copy()
                chart_df["日期"] = pd.to_datetime(
                    chart_df["forecast_date"]
                ).dt.strftime("%m/%d")

                chart_df = chart_df.set_index("日期")[
                    ["max_temp", "min_temp"]
                ].rename(
                    columns={
                        "max_temp": "最高溫",
                        "min_temp": "最低溫"
                    }
                )

                st.line_chart(chart_df, height=280, color=["red", "blue"])
            else:
                st.info(
                    "目前 weekly_forecast_records 尚無一週資料。"
                    "請先加入一週預報 API 同步流程。"
                )

        with week_tab_table:
            st.markdown("#### 📋 未來一週溫度資料")

            if not weekly_df.empty:
                show_week = weekly_df.rename(
                    columns={
                        "forecast_date": "日期",
                        "max_temp": "最高溫(°C)",
                        "min_temp": "最低溫(°C)"
                    }
                )

                st.dataframe(
                    show_week,
                    width="stretch",
                    hide_index=True
                )
            else:
                st.info("尚無一週溫度資料。")