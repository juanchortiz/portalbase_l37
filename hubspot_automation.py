"""
HubSpot Automation Module

Handles creation of HubSpot deals from Portal Base announcements.
Includes company matching/creation by NIF and deal-company association.
"""

import requests
import json
from datetime import datetime
import calendar
from typing import Dict, Any, Optional, Tuple


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

# Pipeline and stage configuration
PIPELINE_NAME = "concursos"
STAGE_NAME = "Alerta de publicação da plataforma"

# Cache for pipeline/stage IDs (to avoid repeated API calls)
_pipeline_cache = {}

# Cache for company lookups by NIF
_company_cache = {}


def get_pipeline_and_stage_ids(api_token: str) -> tuple:
    """
    Get the pipeline ID and stage ID by their names.
    
    Returns:
        Tuple of (pipeline_id, stage_id) or (None, None) if not found
    """
    global _pipeline_cache
    
    cache_key = f"{PIPELINE_NAME}:{STAGE_NAME}"
    if cache_key in _pipeline_cache:
        return _pipeline_cache[cache_key]
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get all deal pipelines
        url = "https://api.hubapi.com/crm/v3/pipelines/deals"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        pipelines = response.json().get('results', [])
        
        pipeline_id = None
        stage_id = None
        
        for pipeline in pipelines:
            if pipeline.get('label', '').lower() == PIPELINE_NAME.lower():
                pipeline_id = pipeline.get('id')
                # Find the stage
                for stage in pipeline.get('stages', []):
                    if stage.get('label', '').lower() == STAGE_NAME.lower():
                        stage_id = stage.get('id')
                        break
                break
        
        if pipeline_id and stage_id:
            _pipeline_cache[cache_key] = (pipeline_id, stage_id)
            print(f"✓ Found pipeline '{PIPELINE_NAME}' (ID: {pipeline_id})")
            print(f"✓ Found stage '{STAGE_NAME}' (ID: {stage_id})")
            return (pipeline_id, stage_id)
        else:
            print(f"⚠️ Pipeline '{PIPELINE_NAME}' or stage '{STAGE_NAME}' not found")
            print(f"   Available pipelines: {[p.get('label') for p in pipelines]}")
            return (None, None)
            
    except Exception as e:
        print(f"⚠️ Error fetching pipelines: {e}")
        return (None, None)


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
        price_str: Price string (may contain Portuguese formatting) or number
        
    Returns:
        Float value or None if invalid
    """
    if not price_str or price_str == 'N/A':
        return None
    try:
        # If already a number, return it directly
        if isinstance(price_str, (int, float)):
            return float(price_str)
        
        price_str = str(price_str).strip()
        
        # If it's already a valid number string, try direct conversion first
        try:
            return float(price_str)
        except ValueError:
            pass
        
        # Check if it contains comma (Portuguese format: 1.234.567,89)
        if ',' in price_str:
            # Portuguese format: remove dots (thousands), replace comma with dot (decimal)
            cleaned_price = price_str.replace('.', '').replace(',', '.')
            return float(cleaned_price)
        else:
            # No comma - might be English format (1234567.89) or Portuguese without decimals (1.234.567)
            # If it has dots and no comma, check if it's Portuguese thousands separator
            # Portuguese format typically has multiple dots (thousands separators)
            if price_str.count('.') > 1:
                # Multiple dots = Portuguese thousands format (1.234.567)
                cleaned_price = price_str.replace('.', '')
                return float(cleaned_price)
            else:
                # Single or no dot = likely English format (1234567.89)
                return float(price_str)
    except (ValueError, AttributeError):
        return None


def find_company_by_nif(nif: str, api_token: str) -> Optional[str]:
    """
    Search for a HubSpot company by NIF.
    
    Args:
        nif: Entity NIF (tax ID)
        api_token: HubSpot API token
        
    Returns:
        Company ID if found, None otherwise
    """
    global _company_cache
    
    if not nif:
        return None
    
    nif = str(nif).strip()
    if nif in _company_cache:
        return _company_cache[nif]
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    search_url = "https://api.hubapi.com/crm/v3/objects/companies/search"
    search_payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "nif",
                        "operator": "EQ",
                        "value": nif
                    }
                ]
            }
        ],
        "properties": ["hs_object_id", "name", "nif"]
    }
    
    try:
        response = requests.post(search_url, headers=headers, json=search_payload, timeout=30)
        response.raise_for_status()
        results = response.json()
        
        if results.get('results') and len(results['results']) > 0:
            company_id = results['results'][0]['id']
            _company_cache[nif] = company_id
            return company_id
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error searching company by NIF {nif}: {e}")
        return None


def get_entity_info_from_api(nif: str) -> Optional[Dict[str, Any]]:
    """
    Get entity information from Base.gov.pt API.
    
    Args:
        nif: Entity NIF
        
    Returns:
        Entity info dictionary or None
    """
    try:
        from base_api_client import BaseAPIClient
        from config import get_api_key
        
        client = BaseAPIClient(get_api_key())
        entity_info = client.get_entity_info(nif_entidade=nif)
        return entity_info if isinstance(entity_info, dict) else None
    except Exception as e:
        print(f"⚠️ Could not fetch entity info for NIF {nif}: {e}")
        return None


def create_company_from_entity(nif: str, entity_name: str, api_token: str, entity_info: Dict[str, Any] = None) -> Optional[str]:
    """
    Create a HubSpot company from entity data.
    
    Args:
        nif: Entity NIF
        entity_name: Entity name (from announcement)
        api_token: HubSpot API token
        entity_info: Optional entity info from Base API (will fetch if None)
        
    Returns:
        New company ID if created, None otherwise
    """
    global _company_cache
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Build company properties - fill both NIF fields
    properties = {
        "name": entity_name,
        "nif": str(nif),
        "num_contrib": str(nif),  # Número de Contribuinte (NIF) - displayed in UI
        "observacoes_adicionais": "Entidade pública - Dados importados de Base.gov.pt"
    }
    
    # Try to enrich with API data
    if entity_info is None:
        entity_info = get_entity_info_from_api(nif)
    
    if entity_info:
        # Country
        if entity_info.get('descPais'):
            properties['country'] = entity_info.get('descPais', 'Portugal')
        
        # Annual revenue (as contracting entity) - use annualrevenue not total_revenue
        tot_valor_adjudicante = entity_info.get('totAdjudicanteValorContratIni', 0)
        if tot_valor_adjudicante:
            try:
                properties['annualrevenue'] = str(int(float(tot_valor_adjudicante)))
            except:
                pass
        
        # Build comprehensive description with contract statistics
        desc_parts = []
        num_contratos = entity_info.get('numContratos', 0)
        tot_adjudicante = entity_info.get('totAdjudicante', 0)
        tot_adjudicatario = entity_info.get('totAdjudicatario', 0)
        tot_valor_contrat = entity_info.get('totValorContratIni', 0)
        
        desc_parts.append("📊 Dados de Contratação Pública (Base.gov.pt)")
        if num_contratos:
            desc_parts.append(f"Total contratos: {num_contratos:,}")
        if tot_adjudicante:
            desc_parts.append(f"Como adjudicante: {tot_adjudicante:,} contratos (€{tot_valor_adjudicante:,.2f})")
        if tot_adjudicatario:
            desc_parts.append(f"Como adjudicatário: {tot_adjudicatario:,} contratos (€{tot_valor_contrat:,.2f})")
        
        if len(desc_parts) > 1:
            properties['description'] = '\n'.join(desc_parts)
        
        # Set type as PROSPECT for new leads
        properties['type'] = 'PROSPECT'
        
        # Set industry as Hospital/Healthcare
        properties['industry'] = 'HOSPITAL_HEALTH_CARE'
    
    payload = {"properties": properties}
    
    try:
        url = "https://api.hubapi.com/crm/v3/objects/companies"
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        company_id = result.get('id')
        if company_id:
            _company_cache[str(nif)] = company_id
            print(f"   ✓ Created company: {entity_name} (NIF: {nif})")
        return company_id
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_msg = f"{error_msg} - {json.dumps(error_detail)}"
            except:
                pass
        print(f"❌ Error creating company {entity_name}: {error_msg}")
        return None


def find_or_create_company(nif: str, entity_name: str, api_token: str) -> Optional[str]:
    """
    Find existing company by NIF or create a new one.
    
    Args:
        nif: Entity NIF
        entity_name: Entity name
        api_token: HubSpot API token
        
    Returns:
        Company ID (existing or newly created), None if failed
    """
    if not nif:
        return None
    
    # First try to find existing company
    company_id = find_company_by_nif(nif, api_token)
    if company_id:
        return company_id
    
    # Not found, create new company
    return create_company_from_entity(nif, entity_name, api_token)


def associate_deal_with_company(deal_id: str, company_id: str, api_token: str) -> bool:
    """
    Create association between a deal and a company in HubSpot.
    
    Args:
        deal_id: HubSpot deal ID
        company_id: HubSpot company ID
        api_token: HubSpot API token
        
    Returns:
        True if successful, False otherwise
    """
    if not deal_id or not company_id:
        return False
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}/associations/companies/{company_id}/deal_to_company"
    
    try:
        response = requests.put(url, headers=headers, timeout=30)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error associating deal {deal_id} with company {company_id}: {e}")
        return False


def convert_announcement_to_deal_properties(announcement: Dict[str, Any], pipeline_id: str = None, stage_id: str = None) -> Dict[str, Any]:
    """
    Convert announcement data to HubSpot deal properties.
    
    Args:
        announcement: Announcement dictionary from API
        pipeline_id: HubSpot pipeline ID (optional)
        stage_id: HubSpot stage ID (optional)
        
    Returns:
        Dictionary of HubSpot deal properties
    """
    announcement_id = announcement.get('nAnuncio', 'N/A')
    description = announcement.get('descricaoAnuncio', 'N/A')
    
    # Use official DR URL from API
    announcement_url = announcement.get('url', '')
    docs_url = announcement.get('PecasProcedimento', '')
    
    # Get deadline as epoch ms - prefer direct value, otherwise calculate
    deadline_epoch_ms = None
    deadline_str = announcement.get('_prazo_directo', '')
    if deadline_str:
        try:
            dt = datetime.strptime(deadline_str, '%d/%m/%Y')
            deadline_epoch_ms = int(dt.timestamp() * 1000)
        except:
            pass
    if not deadline_epoch_ms:
        deadline_days = announcement.get('PrazoPropostas', 0)
        pub_date_str = announcement.get('dataPublicacao', '')
        if pub_date_str and deadline_days:
            try:
                pub_date = datetime.strptime(pub_date_str, '%d/%m/%Y')
                from datetime import timedelta
                deadline = pub_date + timedelta(days=int(deadline_days))
                deadline_epoch_ms = int(deadline.timestamp() * 1000)
            except:
                pass
    
    # Handle CPVs
    cpvs = announcement.get('CPVs', [])
    cpvs = cpvs if isinstance(cpvs, list) else [str(cpvs)]
    cpvs_str = ', '.join(str(x) for x in cpvs[:5])
    
    # Handle location (from contracts)
    locations = announcement.get('localExecucao', [])
    if isinstance(locations, list) and locations:
        location_str = ', '.join(str(loc) for loc in locations[:3])
    else:
        location_str = ''
    
    properties = {
        "dealname": description[:100] if description != 'N/A' else f"Anúncio {announcement_id}",
        "dealstage": stage_id if stage_id else "appointmentscheduled",
        "pipeline": pipeline_id if pipeline_id else "default",
        "ver_anuncio": announcement_url,
        "documentos": docs_url,
        "numero_de_anuncio": announcement_id,
        "descricao_do_procedimento": description[:500],
        "tipo": announcement.get('modeloAnuncio', 'N/A'),
        "codigos_cpv": cpvs_str,
        "entidade_contratante": announcement.get('designacaoEntidade', 'N/A')
    }
    
    # Add NIF if available
    nif = announcement.get('nifEntidade', '')
    if nif:
        properties['nif_entidade'] = str(nif)
    
    # Add announcement type if available (API uses 'tipoActo')
    tipo_anuncio = announcement.get('tipoActo', '') or announcement.get('TipoAnuncio', '')
    if tipo_anuncio:
        properties['tipo_anuncio'] = tipo_anuncio
    
    # Add location if available
    if location_str:
        properties['local_execucao'] = location_str
    
    if deadline_epoch_ms:
        properties['data_limite_submissao'] = deadline_epoch_ms
    
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
    api_token: str = None,
    associate_company: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Create a HubSpot deal from an announcement.
    Optionally finds or creates the contracting entity as a company and associates it.
    
    Args:
        announcement: Announcement dictionary from API
        api_token: HubSpot API token (if None, will use get_hubspot_token())
        associate_company: If True, find/create company by NIF and associate with deal
        
    Returns:
        Response JSON from HubSpot API, or None if failed
    """
    if api_token is None:
        api_token = get_hubspot_token()
    
    # Get pipeline and stage IDs
    pipeline_id, stage_id = get_pipeline_and_stage_ids(api_token)
    
    properties = convert_announcement_to_deal_properties(announcement, pipeline_id, stage_id)
    
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
        result = response.json()
        deal_id = result.get('id')
        
        # Associate with company if requested
        if associate_company and deal_id:
            nif = announcement.get('nifEntidade', '')
            entity_name = announcement.get('designacaoEntidade', '')
            if nif and entity_name:
                company_id = find_or_create_company(nif, entity_name, api_token)
                if company_id:
                    if associate_deal_with_company(deal_id, company_id, api_token):
                        result['_company_id'] = company_id
                        result['_company_associated'] = True
        
        return result
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

