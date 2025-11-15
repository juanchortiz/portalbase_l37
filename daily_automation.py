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
from datetime import datetime, timedelta
from cached_api_client import CachedBaseAPIClient
from config import get_api_key
from filter_utils import filter_contracts
from hubspot_automation import create_deal_from_announcement, check_deal_exists, get_hubspot_token
import time


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
    
    # Date range: yesterday (announcements published before 5 PM are usually available)
    # You can adjust this to check last N days
    DAYS_TO_CHECK = int(os.environ.get('DAYS_TO_CHECK', '1'))
    end_date = datetime.now() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=DAYS_TO_CHECK - 1)
    
    start_date_str = start_date.strftime('%d/%m/%Y')
    end_date_str = end_date.strftime('%d/%m/%Y')
    sync_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"📅 Date range: {start_date_str} to {end_date_str}")
    print(f"🔍 Using saved search: {SAVED_SEARCH_NAME}\n")
    
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
            # Try to fallback to "Default Automation" if the specified search doesn't exist
            print(f"⚠️  Saved search '{SAVED_SEARCH_NAME}' not found!")
            print("💡 Attempting to use 'Default Automation' as fallback...")
            filters = client.load_search('Default Automation')
            
            if not filters:
                error_msg = f"Saved search '{SAVED_SEARCH_NAME}' not found, and 'Default Automation' also not found!"
                print(f"❌ {error_msg}")
                print("\n💡 Available saved searches:")
                searches = client.get_saved_searches()
                if searches:
                    for search in searches:
                        print(f"   - {search['name']}")
                else:
                    print("   (no saved searches found)")
                
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
                print(f"✅ Using 'Default Automation' filters as fallback")
                # Optionally create the requested search with the same filters
                try:
                    client.save_search(SAVED_SEARCH_NAME, filters)
                    print(f"✅ Created saved search '{SAVED_SEARCH_NAME}' with same filters")
                except:
                    pass  # Ignore if save fails (e.g., already exists)
        
        print(f"✅ Loaded filters: {list(filters.keys())}\n")
        
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
        
        # Filter by date range and get only new ones
        def convert_date(date_str):
            """Convert DD/MM/YYYY to YYYY-MM-DD"""
            if not date_str:
                return None
            parts = date_str.split('/')
            if len(parts) != 3:
                return None
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
        
        start_comparable = convert_date(start_date_str)
        end_comparable = convert_date(end_date_str)
        
        new_announcements = []
        announcements_fetched = len(all_fetched_announcements)
        
        for announcement in all_fetched_announcements:
            pub_date = announcement.get('dataPublicacao', '')
            if not pub_date:
                continue
            
            pub_comparable = convert_date(pub_date)
            if not pub_comparable:
                continue
            
            # Check if within date range
            if start_comparable <= pub_comparable <= end_comparable:
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
        print(f"✅ Found {len(new_announcements)} new announcements in date range\n")
        
        # Apply saved search filters
        print("🔍 Applying saved search filters...")
        filtered_announcements = filter_contracts(new_announcements, filters)
        print(f"✅ {len(filtered_announcements)} announcements match filter criteria\n")
        
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

