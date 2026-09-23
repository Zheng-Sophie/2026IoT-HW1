import streamlit as st
from typing import Dict, Any, List

def get_weather_emoji(weather_str: str) -> str:
    """Return appropriate weather emoji based on weather condition string."""
    if not weather_str:
        return "🌡️"
    if "雷" in weather_str or "暴" in weather_str:
        return "⛈️"
    if "雨" in weather_str:
        return "🌧️"
    if "陰" in weather_str:
        return "☁️"
    if "多雲" in weather_str:
        return "⛅"
    if "晴" in weather_str:
        return "☀️"
    return "🌤️"

def render_summary_cards(hottest: Dict[str, Any], coolest: Dict[str, Any], max_diff: Dict[str, Any], total_cities: int):
    """Render top summary metrics across all Taiwan counties."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="全台觀測縣市數",
            value=f"{total_cities} 縣市",
            delta="CWA Open Data"
        )
    with col2:
        if hottest:
            st.metric(
                label="全台最高溫縣市 🔥",
                value=f"{hottest['city']} {hottest['max_temp']}°C",
                delta=f"平均 {hottest['avg_temp']}°C"
            )
        else:
            st.metric("全台最高溫縣市", "N/A")
            
    with col3:
        if coolest:
            st.metric(
                label="全台最低溫縣市 ❄️",
                value=f"{coolest['city']} {coolest['min_temp']}°C",
                delta=f"平均 {coolest['avg_temp']}°C",
                delta_color="inverse"
            )
        else:
            st.metric("全台最低溫縣市", "N/A")

    with col4:
        if max_diff:
            st.metric(
                label="最大日夜溫差縣市 🌡️",
                value=f"{max_diff['city']} {max_diff['temp_diff']}°C",
                delta=f"高 {max_diff['max_temp']}°C / 低 {max_diff['min_temp']}°C"
            )
        else:
            st.metric("最大溫差縣市", "N/A")

def render_city_cards(city_name: str, forecast_records: List[Dict[str, Any]], obs_records: List[Dict[str, Any]]):
    """Render detailed cards for the selected city."""
    st.subheader(f"📍 {city_name} 當前天氣預報與觀測")
    
    # 1. Latest Observation card if available
    if obs_records:
        latest_obs = obs_records[0]
        emoji = get_weather_emoji(latest_obs.get("weather", ""))
        
        st.markdown(f"#### {emoji} 實測天氣觀測（站點：{latest_obs.get('station_name', '縣市站')} - {latest_obs.get('town', '')}）")
        c1, c2, c3, c4, c5 = st.columns(5)
        
        temp_val = f"{latest_obs['temp']}°C" if latest_obs.get('temp') is not None else "N/A"
        max_val = f"{latest_obs['max_temp']}°C" if latest_obs.get('max_temp') is not None else "N/A"
        min_val = f"{latest_obs['min_temp']}°C" if latest_obs.get('min_temp') is not None else "N/A"
        hum_val = f"{latest_obs['humidity']}%" if latest_obs.get('humidity') is not None else "N/A"
        rain_val = f"{latest_obs['rain']} mm" if latest_obs.get('rain') is not None else "0.0 mm"

        c1.metric("氣溫", temp_val, delta=latest_obs.get("weather", ""))
        c2.metric("最高溫 (High)", max_val)
        c3.metric("最低溫 (Low)", min_val)
        c4.metric("相對濕度", hum_val)
        c5.metric("累積雨量", rain_val)

    st.markdown("---")

    # 2. 36-Hour Forecast Cards
    if forecast_records:
        st.markdown("#### 📅 今明 36 小時天氣預報")
        cols = st.columns(min(len(forecast_records), 3))
        
        for idx, rec in enumerate(forecast_records[:3]):
            with cols[idx]:
                start_t = rec['start_time'].split(' ')[-1] if ' ' in rec['start_time'] else rec['start_time']
                end_t = rec['end_time'].split(' ')[-1] if ' ' in rec['end_time'] else rec['end_time']
                emoji = get_weather_emoji(rec.get('weather', ''))
                
                st.markdown(f"**時段 {idx+1} ({start_t} ~ {end_t})**")
                st.markdown(f"### {emoji} {rec.get('weather', '')}")
                st.write(f"🌡️ **溫度:** {rec.get('min_temp')}°C ~ {rec.get('max_temp')}°C")
                st.write(f"💧 **降雨機率:** {rec.get('pop')}%")
                st.write(f"🧘 **舒適度:** {rec.get('comfort', '適中')}")
