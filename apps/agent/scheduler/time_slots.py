#!/usr/bin/env python3
"""
Time Slot Management

Generates and manages 15-minute time slots during work hours (9am-5pm, Mon-Fri).
Handles slot availability tracking and task duration fitting.
"""

import logging
from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple


class TimeSlot:
    """Represents a 15-minute time slot."""

    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end
        self.is_available = True

    def __repr__(self):
        return f"TimeSlot({self.start.strftime('%Y-%m-%d %H:%M')} - {self.end.strftime('%H:%M')})"

    def __eq__(self, other):
        return self.start == other.start and self.end == other.end

    def __hash__(self):
        return hash((self.start, self.end))


class TimeSlotManager:
    """Manages time slots for scheduling tasks."""

    def __init__(
        self,
        work_start_hour: int = 9,
        work_end_hour: int = 17,
        slot_duration_minutes: int = 15,
        schedule_days_ahead: int = 7,
    ):
        self.work_start_hour = work_start_hour
        self.work_end_hour = work_end_hour
        self.slot_duration_minutes = slot_duration_minutes
        self.schedule_days_ahead = schedule_days_ahead
        self.logger = logging.getLogger(__name__)

        # Track occupied slots (slot -> task_id mapping)
        self.occupied_slots = {}

    def generate_work_slots(
        self, start_date: Optional[datetime] = None, days: Optional[int] = None
    ) -> List[TimeSlot]:
        """
        Generate 15-minute time slots during work hours for the next N days.

        Args:
            start_date: Starting datetime (defaults to now)
            days: Number of days ahead (defaults to schedule_days_ahead)

        Returns:
            List of TimeSlot objects during work hours (Mon-Fri only)
        """
        if start_date is None:
            # Use local timezone (matches Notion's display timezone)
            start_date = datetime.now().astimezone()

        if days is None:
            days = self.schedule_days_ahead

        slots = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = current_date + timedelta(days=days)

        while current_date < end_date:
            # Skip weekends (0=Monday, 6=Sunday)
            if current_date.weekday() < 5:  # Monday to Friday
                # Generate slots for this day
                slots.extend(self._generate_day_slots(current_date))

            current_date += timedelta(days=1)

        # Filter out slots that are in the past
        now = datetime.now().astimezone()
        slots = [slot for slot in slots if slot.start >= now]

        return slots

    def _generate_day_slots(self, date: datetime) -> List[TimeSlot]:
        """Generate all time slots for a single work day."""
        slots = []

        # Start at work_start_hour
        current_time = date.replace(
            hour=self.work_start_hour, minute=0, second=0, microsecond=0
        )

        # End at work_end_hour
        end_time = date.replace(
            hour=self.work_end_hour, minute=0, second=0, microsecond=0
        )

        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=self.slot_duration_minutes)
            slots.append(TimeSlot(current_time, slot_end))
            current_time = slot_end

        return slots

    def find_available_slot_range(
        self,
        slots: List[TimeSlot],
        duration_hours: float,
        prefer_before: Optional[datetime] = None,
    ) -> Optional[Tuple[datetime, datetime]]:
        """
        Find a contiguous range of available slots that can fit the task duration.

        Args:
            slots: List of available time slots
            duration_hours: Task duration in hours
            prefer_before: Prefer slots before this datetime (soft constraint)

        Returns:
            Tuple of (start_time, end_time) or None if no suitable range found
        """
        # Convert duration to number of slots needed
        slots_needed = max(1, int((duration_hours * 60) / self.slot_duration_minutes))

        self.logger.debug(
            f"Looking for {slots_needed} slots ({duration_hours}h) "
            f"in {len(slots)} available slots"
        )

        # Try to find contiguous slots before the preferred date first
        if prefer_before:
            before_slots = [s for s in slots if s.start < prefer_before]
            result = self._find_contiguous_slots(before_slots, slots_needed)
            if result:
                return result

            # Log that we're scheduling after the preferred date
            self.logger.info(
                f"No slots available before {prefer_before.strftime('%Y-%m-%d')}, "
                f"scheduling after due date"
            )

        # If no preference or no slots before preference, find any available slots
        return self._find_contiguous_slots(slots, slots_needed)

    def _find_contiguous_slots(
        self, slots: List[TimeSlot], slots_needed: int
    ) -> Optional[Tuple[datetime, datetime]]:
        """Find N contiguous available slots."""
        if not slots:
            return None

        # Look for contiguous available slots
        i = 0
        while i <= len(slots) - slots_needed:
            # Check if we have slots_needed contiguous slots starting at i
            is_contiguous = True
            current_end = slots[i].end

            for j in range(1, slots_needed):
                # Check if next slot starts immediately after current slot ends
                if i + j >= len(slots):
                    is_contiguous = False
                    break

                next_slot = slots[i + j]
                if next_slot.start != current_end:
                    is_contiguous = False
                    break

                # Check if slot crosses into next day and it's a weekend
                if next_slot.start.date() != slots[i].start.date():
                    # Don't allow tasks to span across days
                    is_contiguous = False
                    break

                current_end = next_slot.end

            if is_contiguous:
                start_time = slots[i].start
                end_time = slots[i + slots_needed - 1].end
                return (start_time, end_time)

            i += 1

        return None

    def can_fit_in_remaining_day(
        self, start_slot: TimeSlot, duration_hours: float
    ) -> bool:
        """
        Check if a task can fit in the remaining work hours of the day.

        Args:
            start_slot: The starting time slot
            duration_hours: Task duration in hours

        Returns:
            True if task fits in remaining day, False otherwise
        """
        task_end = start_slot.start + timedelta(hours=duration_hours)

        # Check if task end is on the same day and before work end time
        same_day = task_end.date() == start_slot.start.date()

        work_end = start_slot.start.replace(
            hour=self.work_end_hour, minute=0, second=0, microsecond=0
        )

        before_work_end = task_end <= work_end

        return same_day and before_work_end

    def mark_slots_occupied(
        self, start_time: datetime, end_time: datetime, task_id: str
    ):
        """Mark a time range as occupied by a task."""
        # Generate slots for this time range
        current = start_time
        while current < end_time:
            slot = TimeSlot(
                current,
                min(current + timedelta(minutes=self.slot_duration_minutes), end_time),
            )
            self.occupied_slots[slot] = task_id
            current += timedelta(minutes=self.slot_duration_minutes)

    def get_available_slots(self, all_slots: List[TimeSlot]) -> List[TimeSlot]:
        """Filter slots to return only available (unoccupied) ones."""
        available = []
        for slot in all_slots:
            # Check if this slot or any overlapping slot is occupied
            is_available = True
            for occupied_slot in self.occupied_slots.keys():
                if self._slots_overlap(slot, occupied_slot):
                    is_available = False
                    break

            if is_available:
                available.append(slot)

        return available

    def _slots_overlap(self, slot1: TimeSlot, slot2: TimeSlot) -> bool:
        """Check if two time slots overlap."""
        return slot1.start < slot2.end and slot1.end > slot2.start

    def clear_occupied_slots(self):
        """Clear all occupied slots (useful for rescheduling from scratch)."""
        self.occupied_slots.clear()
