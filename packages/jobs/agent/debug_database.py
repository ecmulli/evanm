#!/usr/bin/env python3
"""
Debug utility to inspect Notion database schema

This helps identify field name mismatches and database structure issues.
"""

import os
import sys
import json
sys.path.append(os.path.dirname(__file__))

from task_creator import TaskCreationAgent

def inspect_database_schema():
    """Fetch and display the database schema for debugging."""
    
    agent = TaskCreationAgent(dry_run=True)
    
    databases = {
        "Personal": os.getenv("PERSONAL_NOTION_DB_ID"),
        "Livepeer": os.getenv("LIVEPEER_NOTION_DB_ID"), 
        "Vanquish": os.getenv("VANQUISH_NOTION_DB_ID")
    }
    
    print("🔍 Inspecting Notion Database Schemas")
    print("=" * 60)
    
    for workspace, db_id in databases.items():
        if not db_id:
            print(f"\n❌ {workspace}: No database ID configured")
            continue
            
        print(f"\n📋 {workspace} Database ({db_id})")
        print("-" * 40)
        
        try:
            # Get database schema
            response = agent.notion_client.databases.retrieve(database_id=db_id)
            
            properties = response.get("properties", {})
            print(f"Properties found: {len(properties)}")
            
            for prop_name, prop_config in properties.items():
                prop_type = prop_config.get("type", "unknown")
                print(f"  📝 '{prop_name}' ({prop_type})")
                
                # Show select options if applicable
                if prop_type == "select" and "select" in prop_config:
                    options = prop_config["select"].get("options", [])
                    option_names = [opt.get("name") for opt in options]
                    print(f"     Options: {option_names}")
                    
                elif prop_type == "status" and "status" in prop_config:
                    groups = prop_config["status"].get("groups", [])
                    for group in groups:
                        option_names = [opt.get("name") for opt in group.get("options", [])]
                        print(f"     Status options: {option_names}")
                        
        except Exception as e:
            print(f"❌ Error accessing {workspace} database: {e}")
    
    print(f"\n🔧 Environment Check:")
    print(f"PERSONAL_NOTION_DB_ID: {os.getenv('PERSONAL_NOTION_DB_ID')}")
    print(f"PERSONAL_NOTION_API_KEY: {'✅ Set' if os.getenv('PERSONAL_NOTION_API_KEY') else '❌ Missing'}")

if __name__ == "__main__":
    inspect_database_schema()
