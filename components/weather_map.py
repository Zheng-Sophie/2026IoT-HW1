import folium
from streamlit_folium import st_folium
import streamlit as st
from typing import List, Dict, Any, Tuple
from components.weather_cards import get_weather_emoji

# Coordinates for Taiwan 22 County/City Governments (縣市政府位置)
CITY_GOV_LOCATIONS = {
    "臺北市": {"name": "臺北市政府", "coords": [25.0375, 121.5637], "zoom": 12},
    "新北市": {"name": "新北市政府", "coords": [24.9901, 121.4628], "zoom": 11},
    "基隆市": {"name": "基隆市政府", "coords": [25.1315, 121.7402], "zoom": 13},
    "桃園市": {"name": "桃園市政府", "coords": [24.9936, 121.3010], "zoom": 11},
    "新竹市": {"name": "新竹市政府", "coords": [24.8066, 120.9686], "zoom": 13},
    "新竹縣": {"name": "新竹縣政府", "coords": [24.8383, 121.0093], "zoom": 11},
    "苗栗縣": {"name": "苗栗縣政府", "coords": [24.5649, 120.8190], "zoom": 11},
    "臺中市": {"name": "臺中市政府", "coords": [24.1631, 120.6478], "zoom": 11},
    "彰化縣": {"name": "彰化縣政府", "coords": [24.0754, 120.5447], "zoom": 11},
    "南投縣": {"name": "南投縣政府", "coords": [23.9027, 120.6904], "zoom": 10},
    "雲林縣": {"name": "雲林縣政府", "coords": [23.7092, 120.4313], "zoom": 11},
    "嘉義市": {"name": "嘉義市政府", "coords": [23.4800, 120.4491], "zoom": 13},
    "嘉義縣": {"name": "嘉義縣政府", "coords": [23.4588, 120.5740], "zoom": 11},
    "臺南市": {"name": "臺南市政府", "coords": [22.9922, 120.1851], "zoom": 11},
    "高雄市": {"name": "高雄市政府", "coords": [22.6234, 120.3123], "zoom": 11},
    "屏東縣": {"name": "屏東縣政府", "coords": [22.6828, 120.4879], "zoom": 11},
    "宜蘭縣": {"name": "宜蘭縣政府", "coords": [24.7308, 121.7631], "zoom": 11},
    "花蓮縣": {"name": "花蓮縣政府", "coords": [23.9922, 121.6186], "zoom": 10},
    "臺東縣": {"name": "臺東縣政府", "coords": [22.7583, 121.1444], "zoom": 10},
    "澎湖縣": {"name": "澎湖縣政府", "coords": [23.5711, 119.5793], "zoom": 11},
    "金門縣": {"name": "金門縣政府", "coords": [24.4357, 118.3186], "zoom": 12},
    "連江縣": {"name": "連江縣政府", "coords": [26.1575, 119.9519], "zoom": 12}
}

def render_taiwan_weather_map(
    stations: List[Dict[str, Any]],
    city_summaries: List[Dict[str, Any]] = None,
    selected_city: str = None
):
    """
    Render Google Maps style full-screen interactive weather map of Taiwan.
    - Zoom out: City Government weather summary badges.
    - Zoom in: Rich local station weather badges showing station temperature, weather icon, and local conditions.
    """
    if not stations and not city_summaries:
        st.info("尚無地圖站點資料")
        return

    # Determine center and zoom level based on selected city
    center = [23.7, 121.0]
    zoom = 7.5
    if selected_city and selected_city in CITY_GOV_LOCATIONS:
        center = CITY_GOV_LOCATIONS[selected_city]["coords"]
        zoom = CITY_GOV_LOCATIONS[selected_city]["zoom"]

    # Google Maps style CartoDB Positron / OpenStreetMap base
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB positron",
        control_scale=True
    )

    # 1. City Government Overview Layer (Zoom Out Summary)
    gov_group = folium.FeatureGroup(name="🏛️ 縣市天氣總覽 (Zoom Out)", show=True).add_to(m)

    summary_dict = {}
    if city_summaries:
        for s in city_summaries:
            summary_dict[s.get("city")] = s

    for city_name, gov_info in CITY_GOV_LOCATIONS.items():
        coords = gov_info["coords"]
        gov_title = gov_info["name"]
        
        c_summary = summary_dict.get(city_name, {})
        avg_temp = c_summary.get("avg_temp")
        max_temp = c_summary.get("max_temp")
        min_temp = c_summary.get("min_temp")
        avg_rain = c_summary.get("avg_rain", 0)
        st_count = c_summary.get("station_count", 0)

        city_stations = [st for st in stations if st.get("city") == city_name]
        rep_weather = city_stations[0].get("weather", "多雲") if city_stations else "多雲"
        emoji = get_weather_emoji(rep_weather)

        temp_display = f"{avg_temp}°C" if avg_temp is not None else "N/A"
        max_display = f"{max_temp}°C" if max_temp is not None else "N/A"
        min_display = f"{min_temp}°C" if min_temp is not None else "N/A"

        # Badge HTML for City Government
        badge_html = f"""
        <div style="
            background: linear-gradient(135deg, #1E88E5, #1565C0);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            font-family: Arial, sans-serif;
            white-space: nowrap;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            border: 2px solid white;
            text-align: center;
        ">
            🏛️ {city_name} {temp_display} {emoji}
        </div>
        """

        hover_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 6px; min-width: 190px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 3px 8px rgba(0,0,0,0.25);">
            <div style="font-weight: bold; color: #1565C0; font-size: 14px; border-bottom: 2px solid #1E88E5; padding-bottom: 4px;">
                🏛️ {gov_title}
            </div>
            <div style="font-size: 12px; margin-top: 6px; line-height: 1.5;">
                {emoji} <b>天氣現象:</b> {rep_weather}<br>
                🌡️ <b>平均氣溫:</b> <span style="color: #E53935; font-weight: bold; font-size: 13px;">{temp_display}</span><br>
                🔥 <b>縣市最高溫:</b> {max_display}<br>
                ❄️ <b>縣市最低溫:</b> {min_display}<br>
                🌧️ <b>平均降雨量:</b> {avg_rain} mm<br>
                <span style="color: #666; font-size: 11px;">📡 轄區氣象站: 共 {st_count} 站</span>
            </div>
        </div>
        """

        folium.Marker(
            location=coords,
            icon=folium.DivIcon(html=badge_html, icon_size=(110, 30), icon_anchor=(55, 15)),
            popup=folium.Popup(hover_html, max_width=250),
            tooltip=folium.Tooltip(hover_html, sticky=True)
        ).add_to(gov_group)

    # 2. Local Weather Stations Layer (Zoom In Local Weather Display)
    stations_group = folium.FeatureGroup(name="📡 各鄉鎮地區即時天氣 (Zoom In)", show=True).add_to(m)

    for st_info in stations:
        lat = st_info.get("lat")
        lon = st_info.get("lon")
        
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
        obs_time = st_info.get("obs_time", "")

        emoji = get_weather_emoji(weather)

        # Local Weather Badge HTML (rendered when zoomed in to township level)
        bg_color = "#1E88E5" if rain > 0 else ("#E53935" if temp and temp >= 30 else "#43A047")
        temp_str = f"{temp}°C" if temp is not None else "N/A"
        max_str = f"{max_t}°C" if max_t is not None else "N/A"
        min_str = f"{min_t}°C" if min_t is not None else "N/A"

        # Local weather badge showing Township/Station Name + Local Temp + Weather Icon
        local_badge_html = f"""
        <div style="
            background-color: {bg_color};
            color: white;
            padding: 3px 6px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: bold;
            font-family: Arial, sans-serif;
            white-space: nowrap;
            box-shadow: 0 1px 4px rgba(0,0,0,0.3);
            border: 1px solid white;
            display: inline-block;
        ">
            📍 {town or st_name} {temp_str} {emoji}
        </div>
        """

        hover_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 5px; min-width: 175px;">
            <div style="font-weight: bold; color: #1565C0; font-size: 13px;">📍 {city} {town} ({st_name})</div>
            <div style="font-size: 11px; margin-top: 3px; line-height: 1.4;">
                {emoji} <b>當前天氣:</b> {weather}<br>
                🌡️ <b>地區氣溫:</b> <span style="color: #E53935; font-weight: bold;">{temp_str}</span><br>
                🔥 <b>本日最高:</b> {max_str} | ❄️ <b>最低:</b> {min_str}<br>
                🌧️ <b>降雨量:</b> {rain} mm | 💧 <b>相對濕度:</b> {hum}%<br>
                <span style="color: #888; font-size: 10px;">觀測時間: {obs_time}</span>
            </div>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=local_badge_html, icon_size=(90, 25), icon_anchor=(45, 12)),
            popup=folium.Popup(hover_html, max_width=250),
            tooltip=folium.Tooltip(hover_html, sticky=True)
        ).add_to(stations_group)

    folium.LayerControl().add_to(m)

    # Render map full container height
    st_folium(m, width="100%", height=850, key="taiwan_weather_fullscreen_map")
