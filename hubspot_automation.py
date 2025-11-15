"""
HubSpot Automation Module

Handles creation of HubSpot deals from Portal Base announcements.
"""

import requests
import json
from datetime import datetime
import calendar
from typing import Dict, Any, Optional


def get_hubspot_token() -> str:
    """
    Get HubSpot API token from environment variable or Secrets file.
    
    Returns:
        str: The HubSpot API token
        
    Raises:
        ValueError: If token is not found
    """
    import os
    
    # Try environment variable first
    token = os.environ.get('HUBSPOT_API_TOKEN')
    if token:
        return token
    
    # Try reading from Secrets file (for local development)
    secrets_file = os.path.join(os.path.dirname(__file__), 'Secrets')
    if os.path.exists(secrets_file):
        try:
            with open(secrets_file, 'r') as f:
                content = f.read().strip()
                # Handle format: HUBSPOT_API_TOKEN:"value" or HUBSPOT_API_TOKEN:value
                for line in content.split('\n'):
                    if line.strip().startswith('HUBSPOT_API_TOKEN'):
                        if ':' in line:
                            token = line.split(':', 1)[1].strip().strip('"')
                            if token:
                                return token
        except Exception:
            pass
    
    # Try Streamlit secrets (for cloud deployments)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'HUBSPOT_API_TOKEN' in st.secrets:
            return st.secrets['HUBSPOT_API_TOKEN']
    except (ImportError, FileNotFoundError, KeyError):
        pass
    
    raise ValueError(
        "HubSpot API token not found! Please set HUBSPOT_API_TOKEN environment variable "
        "or add it to Secrets file as: HUBSPOT_API_TOKEN:\"your_token_here\""
    )


HUBSPOT_API_URL = "https://api.hubapi.com/crm/v3/objects/deals"


def convert_date_to_timestamp(date_str: str) -> Optional[int]:
    """
    Convert DD/MM/YYYY to Unix timestamp in milliseconds at midnight UTC.
    
    Args:
        date_str: Date string in format "DD/MM/YYYY"
        
    Returns:
        Unix timestamp in milliseconds, or None if invalid
    """
    if not date_str or date_str == 'N/A':
        return None
    try:
        dt = datetime.strptime(date_str, '%d/%m/%Y')
        # Convert to UTC midnight using calendar.timegm
        timestamp_seconds = calendar.timegm(dt.timetuple())
        timestamp_ms = timestamp_seconds * 1000
        return timestamp_ms
    except (ValueError, AttributeError):
        return None


def format_price(price_str) -> Optional[float]:
    """
    Convert Portuguese price format to float.
    
    Args:
        price_str: Price string (may contain Portuguese formatting)
        
    Returns:
        Float value or None if invalid
    """
    if not price_str or price_str == 'N/A':
        return None
    try:
        # Handle Portuguese format (e.g., "1.234.567,89")
        cleaned_price = str(price_str).replace('.', '').replace(',', '.')
        return float(cleaned_price)
    except (ValueError, AttributeError):
        return None


def convert_announcement_to_deal_properties(announcement: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert announcement data to HubSpot deal properties.
    
    Args:
        announcement: Announcement dictionary from API
        
    Returns:
        Dictionary of HubSpot deal properties
    """
    announcement_id = announcement.get('nAnuncio', 'N/A')
    description = announcement.get('descricaoAnuncio', 'N/A')
    
    # Create Base.gov.pt link
    announcement_url = f"https://www.base.gov.pt/Base4/pt/detalhe/?type=anuncios&id={announcement_id}" if announcement_id != 'N/A' else ''
    docs_url = announcement.get('PecasProcedimento', '')
    
    # Calculate deadline
    deadline_days = announcement.get('PrazoPropostas', 0)
    pub_date_str = announcement.get('dataPublicacao', '')
    deadline_str = 'N/A'
    if pub_date_str and deadline_days:
        try:
            pub_date = datetime.strptime(pub_date_str, '%d/%m/%Y')
            from datetime import timedelta
            deadline = pub_date + timedelta(days=int(deadline_days))
            deadline_str = deadline.strftime('%d/%m/%Y')
        except:
            deadline_str = f"+{deadline_days} dias"
    
    # Handle CPVs
    cpvs = announcement.get('CPVs', [])
    cpvs = cpvs if isinstance(cpvs, list) else [str(cpvs)]
    cpvs_str = ', '.join(str(x) for x in cpvs[:5])  # Limit to 5 CPVs
    
    properties = {
        "dealname": description[:100] if description != 'N/A' else f"Anúncio {announcement_id}",  # Deal name
        "dealstage": "appointmentscheduled",  # Default stage
        "pipeline": "default",  # Default pipeline
        "ver_anuncio": announcement_url,
        "documentos": docs_url,
        "numero_de_anuncio": announcement_id,
        "prazo_de_submissao": deadline_str,
        "descricao_do_procedimento": description[:500],  # Limit length
        "tipo": announcement.get('modeloAnuncio', 'N/A'),
        "codigos_cpv": cpvs_str,
        "entidade_contratante": announcement.get('designacaoEntidade', 'N/A')
    }
    
    # Add publication date if available
    pub_date = convert_date_to_timestamp(pub_date_str)
    if pub_date:
        properties['data_de_publicacao'] = pub_date
    
    # Add price if available
    price = format_price(announcement.get('PrecoBase', '0'))
    if price:
        properties['preco_eur'] = price
    
    return properties


def create_deal_from_announcement(
    announcement: Dict[str, Any],
    api_token: str = None
) -> Optional[Dict[str, Any]]:
    """
    Create a HubSpot deal from an announcement.
    
    Args:
        announcement: Announcement dictionary from API
        api_token: HubSpot API token (if None, will use get_hubspot_token())
        
    Returns:
        Response JSON from HubSpot API, or None if failed
    """
    if api_token is None:
        api_token = get_hubspot_token()
    
    properties = convert_announcement_to_deal_properties(announcement)
    
    payload = {
        "properties": properties
    }
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(HUBSPOT_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_msg = f"{error_msg} - {json.dumps(error_detail)}"
            except:
                error_msg = f"{error_msg} - {e.response.text[:200]}"
        print(f"❌ Error creating deal for {announcement.get('nAnuncio', 'unknown')}: {error_msg}")
        return None


def check_deal_exists(n_anuncio: str, api_token: str = None) -> Optional[str]:
    """
    Check if a deal already exists in HubSpot for this announcement.
    
    Args:
        n_anuncio: Announcement number
        api_token: HubSpot API token (if None, will use get_hubspot_token())
        
    Returns:
        Deal ID if found, None otherwise
    """
    if api_token is None:
        api_token = get_hubspot_token()
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Search for deal by announcement number
    search_url = "https://api.hubapi.com/crm/v3/objects/deals/search"
    search_payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "numero_de_anuncio",
                        "operator": "EQ",
                        "value": n_anuncio
                    }
                ]
            }
        ],
        "properties": ["hs_object_id"]
    }
    
    try:
        response = requests.post(search_url, headers=headers, json=search_payload, timeout=30)
        response.raise_for_status()
        results = response.json()
        
        if results.get('results') and len(results['results']) > 0:
            return results['results'][0]['id']
        return None
    except requests.exceptions.RequestException as e:
        # If search fails, assume deal doesn't exist (don't block creation)
        print(f"⚠️  Could not check for existing deal: {e}")
        return None

