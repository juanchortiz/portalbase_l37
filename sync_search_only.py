#!/usr/bin/env python3
"""
Sync Only Saved Search to GitHub Actions

This script exports a saved search from the local database and provides
instructions on how to import it into the GitHub Actions database.

Since the database is too large (2GB) to sync directly, this script:
1. Exports the saved search as JSON
2. Provides instructions to manually update the GitHub Actions artifact
3. Or creates a script to update the search in the next workflow run
"""

import sqlite3
import json
import sys
from pathlib import Path


def export_search(db_path, search_name):
    """Export a saved search from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT name, filters FROM saved_searches WHERE name = ?",
        (search_name,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print(f"❌ Saved search '{search_name}' not found in local database!")
        print("\n💡 Available saved searches:")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM saved_searches")
        searches = cursor.fetchall()
        conn.close()
        
        if searches:
            for search in searches:
                print(f"   - {search[0]}")
        else:
            print("   (no saved searches found)")
        return None
    
    name, filters_json = result
    filters = json.loads(filters_json)
    
    return {
        'name': name,
        'filters': filters
}


def main():
    """Main function."""
    print("=" * 80)
    print("🔄 Sync Saved Search to GitHub Actions")
    print("=" * 80)
    print()
    
    if len(sys.argv) > 1:
        search_name = sys.argv[1]
    else:
        search_name = input("Enter saved search name (default: Biogerm): ").strip() or "Biogerm"
    
    db_path = Path(__file__).parent / 'base_cache.db'
    
    if not db_path.exists():
        print(f"❌ Database file not found: {db_path}")
        print("💡 Make sure you've saved a search in the Streamlit app first.")
        return 1
    
    print(f"📦 Loading saved search '{search_name}' from local database...")
    search_data = export_search(db_path, search_name)
    
    if not search_data:
        return 1
    
    print(f"✅ Found saved search: {search_data['name']}")
    print(f"   Filters: {list(search_data['filters'].keys())}")
    print()
    
    # Save to JSON file
    output_file = Path(__file__).parent / f"{search_name}_search.json"
    with open(output_file, 'w') as f:
        json.dump(search_data, f, indent=2)
    
    print(f"💾 Saved search exported to: {output_file}")
    print()
    
    print("=" * 80)
    print("📋 NEXT STEPS: How to Import to GitHub Actions")
    print("=" * 80)
    print()
    print("Since the database is too large to sync directly, here are your options:")
    print()
    print("✅ OPTION 1: Update Search in Next Workflow Run (Recommended)")
    print()
    print("   The workflow will automatically update the search if you:")
    print("   1. Configure the search in Streamlit app locally")
    print("   2. Run: python sync_db_simple.py")
    print("   3. This will sync the entire database (may take time due to size)")
    print()
    print("✅ OPTION 2: Manual Update via Workflow")
    print()
    print("   Create a workflow that updates only the saved search:")
    print("   1. The search JSON is saved in: " + str(output_file))
    print("   2. Create a workflow that reads this JSON and updates the database")
    print("   3. Or manually edit the artifact after download")
    print()
    print("✅ OPTION 3: Use Current Search (Already Created)")
    print()
    print("   The workflow already created 'Biogerm' search with empty filters.")
    print("   You can:")
    print("   1. Configure filters in Streamlit app")
    print("   2. The next workflow run will use the updated search from artifact")
    print("   3. But you need to sync the database first (Option 1)")
    print()
    print("=" * 80)
    print("💡 RECOMMENDED: Configure filters in Streamlit, then sync database")
    print("=" * 80)
    print()
    print(f"Search data saved to: {output_file}")
    print("You can use this file to manually update the search if needed.")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

