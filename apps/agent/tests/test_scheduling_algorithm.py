import sys
from datetime import datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

# Provide a lightweight stub so the scheduler module can import notion_client
sys.modules.setdefault("notion_client", SimpleNamespace(Client=object))

from apps.agent.scheduler.scheduling_algorithm import TaskScheduler
from apps.agent.scheduler.time_slots import TimeSlotManager


def _build_task(
    task_id: str,
    rank: float,
    duration_hours: float,
    scheduled_window: tuple[datetime, datetime] | None = None,
    blocked_by: list[str] | None = None,
):
    """Create a minimal Notion-style task payload for testing."""
    date_prop = {"type": "date", "date": None}
    if scheduled_window:
        start, end = scheduled_window
        date_prop["date"] = {"start": start.isoformat(), "end": end.isoformat()}

    relation_prop = {"type": "relation", "relation": []}
    if blocked_by:
        relation_prop["relation"] = [{"id": rel_id} for rel_id in blocked_by]

    return {
        "id": task_id,
        "properties": {
            "Task name": {"type": "title", "title": [{"plain_text": task_id}]},
            "Rank": {"type": "number", "number": rank},
            "Est Duration Hrs": {"type": "number", "number": duration_hours},
            "Due date": {"type": "date", "date": None},
            "Scheduled Date": date_prop,
            "Status": {"type": "status", "status": {"name": "Todo"}},
            "Blocked by": relation_prop,
        },
    }


def test_skipped_task_preserves_existing_schedule():
    """A task skipped due to blockers should still reserve its original slot."""
    tz = ZoneInfo("UTC")
    manager = TimeSlotManager(
        work_start_hour=9,
        work_end_hour=13,
        slot_duration_minutes=60,
        schedule_days_ahead=2,
        timezone="UTC",
    )
    scheduler = TaskScheduler(None, "db", manager, dry_run=True)

    base_day = datetime.now(tz)
    next_morning = base_day.replace(hour=9, minute=0, second=0, microsecond=0)
    if next_morning <= base_day:
        next_morning = next_morning + timedelta(days=1)
    blocked_start = next_morning
    blocked_end = blocked_start + timedelta(hours=1)

    blocked_task = _build_task(
        "blocked", 1, 1.0, (blocked_start, blocked_end), blocked_by=["blocker"]
    )
    other_task = _build_task("other", 2, 1.0)
    blocker_task = _build_task("blocker", 3, 1.0)

    stats = scheduler.schedule_tasks([blocked_task, other_task, blocker_task])

    assert stats["skipped"] == 1
    assert stats["scheduled"] == 2

    same_day_entries = sorted(
        [
            (slot.start, slot.end, task_id)
            for slot, task_id in manager.occupied_slots.items()
            if slot.start.date() == blocked_start.date()
        ],
        key=lambda entry: entry[0],
    )

    # The skipped task should still own its previously booked slot
    assert same_day_entries[0][2] == "blocked"
    assert same_day_entries[0][0] == blocked_start
    assert same_day_entries[0][1] == blocked_end

    # The next schedulable task must start after the blocked window
    assert same_day_entries[1][2] == "other"
    assert same_day_entries[1][0] == blocked_end
    assert same_day_entries[2][2] == "blocker"
