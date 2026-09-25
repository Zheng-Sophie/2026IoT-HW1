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

def render_summary_cards(hottest: Dict[str, Any], coolest: Dict[str, Any], max_diff: Dict[str, Any], total_cities: int, max_rain: Dict[str, Any] = None):
    """Render top summary metrics across all Taiwan counties with modern dark glass design."""
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 12px;
            padding: 12px 16px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        ">
            <div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">📡 觀測站點覆蓋</div>
            <div style="font-size: 22px; font-weight: 800; color: #38bdf8; margin: 4px 0;">{total_cities} <span style="font-size: 14px; font-weight: 600;">縣市全區</span></div>
            <div style="font-size: 11px; color: #64748b;">363 個 CWA 自動測站連線</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        hot_city = hottest.get("city", "N/A") if hottest else "N/A"
        hot_temp = f"{hottest.get('max_temp', '--')}°C" if hottest else "--"
        hot_avg = f"平均 {hottest.get('avg_temp', '--')}°C" if hottest else ""
        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(239, 68, 68, 0.25);
            border-radius: 12px;
            padding: 12px 16px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        ">
            <div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">🔥 全台最高溫</div>
            <div style="font-size: 22px; font-weight: 800; color: #f87171; margin: 4px 0;">{hot_city} <span style="font-size: 18px;">{hot_temp}</span></div>
            <div style="font-size: 11px; color: #fca5a5;">{hot_avg}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        cool_city = coolest.get("city", "N/A") if coolest else "N/A"
        cool_temp = f"{coolest.get('min_temp', '--')}°C" if coolest else "--"
        cool_avg = f"平均 {coolest.get('avg_temp', '--')}°C" if coolest else ""
        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(59, 130, 246, 0.25);
            border-radius: 12px;
            padding: 12px 16px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        ">
            <div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">❄️ 全台最低溫</div>
            <div style="font-size: 22px; font-weight: 800; color: #60a5fa; margin: 4px 0;">{cool_city} <span style="font-size: 18px;">{cool_temp}</span></div>
            <div style="font-size: 11px; color: #93c5fd;">{cool_avg}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        diff_city = max_diff.get("city", "N/A") if max_diff else "N/A"
        diff_val = f"{max_diff.get('temp_diff', '--')}°C" if max_diff else "--"
        diff_range = f"高 {max_diff.get('max_temp', '--')}° / 低 {max_diff.get('min_temp', '--')}°" if max_diff else ""
        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(245, 158, 11, 0.25);
            border-radius: 12px;
            padding: 12px 16px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        ">
            <div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">🌡️ 最大日夜溫差</div>
            <div style="font-size: 22px; font-weight: 800; color: #fbbf24; margin: 4px 0;">{diff_city} <span style="font-size: 18px;">{diff_val}</span></div>
            <div style="font-size: 11px; color: #fde68a;">{diff_range}</div>
        </div>
        """, unsafe_allow_html=True)

def render_city_cards(city_name: str, forecast_records: List[Dict[str, Any]], obs_records: List[Dict[str, Any]]):
    """Render detailed cards for the selected city with dark theme cards."""
    st.markdown(f"### 📍 {city_name} 天氣總覽與 36 小時預報")

    # 1. Latest Observation card if available
    if obs_records:
        latest_obs = obs_records[0]
        emoji = get_weather_emoji(latest_obs.get("weather", ""))
        st_name = latest_obs.get("station_name", "測站")
        town = latest_obs.get("town", "")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("即時氣溫", f"{latest_obs.get('temp', '--')}°C", delta=f"{emoji} {latest_obs.get('weather', '')}")
        with c2:
            st.metric("最高溫 (High)", f"{latest_obs.get('max_temp', '--')}°C")
        with c3:
            st.metric("最低溫 (Low)", f"{latest_obs.get('min_temp', '--')}°C")
        with c4:
            st.metric("相對濕度", f"{latest_obs.get('humidity', '--')}%")
        with c5:
            st.metric("即時雨量", f"{latest_obs.get('rain', 0.0)} mm")

    st.markdown("---")

    # 2. 36-Hour Forecast Cards
    if forecast_records:
        st.markdown("#### 📅 今明 36 小時時段預報")
        cols = st.columns(min(len(forecast_records), 3))

        for idx, rec in enumerate(forecast_records[:3]):
            with cols[idx]:
                start_t = rec['start_time'].split(' ')[-1] if ' ' in rec['start_time'] else rec['start_time']
                end_t = rec['end_time'].split(' ')[-1] if ' ' in rec['end_time'] else rec['end_time']
                emoji = get_weather_emoji(rec.get('weather', ''))
                pop_val = rec.get('pop', 0)
                comfort_str = rec.get('comfort', '舒適')

                # Rain color badge
                pop_color = "#f87171" if pop_val >= 60 else ("#fbbf24" if pop_val >= 30 else "#34d399")

                st.markdown(f"""
                <div style="
                    background: rgba(15, 23, 42, 0.85);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 14px;
                    padding: 16px;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
                ">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">時段 {idx+1} · {start_t} ~ {end_t}</div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin: 10px 0;">
                        <span style="font-size: 32px;">{emoji}</span>
                        <div style="text-align: right;">
                            <div style="font-size: 16px; font-weight: bold; color: #f8fafc;">{rec.get('weather', '')}</div>
                            <div style="font-size: 12px; color: #94a3b8;">{comfort_str}</div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px;">
                        <div>
                            <span style="font-size: 11px; color: #94a3b8;">預估溫度</span>
                            <div style="font-size: 18px; font-weight: 800; color: #38bdf8;">
                                {rec.get('min_temp')}° ~ {rec.get('max_temp')}°C
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 11px; color: #94a3b8;">降雨機率</span>
                            <div style="font-size: 16px; font-weight: 800; color: {pop_color};">
                                🌧️ {pop_val}%
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
