import folium
from streamlit_folium import st_folium
import streamlit as st
from typing import List, Dict, Any, Tuple
from components.weather_cards import get_weather_emoji

# Coordinates for Taiwan 22 County/City Centers
CITY_GOV_LOCATIONS = {
    "全台灣": {"name": "全台灣", "coords": [23.75, 120.95], "zoom": 8},
    "臺北市": {"name": "臺北市", "coords": [25.0375, 121.5637], "zoom": 12},
    "新北市": {"name": "新北市", "coords": [24.9901, 121.4628], "zoom": 11},
    "基隆市": {"name": "基隆市", "coords": [25.1315, 121.7402], "zoom": 13},
    "桃園市": {"name": "桃園市", "coords": [24.9936, 121.3010], "zoom": 11},
    "新竹市": {"name": "新竹市", "coords": [24.8066, 120.9686], "zoom": 13},
    "新竹縣": {"name": "新竹縣", "coords": [24.8383, 121.0093], "zoom": 11},
    "苗栗縣": {"name": "苗栗縣", "coords": [24.5649, 120.8190], "zoom": 11},
    "臺中市": {"name": "臺中市", "coords": [24.1631, 120.6478], "zoom": 11},
    "彰化縣": {"name": "彰化縣", "coords": [24.0754, 120.5447], "zoom": 11},
    "南投縣": {"name": "南投縣", "coords": [23.9027, 120.6904], "zoom": 10},
    "雲林縣": {"name": "雲林縣", "coords": [23.7092, 120.4313], "zoom": 11},
    "嘉義市": {"name": "嘉義市", "coords": [23.4800, 120.4491], "zoom": 13},
    "嘉義縣": {"name": "嘉義縣", "coords": [23.4588, 120.5740], "zoom": 11},
    "臺南市": {"name": "臺南市", "coords": [22.9922, 120.1851], "zoom": 11},
    "高雄市": {"name": "高雄市", "coords": [22.6234, 120.3123], "zoom": 11},
    "屏東縣": {"name": "屏東縣", "coords": [22.6828, 120.4879], "zoom": 11},
    "宜蘭縣": {"name": "宜蘭縣", "coords": [24.7308, 121.7631], "zoom": 11},
    "花蓮縣": {"name": "花蓮縣", "coords": [23.9922, 121.6186], "zoom": 10},
    "臺東縣": {"name": "臺東縣", "coords": [22.7583, 121.1444], "zoom": 10},
    "澎湖縣": {"name": "澎湖縣", "coords": [23.5711, 119.5793], "zoom": 11},
    "金門縣": {"name": "金門縣", "coords": [24.4357, 118.3186], "zoom": 12},
    "連江縣": {"name": "連江縣", "coords": [26.1575, 119.9519], "zoom": 12}
}

# --- Windy Color Ramp Helpers ---
def get_temperature_color(temp: float) -> str:
    """Return Windy-style color based on temperature value (°C)."""
    if temp is None or temp <= -50:
        return "#64748b"
    if temp < 10:
        return "#2c7bb6"
    elif temp < 15:
        return "#5aa2cf"
    elif temp < 19:
        return "#7fcdbb"
    elif temp < 23:
        return "#d9ef8b"
    elif temp < 26:
        return "#fee08b"
    elif temp < 29:
        return "#fdae61"
    elif temp < 32:
        return "#f46d43"
    else:
        return "#d73027"

def get_rain_color(rain: float) -> str:
    """Return color based on rainfall (mm)."""
    if rain is None or rain <= 0:
        return "#475569"
    elif rain < 2:
        return "#38bdf8"
    elif rain < 10:
        return "#0284c7"
    elif rain < 25:
        return "#2563eb"
    elif rain < 50:
        return "#7c3aed"
    else:
        return "#db2777"

def get_wind_color(speed: float) -> str:
    """Return color based on wind speed (m/s)."""
    if speed is None or speed < 0:
        return "#64748b"
    elif speed < 2:
        return "#10b981"
    elif speed < 4:
        return "#06b6d4"
    elif speed < 7:
        return "#3b82f6"
    elif speed < 11:
        return "#f59e0b"
    elif speed < 15:
        return "#f97316"
    else:
        return "#ef4444"

def get_humidity_color(hum: float) -> str:
    """Return color based on relative humidity (%)."""
    if hum is None or hum <= 0:
        return "#64748b"
    elif hum < 50:
        return "#f59e0b"
    elif hum < 70:
        return "#10b981"
    elif hum < 80:
        return "#06b6d4"
    elif hum < 90:
        return "#3b82f6"
    else:
        return "#6366f1"

def build_legend_html(layer: str) -> str:
    """Generate floating bottom-right gradient scale bar matching taiwan-weather-map.vercel.app."""
    if layer == "temperature":
        unit = "°C"
        gradient = "linear-gradient(to right, #2c7bb6, #5aa2cf, #abd9e9, #7fcdbb, #d9ef8b, #fee08b, #fdae61, #f46d43, #d73027)"
        labels = ["5", "10", "15", "20", "24", "28", "32", "36+"]
    elif layer == "rain":
        unit = "mm"
        gradient = "linear-gradient(to right, #475569, #38bdf8, #0284c7, #2563eb, #7c3aed, #db2777)"
        labels = ["0", "2", "10", "25", "50", "80+"]
    elif layer == "wind":
        unit = "m/s"
        gradient = "linear-gradient(to right, #10b981, #06b6d4, #3b82f6, #f59e0b, #f97316, #ef4444)"
        labels = ["0", "2", "4", "7", "11", "15+"]
    elif layer == "humidity":
        unit = "%"
        gradient = "linear-gradient(to right, #f59e0b, #10b981, #06b6d4, #3b82f6, #6366f1)"
        labels = ["30", "50", "70", "80", "90", "100"]
    else:
        # Default / weather / stations
        unit = "🌤️"
        gradient = "linear-gradient(to right, #38bdf8, #34d399, #facc15, #f97316, #ef4444)"
        labels = ["晴", "多雲", "陰", "陣雨", "雷雨"]

    ticks_html = "".join([f"<span>{lbl}</span>" for lbl in labels])

    return f"""
    <div style="
        position: fixed;
        bottom: 22px;
        right: 22px;
        z-index: 999;
        background: rgba(15, 23, 42, 0.92);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 8px 14px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        width: 250px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        pointer-events: auto;
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 12px; font-weight: 800; color: #f8fafc; min-width: 24px;">{unit}</span>
            <div style="flex: 1;">
                <div style="height: 9px; width: 100%; border-radius: 9999px; background: {gradient};"></div>
                <div style="margin-top: 4px; display: flex; justify-content: space-between; font-size: 9px; font-weight: 600; color: #94a3b8; font-family: monospace;">
                    {ticks_html}
                </div>
            </div>
        </div>
    </div>
    """

def render_taiwan_weather_map(
    stations: List[Dict[str, Any]],
    city_summaries: List[Dict[str, Any]] = None,
    selected_city: str = "全台灣",
    active_layer: str = "temperature",
    show_county_badges: bool = True,
    show_value_labels: bool = True,
    basemap_style: str = "dark",
    **kwargs
):
    """
    Render Taiwan Real-time Weather Map (Windy style).
    - Basemap: CartoDB Dark Matter / Positron / OSM.
    - Layers: 氣溫, 雨量, 風速, 濕度, 天氣, 測站.
    - Visuals: Glassmorphism badges, dynamic color scaling, floating bottom-right legend.
    """
    if not stations and not city_summaries:
        st.info("尚無氣象測站資料")
        return

    # Determine center and zoom level based on selected city
    center = [23.75, 120.95]
    zoom = 8
    if selected_city and selected_city in CITY_GOV_LOCATIONS:
        center = CITY_GOV_LOCATIONS[selected_city]["coords"]
        zoom = CITY_GOV_LOCATIONS[selected_city]["zoom"]

    # Initialize Folium Map
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=None,
        control_scale=True,
        prefer_canvas=True
    )

    # Base Tile Layers
    if basemap_style == "dark":
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            attr='&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            name="深色地圖 (Dark Matter)",
            control=False
        ).add_to(m)
    elif basemap_style == "light":
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            attr='&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            name="淺色地圖 (Positron)",
            control=False
        ).add_to(m)
    else:
        folium.TileLayer(
            tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            name="街道地圖 (OpenStreetMap)",
            control=False
        ).add_to(m)

    # 1. County Summary Overview Badges (Zoom-out county overview)
    if show_county_badges and city_summaries:
        county_group = folium.FeatureGroup(name="🏛️ 縣市氣候概況", show=True).add_to(m)
        summary_dict = {s.get("city"): s for s in city_summaries}

        for city_name, gov_info in CITY_GOV_LOCATIONS.items():
            if city_name == "全台灣":
                continue
            coords = gov_info["coords"]
            c_summary = summary_dict.get(city_name, {})
            avg_temp = c_summary.get("avg_temp")
            max_temp = c_summary.get("max_temp")
            min_temp = c_summary.get("min_temp")
            avg_rain = c_summary.get("avg_rain", 0)
            st_count = c_summary.get("station_count", 0)

            city_stations = [st_item for st_item in stations if st_item.get("city") == city_name]
            rep_weather = city_stations[0].get("weather", "多雲") if city_stations else "多雲"
            emoji = get_weather_emoji(rep_weather)
            color = get_temperature_color(avg_temp) if avg_temp else "#0284c7"

            temp_display = f"{avg_temp}°" if avg_temp is not None else "--"
            max_display = f"{max_temp}°" if max_temp is not None else "--"
            min_display = f"{min_temp}°" if min_temp is not None else "--"

            county_badge_html = f"""
            <div style="
                display: inline-flex;
                align-items: center;
                gap: 5px;
                background: rgba(15, 23, 42, 0.9);
                border: 2px solid {color};
                color: #ffffff;
                padding: 4px 10px;
                border-radius: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 12px;
                font-weight: 700;
                white-space: nowrap;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5), 0 0 10px {color}66;
                cursor: pointer;
            ">
                <span>{city_name}</span>
                <span style="color: {color}; font-weight: 800;">{temp_display}</span>
                <span>{emoji}</span>
            </div>
            """

            county_popup_html = f"""
            <div style="
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0f172a;
                color: #f8fafc;
                padding: 12px 14px;
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.15);
                min-width: 200px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.6);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.15); padding-bottom: 6px;">
                    <span style="font-size: 15px; font-weight: bold; color: #38bdf8;">🏛️ {city_name}</span>
                    <span style="font-size: 13px;">{emoji} {rep_weather}</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; font-size: 12px;">
                    <div style="background: rgba(255,255,255,0.06); padding: 6px 8px; border-radius: 8px;">
                        <div style="color: #94a3b8; font-size: 10px;">平均氣溫</div>
                        <div style="font-size: 15px; font-weight: bold; color: {color};">{temp_display}C</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.06); padding: 6px 8px; border-radius: 8px;">
                        <div style="color: #94a3b8; font-size: 10px;">平均雨量</div>
                        <div style="font-size: 15px; font-weight: bold; color: #38bdf8;">{avg_rain} mm</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.06); padding: 6px 8px; border-radius: 8px;">
                        <div style="color: #94a3b8; font-size: 10px;">轄區最高溫</div>
                        <div style="font-size: 13px; font-weight: bold; color: #f87171;">{max_display}C</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.06); padding: 6px 8px; border-radius: 8px;">
                        <div style="color: #94a3b8; font-size: 10px;">轄區最低溫</div>
                        <div style="font-size: 13px; font-weight: bold; color: #60a5fa;">{min_display}C</div>
                    </div>
                </div>
                <div style="margin-top: 8px; text-align: right; font-size: 10px; color: #64748b;">
                    共監測 {st_count} 個中央氣象署觀測站
                </div>
            </div>
            """

            folium.Marker(
                location=coords,
                icon=folium.DivIcon(
                    html=county_badge_html,
                    icon_size=(100, 30),
                    icon_anchor=(50, 15)
                ),
                popup=folium.Popup(county_popup_html, max_width=260),
                tooltip=folium.Tooltip(f"{city_name} {temp_display} {emoji}", sticky=True)
            ).add_to(county_group)

    # 2. Local Stations Layer (Windy-style Pill Markers)
    stations_group = folium.FeatureGroup(name="📡 即時氣象站點", show=True).add_to(m)

    for st_info in stations:
        lat = st_info.get("lat")
        lon = st_info.get("lon")

        # Skip invalid or default center placeholders
        if not lat or not lon or (lat == 23.7 and lon == 121.0):
            continue

        st_name = st_info.get("station_name", "測站")
        city = st_info.get("city", "")
        town = st_info.get("town", "")
        temp = st_info.get("temp")
        max_t = st_info.get("max_temp")
        min_t = st_info.get("min_temp")
        weather = st_info.get("weather", "多雲")
        rain = st_info.get("rain", 0)
        hum = st_info.get("humidity")
        pressure = st_info.get("pressure")
        wind = st_info.get("wind_speed")
        obs_time = st_info.get("obs_time", "")

        emoji = get_weather_emoji(weather)

        # Determine Badge Content & Color based on active layer
        if active_layer == "temperature":
            badge_color = get_temperature_color(temp)
            val_text = f"{temp:.1f}°" if temp is not None else "--"
            icon_sym = emoji
        elif active_layer == "rain":
            badge_color = get_rain_color(rain)
            val_text = f"{rain:.1f}mm" if rain is not None else "0mm"
            icon_sym = "🌧️" if rain and rain > 0 else "💧"
        elif active_layer == "wind":
            badge_color = get_wind_color(wind)
            val_text = f"{wind:.1f}m/s" if wind is not None else "--"
            icon_sym = "💨"
        elif active_layer == "humidity":
            badge_color = get_humidity_color(hum)
            val_text = f"{int(hum)}%" if hum is not None else "--"
            icon_sym = "💧"
        elif active_layer == "weather":
            badge_color = get_temperature_color(temp)
            val_text = weather[:4]
            icon_sym = emoji
        else:  # stations
            badge_color = "#38bdf8"
            val_text = town or st_name[:3]
            icon_sym = "📍"

        # Rich Windy-style Station Card Popup
        st_popup_html = f"""
        <div style="
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0b0f19;
            color: #f8fafc;
            padding: 14px 16px;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.18);
            min-width: 230px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.7);
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid rgba(255,255,255,0.12); padding-bottom: 8px;">
                <div>
                    <div style="font-size: 15px; font-weight: 800; color: #38bdf8;">📍 {town} · {st_name}</div>
                    <div style="font-size: 11px; color: #94a3b8; margin-top: 1px;">{city} ({st_info.get('station_id', '')})</div>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 20px;">{emoji}</span>
                    <div style="font-size: 11px; color: #cbd5e1; font-weight: 600;">{weather}</div>
                </div>
            </div>

            <!-- Main Temperature Display -->
            <div style="display: flex; align-items: baseline; gap: 8px; margin: 10px 0;">
                <span style="font-size: 28px; font-weight: 900; color: {badge_color};">
                    {temp if temp is not None else '--'}°C
                </span>
                <span style="font-size: 11px; color: #94a3b8;">
                    本日極值: <b style="color: #f87171;">{max_t}°</b> / <b style="color: #60a5fa;">{min_t}°</b>
                </span>
            </div>

            <!-- Detailed Grid Chips -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 11px;">
                <div style="background: rgba(255,255,255,0.06); padding: 6px 8px; border-radius: 8px;">
                    <span style="color: #94a3b8;">🌧️ 雨量:</span>
                    <b style="color: #38bdf8; margin-left: 4px;">{rain if rain is not None else 0} mm</b>
                </div>
                <div style="background: rgba(255,255,255,0.06); padding: 6px 8px; border-radius: 8px;">
                    <span style="color: #94a3b8;">💧 濕度:</span>
                    <b style="color: #34d399; margin-left: 4px;">{hum if hum is not None else '--'} %</b>
                </div>
                <div style="background: rgba(255,255,255,0.06); padding: 6px 8px; border-radius: 8px;">
                    <span style="color: #94a3b8;">💨 風速:</span>
                    <b style="color: #fbbf24; margin-left: 4px;">{wind if wind is not None else '--'} m/s</b>
                </div>
                <div style="background: rgba(255,255,255,0.06); padding: 6px 8px; border-radius: 8px;">
                    <span style="color: #94a3b8;">📊 氣壓:</span>
                    <b style="color: #cbd5e1; margin-left: 4px;">{pressure if pressure is not None else '--'} hPa</b>
                </div>
            </div>

            <div style="margin-top: 8px; padding-top: 6px; border-top: 1px dashed rgba(255,255,255,0.1); font-size: 9px; color: #64748b; display: flex; justify-content: space-between;">
                <span>觀測時間:</span>
                <span>{obs_time}</span>
            </div>
        </div>
        """

        if show_value_labels:
            # Windy-style Pill Badge Marker
            pill_html = f"""
            <div style="
                display: inline-flex;
                align-items: center;
                gap: 3px;
                background: rgba(11, 15, 25, 0.88);
                border: 1.5px solid {badge_color};
                color: #f8fafc;
                padding: 2px 6px;
                border-radius: 9999px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 11px;
                font-weight: 700;
                white-space: nowrap;
                box-shadow: 0 4px 10px rgba(0,0,0,0.5), 0 0 6px {badge_color}44;
                backdrop-filter: blur(4px);
                cursor: pointer;
            ">
                <span style="font-size: 10px;">{icon_sym}</span>
                <span>{val_text}</span>
            </div>
            """
            marker_icon = folium.DivIcon(
                html=pill_html,
                icon_size=(70, 24),
                icon_anchor=(35, 12)
            )
            folium.Marker(
                location=[lat, lon],
                icon=marker_icon,
                popup=folium.Popup(st_popup_html, max_width=280),
                tooltip=folium.Tooltip(f"{town} {st_name}: {val_text} ({weather})", sticky=True)
            ).add_to(stations_group)
        else:
            # Compact circle dot marker
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                color=badge_color,
                fill=True,
                fill_color=badge_color,
                fill_opacity=0.85,
                weight=2,
                popup=folium.Popup(st_popup_html, max_width=280),
                tooltip=folium.Tooltip(f"{town} {st_name}: {val_text}", sticky=True)
            ).add_to(stations_group)

    # 3. Add Floating Bottom-Right Scale Bar
    legend_html = build_legend_html(active_layer)
    m.get_root().html.add_child(folium.Element(legend_html))

    # Render Streamlit Folium
    st_folium(
        m,
        width="100%",
        height=720,
        returned_objects=["last_clicked"],
        key="windy_taiwan_weather_map"
    )
