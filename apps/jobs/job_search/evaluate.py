"""Evaluate job postings using Claude."""

import json
from pathlib import Path

import anthropic

from job_search.models import Evaluation, JobPosting

CRITERIA_PATH = Path(__file__).parent / "criteria.md"
RESUME_PATH = Path(__file__).parent / "resume.md"


def load_criteria() -> str:
    return CRITERIA_PATH.read_text()


def load_resume() -> str:
    return RESUME_PATH.read_text()


def evaluate_job(
    client: anthropic.Anthropic,
    job: JobPosting,
    criteria: str,
    resume: str,
) -> Evaluation:
    """Use Claude to evaluate a single job against criteria and resume."""
    salary_str = "Not listed"
    if job.salary_min and job.salary_max:
        salary_str = f"${job.salary_min:,.0f} - ${job.salary_max:,.0f}"
    elif job.salary_min:
        salary_str = f"${job.salary_min:,.0f}+"

    # Truncate description to keep costs reasonable
    description = job.description[:6000]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        messages=[
            {
                "role": "user",
                "content": f"""You are evaluating a job posting for fit against a candidate's criteria and resume.

## Candidate Criteria
{criteria}

## Candidate Resume (summary)
{resume}

## Job Posting
**Company:** {job.company}
**Title:** {job.title}
**Location:** {job.location}
**Remote:** {"Yes" if job.is_remote else "No"}
**Salary:** {salary_str}
**Source:** {job.source}
**URL:** {job.url}

**Description:**
{description}

## Instructions
Evaluate this job against the criteria and resume. Return ONLY valid JSON (no markdown fences):
{{
  "score": <1-10>,
  "summary": "<2-3 sentence summary of what this role is>",
  "fit_reasons": ["<reason 1>", "<reason 2>"],
  "concerns": ["<concern 1>", "<concern 2>"],
  "recommendation": "<apply|review|skip>",
  "tier": "<director|ic>"
}}

Score guidance:
- 9-10: Nearly perfect match. Recommend "apply".
- 7-8: Strong match with minor gaps. Recommend "apply".
- 5-6: Decent match, needs manual review. Recommend "review".
- 1-4: Poor fit. Recommend "skip".

Set tier to "director" if the role is Director/Head/VP level, "ic" if Analytics Engineer / Lead / Senior / Staff / Principal level.
""",
            }
        ],
    )

    result = json.loads(response.content[0].text)
    return Evaluation(**result)


def evaluate_batch(
    jobs: list[JobPosting],
    criteria: str,
    resume: str,
    api_key: str | None = None,
) -> list[tuple[JobPosting, Evaluation]]:
    """Evaluate a batch of jobs sequentially."""
    client = anthropic.Anthropic(api_key=api_key)
    results = []

    for i, job in enumerate(jobs, 1):
        print(f"  [{i}/{len(jobs)}] {job.title} @ {job.company}...", end=" ")
        try:
            evaluation = evaluate_job(client, job, criteria, resume)
            results.append((job, evaluation))
            print(f"Score: {evaluation.score}/10 ({evaluation.recommendation})")
        except Exception as e:
            print(f"FAILED: {e}")

    return results
