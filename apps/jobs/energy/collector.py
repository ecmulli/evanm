"""
Energy data collector.

Fetches production and consumption data from the Enphase API
and stores it in Postgres.
"""

import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import Config
from .db import Database
from .enphase_client import EnphaseClient

logger = logging.getLogger(__name__)


class Collector:
    """Collects Enphase telemetry data into Postgres."""

    # Fetch 6 hours of data per run (overlaps are handled by upsert)
    LOOKBACK_HOURS = 6

    def __init__(self, config: Config, db: Database, client: EnphaseClient):
        self.config = config
        self.db = db
        self.client = client
        self.timezone = ZoneInfo(config.timezone)

    def collect(self) -> dict:
        """
        Fetch recent data from Enphase and store in Postgres.

        Returns summary of what was collected.
        """
        now = int(time.time())
        start_at = now - (self.LOOKBACK_HOURS * 3600)

        logger.info(
            f"Collecting {self.LOOKBACK_HOURS}h of data: "
            f"{datetime.fromtimestamp(start_at, self.timezone)} to "
            f"{datetime.fromtimestamp(now, self.timezone)}"
        )

        results = {"production": 0, "consumption": 0, "errors": []}

        # Fetch production
        try:
            prod = self.client.get_production_intervals(start_at, now)
            readings = [
                {
                    "timestamp": datetime.fromtimestamp(i.end_at, self.timezone).isoformat(),
                    "metric_type": "production",
                    "watt_hours": i.wh_del or 0,
                    "watts": i.powr,
                }
                for i in prod.intervals
            ]
            results["production"] = self.db.upsert_readings(readings)
            logger.info(f"Production: {len(prod.intervals)} intervals fetched, {results['production']} new")
        except Exception as e:
            logger.error(f"Failed to collect production data: {e}")
            results["errors"].append(f"production: {e}")

        # Fetch consumption
        try:
            cons = self.client.get_consumption_intervals(start_at, now)
            readings = [
                {
                    "timestamp": datetime.fromtimestamp(i.end_at, self.timezone).isoformat(),
                    "metric_type": "consumption",
                    "watt_hours": i.enwh or 0,
                    "watts": i.powr,
                }
                for i in cons.intervals
            ]
            results["consumption"] = self.db.upsert_readings(readings)
            logger.info(f"Consumption: {len(cons.intervals)} intervals fetched, {results['consumption']} new")
        except Exception as e:
            logger.error(f"Failed to collect consumption data: {e}")
            results["errors"].append(f"consumption: {e}")

        return results
