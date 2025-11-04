"""
Get all items published yesterday from Base.gov.pt API
"""

from base_api_client import BaseAPIClient
from config import get_api_key
from datetime import datetime, timedelta

def main():
    # Initialize the client with the API key
    ACCESS_TOKEN = get_api_key()
    client = BaseAPIClient(ACCESS_TOKEN)
    
    # Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime("%d/%m/%Y")  # Portuguese date format
    current_year = str(yesterday.year)
    
    print("=" * 80)
    print(f"Fetching all items published on {yesterday_str} (yesterday)")
    print("=" * 80)
    
    # Get all contracts from the current year
    print(f"\n📋 Searching contracts for year {current_year}...")
    try:
        all_contracts = client.search_contracts_by_year(current_year)
        print(f"   Retrieved {len(all_contracts)} total contracts for {current_year}")
        
        # Filter for yesterday's publication date
        yesterday_contracts = []
        for contract in all_contracts:
            pub_date = contract.get("dataPublicacao", "")
            if pub_date == yesterday_str:
                yesterday_contracts.append(contract)
        
        print(f"   ✅ Found {len(yesterday_contracts)} contract(s) published on {yesterday_str}")
        
        # Display contract details
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
                print(f"      Publication Date: {contract.get('dataPublicacao', 'N/A')}")
        else:
            print(f"\n   ℹ️  No contracts were published on {yesterday_str}")
    
    except Exception as e:
        print(f"   ❌ Error retrieving contracts: {e}")
    
    # Get all announcements from the current year
    print(f"\n\n📢 Searching announcements for year {current_year}...")
    try:
        all_announcements = client.get_announcement_info(ano=current_year)
        
        # Handle single announcement vs list
        if not isinstance(all_announcements, list):
            all_announcements = [all_announcements] if all_announcements else []
        
        print(f"   Retrieved {len(all_announcements)} total announcements for {current_year}")
        
        # Filter for yesterday's publication date
        yesterday_announcements = []
        for announcement in all_announcements:
            pub_date = announcement.get("dataPublicacao", "")
            if pub_date == yesterday_str:
                yesterday_announcements.append(announcement)
        
        print(f"   ✅ Found {len(yesterday_announcements)} announcement(s) published on {yesterday_str}")
        
        # Display announcement details
        if yesterday_announcements:
            print(f"\n   Announcement Details:")
            print("   " + "-" * 76)
            for i, announcement in enumerate(yesterday_announcements, 1):
                print(f"\n   Announcement #{i}:")
                print(f"      Number: {announcement.get('nAnuncio', 'N/A')}")
                print(f"      Type: {announcement.get('TipoAnuncio', 'N/A')}")
                print(f"      Entity NIF: {announcement.get('nifEntidade', 'N/A')}")
                print(f"      Publication Date: {announcement.get('dataPublicacao', 'N/A')}")
        else:
            print(f"\n   ℹ️  No announcements were published on {yesterday_str}")
    
    except Exception as e:
        print(f"   ❌ Error retrieving announcements: {e}")
    
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


if __name__ == "__main__":
    main()

