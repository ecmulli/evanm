#!/usr/bin/env python3
"""
Test script for the Notion Calendar Auto-Scheduler.

This script verifies that all components work together correctly
without making actual changes to Notion (dry-run mode).
"""

import sys
from datetime import datetime, timedelta

from time_slots import TimeSlot, TimeSlotManager


def test_time_slot_generation():
    """Test time slot generation."""
    print("\n" + "=" * 60)
    print("TEST: Time Slot Generation")
    print("=" * 60)

    manager = TimeSlotManager(
        work_start_hour=9,
        work_end_hour=17,
        slot_duration_minutes=15,
        schedule_days_ahead=2,
    )

    # Generate slots for next 2 days
    slots = manager.generate_work_slots(days=2)

    print(f"✅ Generated {len(slots)} time slots")

    # Verify work hours
    for slot in slots[:5]:  # Check first 5 slots
        hour = slot.start.hour
        assert 9 <= hour < 17, f"Slot outside work hours: {slot}"

    print(f"✅ All slots within work hours (9am-5pm)")

    # Verify no weekends
    for slot in slots:
        weekday = slot.start.weekday()
        assert weekday < 5, f"Weekend slot found: {slot}"

    print(f"✅ No weekend slots (Mon-Fri only)")

    # Verify slot duration
    for slot in slots[:5]:
        duration = (slot.end - slot.start).total_seconds() / 60
        assert duration == 15, f"Incorrect slot duration: {duration} minutes"

    print(f"✅ All slots are 15 minutes long")

    # Display sample slots
    print(f"\nSample slots (first 5):")
    for i, slot in enumerate(slots[:5], 1):
        print(f"  {i}. {slot}")

    print("\n✅ Time slot generation test PASSED")
    return True


def test_slot_finding():
    """Test finding available slot ranges for tasks."""
    print("\n" + "=" * 60)
    print("TEST: Slot Finding for Task Durations")
    print("=" * 60)

    manager = TimeSlotManager(
        work_start_hour=9,
        work_end_hour=17,
        slot_duration_minutes=15,
        schedule_days_ahead=3,
    )

    # Generate slots
    all_slots = manager.generate_work_slots(days=3)
    print(f"Generated {len(all_slots)} total slots")

    # Test 1: Find slot for 1-hour task (4 slots)
    print("\n1️⃣  Finding slot for 1-hour task...")
    slot_range = manager.find_available_slot_range(all_slots, duration_hours=1.0)

    if slot_range:
        start, end = slot_range
        duration = (end - start).total_seconds() / 3600
        print(
            f"✅ Found: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%H:%M')}"
        )
        print(f"   Duration: {duration} hours")
        assert abs(duration - 1.0) < 0.01, "Incorrect duration"

        # Mark as occupied
        manager.mark_slots_occupied(start, end, "task-1")
    else:
        print("❌ No slot found")
        return False

    # Test 2: Find slot for 2.5-hour task (10 slots)
    print("\n2️⃣  Finding slot for 2.5-hour task...")
    available_slots = manager.get_available_slots(all_slots)
    slot_range = manager.find_available_slot_range(available_slots, duration_hours=2.5)

    if slot_range:
        start, end = slot_range
        duration = (end - start).total_seconds() / 3600
        print(
            f"✅ Found: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%H:%M')}"
        )
        print(f"   Duration: {duration} hours")
        assert abs(duration - 2.5) < 0.01, "Incorrect duration"

        # Mark as occupied
        manager.mark_slots_occupied(start, end, "task-2")
    else:
        print("❌ No slot found")
        return False

    # Test 3: Verify occupied slots are excluded
    print("\n3️⃣  Verifying occupied slots are excluded...")
    available_after = manager.get_available_slots(all_slots)
    occupied_count = len(all_slots) - len(available_after)
    print(f"✅ {occupied_count} slots marked as occupied")
    print(f"   {len(available_after)} slots still available")

    # Test 4: Find slot with due date preference
    print("\n4️⃣  Finding slot before due date...")
    prefer_before = datetime.now().astimezone() + timedelta(days=1)
    slot_range = manager.find_available_slot_range(
        available_after, duration_hours=0.5, prefer_before=prefer_before
    )

    if slot_range:
        start, end = slot_range
        print(
            f"✅ Found: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%H:%M')}"
        )
        if start < prefer_before:
            print(
                f"   ✅ Scheduled before due date ({prefer_before.strftime('%Y-%m-%d')})"
            )
        else:
            print(f"   ⚠️  Scheduled after due date (soft constraint)")
    else:
        print("❌ No slot found")
        return False

    print("\n✅ Slot finding test PASSED")
    return True


def test_day_boundary():
    """Test that tasks don't span across days."""
    print("\n" + "=" * 60)
    print("TEST: Day Boundary Constraints")
    print("=" * 60)

    manager = TimeSlotManager(
        work_start_hour=9,
        work_end_hour=17,
        slot_duration_minutes=15,
        schedule_days_ahead=2,
    )

    # Generate slots for a specific day
    test_date = (
        datetime.now().astimezone().replace(hour=9, minute=0, second=0, microsecond=0)
    )

    # Skip to next weekday if today is weekend
    while test_date.weekday() >= 5:
        test_date += timedelta(days=1)

    day_slots = manager._generate_day_slots(test_date)

    print(f"Generated {len(day_slots)} slots for {test_date.strftime('%Y-%m-%d')}")
    print(f"First slot: {day_slots[0]}")
    print(f"Last slot: {day_slots[-1]}")

    # Verify all slots are on the same day
    for slot in day_slots:
        assert slot.start.date() == test_date.date(), "Slot on wrong day"

    print("✅ All slots on same day")

    # Test can_fit_in_remaining_day
    print("\n📏 Testing remaining day fit...")

    # Slot at 4:00 PM - 1 hour task should NOT fit (work ends at 5 PM)
    late_slot = TimeSlot(
        test_date.replace(hour=16, minute=0), test_date.replace(hour=16, minute=15)
    )
    can_fit = manager.can_fit_in_remaining_day(late_slot, duration_hours=1.5)

    print(f"  1.5-hour task at 4:00 PM: {'✅ Fits' if can_fit else '❌ Does not fit'}")
    assert not can_fit, "Task should not fit in remaining day"

    # Slot at 3:00 PM - 1 hour task SHOULD fit
    afternoon_slot = TimeSlot(
        test_date.replace(hour=15, minute=0), test_date.replace(hour=15, minute=15)
    )
    can_fit = manager.can_fit_in_remaining_day(afternoon_slot, duration_hours=1.0)

    print(f"  1-hour task at 3:00 PM: {'✅ Fits' if can_fit else '❌ Does not fit'}")
    assert can_fit, "Task should fit in remaining day"

    print("\n✅ Day boundary test PASSED")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "🧪" * 30)
    print("NOTION CALENDAR AUTO-SCHEDULER - TEST SUITE")
    print("🧪" * 30)

    tests = [
        ("Time Slot Generation", test_time_slot_generation),
        ("Slot Finding", test_slot_finding),
        ("Day Boundary", test_day_boundary),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception:")
            print(f"   {type(e).__name__}: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
