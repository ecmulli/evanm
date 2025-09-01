"""
Jobs package for scheduled automation tasks.

This package provides a framework for running scheduled jobs and automation tasks.
"""

__version__ = "1.0.0"
__author__ = "Evan Mullins"

from .base_job import BaseJob
from .scheduler import JobScheduler

__all__ = ["JobScheduler", "BaseJob"]
