"""
Main entry point for the jobs package.

Usage:
    python -m jobs              # Run all scheduled jobs
    python -m jobs --dev        # Run in development mode
    python -m jobs --job <name> # Run a specific job
"""

import argparse
import sys
from pathlib import Path

# Add the package root to the path
package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

from jobs.config import load_config
from jobs.scheduler import JobScheduler


def main():
    parser = argparse.ArgumentParser(description="Run scheduled jobs")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    parser.add_argument("--job", type=str, help="Run a specific job by name")
    parser.add_argument("--list", action="store_true", help="List all available jobs")
    parser.add_argument(
        "--once", action="store_true", help="Run all jobs once and exit"
    )
    parser.add_argument(
        "--duration", type=int, help="Run scheduler for N seconds then exit"
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(dev_mode=args.dev)

    # Initialize scheduler
    scheduler = JobScheduler(config)

    if args.list:
        scheduler.list_jobs()
        return

    if args.job:
        scheduler.run_job(args.job)
    elif args.once:
        results = scheduler.run_once()
        print(f"\nJob Results:")
        for job_name, success in results.items():
            status = (
                "✅ Success"
                if success
                else "❌ Failed" if success is False else "⏭️ Skipped"
            )
            print(f"  {job_name}: {status}")
    elif args.duration:
        scheduler.run_for_duration(args.duration)
    else:
        scheduler.run_all()


if __name__ == "__main__":
    main()
