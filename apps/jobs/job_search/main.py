"""
Nightly job search automation.

Usage:
    cd apps/jobs
    uv run python -m job_search
    uv run python -m job_search --dry-run  # Skip Notion writes
"""

import asyncio
from datetime import datetime, timezone

from job_search.config import Settings
from job_search.evaluate import evaluate_batch, load_criteria, load_resume
from job_search.models import EvaluatedJob
from job_search.notion_db import NotionJobDB
from job_search.search import fetch_jobs


async def main(dry_run: bool = False):
    settings = Settings()
    criteria = load_criteria()
    resume = load_resume()

    # Initialize Notion
    notion = NotionJobDB(settings.notion_token, settings.notion_database_id)

    # Step 1: Fetch and pre-filter jobs from all sources
    print("Fetching jobs from job boards...")
    all_jobs = fetch_jobs()
    print(f"\nAfter search + title pre-filter: {len(all_jobs)} jobs")

    if not all_jobs:
        print("\nNo matching jobs found. Try broadening search queries.")
        return

    # Step 2: Deduplicate against Notion
    print("\nChecking Notion for already-seen jobs...")
    seen_ids = await notion.get_seen_ids()
    new_jobs = [j for j in all_jobs if j.id not in seen_ids]
    print(f"New jobs to evaluate: {len(new_jobs)} ({len(all_jobs) - len(new_jobs)} already seen)")

    if not new_jobs:
        print("\nNo new jobs to evaluate. All caught up!")
        return

    # Step 3: Evaluate with Claude
    print(f"\nEvaluating {len(new_jobs)} jobs with Claude...")
    evaluated = evaluate_batch(new_jobs, criteria, resume, api_key=settings.anthropic_api_key)

    # Step 4: Sort by score and write to Notion
    evaluated.sort(key=lambda x: x[1].score, reverse=True)

    now = datetime.now(timezone.utc)
    top_matches = []

    for job, eval_result in evaluated:
        evaluated_job = EvaluatedJob(
            posting=job,
            evaluation=eval_result,
            seen_at=now,
        )

        if not dry_run:
            try:
                await notion.add_job(evaluated_job)
            except Exception as e:
                print(f"  ! Failed to write to Notion: {job.title} @ {job.company}: {e}")

        if eval_result.score >= 7:
            top_matches.append(evaluated_job)

    # Step 5: Print summary
    print(f"\n{'=' * 60}")
    print("RESULTS SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total from search:  {len(all_jobs)}")
    print(f"New (unseen):       {len(new_jobs)}")
    print(f"Evaluated:          {len(evaluated)}")
    print(f"Top matches (7+):   {len(top_matches)}")

    if top_matches:
        print(f"\nTOP MATCHES (score >= 7):")
        print(f"{'-' * 60}")
        for match in top_matches:
            p = match.posting
            e = match.evaluation
            print(f"\n  [{e.score}/10] {p.title} @ {p.company}")
            print(f"  Location: {p.location} {'(Remote)' if p.is_remote else ''}")
            print(f"  URL: {p.url}")
            print(f"  {e.summary}")
            if p.salary_min:
                sal = f"${p.salary_min:,.0f}"
                if p.salary_max:
                    sal += f" - ${p.salary_max:,.0f}"
                print(f"  Salary: {sal}")
            print(f"  Fit: {', '.join(e.fit_reasons[:2])}")
            if e.concerns:
                print(f"  Concerns: {', '.join(e.concerns[:2])}")
            print(f"  Resume tier: {e.tier}")
    else:
        print("\nNo strong matches today. Check back tomorrow!")

    if dry_run:
        print("\n[DRY RUN - nothing written to Notion]")
