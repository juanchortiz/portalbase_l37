"""
Filter utilities for Portal Base data

Reusable filtering logic for contracts and announcements.
"""


def format_price(price_str):
    """Convert Portuguese price format to float."""
    try:
        if not price_str or price_str == "N/A":
            return 0.0
        return float(str(price_str).replace(".", "").replace(",", "."))
    except (ValueError, AttributeError):
        return 0.0


def filter_contracts(contracts, filters):
    """
    Apply filters to contracts and announcements (unified function).
    
    Args:
        contracts: List of contract or announcement dictionaries
        filters: Dictionary with filter settings:
            - keyword: Comma-separated keywords to search
            - fornecedor_nif: Supplier NIF to filter
            - location: List of location strings to match
            - cpv_codes: List of CPV codes to match
    
    Returns:
        Filtered list of contracts/announcements
    """
    filtered = contracts
    
    # Keyword filter (supports comma-separated keywords)
    if filters.get('keyword'):
        keywords = [kw.strip().lower() for kw in filters['keyword'].split(',') if kw.strip()]
        filtered = [
            c for c in filtered
            if any(
                # Contract fields
                keyword in c.get('objectoContrato', '').lower() or
                keyword in c.get('descContrato', '').lower() or
                keyword in ' '.join(str(x) for x in (c.get('cpv', []) if isinstance(c.get('cpv'), list) else [])).lower() or
                # Announcement fields
                keyword in c.get('descricaoAnuncio', '').lower() or
                keyword in ' '.join(str(x) for x in (c.get('CPVs', []) if isinstance(c.get('CPVs'), list) else [])).lower()
                for keyword in keywords
            )
        ]
    
    # Fornecedor (Supplier) NIF filter
    if filters.get('fornecedor_nif'):
        nif = filters['fornecedor_nif'].strip()
        filtered = [
            c for c in filtered
            if nif in ' '.join(str(x) for x in (c.get('adjudicatarios', []) if isinstance(c.get('adjudicatarios'), list) else []))  # Contract suppliers only
        ]
    
    # Location filter (multiple selection) - only applies to contracts, not announcements
    if filters.get('location') and filters['location']:
        location_list = filters['location'] if isinstance(filters['location'], list) else [filters['location']]
        filtered = [
            c for c in filtered
            # Keep if it's an announcement (no localExecucao) OR if it matches location filter
            if not c.get('localExecucao') or (  # Announcement without location
                isinstance(c.get('localExecucao'), list) and any(
                    any(filter_loc.lower() in str(loc).lower() for filter_loc in location_list)
                    for loc in c.get('localExecucao', [])
                )
            )
        ]
    
    # CPV codes filter (multiple selection)
    if filters.get('cpv_codes') and filters['cpv_codes']:
        cpv_list = filters['cpv_codes']
        # Match CPV codes - check if any selected CPV code is in any contract/announcement CPV
        filtered = [
            c for c in filtered
            if (
                # Contract CPV matching
                (c.get('cpv') and any(
                    any(cpv_filter.split('-')[0] in str(cpv_item) for cpv_filter in cpv_list)
                    for cpv_item in c.get('cpv', [])
                )) or 
                # Announcement CPV matching (capital CPVs)
                (c.get('CPVs') and any(
                    any(cpv_filter.split('-')[0] in str(cpv_item) for cpv_filter in cpv_list)
                    for cpv_item in c.get('CPVs', [])
                ))
            )
        ]
    
    return filtered


