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
    Backfill historical data using efficient endpoint strategy.

    Phase 1: Fetch ALL production daily totals via energy_lifetime (1 API call).
    Phase 2: Fetch consumption via rgm_stats in 7-day chunks (1 API call per chunk).
    Phase 3: Aggregate and run anomaly detection.

    Total API calls: 1 + ceil(N/7) (vs 2N before). 30 days = ~6 calls.
    Rate limiter in EnphaseClient handles the 10 req/min limit automatically.
    """
    client = EnphaseClient(config, db)
    aggregator = Aggregator(db, config.timezone)
    detector = AnomalyDetector(db, config.timezone)
    tz = ZoneInfo(config.timezone)

    today = date.today()
    start_date = today - timedelta(days=days)

    logger.info(f"=== Backfilling {days} days ({start_date} to {today - timedelta(days=1)}) ===")

    # Phase 1: Production lifetime — 1 API call for all days
    logger.info("Phase 1: Fetching production lifetime (1 API call)...")
    prod_by_date: dict[date, int] = {}
    try:
        prod = client.get_production_lifetime(
            start_date=str(start_date),
            end_date=str(today - timedelta(days=1)),
        )
        # Map array index to date
        base = date.fromisoformat(prod.start_date)
        for i, wh in enumerate(prod.production):
            d = base + timedelta(days=i)
            prod_by_date[d] = wh
        logger.info(f"Got {len(prod.production)} days of production data")
    except Exception as e:
        logger.error(f"energy_lifetime failed: {e}")
        logger.info("Falling back to per-day telemetry for production")

    # Phase 2: Consumption via rgm_stats in 7-day chunks
    CHUNK_DAYS = 7
    num_chunks = (days + CHUNK_DAYS - 1) // CHUNK_DAYS
    logger.info(f"Phase 2: Fetching consumption in {num_chunks} chunks of up to {CHUNK_DAYS} days...")

    chunk_start = start_date
    chunk_num = 0
    while chunk_start < today:
        chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS), today)
        chunk_num += 1

        start_dt = datetime(chunk_start.year, chunk_start.month, chunk_start.day, tzinfo=tz)
        end_dt = datetime(chunk_end.year, chunk_end.month, chunk_end.day, tzinfo=tz)
        start_at = int(start_dt.timestamp())
        end_at = int(end_dt.timestamp())

        logger.info(f"  Chunk {chunk_num}/{num_chunks}: {chunk_start} to {chunk_end - timedelta(days=1)}")

        try:
            # If production lifetime failed, fetch production telemetry for this chunk too
            needs_prod = any(
                (chunk_start + timedelta(days=d)) not in prod_by_date
                for d in range((chunk_end - chunk_start).days)
            )
            if needs_prod:
                prod_data = client.get_production_intervals(start_at, end_at)
                readings = [
                    {
                        "timestamp": datetime.fromtimestamp(iv.end_at, tz).isoformat(),
                        "metric_type": "production",
                        "watt_hours": iv.wh_del or 0,
                        "watts": iv.powr,
                    }
                    for iv in prod_data.intervals
                ]
                db.upsert_readings(readings)

            # Fetch consumption via rgm_stats (channel 2 = consumption)
            rgm = client.get_consumption_intervals(start_at, end_at)
            cons_readings = []
            for group in rgm.meter_intervals:
                for iv in group.intervals:
                    if iv.channel == 2:  # Consumption channel
                        cons_readings.append({
                            "timestamp": datetime.fromtimestamp(iv.end_at, tz).isoformat(),
                            "metric_type": "consumption",
                            "watt_hours": int(iv.wh_del or 0),
                            "watts": iv.curr_w,
                        })
            db.upsert_readings(cons_readings)

            logger.info(f"  Got {len(cons_readings)} consumption intervals")

        except Exception as e:
            logger.error(f"Failed to backfill chunk {chunk_start}-{chunk_end}: {e}")

        chunk_start = chunk_end

    # Phase 3: Aggregate and detect anomalies
    logger.info("Phase 3: Aggregating summaries and detecting anomalies...")
    for i in range(days, 0, -1):
        target = today - timedelta(days=i)
        try:
            aggregator.aggregate_date(target)
            detector.check_date(target)
        except Exception as e:
            logger.error(f"Aggregation/anomaly detection failed for {target}: {e}")

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
