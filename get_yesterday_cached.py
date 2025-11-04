"""
Get all items published yesterday from Base.gov.pt API using cached client

This version uses local caching to avoid repeatedly fetching all year data.
"""

from cached_api_client import CachedBaseAPIClient
from config import get_api_key
from datetime import datetime, timedelta


def main():
    # Initialize the cached client
    ACCESS_TOKEN = get_api_key()
    client = CachedBaseAPIClient(ACCESS_TOKEN)
    
    # Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime("%d/%m/%Y")  # Portuguese date format
    
    print("=" * 80)
    print(f"Fetching all items published on {yesterday_str} (yesterday)")
    print("=" * 80)
    
    # Show cache stats
    print("\n📊 Cache Statistics:")
    stats = client.get_cache_stats()
    print(f"   Total cached contracts: {stats['total_contracts']}")
    print(f"   Total cached announcements: {stats['total_announcements']}")
    print(f"   Years in cache:")
    for year_info in stats['years_cached']:
        print(f"      - {year_info['year']}: {year_info['record_count']} records "
              f"(last updated: {year_info['last_fetched'][:19]})")
    
    # Get contracts for yesterday (will auto-sync if needed)
    print(f"\n📋 Fetching contracts published on {yesterday_str}...")
    try:
        yesterday_contracts = client.get_contracts_by_date(yesterday_str)
        print(f"   ✅ Found {len(yesterday_contracts)} contract(s)")
        
        if yesterday_contracts:
            print(f"\n   Contract Details:")
            print("   " + "-" * 76)
            for i, contract in enumerate(yesterday_contracts, 1):
                print(f"\n   Contract #{i}:")
                print(f"      ID: {contract.get('idContrato', 'N/A')}")
                print(f"      Object: {contract.get('objectoContrato', 'N/A')}")
                print(f"      Type: {', '.join(contract.get('tipoContrato', ['N/A']))}")
                print(f"      Price: €{contract.get('precoContratual', 'N/A')}")
                print(f"      Contracting Entity: {', '.join(contract.get('adjudicante', ['N/A']))}")
                print(f"      Contractors: {', '.join(contract.get('adjudicatarios', ['N/A']))}")
                print(f"      Announcement: {contract.get('nAnuncio', 'N/A')}")
        else:
            print(f"\n   ℹ️  No contracts were published on {yesterday_str}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Get announcements for yesterday
    print(f"\n📢 Fetching announcements published on {yesterday_str}...")
    try:
        yesterday_announcements = client.get_announcements_by_date(yesterday_str)
        print(f"   ✅ Found {len(yesterday_announcements)} announcement(s)")
        
        if yesterday_announcements:
            print(f"\n   Announcement Details:")
            print("   " + "-" * 76)
            for i, announcement in enumerate(yesterday_announcements, 1):
                print(f"\n   Announcement #{i}:")
                print(f"      Number: {announcement.get('nAnuncio', 'N/A')}")
                print(f"      Type: {announcement.get('TipoAnuncio', 'N/A')}")
                print(f"      Entity NIF: {announcement.get('nifEntidade', 'N/A')}")
        else:
            print(f"\n   ℹ️  No announcements were published on {yesterday_str}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    try:
        total_items = len(yesterday_contracts) + len(yesterday_announcements)
        print(f"   Total items published on {yesterday_str}: {total_items}")
        print(f"   - Contracts: {len(yesterday_contracts)}")
        print(f"   - Announcements: {len(yesterday_announcements)}")
    except:
        print("   Unable to generate summary due to errors above")
    print("=" * 80)
    
    print("\n💡 Tip: The cache automatically refreshes daily (once per calendar day).")
    print("   Use 'sync_year_data.py' to manually sync or refresh cache.")


if __name__ == "__main__":
    main()

