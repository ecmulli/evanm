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

        # Fetch production + consumption via rgm_stats (1 API call, both channels)
        # Channel 1 = production, Channel 2 = consumption
        try:
            rgm = self.client.get_consumption_intervals(start_at, now)
            prod_readings = []
            cons_readings = []
            for group in rgm.meter_intervals:
                for iv in group.intervals:
                    reading = {
                        "timestamp": datetime.fromtimestamp(iv.end_at, self.timezone).isoformat(),
                        "watt_hours": int(iv.wh_del or 0),
                        "watts": iv.curr_w,
                    }
                    if iv.channel == 1:  # Production
                        reading["metric_type"] = "production"
                        prod_readings.append(reading)
                    elif iv.channel == 2:  # Consumption
                        reading["metric_type"] = "consumption"
                        cons_readings.append(reading)

            results["production"] = self.db.upsert_readings(prod_readings)
            results["consumption"] = self.db.upsert_readings(cons_readings)
            logger.info(
                f"Production: {len(prod_readings)} intervals, {results['production']} upserted | "
                f"Consumption: {len(cons_readings)} intervals, {results['consumption']} upserted"
            )
        except Exception as e:
            logger.error(f"Failed to collect data: {e}")
            results["errors"].append(f"rgm_stats: {e}")

        return results
