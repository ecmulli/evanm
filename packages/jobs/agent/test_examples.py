#!/usr/bin/env python3
"""
Test examples for the AI Task Creation Agent

Demonstrates the intelligent parsing capabilities for priority, duration, and workspace detection.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from task_creator import TaskCreationAgent

def test_intelligent_parsing():
    """Test the intelligent parsing features with various input examples."""
    
    # Initialize agent in dry run mode for testing
    agent = TaskCreationAgent(dry_run=True)
    
    test_cases = [
        {
            "name": "High Priority + Duration + Livepeer",
            "input": "This is urgent! The Livepeer analytics dashboard is broken and needs a 2 hour fix ASAP."
        },
        {
            "name": "Vanquish + Low Priority",
            "input": "Create a new marketing campaign template for Vanquish client. This is low priority, can do when time permits."
        },
        {
            "name": "Quick Personal Task", 
            "input": "Quick 15 minute task to update my personal portfolio website with the new project."
        },
        {
            "name": "Full Day Task",
            "input": "Need to implement streaming optimization feature - this is a full day task, high priority for the video platform."
        },
        {
            "name": "Default Values Test",
            "input": "Simple task with no specific context clues to test defaults."
        },
        {
            "name": "Half Hour Client Work",
            "input": "Update the client's ad campaign settings - should take about 30 minutes for Vanquish."
        }
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
                text_inputs=[test_case['input']],
                image_texts=[],
                suggested_workspace=None
            )
            
            print(f"✅ Parsed successfully!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_intelligent_parsing()
