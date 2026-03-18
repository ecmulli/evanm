"""Job search using python-jobspy."""

import hashlib
from datetime import datetime

import pandas as pd
from jobspy import scrape_jobs

from job_search.models import JobPosting

# Search queries targeting Evan's role types
SEARCH_QUERIES = [
    "director of data",
    "director of analytics",
    "head of data",
    "head of analytics",
    "VP analytics",
    "analytics engineer",
    "senior analytics engineer",
    "lead analytics engineer",
    "founding analytics engineer",
    "principal analytics engineer",
    "staff analytics engineer",
]

# Sites to search (skip linkedin by default — aggressive rate limiting without proxies)
DEFAULT_SITES = ["indeed", "zip_recruiter", "google"]

# Titles that pass the cheap pre-filter (lowercase substrings)
TITLE_KEYWORDS = [
    "data",
    "analytics",
    "business intelligence",
    "bi ",
    " bi",
]

# Titles to exclude (clearly wrong roles)
TITLE_EXCLUDES = [
    "intern",
    "entry level",
    "junior",
    "nurse",
    "physician",
    "medical",
    "dental",
    "teacher",
    "instructor",
    "professor",
    "custodian",
    "warehouse",  # physical warehouse, not data warehouse
]


def _make_job_id(row: pd.Series) -> str:
    """Create a stable unique ID from source + job URL."""
    raw = f"{row.get('site', 'unknown')}:{row.get('job_url', '')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _row_to_posting(row: pd.Series) -> JobPosting | None:
    """Convert a jobspy DataFrame row to a JobPosting model."""
    try:
        url = str(row.get("job_url", ""))
        if not url or url == "nan":
            return None

        description = str(row.get("description", ""))
        if not description or description == "nan":
            description = ""

        title = str(row.get("title", ""))
        company = str(row.get("company", ""))
        if not title or title == "nan" or not company or company == "nan":
            return None

        # Parse location
        city = str(row.get("city", "")) if pd.notna(row.get("city")) else ""
        state = str(row.get("state", "")) if pd.notna(row.get("state")) else ""
        location_parts = [p for p in [city, state] if p]
        location = ", ".join(location_parts) if location_parts else "Unknown"

        # Parse salary
        salary_min = row.get("min_amount") if pd.notna(row.get("min_amount")) else None
        salary_max = row.get("max_amount") if pd.notna(row.get("max_amount")) else None
        currency = str(row.get("currency", "")) if pd.notna(row.get("currency")) else None

        # Parse date
        date_posted = None
        if pd.notna(row.get("date_posted")):
            try:
                date_posted = pd.to_datetime(row["date_posted"]).to_pydatetime()
            except Exception:
                pass

        return JobPosting(
            id=_make_job_id(row),
            source=str(row.get("site", "unknown")),
            company=company,
            title=title,
            location=location,
            url=url,
            description=description,
            is_remote=bool(row.get("is_remote", False)),
            salary_min=float(salary_min) if salary_min is not None else None,
            salary_max=float(salary_max) if salary_max is not None else None,
            salary_currency=currency if currency and currency != "nan" else None,
            date_posted=date_posted,
        )
    except Exception as e:
        print(f"  ! Failed to parse row: {e}")
        return None


def title_passes_prefilter(title: str) -> bool:
    """Cheap pre-filter: does this title look like a data/analytics role?"""
    lower = title.lower()
    if any(ex in lower for ex in TITLE_EXCLUDES):
        return False
    return any(kw in lower for kw in TITLE_KEYWORDS)


def fetch_jobs(
    queries: list[str] | None = None,
    sites: list[str] | None = None,
    results_per_query: int = 25,
    hours_old: int = 24,
) -> list[JobPosting]:
    """Search for jobs using python-jobspy across multiple queries.

    Returns deduplicated list of JobPostings that pass the title pre-filter.
    """
    queries = queries or SEARCH_QUERIES
    sites = sites or DEFAULT_SITES
    all_jobs: dict[str, JobPosting] = {}  # keyed by ID for dedup

    for query in queries:
        print(f"  Searching: '{query}' on {', '.join(sites)}...")
        try:
            df = scrape_jobs(
                site_name=sites,
                search_term=query,
                location="USA",
                results_wanted=results_per_query,
                hours_old=hours_old,
                country_indeed="USA",
                is_remote=True,
                enforce_annual_salary=True,
                description_format="markdown",
            )

            if df is None or df.empty:
                print(f"    No results for '{query}'")
                continue

            count = 0
            for _, row in df.iterrows():
                posting = _row_to_posting(row)
                if posting is None:
                    continue
                if not title_passes_prefilter(posting.title):
                    continue
                if posting.id not in all_jobs:
                    all_jobs[posting.id] = posting
                    count += 1

            print(f"    Found {count} new matching jobs")

        except Exception as e:
            print(f"    ! Error searching '{query}': {e}")

    return list(all_jobs.values())
