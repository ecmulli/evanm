from pydantic import BaseModel
from datetime import datetime


class JobPosting(BaseModel):
    """Raw job posting from python-jobspy."""

    id: str
    source: str  # indeed, linkedin, glassdoor, zip_recruiter, google
    company: str
    title: str
    location: str
    url: str
    description: str
    is_remote: bool = False
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    date_posted: datetime | None = None


class Evaluation(BaseModel):
    """Claude's evaluation of a job posting."""

    score: int  # 1-10
    summary: str
    fit_reasons: list[str]
    concerns: list[str]
    recommendation: str  # apply, review, skip
    tier: str  # director, ic


class EvaluatedJob(BaseModel):
    """A job posting with its evaluation."""

    posting: JobPosting
    evaluation: Evaluation
    seen_at: datetime
    status: str = "new"
