#!/usr/bin/env python3
"""
Comprehensive tests for the AI Task Creation Agent

Tests intelligent parsing capabilities for priority, duration, workspace, and due date detection.
"""

import os
import sys

sys.path.append(os.path.dirname(__file__))

from task_creator import TaskCreationAgent


def test_intelligent_parsing():
    """Test the intelligent parsing features with various input examples."""

    # Initialize agent in dry run mode for testing
    agent = TaskCreationAgent(dry_run=True)

    test_cases = [
        {
            "name": "High Priority + Duration + Livepeer",
            "input": "This is urgent! The Livepeer analytics dashboard is broken and needs a 2 hour fix ASAP. Users can't see their streaming metrics.",
        },
        {
            "name": "Vanquish + Low Priority",
            "input": "Create a new marketing campaign template for Vanquish client. This is low priority, can do when time permits.",
        },
        {
            "name": "Quick Personal Task",
            "input": "Quick 15 minute task to update my personal portfolio website with the new project.",
        },
        {
            "name": "Full Day Task",
            "input": "Need to implement streaming optimization feature - this is a full day task, high priority for the video platform.",
        },
        {
            "name": "Default Values Test",
            "input": "Simple task with no specific context clues to test defaults.",
        },
        {
            "name": "Half Hour Client Work",
            "input": "Update the client's ad campaign settings - should take about 30 minutes for Vanquish.",
        },
        {
            "name": "Complex Task with Multiple Requirements",
            "input": "Build a new user onboarding flow for the Livepeer platform. This is high priority and should take about 8 hours. Need to cover signup, verification, dashboard tour, and first stream setup.",
        },
    ]

    print("🧪 Testing Intelligent Parsing Features")
    print("=" * 60)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        print("-" * 40)

        try:
            # Test just the synthesis (without creating task)
            task_info = agent.synthesize_task_info(
                text_inputs=[test_case["input"]],
                image_texts=[],
                suggested_workspace=None,
            )

            print(f"✅ Parsed successfully!")

        except Exception as e:
            print(f"❌ Error: {e}")

        print("-" * 40)


def test_due_date_parsing():
    """Test due date parsing with various time expressions."""

    # Initialize agent in dry run mode for testing
    agent = TaskCreationAgent(dry_run=True)

    due_date_cases = [
        {
            "name": "Tomorrow Deadline",
            "input": "Fix the urgent bug by tomorrow. This is for Livepeer and should take 2 hours.",
        },
        {
            "name": "End of Week",
            "input": "Update marketing campaign by end of week. Vanquish client work, 3 hours.",
        },
        {
            "name": "Today Deadline",
            "input": "Quick task that needs to be done today by end of day. 1 hour personal task.",
        },
        {
            "name": "Next Week",
            "input": "Prepare quarterly report by next week. This is important for the team.",
        },
        {
            "name": "Specific Day - Friday",
            "input": "Submit the proposal by Friday. High priority Livepeer work, 4 hours.",
        },
        {
            "name": "Next Monday",
            "input": "Start the new project next Monday. Full day task for Vanquish.",
        },
        {
            "name": "In 3 Days",
            "input": "Review and approve content in 3 days. Marketing task, 2 hours.",
        },
        {
            "name": "No Due Date Mentioned (Default Test)",
            "input": "Regular maintenance task for the server. No rush on this one.",
        },
        {
            "name": "End of Day",
            "input": "Send out the newsletter by end of day. Vanquish client work.",
        },
        {
            "name": "This Friday",
            "input": "Complete the analytics report this Friday. Livepeer task, 3 hours.",
        },
    ]

    print("\n\n📅 Testing Due Date Parsing Features")
    print("=" * 60)

    for i, test_case in enumerate(due_date_cases, 1):
        print(f"\n🗓️  Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        print("-" * 40)

        try:
            # Test just the synthesis (without creating task)
            task_info = agent.synthesize_task_info(
                text_inputs=[test_case["input"]],
                image_texts=[],
                suggested_workspace=None,
            )

            # Show specifically the due date that was parsed
            print(f"✅ Due Date Parsed: {task_info.get('due_date', 'Not specified')}")

        except Exception as e:
            print(f"❌ Error: {e}")

        print("-" * 40)


def test_comprehensive_parsing():
    """Test parsing of multiple attributes together."""

    # Initialize agent in dry run mode for testing
    agent = TaskCreationAgent(dry_run=True)

    comprehensive_cases = [
        {
            "name": "All Attributes Present",
            "input": "URGENT: Fix the payment system bug by tomorrow! This is critical Livepeer work that needs 4 hours of immediate attention.",
        },
        {
            "name": "Weekend Timeline",
            "input": "Low priority Vanquish task to update social media templates. Should take 30 minutes, can be done by end of week.",
        },
        {
            "name": "Week-Long Project",
            "input": "Implement the new user dashboard for Livepeer. High priority project that will take about 40 hours total. Deadline is next week.",
        },
    ]

    print("\n\n🎯 Testing Comprehensive Attribute Parsing")
    print("=" * 60)

    for i, test_case in enumerate(comprehensive_cases, 1):
        print(f"\n🎨 Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        print("-" * 40)

        try:
            # Test just the synthesis (without creating task)
            task_info = agent.synthesize_task_info(
                text_inputs=[test_case["input"]],
                image_texts=[],
                suggested_workspace=None,
            )

            print(f"✅ Comprehensive parsing successful!")
            print(f"   📋 Task: {task_info.get('task_name', 'Unknown')}")
            print(f"   🏢 Workspace: {task_info.get('workspace', 'Unknown')}")
            print(f"   ⚡ Priority: {task_info.get('priority', 'Unknown')}")
            print(
                f"   ⏱️  Duration: {task_info.get('estimated_hours', 'Unknown')} hours"
            )
            print(f"   📅 Due Date: {task_info.get('due_date', 'Unknown')}")

        except Exception as e:
            print(f"❌ Error: {e}")

        print("-" * 40)


def run_all_tests():
    """Run all test suites."""
    print("🚀 Starting AI Task Creation Agent Tests")
    print("=" * 60)

    # Run all test suites
    test_intelligent_parsing()
    test_due_date_parsing()
    test_comprehensive_parsing()

    print("\n\n✅ All tests completed!")


if __name__ == "__main__":
    run_all_tests()
