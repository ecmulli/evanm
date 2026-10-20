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
from .models import EnphaseProductionResponse

logger = logging.getLogger(__name__)

# Intervals are 15 minutes, so average power in W is Wh * 4.
INTERVALS_PER_HOUR = 4


def meter_readings(
    production: EnphaseProductionResponse,
    consumption: EnphaseProductionResponse,
    tz: ZoneInfo,
    end_at: int | None = None,
) -> tuple[list[dict], list[dict]]:
    """Convert meter telemetry into energy_readings rows. Drops intervals that end after end_at."""

    def rows(resp: EnphaseProductionResponse, metric: str, field: str) -> list[dict]:
        out = []
        for iv in resp.intervals:
            if end_at is not None and iv.end_at > end_at:
                continue
            wh = int(round(getattr(iv, field) or 0))
            out.append(
                {
                    "timestamp": datetime.fromtimestamp(iv.end_at, tz).isoformat(),
                    "metric_type": metric,
                    "watt_hours": wh,
                    "watts": wh * INTERVALS_PER_HOUR,
                }
            )
        return out

    return rows(production, "production", "wh_del"), rows(consumption, "consumption", "enwh")


def fetch_and_store(
    client: EnphaseClient,
    db: Database,
    tz: ZoneInfo,
    start_at: int,
    end_at: int,
    granularity: str,
    overwrite: bool = False,
) -> dict:
    """Fetch production and consumption meter intervals (2 API calls) and upsert them."""
    production = client.get_production_meter(start_at, granularity)
    consumption = client.get_consumption_meter(start_at, granularity)
    prod_rows, cons_rows = meter_readings(production, consumption, tz, end_at)
    db.upsert_readings(prod_rows, overwrite=overwrite)
    db.upsert_readings(cons_rows, overwrite=overwrite)
    return {
        "production": len(prod_rows),
        "consumption": len(cons_rows),
        "production_wh": sum(r["watt_hours"] for r in prod_rows),
        "consumption_wh": sum(r["watt_hours"] for r in cons_rows),
    }


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
        try:
            results.update(fetch_and_store(self.client, self.db, self.timezone, start_at, now, "day"))
            logger.info(f"Production: {results['production']} intervals | Consumption: {results['consumption']} intervals")
        except Exception as e:
            logger.error(f"Failed to collect data: {e}")
            results["errors"].append(f"meter telemetry: {e}")

        return results
