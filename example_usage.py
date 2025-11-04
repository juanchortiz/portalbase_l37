"""
Example usage of the Base.gov.pt API Client

This file demonstrates various ways to use the API client to query
Portuguese public procurement data.
"""

from base_api_client import BaseAPIClient
from config import get_api_key


def main():
    # Initialize the client with your access token
    ACCESS_TOKEN = get_api_key()
    client = BaseAPIClient(ACCESS_TOKEN)
    
    print("=" * 70)
    print("Base.gov.pt API Client - Usage Examples")
    print("=" * 70)
    
    # Example 1: Get contract by ID
    print("\n1. Getting contract information by ID...")
    try:
        contract = client.get_contract_info(id_contrato="12345")
        print(f"   Contract ID: {contract.get('idContrato')}")
        print(f"   Object: {contract.get('objectoContrato')}")
        print(f"   Price: €{contract.get('precoContratual')}")
        print(f"   Year: {contract.get('Ano')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 2: Get announcement information
    print("\n2. Getting announcement information...")
    try:
        announcement = client.get_announcement_info(n_anuncio="1234/2015")
        print(f"   Announcement: {announcement.get('nAnuncio')}")
        print(f"   Type: {announcement.get('TipoAnuncio')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 3: Get entity information
    print("\n3. Getting entity information...")
    try:
        entity = client.get_entity_info(nif_entidade="654123987")
        print(f"   Entity NIF: {entity.get('nifEntidade')}")
        print(f"   Name: {entity.get('nome', 'N/A')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 4: Get contract modifications
    print("\n4. Getting contract modification information...")
    try:
        modification = client.get_contract_modification_info(id_contrato="12345")
        print(f"   Contract ID: {modification.get('idContrato')}")
        print(f"   Modifications found: {len(modification) if isinstance(modification, list) else 1}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 5: Search contracts by year
    print("\n5. Searching contracts by year (2015)...")
    try:
        contracts = client.search_contracts_by_year("2015")
        print(f"   Found {len(contracts)} contract(s)")
        
        # Calculate total value
        total_value = 0
        for contract in contracts:
            price_str = contract.get("precoContratual", "0")
            try:
                # Handle Portuguese number format (. as thousands separator, , as decimal)
                price = float(price_str.replace(".", "").replace(",", "."))
                total_value += price
            except (ValueError, AttributeError):
                pass
        
        print(f"   Total contract value: €{total_value:,.2f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 6: Search contracts by entity
    print("\n6. Searching contracts by entity...")
    try:
        entity_contracts = client.search_contracts_by_entity("654123987", "2015")
        print(f"   Found {len(entity_contracts)} contract(s) for entity")
        
        # Display contract types
        contract_types = set()
        for contract in entity_contracts:
            types = contract.get("tipoContrato", [])
            if isinstance(types, list):
                contract_types.update(types)
        
        print(f"   Contract types: {', '.join(contract_types) if contract_types else 'N/A'}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 7: Advanced filtering
    print("\n7. Advanced filtering example...")
    try:
        # Get contracts for a year
        all_contracts = client.search_contracts_by_year("2015")
        
        # Filter for high-value contracts (> €100,000)
        high_value_contracts = []
        for contract in all_contracts:
            price_str = contract.get("precoContratual", "0")
            try:
                price = float(price_str.replace(".", "").replace(",", "."))
                if price > 100000:
                    high_value_contracts.append(contract)
            except (ValueError, AttributeError):
                pass
        
        print(f"   Contracts over €100,000: {len(high_value_contracts)}")
        
        # Filter by location
        lisbon_contracts = [
            c for c in all_contracts
            if any("Lisboa" in loc for loc in c.get("localExecucao", []))
        ]
        print(f"   Contracts in Lisboa: {len(lisbon_contracts)}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
