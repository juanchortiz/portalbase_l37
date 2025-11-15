#!/usr/bin/env python3
"""
Script to sync cache with Portal Base API
Populates the local database with contracts and announcements
"""

from cached_api_client import CachedBaseAPIClient
from config import get_api_key
from datetime import datetime

def main():
    print("🔄 Starting cache synchronization...")
    
    # Get API key
    try:
        api_key = get_api_key()
        print("✅ API key loaded")
    except Exception as e:
        print(f"❌ Error loading API key: {e}")
        return
    
    # Initialize client
    try:
        client = CachedBaseAPIClient(api_key)
        print("✅ Client initialized")
    except Exception as e:
        print(f"❌ Error initializing client: {e}")
        return
    
    # Sync current year and previous year
    current_year = datetime.now().year
    years_to_sync = [current_year, current_year - 1]
    
    for year in years_to_sync:
        print(f"\n📥 Syncing year {year}...")
        try:
            client.sync_year(str(year), force=True)
            print(f"✅ Year {year} synced successfully")
        except Exception as e:
            print(f"❌ Error syncing year {year}: {e}")
    
    # Show stats
    print("\n" + "="*60)
    print("📊 Cache Statistics:")
    stats = client.get_cache_stats()
    print(f"  Total contracts: {stats['total_contracts']:,}")
    print(f"  Total announcements: {stats['total_announcements']:,}")
    print(f"  Years cached: {len(stats['years_cached'])}")
    for year_info in stats['years_cached']:
        print(f"    - {year_info['year']}: {year_info['record_count']:,} records")
    print("="*60)
    print("\n✅ Cache synchronization completed!")

if __name__ == "__main__":
    main()




