"""Notion integration for tracking seen/evaluated jobs."""

import httpx

from job_search.models import EvaluatedJob

NOTION_API = "https://api.notion.com/v1"


class NotionJobDB:
    def __init__(self, token: str, database_id: str):
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    async def get_seen_ids(self) -> set[str]:
        """Get all job IDs already in the database."""
        seen = set()
        has_more = True
        start_cursor = None

        async with httpx.AsyncClient() as client:
            while has_more:
                body: dict = {"page_size": 100}
                if start_cursor:
                    body["start_cursor"] = start_cursor

                resp = await client.post(
                    f"{NOTION_API}/databases/{self.database_id}/query",
                    headers=self.headers,
                    json=body,
                    timeout=30.0,
                )
                resp.raise_for_status()
                data = resp.json()

                for page in data.get("results", []):
                    title_prop = page["properties"].get("Job ID", {})
                    if title_prop.get("title"):
                        seen.add(title_prop["title"][0]["plain_text"])

                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")

        return seen

    async def add_job(self, job: EvaluatedJob) -> None:
        """Add an evaluated job to the Notion database."""
        p = job.posting
        e = job.evaluation

        properties: dict = {
            "Job ID": {"title": [{"text": {"content": p.id}}]},
            "Company": {"rich_text": [{"text": {"content": p.company[:2000]}}]},
            "Title": {"rich_text": [{"text": {"content": p.title[:2000]}}]},
            "Score": {"number": e.score},
            "Recommendation": {"select": {"name": e.recommendation}},
            "Tier": {"select": {"name": e.tier}},
            "URL": {"url": p.url},
            "Status": {"select": {"name": "new"}},
            "Summary": {"rich_text": [{"text": {"content": e.summary[:2000]}}]},
            "Fit Reasons": {
                "rich_text": [
                    {"text": {"content": "\n".join(e.fit_reasons)[:2000]}}
                ]
            },
            "Concerns": {
                "rich_text": [
                    {"text": {"content": "\n".join(e.concerns)[:2000]}}
                ]
            },
            "Location": {"rich_text": [{"text": {"content": p.location[:2000]}}]},
            "Source": {"select": {"name": p.source}},
            "Remote": {"checkbox": p.is_remote},
            "Seen At": {"date": {"start": job.seen_at.isoformat()}},
        }

        if p.salary_min and p.salary_max:
            properties["Salary"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": f"${p.salary_min:,.0f} - ${p.salary_max:,.0f}"
                        }
                    }
                ]
            }
        elif p.salary_min:
            properties["Salary"] = {
                "rich_text": [{"text": {"content": f"${p.salary_min:,.0f}+"}}]
            }

        if p.date_posted:
            properties["Date Posted"] = {
                "date": {"start": p.date_posted.strftime("%Y-%m-%d")}
            }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{NOTION_API}/pages",
                headers=self.headers,
                json={
                    "parent": {"database_id": self.database_id},
                    "properties": properties,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
