#!/usr/bin/env python3
"""
Simple debug utility to inspect Notion database schema
"""

import os
import sys
sys.path.append('..')

from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.dev"))

def inspect_personal_database():
    """Fetch and display just the personal database schema."""
    
    api_key = os.getenv("PERSONAL_NOTION_API_KEY")
    db_id = os.getenv("PERSONAL_NOTION_DB_ID")
    
    print("🔍 Inspecting Personal Notion Database Schema")
    print("=" * 60)
    
    if not api_key:
        print("❌ PERSONAL_NOTION_API_KEY not found")
        return
        
    if not db_id:
        print("❌ PERSONAL_NOTION_DB_ID not found")
        return
    
    try:
        client = Client(auth=api_key)
        
        print(f"📋 Personal Database ({db_id})")
        print("-" * 40)
        
        # Get database schema
        response = client.databases.retrieve(database_id=db_id)
        
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
                all_options = []
                for group in groups:
                    options = group.get("options", [])
                    group_options = [opt.get("name") for opt in options]
                    all_options.extend(group_options)
                print(f"     Status options: {all_options}")
                
                # Also print the raw structure for debugging
                if not all_options:
                    print(f"     Raw status config: {prop_config['status']}")
                    
    except Exception as e:
        print(f"❌ Error accessing personal database: {e}")

if __name__ == "__main__":
    inspect_personal_database()
