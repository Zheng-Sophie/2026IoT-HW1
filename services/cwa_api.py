import json
import logging
import requests
import urllib3
from datetime import datetime
from config import CWA_API_KEY, CWA_BASE_URL, FORECAST_DATASET_ID, OBSERVATION_DATASET_ID, SAMPLE_DATA_PATH

# Disable SSL warnings for CWA certificate quirk
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class CWAAPIClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or CWA_API_KEY

    def fetch_dataset(self, dataset_id: str, max_retries: int = 3, timeout: int = 10) -> dict:
        """
        Fetch JSON data from CWA Open Data API with retry logic and fallback handling.
        """
        if not self.api_key:
            logger.warning("No CWA API key provided. Using fallback dataset.")
            return self._load_fallback_data()

        url = f"{CWA_BASE_URL}/{dataset_id}"
        params = {"Authorization": self.api_key}

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, params=params, verify=False, timeout=timeout)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") == "true" or data.get("success") is True:
                        data["_fetched_at"] = datetime.now().isoformat()
                        data["_source"] = "CWA_API"
                        return data
                    else:
                        logger.error(f"API returned success=false: {data}")
                else:
                    logger.warning(f"HTTP {response.status_code} on attempt {attempt}")
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed with error: {e}")

        logger.error("All API retries failed. Loading fallback data.")
        return self._load_fallback_data()

    def fetch_observations(self) -> dict:
        """Fetch O-A0003-001 Automatic Station Weather Observations"""
        return self.fetch_dataset(OBSERVATION_DATASET_ID)

    def fetch_forecast(self) -> dict:
        """Fetch F-C0032-001 36h Weather Forecast"""
        return self.fetch_dataset(FORECAST_DATASET_ID)

    def _load_fallback_data(self) -> dict:
        """Load local fallback sample data if available"""
        if SAMPLE_DATA_PATH.exists():
            with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_fetched_at"] = datetime.now().isoformat()
                data["_source"] = "SAMPLE_FALLBACK"
                return data
        return {"success": False, "records": {}, "_source": "EMPTY"}
