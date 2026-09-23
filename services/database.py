import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import DB_PATH

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Create SQLite database tables and indexes if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Forecast records table (as required by myplan.md)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forecast_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    forecast_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    weather TEXT,
                    min_temp REAL,
                    max_temp REAL,
                    pop REAL,
                    comfort TEXT,
                    fetched_at TEXT NOT NULL,
                    UNIQUE(city, start_time, end_time)
                )
            """)

            # Observation records table (O-A0003-001)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS observation_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id TEXT NOT NULL,
                    station_name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    town TEXT,
                    lat REAL,
                    lon REAL,
                    obs_time TEXT NOT NULL,
                    weather TEXT,
                    temp REAL,
                    min_temp REAL,
                    max_temp REAL,
                    humidity REAL,
                    pressure REAL,
                    rain REAL,
                    wind_speed REAL,
                    fetched_at TEXT NOT NULL,
                    UNIQUE(station_id, obs_time)
                )
            """)

            # Indexes for fast querying
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fcst_city ON forecast_records (city)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fcst_date ON forecast_records (forecast_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_obs_city ON observation_records (city)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_obs_time ON observation_records (obs_time)")
            
            conn.commit()

    def save_forecast_records(self, records: List[Dict[str, Any]]) -> int:
        """Insert or replace forecast records into database."""
        if not records:
            return 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            inserted = 0
            for r in records:
                cursor.execute("""
                    INSERT OR REPLACE INTO forecast_records 
                    (city, forecast_date, start_time, end_time, weather, min_temp, max_temp, pop, comfort, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.get("city"), r.get("forecast_date"), r.get("start_time"), r.get("end_time"),
                    r.get("weather"), r.get("min_temp"), r.get("max_temp"), r.get("pop"),
                    r.get("comfort"), r.get("fetched_at")
                ))
                inserted += 1
            conn.commit()
            return inserted

    def save_observation_records(self, records: List[Dict[str, Any]]) -> int:
        """Insert or replace observation records into database."""
        if not records:
            return 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            inserted = 0
            for r in records:
                cursor.execute("""
                    INSERT OR REPLACE INTO observation_records
                    (station_id, station_name, city, town, lat, lon, obs_time, weather, temp, min_temp, max_temp, humidity, pressure, rain, wind_speed, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.get("station_id"), r.get("station_name"), r.get("city"), r.get("town"),
                    r.get("lat"), r.get("lon"), r.get("obs_time"), r.get("weather"),
                    r.get("temp"), r.get("min_temp"), r.get("max_temp"), r.get("humidity"),
                    r.get("pressure"), r.get("rain"), r.get("wind_speed"), r.get("fetched_at")
                ))
                inserted += 1
            conn.commit()
            return inserted

    def get_all_cities(self) -> List[str]:
        """Return list of distinct cities from DB."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT city FROM (
                    SELECT city FROM observation_records WHERE city != ''
                    UNION
                    SELECT city FROM forecast_records WHERE city != ''
                ) ORDER BY city
            """)
            return [row["city"] for row in cursor.fetchall()]

    def query_forecast_by_city(self, city: str) -> List[Dict[str, Any]]:
        """Query forecast records for a specific city."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM forecast_records WHERE city = ? ORDER BY start_time ASC
            """, (city,))
            return [dict(row) for row in cursor.fetchall()]

    def query_observations_by_city(self, city: str) -> List[Dict[str, Any]]:
        """Query observation records for a specific city."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM observation_records WHERE city = ? ORDER BY obs_time DESC
            """, (city,))
            return [dict(row) for row in cursor.fetchall()]

    def query_latest_observations(self) -> List[Dict[str, Any]]:
        """Get latest observations for all stations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o1.* FROM observation_records o1
                INNER JOIN (
                    SELECT station_id, MAX(obs_time) as max_time
                    FROM observation_records
                    GROUP BY station_id
                ) o2 ON o1.station_id = o2.station_id AND o1.obs_time = o2.max_time
            """)
            return [dict(row) for row in cursor.fetchall()]

    def query_city_summary_observations(self) -> List[Dict[str, Any]]:
        """Aggregated observation summary grouped by city."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT city,
                       AVG(temp) as avg_temp,
                       MAX(max_temp) as city_max_temp,
                       MIN(min_temp) as city_min_temp,
                       AVG(rain) as avg_rain,
                       COUNT(station_id) as station_count,
                       MAX(obs_time) as obs_time
                FROM (
                    SELECT o1.* FROM observation_records o1
                    INNER JOIN (
                        SELECT station_id, MAX(obs_time) as max_time
                        FROM observation_records
                        GROUP BY station_id
                    ) o2 ON o1.station_id = o2.station_id AND o1.obs_time = o2.max_time
                )
                WHERE city != ''
                GROUP BY city
                ORDER BY city
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_last_updated_time(self) -> Optional[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(fetched_at) as last_time FROM (
                    SELECT fetched_at FROM forecast_records
                    UNION
                    SELECT fetched_at FROM observation_records
                )
            """)
            row = cursor.fetchone()
            return row["last_time"] if row and row["last_time"] else None
