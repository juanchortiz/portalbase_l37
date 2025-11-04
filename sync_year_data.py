"""
Utility script to sync/refresh cached data for specific years

This allows you to manually control when to fetch data from the API.
"""

from cached_api_client import CachedBaseAPIClient
from config import get_api_key
import sys


def main():
    ACCESS_TOKEN = get_api_key()
    client = CachedBaseAPIClient(ACCESS_TOKEN)
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python sync_year_data.py <year> [--force]")
        print("\nExamples:")
        print("  python sync_year_data.py 2025")
        print("  python sync_year_data.py 2025 --force  (force refresh even if cache is recent)")
        print("\nCurrent cache status:")
        stats = client.get_cache_stats()
        print(f"\nTotal cached contracts: {stats['total_contracts']}")
        print(f"Total cached announcements: {stats['total_announcements']}")
        print("\nYears in cache:")
        for year_info in stats['years_cached']:
            print(f"  - {year_info['year']}: {year_info['record_count']} records "
                  f"(last updated: {year_info['last_fetched'][:19]})")
        sys.exit(1)
    
    year = sys.argv[1]
    force = "--force" in sys.argv
    
    print("=" * 80)
    print(f"Syncing data for year {year}")
    print("=" * 80)
    
    try:
        client.sync_year(year, force=force)
        
        # Show updated stats
        print("\n" + "=" * 80)
        print("✅ Sync complete!")
        print("=" * 80)
        
        stats = client.get_cache_stats()
        print(f"\nTotal cached contracts: {stats['total_contracts']}")
        print(f"Total cached announcements: {stats['total_announcements']}")
        
    except Exception as e:
        print(f"\n❌ Error during sync: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

