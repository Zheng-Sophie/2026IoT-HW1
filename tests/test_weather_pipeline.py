import unittest
import os
import gc
import sqlite3
from pathlib import Path
from config import CWA_API_KEY, SAMPLE_DATA_PATH
from services.cwa_api import CWAAPIClient
from services.weather_parser import WeatherParser
from services.database import DatabaseManager
from services.weather_service import WeatherService

class TestWeatherPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_path = Path("database/test_weather.db")
        if cls.test_db_path.exists():
            try:
                cls.test_db_path.unlink()
            except Exception:
                pass
        cls.db = DatabaseManager(db_path=cls.test_db_path)
        cls.api = CWAAPIClient(api_key=CWA_API_KEY)
        cls.service = WeatherService(db_manager=cls.db, api_client=cls.api)

    @classmethod
    def tearDownClass(cls):
        del cls.service
        del cls.db
        gc.collect()
        if cls.test_db_path.exists():
            try:
                cls.test_db_path.unlink()
            except Exception:
                pass

    def test_01_api_fetch(self):
        """Test API data fetching (Observation and Forecast)."""
        obs = self.api.fetch_observations()
        self.assertIn("records", obs)
        self.assertIn("_source", obs)

        fcst = self.api.fetch_forecast()
        self.assertIn("records", fcst)
        self.assertIn("_source", fcst)

    def test_02_json_parsing(self):
        """Test JSON Parsing into structured record list."""
        obs_json = self.api.fetch_observations()
        obs_records = WeatherParser.parse_observation_json(obs_json)
        self.assertGreater(len(obs_records), 0)
        sample_st = obs_records[0]
        self.assertIn("station_id", sample_st)
        self.assertIn("city", sample_st)
        self.assertIn("lat", sample_st)

        fcst_json = self.api.fetch_forecast()
        fcst_records = WeatherParser.parse_forecast_json(fcst_json)
        self.assertGreater(len(fcst_records), 0)
        sample_fcst = fcst_records[0]
        self.assertIn("city", sample_fcst)
        self.assertIn("start_time", sample_fcst)
        self.assertIn("max_temp", sample_fcst)

    def test_03_sqlite_database_crud(self):
        """Test SQLite schema creation, insertion, deduplication, and queries."""
        fcst_records = [
            {
                "city": "測試市",
                "forecast_date": "2026-09-23",
                "start_time": "2026-09-23 18:00:00",
                "end_time": "2026-09-24 06:00:00",
                "weather": "多雲短暫雨",
                "min_temp": 24.0,
                "max_temp": 30.0,
                "pop": 40.0,
                "comfort": "舒適",
                "fetched_at": "2026-09-23T19:00:00"
            }
        ]
        
        inserted = self.db.save_forecast_records(fcst_records)
        self.assertEqual(inserted, 1)

        # Test deduplication with same primary unique keys
        inserted_dup = self.db.save_forecast_records(fcst_records)
        self.assertEqual(inserted_dup, 1)

        # Query back
        res = self.db.query_forecast_by_city("測試市")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["weather"], "多雲短暫雨")
        self.assertEqual(res[0]["min_temp"], 24.0)

    def test_04_pop_classification(self):
        """Test rule-based rain probability classification (Step 4 Requirement)."""
        self.assertIn("低降雨機率", WeatherService.classify_pop(10.0))
        self.assertIn("中降雨機率", WeatherService.classify_pop(45.0))
        self.assertIn("高降雨機率", WeatherService.classify_pop(80.0))

    def test_05_service_sync(self):
        """Test complete data sync pipeline."""
        obs_cnt, fcst_cnt = self.service.sync_data()
        self.assertGreater(obs_cnt, 0)
        self.assertGreater(fcst_cnt, 0)

        cities = self.service.get_cities()
        self.assertGreater(len(cities), 0)

        rankings = self.service.get_county_rankings()
        self.assertIn("cities_data", rankings)

if __name__ == "__main__":
    unittest.main()
