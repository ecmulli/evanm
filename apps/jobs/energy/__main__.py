"""
Energy data collection entry point.

Usage:
    python -m apps.jobs.energy              # Normal collection run
    python -m apps.jobs.energy --backfill 30  # Backfill last 30 days
"""

import argparse
import logging
import sys
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .aggregator import Aggregator
from .anomaly_detector import AnomalyDetector
from .collector import Collector
from .config import Config
from .db import Database
from .enphase_client import EnphaseClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_collection(config: Config, db: Database):
    """Normal collection run: fetch recent data, aggregate, check anomalies."""
    client = EnphaseClient(config, db)
    collector = Collector(config, db, client)
    aggregator = Aggregator(db, config.timezone)
    detector = AnomalyDetector(db, config.timezone)

    # 1. Collect recent data from Enphase API
    logger.info("=== Starting energy data collection ===")
    results = collector.collect()
    logger.info(f"Collection results: {results}")

    # 2. Aggregate daily summaries for today and yesterday
    logger.info("=== Aggregating daily summaries ===")
    aggregator.aggregate_recent(days=2)

    # 3. Run anomaly detection on yesterday (complete day)
    yesterday = date.today() - timedelta(days=1)
    logger.info(f"=== Running anomaly detection for {yesterday} ===")
    anomalies = detector.check_date(yesterday)
    if anomalies:
        for a in anomalies:
            logger.warning(f"ANOMALY [{a['severity']}] {a['anomaly_type']}: {a['description']}")
    else:
        logger.info("No anomalies detected")

    logger.info("=== Collection complete ===")


def run_backfill(config: Config, db: Database, days: int):
    """
    Backfill historical data.

    Fetches data day by day to stay within rate limits.
    Each day = 2 API calls (production + consumption).
    """
    client = EnphaseClient(config, db)
    aggregator = Aggregator(db, config.timezone)
    detector = AnomalyDetector(db, config.timezone)
    tz = ZoneInfo(config.timezone)

    logger.info(f"=== Backfilling {days} days of data ===")

    today = date.today()
    for i in range(days, 0, -1):
        target = today - timedelta(days=i)
        start_dt = datetime(target.year, target.month, target.day, tzinfo=tz)
        end_dt = start_dt + timedelta(days=1)

        start_at = int(start_dt.timestamp())
        end_at = int(end_dt.timestamp())

        logger.info(f"Backfilling {target} ({days - i + 1}/{days})")

        try:
            # Fetch production
            prod = client.get_production_intervals(start_at, end_at)
            readings = [
                {
                    "timestamp": datetime.fromtimestamp(iv.end_at, tz).isoformat(),
                    "metric_type": "production",
                    "watt_hours": iv.wh_del or 0,
                    "watts": iv.powr,
                }
                for iv in prod.intervals
            ]
            db.upsert_readings(readings)

            # Fetch consumption
            cons = client.get_consumption_intervals(start_at, end_at)
            readings = [
                {
                    "timestamp": datetime.fromtimestamp(iv.end_at, tz).isoformat(),
                    "metric_type": "consumption",
                    "watt_hours": iv.enwh or 0,
                    "watts": iv.powr,
                }
                for iv in cons.intervals
            ]
            db.upsert_readings(readings)

            # Aggregate
            aggregator.aggregate_date(target)

            # Detect anomalies
            detector.check_date(target)

            logger.info(f"Backfilled {target}: {len(prod.intervals)} prod + {len(cons.intervals)} cons intervals")

        except Exception as e:
            logger.error(f"Failed to backfill {target}: {e}")

        # Small delay to be nice to the API
        time.sleep(1)

    logger.info("=== Backfill complete ===")


def main():
    parser = argparse.ArgumentParser(description="Energy data collection")
    parser.add_argument(
        "--backfill",
        type=int,
        metavar="DAYS",
        help="Backfill N days of historical data",
    )
    args = parser.parse_args()

    config = Config.from_env()
    if not config.database_url:
        logger.error("DATABASE_URL or ENERGY_DATABASE_URL not set")
        sys.exit(1)
    if not config.enphase_api_key:
        logger.error("ENPHASE_API_KEY not set")
        sys.exit(1)

    db = Database(config.database_url)

    try:
        if args.backfill:
            run_backfill(config, db, args.backfill)
        else:
            run_collection(config, db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
