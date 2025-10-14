"""
Task Scheduler Module

Auto-schedules Notion tasks into calendar time slots based on priority ranking.
"""

from .time_slots import TimeSlot, TimeSlotManager
from .scheduling_algorithm import TaskScheduler

__all__ = ["TimeSlot", "TimeSlotManager", "TaskScheduler"]

