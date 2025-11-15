#!/usr/bin/env python3
"""
Create a test saved search for automation testing
"""

from cached_api_client import CachedBaseAPIClient
from config import get_api_key

def main():
    print("=" * 80)
    print("🔧 Creating Test Saved Search")
    print("=" * 80)
    
    try:
        api_key = get_api_key()
        client = CachedBaseAPIClient(api_key)
        
        # Create a test saved search with some common filters
        test_filters = {
            'keyword': '',  # Empty = no keyword filter
            'fornecedor_nif': '',  # Empty = no supplier filter
            'location': [],  # Empty = no location filter
            'cpv_codes': [
                '33696500-0',  # REAGENTES DE LABORATÓRIO
                '33000000-0',  # EQUIPAMENTO MÉDICO
                '33600000-6',  # PRODUTOS FARMACÊUTICOS
            ]
        }
        
        search_name = "Default Automation"
        
        # Check if already exists
        existing = client.load_search(search_name)
        if existing:
            print(f"⚠️  Saved search '{search_name}' already exists!")
            print("   Filters:", existing)
            response = input("   Do you want to overwrite it? (y/n): ")
            if response.lower() != 'y':
                print("   Cancelled.")
                return
        
        # Save the search
        success = client.save_search(search_name, test_filters)
        
        if success:
            print(f"\n✅ Saved search '{search_name}' created successfully!")
            print("\n   Filters configured:")
            print(f"   - CPV Codes: {len(test_filters['cpv_codes'])} codes")
            print(f"   - Keywords: {test_filters['keyword'] or 'None'}")
            print(f"   - Location: {test_filters['location'] or 'None'}")
            print(f"   - Supplier NIF: {test_filters['fornecedor_nif'] or 'None'}")
            print("\n💡 You can now test the automation:")
            print("   python3 daily_automation.py")
        else:
            print(f"❌ Failed to create saved search (name might already exist)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


