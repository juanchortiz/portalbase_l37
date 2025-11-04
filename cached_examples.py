"""
Examples of using the Cached API Client

Shows various ways to query data efficiently with local caching.
"""

from cached_api_client import CachedBaseAPIClient
from config import get_api_key
from datetime import datetime, timedelta


def main():
    ACCESS_TOKEN = get_api_key()
    client = CachedBaseAPIClient(ACCESS_TOKEN)
    
    print("=" * 80)
    print("Cached Base.gov.pt API Client - Usage Examples")
    print("=" * 80)
    
    # Example 1: Get yesterday's data
    print("\n1️⃣  Getting yesterday's publications...")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    contracts = client.get_contracts_by_date(yesterday)
    announcements = client.get_announcements_by_date(yesterday)
    print(f"   Contracts: {len(contracts)}")
    print(f"   Announcements: {len(announcements)}")
    
    # Example 2: Get today's data
    print("\n2️⃣  Getting today's publications...")
    today = datetime.now().strftime("%d/%m/%Y")
    contracts = client.get_contracts_by_date(today)
    announcements = client.get_announcements_by_date(today)
    print(f"   Contracts: {len(contracts)}")
    print(f"   Announcements: {len(announcements)}")
    
    # Example 3: Get last week's data
    print("\n3️⃣  Getting last week's publications...")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%d/%m/%Y")
    today = datetime.now().strftime("%d/%m/%Y")
    contracts = client.get_contracts_by_date_range(week_ago, today)
    print(f"   Contracts in last 7 days: {len(contracts)}")
    
    # Calculate total value
    if contracts:
        total_value = 0
        for contract in contracts:
            price_str = contract.get("precoContratual", "0")
            try:
                price = float(price_str.replace(".", "").replace(",", "."))
                total_value += price
            except (ValueError, AttributeError):
                pass
        print(f"   Total value: €{total_value:,.2f}")
    
    # Example 4: Get specific date data
    print("\n4️⃣  Getting data for a specific date (01/11/2025)...")
    specific_date = "01/11/2025"
    contracts = client.get_contracts_by_date(specific_date)
    print(f"   Contracts on {specific_date}: {len(contracts)}")
    
    if contracts:
        print("\n   Sample contract:")
        contract = contracts[0]
        print(f"      Object: {contract.get('objectoContrato', 'N/A')}")
        print(f"      Price: €{contract.get('precoContratual', 'N/A')}")
        print(f"      Entity: {', '.join(contract.get('adjudicante', ['N/A']))}")
    
    # Example 5: Cache statistics
    print("\n5️⃣  Cache statistics...")
    stats = client.get_cache_stats()
    print(f"   Total cached contracts: {stats['total_contracts']}")
    print(f"   Total cached announcements: {stats['total_announcements']}")
    print(f"   Years cached: {len(stats['years_cached'])}")
    
    # Example 6: Manual sync for a specific year
    print("\n6️⃣  Manual cache sync (if needed)...")
    current_year = str(datetime.now().year)
    print(f"   Syncing {current_year}...")
    try:
        client.sync_year(current_year, force=False)
    except Exception as e:
        print(f"   Note: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Examples complete!")
    print("=" * 80)
    
    print("\n💡 Tips:")
    print("   - First query of each year will sync data from API (may take a moment)")
    print("   - Subsequent queries use local cache (instant)")
    print("   - Cache auto-refreshes daily (once per calendar day)")
    print("   - Use sync_year_data.py to manually refresh specific years")


if __name__ == "__main__":
    main()

