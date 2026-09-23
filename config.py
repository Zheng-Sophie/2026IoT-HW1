import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

CWA_API_KEY = os.getenv("CWA_API_KEY", "")

# Datasets
OBSERVATION_DATASET_ID = "O-A0003-001"  # 自動氣象站觀測資料
FORECAST_DATASET_ID = "F-C0032-001"     # 一般天氣預報-今明36小時天氣預報

CWA_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"

DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "weather.db"
SAMPLE_DATA_PATH = BASE_DIR / "data" / "sample.json"

# Ensure directories exist
DB_DIR.mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
