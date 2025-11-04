"""
Get all items published on a specific date from Base.gov.pt API using cache

This version uses local caching - after the first sync, queries are instant!
"""

from cached_api_client import CachedBaseAPIClient
from config import get_api_key
import sys


def main():
    # Initialize the cached client
    ACCESS_TOKEN = get_api_key()
    client = CachedBaseAPIClient(ACCESS_TOKEN)
    
    # Get date from command line or use default
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = "31/10/2025"  # Default to October 31, 2025
    
    print("=" * 80)
    print(f"Fetching all items published on {date_str}")
    print("=" * 80)
    
    # Get contracts for the date (uses cache - instant!)
    print(f"\n📋 Fetching contracts published on {date_str}...")
    try:
        contracts = client.get_contracts_by_date(date_str)
        print(f"   ✅ Found {len(contracts)} contract(s)")
        
        if contracts:
            # Calculate total value
            total_value = 0
            for contract in contracts:
                price_str = contract.get("precoContratual", "0")
                try:
                    price = float(price_str.replace(".", "").replace(",", "."))
                    total_value += price
                except (ValueError, AttributeError):
                    pass
            
            print(f"   💰 Total contract value: €{total_value:,.2f}")
            
            print(f"\n   Contract Details:")
            print("   " + "-" * 76)
            for i, contract in enumerate(contracts, 1):
                print(f"\n   Contract #{i}:")
                print(f"      ID: {contract.get('idContrato', 'N/A')}")
                print(f"      Object: {contract.get('objectoContrato', 'N/A')}")
                print(f"      Type: {', '.join(contract.get('tipoContrato', ['N/A']))}")
                print(f"      Price: €{contract.get('precoContratual', 'N/A')}")
                print(f"      Contracting Entity: {', '.join(contract.get('adjudicante', ['N/A']))}")
                print(f"      Contractors: {', '.join(contract.get('adjudicatarios', ['N/A']))}")
                if contract.get('nAnuncio'):
                    print(f"      Announcement: {contract.get('nAnuncio')}")
        else:
            print(f"\n   ℹ️  No contracts were published on {date_str}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        contracts = []
    
    # Get announcements for the date
    print(f"\n📢 Fetching announcements published on {date_str}...")
    try:
        announcements = client.get_announcements_by_date(date_str)
        print(f"   ✅ Found {len(announcements)} announcement(s)")
        
        if announcements:
            print(f"\n   Announcement Details:")
            print("   " + "-" * 76)
            for i, announcement in enumerate(announcements, 1):
                print(f"\n   Announcement #{i}:")
                print(f"      Number: {announcement.get('nAnuncio', 'N/A')}")
                print(f"      Type: {announcement.get('TipoAnuncio', 'N/A')}")
                print(f"      Entity NIF: {announcement.get('nifEntidade', 'N/A')}")
        else:
            print(f"\n   ℹ️  No announcements were published on {date_str}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        announcements = []
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    total_items = len(contracts) + len(announcements)
    print(f"   Total items published on {date_str}: {total_items}")
    print(f"   - Contracts: {len(contracts)}")
    print(f"   - Announcements: {len(announcements)}")
    print("=" * 80)
    
    print("\n💡 Note: This query used the local cache - no API call needed!")


if __name__ == "__main__":
    main()

