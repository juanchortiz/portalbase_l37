#!/usr/bin/env python3
"""
Sync announcements from CSV to HubSpot deals.
Checks for existing deals and creates missing ones.
"""

import csv
import sys
from hubspot_automation import (
    get_hubspot_token, 
    check_deal_exists, 
    create_deal_from_announcement,
    get_pipeline_and_stage_ids,
    PIPELINE_NAME,
    STAGE_NAME
)
import requests
import time


def get_deal_details(deal_id: str, api_token: str) -> dict:
    """Get deal details including pipeline and stage."""
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"
    params = {"properties": "dealname,dealstage,pipeline,numero_de_anuncio"}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ⚠️ Error getting deal details: {e}")
        return None


def convert_csv_row_to_announcement(row: dict) -> dict:
    """Convert CSV row to announcement format expected by hubspot_automation."""
    return {
        'nAnuncio': row.get('N° Anúncio', ''),
        'descricaoAnuncio': row.get('Descrição', ''),
        'url': row.get('View', ''),
        'PecasProcedimento': row.get('Docs', ''),
        'dataPublicacao': row.get('Data Publicação', ''),
        'modeloAnuncio': row.get('Tipo Procedimento', ''),
        'PrecoBase': row.get('Preço Base (€)', '0'),
        'CPVs': [row.get('CPV', '')],
        'designacaoEntidade': row.get('Entidade', ''),
        'PrazoPropostas': 0,
        '_prazo_directo': row.get('Prazo', '')  # Direct deadline from CSV
    }


def main():
    """
    Sync deals from CSV export to HubSpot.
    
    Usage:
        python sync_hubspot_deals.py [csv_path]
        
    If csv_path not provided, uses default path.
    """
    import os
    
    # Get CSV path from command line or use default
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = os.path.join(os.path.dirname(__file__), "announcements_export.csv")
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        print("Usage: python sync_hubspot_deals.py [path_to_csv]")
        sys.exit(1)
    
    print("=" * 80)
    print("🔄 HubSpot Deal Sync from CSV")
    print("=" * 80)
    
    # Get HubSpot token
    try:
        token = get_hubspot_token()
        print("✅ HubSpot token loaded")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Get pipeline and stage IDs
    pipeline_id, stage_id = get_pipeline_and_stage_ids(token)
    if not pipeline_id or not stage_id:
        print(f"❌ Could not find pipeline '{PIPELINE_NAME}' or stage '{STAGE_NAME}'")
        sys.exit(1)
    
    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"\n📋 Found {len(rows)} announcements in CSV\n")
    
    # Stats
    existing = 0
    created = 0
    failed = 0
    wrong_stage = []
    
    for i, row in enumerate(rows, 1):
        n_anuncio = row.get('N° Anúncio', 'unknown')
        desc = row.get('Descrição', '')[:50]
        print(f"[{i}/{len(rows)}] {n_anuncio}: {desc}...", end=" ")
        
        # Check if exists
        existing_deal_id = check_deal_exists(n_anuncio, token)
        
        if existing_deal_id:
            existing += 1
            # Check stage
            deal_details = get_deal_details(existing_deal_id, token)
            if deal_details:
                props = deal_details.get('properties', {})
                current_stage = props.get('dealstage', '')
                current_pipeline = props.get('pipeline', '')
                
                if current_stage != stage_id or current_pipeline != pipeline_id:
                    wrong_stage.append({
                        'deal_id': existing_deal_id,
                        'n_anuncio': n_anuncio,
                        'current_stage': current_stage,
                        'current_pipeline': current_pipeline,
                        'expected_stage': stage_id,
                        'expected_pipeline': pipeline_id
                    })
                    print(f"⚠️ Exists (ID: {existing_deal_id}) but in different stage/pipeline")
                else:
                    print(f"✓ Exists (ID: {existing_deal_id})")
            else:
                print(f"✓ Exists (ID: {existing_deal_id})")
        else:
            # Create deal
            announcement = convert_csv_row_to_announcement(row)
            result = create_deal_from_announcement(announcement, token)
            
            if result and result.get('id'):
                created += 1
                print(f"✅ Created (ID: {result['id']})")
            else:
                failed += 1
                print("❌ Failed to create")
        
        # Rate limiting
        time.sleep(0.3)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary")
    print("=" * 80)
    print(f"  Total announcements: {len(rows)}")
    print(f"  Already existed: {existing}")
    print(f"  Created: {created}")
    print(f"  Failed: {failed}")
    
    if wrong_stage:
        print(f"\n⚠️ {len(wrong_stage)} deals in wrong stage/pipeline:")
        for deal in wrong_stage:
            print(f"  - {deal['n_anuncio']} (Deal ID: {deal['deal_id']})")
            print(f"    Current: pipeline={deal['current_pipeline']}, stage={deal['current_stage']}")
    
    print("\n✅ Sync complete!")


if __name__ == "__main__":
    main()
