#!/usr/bin/env python3
"""
Daily Automation Script for Portal Base

This script:
1. Syncs new announcements from Base.gov.pt API (incremental update)
2. Filters announcements based on saved search criteria
3. Creates HubSpot deals for matching new announcements
4. Logs all operations

Designed to run daily via GitHub Actions or scheduled task.
"""

import sys
from datetime import datetime, timedelta, date
from cached_api_client import CachedBaseAPIClient
from config import get_api_key
from filter_utils import filter_contracts
from hubspot_automation import create_deal_from_announcement, check_deal_exists, get_hubspot_token
import time


def parse_date_value(value):
    if not value:
        return None
    s = str(value).strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None


def range_from_option(option):
    if not option:
        return None
    today = datetime.now().date()
    if option == "Today":
        return today, today
    if option == "Yesterday":
        y = today - timedelta(days=1)
        return y, y
    if option == "Last 30 days":
        end = today - timedelta(days=1)
        start = today - timedelta(days=30)
        return start, end
    if option == "Last 90 days":
        end = today - timedelta(days=1)
        start = today - timedelta(days=90)
        return start, end
    return None


def resolve_date_range(filters, env_vars, days_to_check, safety_days):
    env_start = parse_date_value(env_vars.get('START_DATE'))
    env_end = parse_date_value(env_vars.get('END_DATE'))
    if env_start and env_end:
        return env_start, env_end, "env override"
    if env_start or env_end:
        raise ValueError("Both START_DATE and END_DATE must be provided when overriding.")

    option = (filters or {}).get('date_option') if filters else None
    if option == "Custom range":
        fs = parse_date_value((filters or {}).get('start_date'))
        fe = parse_date_value((filters or {}).get('end_date'))
        if fs and fe:
            return fs, fe, "saved search custom"
    else:
        opt_range = range_from_option(option)
        if opt_range:
            return opt_range[0], opt_range[1], f"saved search ({option})"

    end_date = (datetime.now() - timedelta(days=1)).date()
    span = max(0, days_to_check - 1 + max(0, safety_days))
    start_date = end_date - timedelta(days=span)
    return start_date, end_date, "default sliding"


def main():
    """Main automation function."""
    print("=" * 80)
    print("🔄 Portal Base Daily Automation")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    import os
    
    # Configuration
    # Set the name of the saved search to use for filtering
    # This should match a saved search created in the Streamlit app
    SAVED_SEARCH_NAME = os.environ.get('AUTOMATION_SAVED_SEARCH', 'Default Automation')
    
    sync_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Initialize API client
        print("🔑 Loading API credentials...")
        api_key = get_api_key()
        client = CachedBaseAPIClient(api_key)
        print("✅ API client initialized\n")
        
        # Load saved search filters
        print(f"📋 Loading saved search: {SAVED_SEARCH_NAME}...")
        filters = client.load_search(SAVED_SEARCH_NAME)
        if not filters:
            # Check if this is the first run (no saved searches exist)
            all_searches = client.get_saved_searches()
            
            if not all_searches:
                # First run - FAIL instead of creating empty search
                error_msg = f"Saved search '{SAVED_SEARCH_NAME}' not found and no saved searches exist!"
                print(f"❌ {error_msg}")
                print(f"\n⚠️  CRITICAL: Cannot proceed with empty filters - this would create deals for ALL announcements!")
                print(f"\n💡 To fix this:")
                print(f"   1. Go to GitHub Actions → 'Update Saved Search' workflow")
                print(f"   2. Run it with search_file: 'Biogerm_search.json'")
                print(f"   3. Or create the search '{SAVED_SEARCH_NAME}' in the Streamlit app first")
                print(f"   4. Then sync the database to GitHub Actions")
                
                client.log_daily_sync(
                    sync_date=sync_date,
                    announcements_fetched=0,
                    announcements_new=0,
                    deals_created=0,
                    deals_failed=0,
                    sync_status="error",
                    error_message=error_msg
                )
                sys.exit(1)
            else:
                # Other searches exist but not the requested one - fail
                error_msg = f"Saved search '{SAVED_SEARCH_NAME}' not found!"
                print(f"❌ {error_msg}")
                print("\n💡 Available saved searches:")
                for search in all_searches:
                    print(f"   - {search['name']}")
                print(f"\n⚠️  Please create and save the search '{SAVED_SEARCH_NAME}' in the Streamlit app first.")
                print(f"   Or use the 'Update Saved Search' workflow to sync it from the repository.")
                
                client.log_daily_sync(
                    sync_date=sync_date,
                    announcements_fetched=0,
                    announcements_new=0,
                    deals_created=0,
                    deals_failed=0,
                    sync_status="error",
                    error_message=error_msg
                )
                sys.exit(1)
        
        print(f"✅ Loaded filters: {list(filters.keys())}")
        print(f"📋 Filter details:")
        print(f"   - Keywords: '{filters.get('keyword', '')}'")
        print(f"   - Fornecedor NIF: '{filters.get('fornecedor_nif', '')}'")
        print(f"   - Locations: {filters.get('location', [])}")
        print(f"   - CPV Codes: {filters.get('cpv_codes', [])}")
        print(f"   - Search Type: {filters.get('search_type', 'not set')}")
        
        # Validate filters - fail if all filters are empty
        has_filters = (
            filters.get('keyword', '').strip() or
            filters.get('fornecedor_nif', '').strip() or
            filters.get('location', []) or
            filters.get('cpv_codes', [])
        )
        
        if not has_filters:
            error_msg = f"CRITICAL: Saved search '{SAVED_SEARCH_NAME}' has empty filters! This would create deals for ALL announcements."
            print(f"\n❌ {error_msg}")
            print(f"\n💡 To fix this:")
            print(f"   1. Go to GitHub Actions → 'Update Saved Search' workflow")
            print(f"   2. Run it with search_file: 'Biogerm_search.json'")
            print(f"   3. Or update the search '{SAVED_SEARCH_NAME}' in the Streamlit app with proper filters")
            
            client.log_daily_sync(
                sync_date=sync_date,
                announcements_fetched=0,
                announcements_new=0,
                deals_created=0,
                deals_failed=0,
                sync_status="error",
                error_message=error_msg
            )
            sys.exit(1)
        
        print()
        
        DAYS_TO_CHECK = int(os.environ.get('DAYS_TO_CHECK', '1'))
        SAFETY_DAYS = int(os.environ.get('SAFETY_DAYS', '0'))
        start_date, end_date, date_source = resolve_date_range(filters, os.environ, DAYS_TO_CHECK, SAFETY_DAYS)
        start_date_str = start_date.strftime('%d/%m/%Y')
        end_date_str = end_date.strftime('%d/%m/%Y')
        print(f"📅 Date range: {start_date_str} to {end_date_str} (source: {date_source})")
        print(f"🔍 Using saved search: {SAVED_SEARCH_NAME}\n")
        
        # Sync new announcements
        print("📥 Syncing new announcements from API...")
        all_fetched_announcements = []
        
        # Fetch announcements for the date range
        # Note: API returns by year, so we need to fetch the year and filter by date
        for year in range(int(start_date.strftime('%Y')), int(end_date.strftime('%Y')) + 1):
            try:
                year_announcements = client.client.get_announcement_info(ano=str(year))
                if not isinstance(year_announcements, list):
                    year_announcements = [year_announcements] if year_announcements else []
                all_fetched_announcements.extend(year_announcements)
            except Exception as e:
                print(f"⚠️  Error fetching year {year}: {e}")
        
        # Robust date parsing and comparison
        from datetime import datetime as _dt, date as _date
        def _parse_any_date(s: str) -> _date | None:
            if not s:
                return None
            s = str(s).strip()
            # Try DD/MM/YYYY
            try:
                return _dt.strptime(s, "%d/%m/%Y").date()
            except Exception:
                pass
            # Try YYYY-MM-DD
            try:
                return _dt.strptime(s, "%Y-%m-%d").date()
            except Exception:
                return None

        def _get_announcement_pub_date(a: dict) -> _date | None:
            for key in ("dataPublicacao", "DataPublicacao", "data_publicacao", "DataPublicacaoAnuncio", "dataPublicacaoTexto", "Data"):
                if key in a and a.get(key):
                    d = _parse_any_date(a.get(key))
                    if d:
                        return d
            return None

        start_date_obj = _dt.strptime(start_date_str, "%d/%m/%Y").date()
        end_date_obj = _dt.strptime(end_date_str, "%d/%m/%Y").date()
        
        new_announcements = []
        announcements_fetched = len(all_fetched_announcements)
        
        parsed_ok = 0
        parsed_fail = 0
        for announcement in all_fetched_announcements:
            pub_date = _get_announcement_pub_date(announcement)
            if not pub_date:
                parsed_fail += 1
                continue
            parsed_ok += 1
            # Check if within date range
            if start_date_obj <= pub_date <= end_date_obj:
                n_anuncio = announcement.get('nAnuncio')
                if not n_anuncio:
                    continue
                
                # Check if already in cache
                if not client.is_announcement_processed(n_anuncio):
                    # Store in cache if not already there
                    try:
                        # Check if exists in announcements table
                        import sqlite3
                        import json
                        conn_db = sqlite3.connect(client.db_path)
                        cursor = conn_db.cursor()
                        cursor.execute(
                            "SELECT n_anuncio FROM announcements WHERE n_anuncio = ?",
                            (n_anuncio,)
                        )
                        if not cursor.fetchone():
                            # Store new announcement
                            cursor.execute("""
                                INSERT OR REPLACE INTO announcements 
                                (n_anuncio, data_publicacao, ano, tipo_anuncio, nif_entidade, 
                                 raw_data, last_updated)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                n_anuncio,
                                pub_date,
                                announcement.get('Ano'),
                                announcement.get('TipoAnuncio'),
                                announcement.get('nifEntidade'),
                                json.dumps(announcement),
                                datetime.now().isoformat()
                            ))
                            conn_db.commit()
                        conn_db.close()
                    except Exception as e:
                        print(f"⚠️  Error storing announcement {n_anuncio}: {e}")
                    
                    new_announcements.append(announcement)
        
        print(f"✅ Fetched {announcements_fetched} announcements from API")
        print(f"ℹ️  Parsed dates OK: {parsed_ok}, skipped (no/invalid date): {parsed_fail}")
        print(f"✅ Found {len(new_announcements)} new announcements in date range")

        # Build full candidate set in date range (including already cached ones)
        candidates_in_range = []
        for announcement in all_fetched_announcements:
            pub_date = _get_announcement_pub_date(announcement)
            if pub_date and (start_date_obj <= pub_date <= end_date_obj):
                candidates_in_range.append(announcement)
        print(f"ℹ️  Total announcements in date range (new + existing): {len(candidates_in_range)}\n")
        
        # Apply saved search filters
        print("🔍 Applying saved search filters...")
        print(f"   - Total candidates before filtering: {len(candidates_in_range)} (new: {len(new_announcements)})")
        
        # Ensure filters have all required keys
        filter_dict = {
            'keyword': filters.get('keyword', ''),
            'fornecedor_nif': filters.get('fornecedor_nif', ''),
            'location': filters.get('location', []),
            'cpv_codes': filters.get('cpv_codes', [])
        }
        
        # Debug: Check CPV structure in first few announcements
        if candidates_in_range and filter_dict.get('cpv_codes'):
            print(f"   🔍 Debug: Checking CPV structure in announcements...")
            sample = candidates_in_range[:3]
            for ann in sample:
                cpvs = ann.get('CPVs', [])
                print(f"      - Announcement {ann.get('nAnuncio', 'N/A')}: CPVs = {cpvs} (type: {type(cpvs)})")
        
        # Filter all candidates (not just newly stored)
        filtered_announcements = filter_contracts(candidates_in_range, filter_dict)
        print(f"✅ {len(filtered_announcements)} announcements match filter criteria")

        if candidates_in_range:
            filtered_out = len(candidates_in_range) - len(filtered_announcements)
            print(f"   ℹ️  Filtered out {filtered_out} announcements")
        print()
        
        # Create HubSpot deals
        deals_created = 0
        deals_failed = 0
        
        if filtered_announcements:
            print("🔗 Creating HubSpot deals...")
            try:
                hubspot_token = get_hubspot_token()
            except ValueError as e:
                print(f"⚠️  {e}")
                print("⚠️  Skipping HubSpot deal creation")
                hubspot_token = None
            
            if hubspot_token:
                for i, announcement in enumerate(filtered_announcements, 1):
                    n_anuncio = announcement.get('nAnuncio', 'unknown')
                    print(f"  [{i}/{len(filtered_announcements)}] Processing: {n_anuncio}...", end=" ")
                    
                    # Check if already processed
                    if client.is_announcement_processed(n_anuncio):
                        print("⏭️  Already processed, skipping")
                        continue
                    
                    # Check if deal already exists in HubSpot
                    existing_deal_id = check_deal_exists(n_anuncio, hubspot_token)
                    if existing_deal_id:
                        print(f"✓ Deal already exists (ID: {existing_deal_id})")
                        client.mark_announcement_processed(
                            n_anuncio,
                            hubspot_deal_id=existing_deal_id,
                            saved_search_name=SAVED_SEARCH_NAME
                        )
                        continue
                    
                    # Create new deal
                    result = create_deal_from_announcement(announcement, hubspot_token)
                    
                    if result and result.get('id'):
                        deal_id = result['id']
                        print(f"✓ Deal created (ID: {deal_id})")
                        deals_created += 1
                        client.mark_announcement_processed(
                            n_anuncio,
                            hubspot_deal_id=deal_id,
                            saved_search_name=SAVED_SEARCH_NAME
                        )
                    else:
                        print("✗ Failed to create deal")
                        deals_failed += 1
                        # Still mark as processed to avoid retrying failed ones indefinitely
                        client.mark_announcement_processed(
                            n_anuncio,
                            saved_search_name=SAVED_SEARCH_NAME
                        )
                    
                    # Rate limiting - wait between requests
                    time.sleep(0.3)
                
                print(f"\n✅ Deal creation complete: {deals_created} created, {deals_failed} failed")
            else:
                print("⚠️  HubSpot token not available, skipping deal creation")
        else:
            print("ℹ️  No matching announcements to process")
        
        # Log results
        client.log_daily_sync(
            sync_date=sync_date,
            announcements_fetched=announcements_fetched,
            announcements_new=len(new_announcements),
            deals_created=deals_created,
            deals_failed=deals_failed,
            sync_status="success" if deals_failed == 0 else "partial"
        )
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 Summary")
        print("=" * 80)
        print(f"  Announcements fetched: {announcements_fetched}")
        print(f"  New announcements: {len(new_announcements)}")
        print(f"  Matching filter: {len(filtered_announcements)}")
        print(f"  Deals created: {deals_created}")
        print(f"  Deals failed: {deals_failed}")
        print("=" * 80)
        print("✅ Automation completed successfully!")
        
    except Exception as e:
        error_msg = f"Fatal error: {str(e)}"
        print(f"\n❌ {error_msg}")
        import traceback
        traceback.print_exc()
        
        # Log error
        try:
            client.log_daily_sync(
                sync_date=sync_date,
                announcements_fetched=0,
                announcements_new=0,
                deals_created=0,
                deals_failed=0,
                sync_status="error",
                error_message=error_msg
            )
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    import os
    main()

