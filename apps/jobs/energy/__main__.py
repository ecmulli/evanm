"""
Energy data collection entry point.

Usage:
    python -m apps.jobs.energy                                          # Normal collection run
    python -m apps.jobs.energy --backfill 30                            # Backfill last 30 days
    python -m apps.jobs.energy --start-date 2026-02-01                  # Backfill from date to today
    python -m apps.jobs.energy --start-date 2026-02-01 --end-date 2026-02-15  # Backfill date range
"""

import argparse
import logging
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .aggregator import Aggregator
from .anomaly_detector import AnomalyDetector
from .collector import Collector, fetch_and_store
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


def run_backfill(config: Config, db: Database, start_date: date, end_date: date):
    """
    Backfill historical data in 7-day chunks from the production and consumption meters.

    Phase 1: Fetch 15-min production and consumption intervals, 2 API calls per 7-day chunk.
             Rows are overwritten, so a backfill corrects old data.
    Phase 2: Aggregate daily summaries and run anomaly detection.

    Total API calls: 2 * ceil(N/7). 30 days = ~10 calls.
    Enphase keeps interval data for 2 years only.
    Rate limiter in EnphaseClient handles the 10 req/min limit automatically.
    """
    client = EnphaseClient(config, db)
    aggregator = Aggregator(db, config.timezone)
    detector = AnomalyDetector(db, config.timezone)
    tz = ZoneInfo(config.timezone)

    today = date.today()
    # Clamp end_date to today (can't fetch future data)
    if end_date > today:
        end_date = today

    days = (end_date - start_date).days

    logger.info(f"=== Backfilling {days} days ({start_date} to {end_date - timedelta(days=1)}) ===")

    CHUNK_DAYS = 7
    num_chunks = (days + CHUNK_DAYS - 1) // CHUNK_DAYS
    logger.info(f"Phase 1: Fetching production + consumption in {num_chunks} chunks of up to {CHUNK_DAYS} days...")

    failed = []
    chunk_start = start_date
    chunk_num = 0
    while chunk_start < end_date:
        chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS), end_date)
        chunk_num += 1

        start_at = int(datetime(chunk_start.year, chunk_start.month, chunk_start.day, tzinfo=tz).timestamp())
        end_at = int(datetime(chunk_end.year, chunk_end.month, chunk_end.day, tzinfo=tz).timestamp())

        logger.info(f"  Chunk {chunk_num}/{num_chunks}: {chunk_start} to {chunk_end - timedelta(days=1)}")
        try:
            r = fetch_and_store(client, db, tz, start_at, end_at, "week", overwrite=True)
            logger.info(
                f"    Production: {r['production']} ({r['production_wh'] / 1000:.1f} kWh) | "
                f"Consumption: {r['consumption']} ({r['consumption_wh'] / 1000:.1f} kWh)"
            )
        except Exception as e:
            logger.error(f"    Failed chunk {chunk_start}-{chunk_end}: {e}")
            failed.append(str(chunk_start))

        chunk_start = chunk_end

    # Phase 2: Aggregate and detect anomalies
    logger.info("Phase 2: Aggregating summaries and detecting anomalies...")
    for i in range(days):
        target = start_date + timedelta(days=i)
        try:
            aggregator.aggregate_date(target)
            detector.check_date(target)
        except Exception as e:
            logger.error(f"Aggregation/anomaly detection failed for {target}: {e}")

    if failed:
        logger.error(f"=== Backfill finished with {len(failed)} failed chunks: {', '.join(failed)} ===")
        sys.exit(1)
    logger.info("=== Backfill complete ===")


def main():
    parser = argparse.ArgumentParser(description="Energy data collection")
    parser.add_argument(
        "--backfill",
        type=int,
        metavar="DAYS",
        help="Backfill last N days of historical data",
    )
    parser.add_argument(
        "--start-date",
        type=date.fromisoformat,
        metavar="YYYY-MM-DD",
        help="Backfill start date (inclusive)",
    )
    parser.add_argument(
        "--end-date",
        type=date.fromisoformat,
        metavar="YYYY-MM-DD",
        help="Backfill end date (exclusive, defaults to today)",
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
        if args.start_date or args.backfill:
            if args.start_date:
                start = args.start_date
                end = args.end_date or date.today()
            else:
                end = date.today()
                start = end - timedelta(days=args.backfill)
            if start >= end:
                logger.error(f"start-date ({start}) must be before end-date ({end})")
                sys.exit(1)
            run_backfill(config, db, start, end)
        else:
            run_collection(config, db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
