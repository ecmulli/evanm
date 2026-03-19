"""Job search using python-jobspy."""

import hashlib
import re

import pandas as pd
from jobspy import scrape_jobs

from job_search.models import JobPosting

# Search queries targeting Evan's role types.
# Quoted strings force exact phrase match on Indeed (otherwise it matches any word).
SEARCH_QUERIES = [
    '"analytics engineer"',
    '"senior analytics engineer"',
    '"lead analytics engineer"',
    '"staff analytics engineer"',
    '"principal analytics engineer"',
    '"founding analytics engineer"',
    '"head of data"',
    '"head of analytics"',
    '"director of data"',
    '"director of analytics"',
    '"VP of analytics"',
    '"VP of data"',
]

# Indeed + LinkedIn. ZipRecruiter rate-limits aggressively.
# Google returns 0 results for job searches via jobspy.
DEFAULT_SITES = ["indeed", "linkedin"]

# Titles that pass the cheap pre-filter.
# These are regex patterns matched against the full title (case-insensitive).
TITLE_INCLUDE_PATTERNS = [
    r"analytics engineer",
    r"head of (data|analytics)",
    r"director.*(data|analytics)",
    r"vp.*(data|analytics)",
    r"vice president.*(data|analytics)",
    r"(data|analytics).*(director|head|vp|vice president|lead|manager)",
    r"(senior|lead|staff|principal|founding).*(data|analytics)",
    r"data scientist",
    r"data science.*(director|head|lead|manager)",
    r"business intelligence",
]

# Titles to exclude even if they match above (clearly wrong roles).
TITLE_EXCLUDE_PATTERNS = [
    r"intern\b",
    r"entry level",
    r"junior",
    r"data center",          # physical data centers, not data roles
    r"data entry",
    r"database admin",
    r"data governance",      # compliance-heavy, not analytics
    r"data architect",       # infra-heavy, not analytics
    r"data collection",
    r"data verification",
    r"data quality",         # QA-focused, not analytics
    r"data integrity",
    r"data mining",
    r"data security",
    r"data domain lead",
    r"product manage",       # product managers mentioning data
    r"software engineer",
    r"account (exec|director)",
    r"sales",
    r"recruiter",
    r"nurse|physician|medical|dental|teacher|professor|custodian",
    r"cybersecurity|security engineer|cyber defense",
    r"ssd|hardware",
    r"construction|facilities|mechanical|electrical engineer",
    r"forward deployed",
    r"enrollment",           # education enrollment, not tech
    r"compliance",
    r"prospect management",
    r"visualization.experience",  # UX roles, not analytics
    r"data partnerships",
]

_include_re = [re.compile(p, re.IGNORECASE) for p in TITLE_INCLUDE_PATTERNS]
_exclude_re = [re.compile(p, re.IGNORECASE) for p in TITLE_EXCLUDE_PATTERNS]


def _make_job_id(row: pd.Series) -> str:
    """Create a stable unique ID from source + job URL."""
    raw = f"{row.get('site', 'unknown')}:{row.get('job_url', '')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _make_dedup_key(title: str, company: str) -> str:
    """Create a key for deduplicating same job posted multiple times/locations."""
    # Normalize: lowercase, strip whitespace, remove common suffixes
    t = re.sub(r"\s+", " ", title.lower().strip())
    c = re.sub(r"\s+", " ", company.lower().strip())
    # Remove location suffixes like "... in New York, NY"
    t = re.sub(r"\s*(in|at|-)?\s*[\w\s,]+,\s*[A-Z]{2}\s*$", "", t)
    return f"{c}:{t}"


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
    """Pre-filter by title. Must match an include pattern and not match any exclude."""
    if any(p.search(title) for p in _exclude_re):
        return False
    return any(p.search(title) for p in _include_re)


def fetch_jobs(
    queries: list[str] | None = None,
    sites: list[str] | None = None,
    results_per_query: int = 50,
    hours_old: int = 72,
) -> list[JobPosting]:
    """Search for jobs using python-jobspy across multiple queries.

    Returns deduplicated list of JobPostings that pass the title pre-filter.

    Note on Indeed filter conflicts: Indeed only supports ONE of hours_old,
    is_remote/job_type, or easy_apply. We use hours_old and skip is_remote
    to avoid the conflict. Remote filtering happens via Claude evaluation.
    """
    queries = queries or SEARCH_QUERIES
    sites = sites or DEFAULT_SITES
    all_jobs: dict[str, JobPosting] = {}  # keyed by URL hash for dedup
    seen_dedup_keys: dict[str, str] = {}  # company+title -> first job ID

    for query in queries:
        print(f"  Searching: {query} on {', '.join(sites)}...")
        try:
            df = scrape_jobs(
                site_name=sites,
                search_term=query,
                location="United States",
                results_wanted=results_per_query,
                hours_old=hours_old,
                country_indeed="USA",
                enforce_annual_salary=True,
                description_format="markdown",
            )

            if df is None or df.empty:
                print(f"    No results")
                continue

            count = 0
            for _, row in df.iterrows():
                posting = _row_to_posting(row)
                if posting is None:
                    continue
                if not title_passes_prefilter(posting.title):
                    continue
                # Dedup by URL hash
                if posting.id in all_jobs:
                    continue
                # Dedup by company+title (catches same job posted to multiple locations)
                dedup_key = _make_dedup_key(posting.title, posting.company)
                if dedup_key in seen_dedup_keys:
                    continue
                seen_dedup_keys[dedup_key] = posting.id
                all_jobs[posting.id] = posting
                count += 1

            print(f"    {count} new matching jobs")

        except Exception as e:
            print(f"    ! Error: {e}")

    return list(all_jobs.values())
