import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class WeatherParser:
    @staticmethod
    def parse_forecast_json(json_data: dict, fetched_at: str = None) -> List[Dict[str, Any]]:
        """
        Parse F-C0032-001 JSON into structured records for SQLite.
        """
        records = []
        fetched_time = fetched_at or json_data.get("_fetched_at") or datetime.now().isoformat()
        
        # If wrapped in sample format
        if "forecast" in json_data and isinstance(json_data["forecast"], dict):
            json_data = json_data["forecast"]

        cwa_records = json_data.get("records", {})
        locations = cwa_records.get("location", [])

        for loc in locations:
            city_name = loc.get("locationName", "")
            weather_elements = loc.get("weatherElement", [])
            
            # Extract elements by name
            elem_map = {}
            for elem in weather_elements:
                elem_name = elem.get("elementName", "")
                elem_map[elem_name] = elem.get("time", [])

            # We iterate through time slots (usually 3 slots for 36h)
            wx_times = elem_map.get("Wx", [])
            min_t_times = elem_map.get("MinT", [])
            max_t_times = elem_map.get("MaxT", [])
            pop_times = elem_map.get("PoP", [])
            ci_times = elem_map.get("CI", [])

            for i in range(len(wx_times)):
                time_slot = wx_times[i]
                start_time = time_slot.get("startTime", "")
                end_time = time_slot.get("endTime", "")
                weather_desc = time_slot.get("parameter", {}).get("parameterName", "")

                forecast_date = start_time.split(" ")[0] if " " in start_time else start_time.split("T")[0]

                min_t = WeatherParser._safe_float(
                    min_t_times[i].get("parameter", {}).get("parameterName", "") if i < len(min_t_times) else 0
                )
                max_t = WeatherParser._safe_float(
                    max_t_times[i].get("parameter", {}).get("parameterName", "") if i < len(max_t_times) else 0
                )
                pop = WeatherParser._safe_float(
                    pop_times[i].get("parameter", {}).get("parameterName", "") if i < len(pop_times) else 0
                )
                comfort = ci_times[i].get("parameter", {}).get("parameterName", "") if i < len(ci_times) else ""

                record = {
                    "city": city_name,
                    "forecast_date": forecast_date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "weather": weather_desc,
                    "min_temp": min_t,
                    "max_temp": max_t,
                    "pop": pop,
                    "comfort": comfort,
                    "fetched_at": fetched_time
                }
                records.append(record)

        return records

    @staticmethod
    def parse_observation_json(json_data: dict, fetched_at: str = None) -> List[Dict[str, Any]]:
        """
        Parse O-A0003-001 Observation JSON into structured records for SQLite.
        """
        records = []
        fetched_time = fetched_at or json_data.get("_fetched_at") or datetime.now().isoformat()

        if "observation" in json_data and isinstance(json_data["observation"], dict):
            json_data = json_data["observation"]

        cwa_records = json_data.get("records", {})
        stations = cwa_records.get("Station", [])

        for st in stations:
            st_id = st.get("StationId", "")
            st_name = st.get("StationName", "")
            obs_time = st.get("ObsTime", {}).get("DateTime", "")
            geo = st.get("GeoInfo", {})
            county = geo.get("CountyName", "")
            town = geo.get("TownName", "")

            # Get WGS84 coords
            lat, lon = 23.7, 121.0
            coords = geo.get("Coordinates", [])
            for c in coords:
                if c.get("CoordinateName") == "WGS84":
                    lat = WeatherParser._safe_float(c.get("StationLatitude", "23.7"))
                    lon = WeatherParser._safe_float(c.get("StationLongitude", "121.0"))
                    break

            elem = st.get("WeatherElement", {})
            weather_desc = elem.get("Weather", "多雲")
            air_temp = WeatherParser._safe_float(elem.get("AirTemperature", "-99"))
            humidity = WeatherParser._safe_float(elem.get("RelativeHumidity", "-99"))
            pressure = WeatherParser._safe_float(elem.get("AirPressure", "-99"))
            wind_speed = WeatherParser._safe_float(elem.get("WindSpeed", "0"))
            rain = WeatherParser._safe_float(elem.get("Now", {}).get("Precipitation", "0"))

            daily_high = WeatherParser._safe_float(
                elem.get("DailyExtreme", {}).get("DailyHigh", {}).get("TemperatureInfo", {}).get("AirTemperature", str(air_temp))
            )
            daily_low = WeatherParser._safe_float(
                elem.get("DailyExtreme", {}).get("DailyLow", {}).get("TemperatureInfo", {}).get("AirTemperature", str(air_temp))
            )

            # Filter out invalid / offline sensor readings (-99)
            if air_temp == -99:
                air_temp = None
            if daily_high == -99:
                daily_high = air_temp
            if daily_low == -99:
                daily_low = air_temp

            record = {
                "station_id": st_id,
                "station_name": st_name,
                "city": county,
                "town": town,
                "lat": lat,
                "lon": lon,
                "obs_time": obs_time,
                "weather": weather_desc,
                "temp": air_temp,
                "min_temp": daily_low,
                "max_temp": daily_high,
                "humidity": humidity if humidity != -99 else None,
                "pressure": pressure if pressure != -99 else None,
                "rain": rain if rain >= 0 else 0,
                "wind_speed": wind_speed if wind_speed >= 0 else 0,
                "fetched_at": fetched_time
            }
            records.append(record)

        return records

    @staticmethod
    def _safe_float(val: Any) -> float:
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0
