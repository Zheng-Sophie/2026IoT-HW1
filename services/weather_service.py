import logging
from typing import List, Dict, Any, Tuple
from services.cwa_api import CWAAPIClient
from services.weather_parser import WeatherParser
from services.database import DatabaseManager

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self, db_manager: DatabaseManager = None, api_client: CWAAPIClient = None):
        self.db = db_manager or DatabaseManager()
        self.api = api_client or CWAAPIClient()

    def sync_data(self) -> Tuple[int, int]:
        """Fetch latest API data, parse, and update SQLite database."""
        obs_inserted = 0
        fcst_inserted = 0

        # Sync Observations (O-A0003-001)
        try:
            obs_json = self.api.fetch_observations()
            obs_records = WeatherParser.parse_observation_json(obs_json)
            obs_inserted = self.db.save_observation_records(obs_records)
        except Exception as e:
            logger.error(f"Error syncing observation data: {e}")

        # Sync Forecasts (F-C0032-001)
        try:
            fcst_json = self.api.fetch_forecast()
            fcst_records = WeatherParser.parse_forecast_json(fcst_json)
            fcst_inserted = self.db.save_forecast_records(fcst_records)
        except Exception as e:
            logger.error(f"Error syncing forecast data: {e}")

        return obs_inserted, fcst_inserted

    def get_cities(self) -> List[str]:
        cities = self.db.get_all_cities()
        if not cities:
            # Sync once if empty
            self.sync_data()
            cities = self.db.get_all_cities()
        return cities

    def get_city_forecast(self, city: str) -> List[Dict[str, Any]]:
        return self.db.query_forecast_by_city(city)

    def get_city_observations(self, city: str) -> List[Dict[str, Any]]:
        return self.db.query_observations_by_city(city)

    def get_all_map_stations(self) -> List[Dict[str, Any]]:
        stations = self.db.query_latest_observations()
        if not stations:
            self.sync_data()
            stations = self.db.query_latest_observations()
        return stations

    def get_last_updated_time(self) -> str:
        t = self.db.get_last_updated_time()
        return t if t else "尚未更新"

    @staticmethod
    def classify_pop(pop_value: float) -> str:
        """
        Rule-based rain probability classification (Step 4 requirement):
        - PoP < 30%: 低降雨機率 🟢
        - 30% <= PoP < 60%: 中降雨機率 🟡
        - PoP >= 60%: 高降雨機率 🔴
        """
        if pop_value < 30:
            return "低降雨機率 (晴/多雲)"
        elif pop_value < 60:
            return "中降雨機率 (可能陣雨)"
        else:
            return "高降雨機率 (提醒帶傘)"

    def get_county_rankings(self) -> Dict[str, Any]:
        """Compute county-wide rankings for analytics."""
        obs_summaries = self.db.query_city_summary_observations()
        if not obs_summaries:
            return {}

        processed = []
        for item in obs_summaries:
            c_max = item.get("city_max_temp") if item.get("city_max_temp") is not None else (item.get("avg_temp") or 0)
            c_min = item.get("city_min_temp") if item.get("city_min_temp") is not None else (item.get("avg_temp") or 0)
            processed.append({
                "city": item.get("city"),
                "avg_temp": round(item.get("avg_temp") or 0, 1),
                "max_temp": round(c_max, 1),
                "min_temp": round(c_min, 1),
                "temp_diff": round(c_max - c_min, 1),
                "station_count": item.get("station_count", 0),
                "avg_rain": round(item.get("avg_rain") or 0, 1)
            })

        processed.sort(key=lambda x: x["max_temp"], reverse=True)
        hottest = processed[0] if processed else None
        
        processed_min = sorted(processed, key=lambda x: x["min_temp"])
        coolest = processed_min[0] if processed_min else None

        processed_diff = sorted(processed, key=lambda x: x["temp_diff"], reverse=True)
        max_diff = processed_diff[0] if processed_diff else None

        return {
            "cities_data": processed,
            "hottest": hottest,
            "coolest": coolest,
            "max_diff": max_diff
        }
