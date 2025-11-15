"""
Portal Base - Interactive Web Application

A Streamlit app for browsing and filtering Portuguese public procurement data.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from cached_api_client import CachedBaseAPIClient
from config import get_api_key
import json

# CPV Codes Dictionary - Portuguese Healthcare and Laboratory Focus
CPV_CODES = {
    # Healthcare & Medical Equipment
    "33000000-0": "EQUIPAMENTO MÉDICO, MEDICAMENTOS E PRODUTOS PARA CUIDADOS PESSOAIS",
    "33100000-1": "EQUIPAMENTO MÉDICO",
    "33140000-3": "CONSUMÍVEIS MÉDICOS",
    "33141000-0": "PRODUTOS MÉDICOS DESCARTÁVEIS NÃO QUÍMICOS",
    "33183000-0": "DISPOSITIVOS DE PERFUSÃO, INJECTÁVEIS E DE IRRIGAÇÃO",
    "33600000-6": "PRODUTOS FARMACÊUTICOS",
    "33631000-8": "PRODUTOS FARMACÊUTICOS PARA O APARELHO DIGESTIVO E METABOLISMO",
    "33651000-4": "PRODUTOS FARMACÊUTICOS PARA O SANGUE E ÓRGÃOS HEMATOPOIÉTICOS",
    "33690000-3": "PRODUTOS FARMACÊUTICOS VÁRIOS",
    "33692000-7": "PRODUTOS NUTRICIONAIS",
    
    # Laboratory & Diagnostics
    "33696500-0": "REAGENTES DE LABORATÓRIO",
    "33698000-4": "KITS DE DIAGNÓSTICO",
    "33527200-7": "EQUIPAMENTO DE IMAGIOLOGIA MÉDICA",
    "33124100-3": "APARELHOS DE DIAGNÓSTICO",
    "38000000-5": "EQUIPAMENTO DE LABORATÓRIO, ÓPTICO E DE PRECISÃO",
    "38430000-4": "EQUIPAMENTO DE MEDIÇÃO E CONTROLO",
    "38433000-5": "INSTRUMENTOS DE ANÁLISE",
    "38434000-2": "INSTRUMENTOS DE LABORATÓRIO",
    "38436000-6": "EQUIPAMENTO DE TESTES",
    "24931250-6": "MEIOS DE CULTURA",
    "24000000-4": "PRODUTOS QUÍMICOS",
    "24300000-7": "PRODUTOS QUÍMICOS DE BASE",
    "24900000-6": "PRODUTOS QUÍMICOS DIVERSOS",
    
    # Health Services
    "85000000-9": "SERVIÇOS SAÚDE E ACÇÃO SOCIAL",
    "85100000-0": "SERVIÇOS DE SAÚDE",
    "85110000-3": "SERVIÇOS HOSPITALARES E SERVIÇOS CONEXOS",
    "85121000-3": "SERVIÇOS MÉDICOS",
    "85140000-2": "SERVIÇOS DIVERSOS DE SAÚDE",
    "85145000-7": "SERVIÇOS DE ANÁLISES MÉDICAS",
    
    # Environmental & Waste Services
    "90000000-7": "SERVIÇOS RELATIVOS A ÁGUAS RESIDUAIS, RESÍDUOS, LIMPEZA E AMBIENTE",
    "90500000-2": "SERVIÇOS RELACIONADOS COM RESÍDUOS E LIXO",
    "90511000-2": "SERVIÇOS DE RECOLHA DE LIXO",
    "90520000-8": "SERVIÇOS RELACIONADOS COM RESÍDUOS RADIOACTIVOS, TÓXICOS, MÉDICOS E PERIGOSOS",
    "90524000-6": "SERVIÇOS DE GESTÃO DE RESÍDUOS MÉDICOS",
}

def get_cpv_display_options():
    """Get CPV codes formatted for display in multiselect."""
    return [f"{code} - {desc}" for code, desc in sorted(CPV_CODES.items())]

def extract_cpv_codes_from_selection(selected_options):
    """Extract CPV codes from selected display options."""
    if not selected_options:
        return []
    return [option.split(' - ')[0] for option in selected_options]

# Common locations in Portugal (from database analysis)
COMMON_LOCATIONS = [
    "All",
    "Portugal",
    "Portugal, Lisboa, Lisboa",
    "Portugal, Porto, Porto",
    "Portugal, Braga, Braga",
    "Portugal, Coimbra, Coimbra",
    "Portugal, Região Autónoma da Madeira, Funchal",
    "Portugal, Viseu, Viseu",
    "Portugal, Porto, Vila Nova de Gaia",
    "Portugal, Porto, Matosinhos",
    "Portugal, Braga, Barcelos",
    "Portugal, Braga, Guimarães",
    "Portugal, Braga, Vila Nova de Famalicão",
    "Portugal, Évora, Évora",
    "Portugal, Beja, Beja",
    "Portugal, Leiria, Leiria",
    "Portugal, Leiria, Caldas da Rainha",
    "Portugal, Lisboa, Sintra",
    "Portugal, Lisboa, Cascais",
    "Portugal, Lisboa, Loures",
    "Portugal, Lisboa, Oeiras",
    "Portugal, Lisboa, Odivelas",
    "Portugal, Setúbal, Setúbal",
    "Portugal, Setúbal, Almada",
    "Portugal, Setúbal, Seixal",
    "Portugal, Porto, Felgueiras",
    "Portugal, Porto, Paredes",
    "Portugal, Porto, Paços de Ferreira",
    "Portugal, Coimbra, Figueira da Foz",
    "Portugal, Coimbra, Arganil",
    "Portugal, Coimbra, Miranda do Corvo",
    "Portugal, Aveiro, Santa Maria da Feira",
    "Portugal, Viana do Castelo, Viana do Castelo",
    "Portugal, Santarém, Ourém",
    "Portugal, Castelo Branco, Castelo Branco",
    "Portugal, Castelo Branco, Covilhã",
    "Portugal, Vila Real, Vila Real",
    "Portugal, Região Autónoma dos Açores, Ponta Delgada",
    "Portugal, Região Autónoma dos Açores, Angra do Heroismo",
]


# Page configuration
st.set_page_config(
    page_title="Portal Base - Public Procurement",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state - lazy loading to avoid startup delays
if 'client' not in st.session_state:
    st.session_state.client = None
    
if 'client_initialized' not in st.session_state:
    st.session_state.client_initialized = False

if 'filtered_contracts' not in st.session_state:
    st.session_state.filtered_contracts = []

if 'filtered_announcements' not in st.session_state:
    st.session_state.filtered_announcements = []

if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False

if 'loaded_filters' not in st.session_state:
    st.session_state.loaded_filters = None

if 'current_search_name' not in st.session_state:
    st.session_state.current_search_name = None

if 'search_type' not in st.session_state:
    st.session_state.search_type = 'contracts'  # 'contracts' or 'announcements'


def format_price(price_str):
    """Convert Portuguese price format to float."""
    try:
        if not price_str or price_str == "N/A":
            return 0.0
        return float(str(price_str).replace(".", "").replace(",", "."))
    except (ValueError, AttributeError):
        return 0.0


def filter_contracts(contracts, filters):
    """Apply filters to contracts and announcements (unified function)."""
    filtered = contracts
    
    # Keyword filter (supports comma-separated keywords)
    if filters['keyword']:
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
    if filters['fornecedor_nif']:
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


def contracts_to_dataframe(contracts):
    """Convert contracts to a pandas DataFrame with clickable links."""
    if not contracts:
        return pd.DataFrame()
    
    data = []
    for contract in contracts:
        # API returns lowercase 'idcontrato' not 'idContrato'
        contract_id = contract.get('idcontrato') or contract.get('idContrato', 'N/A')
        announcement_id = contract.get('nAnuncio', 'N/A')
        
        # Create Base.gov.pt links
        contract_url = f"https://www.base.gov.pt/Base4/pt/detalhe/?type=contratos&id={contract_id}" if contract_id != 'N/A' else ''
        announcement_url = f"https://www.base.gov.pt/Base4/pt/detalhe/?type=anuncios&id={announcement_id}" if announcement_id != 'N/A' else ''
        
        # Safely handle list fields that might contain non-strings
        tipo_contrato = contract.get('tipoContrato', ['N/A'])
        tipo_contrato = tipo_contrato if isinstance(tipo_contrato, list) else [str(tipo_contrato)]
        
        cpv = contract.get('cpv', ['N/A'])
        cpv = cpv if isinstance(cpv, list) else [str(cpv)]
        
        adjudicante = contract.get('adjudicante', ['N/A'])
        adjudicante = adjudicante if isinstance(adjudicante, list) else [str(adjudicante)]
        
        adjudicatarios = contract.get('adjudicatarios', ['N/A'])
        adjudicatarios = adjudicatarios if isinstance(adjudicatarios, list) else [str(adjudicatarios)]
        
        local = contract.get('localExecucao', ['N/A'])
        local = local if isinstance(local, list) else [str(local)]
        
        data.append({
            'View Contract': contract_url,  # New column with link
            'ID': contract_id,
            'Publication Date': contract.get('dataPublicacao', 'N/A'),
            'Object': contract.get('objectoContrato', 'N/A'),
            'Type': ', '.join(str(x) for x in tipo_contrato),
            'Price (€)': format_price(contract.get('precoContratual', '0')),
            'CPV Codes': ', '.join(str(x) for x in cpv[:3]),
            'Contracting Entity': ', '.join(str(x) for x in adjudicante),
            'Contractors': ', '.join(str(x) for x in adjudicatarios),
            'Location': ', '.join(str(x) for x in local),
        })
    
    return pd.DataFrame(data)


def announcements_to_dataframe(announcements):
    """Convert announcements to a pandas DataFrame with clickable links."""
    if not announcements:
        return pd.DataFrame()
    
    data = []
    for announcement in announcements:
        announcement_id = announcement.get('nAnuncio', 'N/A')
        
        # Create Base.gov.pt link
        announcement_url = f"https://www.base.gov.pt/Base4/pt/detalhe/?type=anuncios&id={announcement_id}" if announcement_id != 'N/A' else ''
        docs_url = announcement.get('PecasProcedimento', '')
        
        # Calculate deadline date
        from datetime import datetime, timedelta
        deadline_days = announcement.get('PrazoPropostas', 0)
        pub_date_str = announcement.get('dataPublicacao', '')
        deadline_str = 'N/A'
        if pub_date_str and deadline_days:
            try:
                pub_date = datetime.strptime(pub_date_str, '%d/%m/%Y')
                deadline = pub_date + timedelta(days=int(deadline_days))
                deadline_str = deadline.strftime('%d/%m/%Y')
            except:
                deadline_str = f"+{deadline_days} dias"
        
        # Safely handle CPVs field
        cpvs = announcement.get('CPVs', ['N/A'])
        cpvs = cpvs if isinstance(cpvs, list) else [str(cpvs)]
        
        data.append({
            'View': announcement_url,
            'Docs': docs_url,
            'N° Anúncio': announcement_id,
            'Data Publicação': pub_date_str,
            'Prazo': deadline_str,
            'Descrição': announcement.get('descricaoAnuncio', 'N/A')[:100],
            'Tipo Procedimento': announcement.get('modeloAnuncio', 'N/A'),
            'Preço Base (€)': format_price(announcement.get('PrecoBase', '0')),
            'CPV': ', '.join(str(x) for x in cpvs[:2]),
            'Entidade': announcement.get('designacaoEntidade', 'N/A'),
        })
    
    return pd.DataFrame(data)


def main():
    # Hero section with brand gradient background
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #6e0102 0%, #191d34 100%);
        height: 200px;
        width: 100%;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 40px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    ">
        <div style="color: white;">
            <h1 style="margin: 0; font-size: 2.5em; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🚨 Portal Base</h1>
            <p style="margin: 5px 0 0 0; font-size: 1.2em; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">Concursos e Contratos Públicos</p>
            <p style="margin: 5px 0 0 0; font-size: 0.9em; color: rgba(255,255,255,0.8);">Powered by Link37</p>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 60px; font-weight: bold; color: #FFFFFF; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">link</span><span style="font-size: 60px; font-weight: bold; color: #FFFFFF; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">37</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Initialize API client lazily
    if not st.session_state.client_initialized:
        try:
            with st.spinner('Initializing database...'):
                ACCESS_TOKEN = get_api_key()
                st.session_state.client = CachedBaseAPIClient(ACCESS_TOKEN)
                st.session_state.client_initialized = True
        except Exception as e:
            st.error(f"❌ Error initializing: {str(e)}")
            st.info("Please refresh the page or check your API key configuration.")
            st.stop()
    
    # Sidebar - Filters
    st.sidebar.header("🔍 Filtros")
    
    # Date range selection
    # Search Type Selection (Contracts or Open Procedures)
    st.sidebar.subheader("Tipo de Busca")
    search_type = st.sidebar.radio(
        "Buscar:",
        ["📋 Contratos", "📢 Procedimentos Abertos"],
        index=0 if st.session_state.search_type == 'contracts' else 1,
        help="Escolha entre buscar contratos celebrados ou procedimentos abertos (anúncios)"
    )
    st.session_state.search_type = 'contracts' if search_type == "📋 Contratos" else 'announcements'
    
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("Datas")
    
    # Show cache info
    stats = st.session_state.client.get_cache_stats()
    if stats['years_cached']:
        last_update = stats['years_cached'][0]['last_fetched'][:10] if stats['years_cached'] else 'Unknown'
        st.sidebar.caption(f"📅 Cache last updated: {last_update}")
    
    # Check if we have loaded filters
    loaded = st.session_state.loaded_filters
    if loaded and loaded.get('search_type'):
        # Update search type if loaded from saved search
        st.session_state.search_type = loaded.get('search_type', 'contracts')
    
    date_options = ["Last 30 days", "Last 90 days", "Custom range", "Today", "Yesterday"]
    default_date_idx = 0
    if loaded and loaded.get('date_option'):
        try:
            default_date_idx = date_options.index(loaded['date_option'])
        except ValueError:
            pass
    
    date_option = st.sidebar.radio(
        "Select period:",
        date_options,
        index=default_date_idx
    )
    
    if date_option == "Custom range":
        st.sidebar.markdown("**Data Inicial**")
        default_start = datetime.now() - timedelta(days=30)
        if loaded and loaded.get('start_date'):
            try:
                from datetime import date
                default_start = date.fromisoformat(loaded['start_date'])
            except:
                pass
        
        start_date = st.sidebar.date_input(
            "Escolher data inicial:",
            value=default_start,
            max_value=datetime.now(),
            format="DD/MM/YYYY",
            label_visibility="collapsed"
        )
        
        st.sidebar.markdown("**Data Final**")
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            default_end = datetime.now() - timedelta(days=1)
            if loaded and loaded.get('end_date'):
                try:
                    from datetime import date
                    default_end = date.fromisoformat(loaded['end_date'])
                except:
                    pass
            
            end_date = st.date_input(
                "Escolher data final:",
                value=default_end,
                max_value=datetime.now(),
                format="DD/MM/YYYY",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("Hoje", use_container_width=True):
                end_date = datetime.now().date()
                st.rerun()
        
        # Validate date range
        if start_date > end_date:
            st.sidebar.error("⚠️ Data inicial não pode ser posterior à data final!")
            # Reset to valid range
            start_date = end_date
    else:
        if date_option == "Today":
            start_date = end_date = datetime.now().date()
        elif date_option == "Yesterday":
            start_date = end_date = (datetime.now() - timedelta(days=1)).date()
        elif date_option == "Last 90 days":
            start_date = (datetime.now() - timedelta(days=90)).date()
            end_date = (datetime.now() - timedelta(days=1)).date()
        else:  # Last 30 days
            start_date = (datetime.now() - timedelta(days=30)).date()
            end_date = (datetime.now() - timedelta(days=1)).date()
    
    st.sidebar.markdown("---")
    
    # Keyword filter
    st.sidebar.subheader("Keyword Search")
    default_keyword = loaded.get('keyword', '') if loaded else ''
    keyword = st.sidebar.text_input(
        "Search keywords (comma-separated):",
        value=default_keyword,
        help="Enter keywords separated by commas. Example: 'reagentes, laboratório, análises'"
    )
    
    # Fornecedor (Supplier) filter
    st.sidebar.subheader("Fornecedores (adjudicatarios) ")
    default_nif = loaded.get('fornecedor_nif', '') if loaded else ''
    fornecedor_nif = st.sidebar.text_input(
        "NIF do Fornecedor:",
        value=default_nif,
        help="Filter by supplier/contractor NIF"
    )
    
    # Location filter
    st.sidebar.subheader("Location")
    default_locations = loaded.get('location', []) if loaded else []
    selected_locations = st.sidebar.multiselect(
        "Select Locations:",
        options=[loc for loc in COMMON_LOCATIONS if loc != "All"],
        default=default_locations,
        help="Filter by execution location (select multiple)"
    )
    # Convert list to filter format
    location = selected_locations if selected_locations else []
    
    # CPV filter
    st.sidebar.subheader("CPV Classification")
    cpv_options = get_cpv_display_options()
    default_cpvs = loaded.get('cpv_codes', []) if loaded else []
    selected_cpvs = st.sidebar.multiselect(
        "Select CPV Categories:",
        options=cpv_options,
        default=default_cpvs,
        help="Select one or more CPV categories. Use the search to find specific categories.",
        placeholder="Search and select CPV codes..."
    )
    cpv_codes = extract_cpv_codes_from_selection(selected_cpvs)
    
    # Clear loaded filters after applying them
    if st.session_state.loaded_filters:
        st.session_state.loaded_filters = None
    
    st.sidebar.markdown("---")
    
    # Saved Searches section
    with st.sidebar.expander("💾 Saved Searches"):
        # Get all saved searches
        try:
            saved_searches = st.session_state.client.get_saved_searches()
        except Exception as e:
            st.error(f"Error loading saved searches: {str(e)}")
            saved_searches = []
        
        # Show current loaded search
        if st.session_state.current_search_name:
            st.info(f"📂 Loaded: **{st.session_state.current_search_name}**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Update Search", use_container_width=True, help="Update the loaded search with current filters"):
                    # Collect current filters
                    current_filters = {
                        'search_type': st.session_state.search_type,
                        'date_option': date_option,
                        'start_date': start_date.isoformat() if date_option == "Custom range" else None,
                        'end_date': end_date.isoformat() if date_option == "Custom range" else None,
                        'keyword': keyword,
                        'fornecedor_nif': fornecedor_nif,
                        'location': location,
                        'cpv_codes': selected_cpvs
                    }
                    
                    if st.session_state.client.save_search(st.session_state.current_search_name, current_filters):
                        st.success(f"✅ Updated: {st.session_state.current_search_name}")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to update")
            with col2:
                if st.button("❌ Clear", use_container_width=True, help="Clear loaded search"):
                    st.session_state.current_search_name = None
                    st.session_state.loaded_filters = None
                    st.rerun()
            st.markdown("---")
        
        # Load saved search
        if saved_searches:
            st.markdown("**Load a saved search:**")
            search_names = [s['name'] for s in saved_searches]
            selected_search = st.selectbox(
                "Select search:",
                [""] + search_names,
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📂 Load", disabled=not selected_search, use_container_width=True):
                    loaded_filters = st.session_state.client.load_search(selected_search)
                    if loaded_filters:
                        # Store loaded filters to apply them
                        st.session_state.loaded_filters = loaded_filters
                        st.session_state.current_search_name = selected_search
                        # Update search type if saved in search
                        if loaded_filters.get('search_type'):
                            st.session_state.search_type = loaded_filters.get('search_type', 'contracts')
                        st.success(f"Loaded: {selected_search}")
                        st.rerun()
            with col2:
                if st.button("🗑️ Delete", disabled=not selected_search, use_container_width=True):
                    if st.session_state.client.delete_search(selected_search):
                        if st.session_state.current_search_name == selected_search:
                            st.session_state.current_search_name = None
                            st.session_state.loaded_filters = None
                        st.success(f"Deleted: {selected_search}")
                        st.rerun()
        else:
            st.info("No saved searches yet")
        
        st.markdown("---")
        
        # Save current search
        st.markdown("**Save current filters:**")
        search_name = st.text_input(
            "Search name:",
            placeholder="e.g., Lab Equipment Porto",
            value=st.session_state.current_search_name if st.session_state.current_search_name else "",
            label_visibility="collapsed"
        )
        if st.button("💾 Save Search", use_container_width=True, disabled=not search_name):
            # Collect current filters
            current_filters = {
                'search_type': st.session_state.search_type,
                'date_option': date_option,
                'start_date': start_date.isoformat() if date_option == "Custom range" else None,
                'end_date': end_date.isoformat() if date_option == "Custom range" else None,
                'keyword': keyword,
                'fornecedor_nif': fornecedor_nif,
                'location': location,
                'cpv_codes': selected_cpvs
            }
            
            if st.session_state.client.save_search(search_name, current_filters):
                st.session_state.current_search_name = search_name
                st.success(f"✅ Saved: {search_name}")
                st.rerun()
            else:
                st.error(f"❌ Name '{search_name}' already exists")
    
    st.sidebar.markdown("---")
    
    # Search button
    search_button = st.sidebar.button("🔎 Search", type="primary", use_container_width=True)
    
    # Cache info in sidebar
    with st.sidebar.expander("ℹ️ Cache Information"):
        stats = st.session_state.client.get_cache_stats()
        st.write(f"**Total contracts cached:** {stats['total_contracts']:,}")
        st.write(f"**Total announcements cached:** {stats['total_announcements']:,}")
        if stats['years_cached']:
            st.write("**Years in cache:**")
            for year_info in stats['years_cached']:
                last_fetched = datetime.fromisoformat(year_info['last_fetched'][:19])
                st.write(f"  • {year_info['year']}: {last_fetched.strftime('%Y-%m-%d %H:%M')}")
    
    # Main content area
    if search_button:
        st.session_state.search_performed = True  # Mark that a search has been performed
        search_type_label = "contracts" if st.session_state.search_type == 'contracts' else "open procedures"
        with st.spinner(f'Searching {search_type_label}...'):
            # Convert dates to Portuguese format
            start_str = start_date.strftime("%d/%m/%Y")
            end_str = end_date.strftime("%d/%m/%Y")
            
            # Get data based on search type
            if st.session_state.search_type == 'contracts':
                # Get contracts only
                if start_date == end_date:
                    contracts = st.session_state.client.get_contracts_by_date(start_str)
                    announcements = []
                else:
                    contracts = st.session_state.client.get_contracts_by_date_range(start_str, end_str)
                    announcements = []
            else:
                # Get announcements (open procedures) only
                contracts = []
                if start_date == end_date:
                    announcements = st.session_state.client.get_announcements_by_date(start_str)
                else:
                    announcements = []
                    current_date = start_date
                    while current_date <= end_date:
                        date_str = current_date.strftime("%d/%m/%Y")
                        announcements.extend(st.session_state.client.get_announcements_by_date(date_str))
                        current_date += timedelta(days=1)
            
            # Debug: Show initial results
            if st.session_state.search_type == 'contracts':
                st.info(f"📊 Found {len(contracts)} contracts in date range")
            else:
                st.info(f"📊 Found {len(announcements)} open procedures in date range")
            
            # Apply filters
            filters = {
                'keyword': keyword,
                'fornecedor_nif': fornecedor_nif,
                'location': location,
                'cpv_codes': cpv_codes
            }
            
            # Debug: Show active filters
            active_filters = []
            if keyword: active_filters.append(f"Keywords: {keyword}")
            if fornecedor_nif: active_filters.append(f"Fornecedor NIF: {fornecedor_nif}")
            if location: active_filters.append(f"Locations: {len(location)}")
            if cpv_codes: 
                active_filters.append(f"CPV Codes: {len(cpv_codes)}")
                with st.expander("🔍 View selected CPV codes"):
                    for code in cpv_codes[:10]:
                        st.write(f"- {code}")
                    if len(cpv_codes) > 10:
                        st.write(f"... and {len(cpv_codes) - 10} more")
            
            if active_filters:
                st.info(f"🔍 Active filters: {', '.join(active_filters)}")
            
            # Filter based on search type
            if st.session_state.search_type == 'contracts':
                filtered = filter_contracts(contracts, filters)
                st.session_state.filtered_contracts = filtered
                st.session_state.filtered_announcements = []
            else:
                filtered_announcements = filter_contracts(announcements, filters)
                st.session_state.filtered_announcements = filtered_announcements
                st.session_state.filtered_contracts = []
            
            # Debug: Show filtered results
            if st.session_state.search_type == 'contracts':
                if filtered:
                    st.success(f"✅ {len(filtered)} contracts match your filters")
                else:
                    st.warning(f"⚠️ No contracts found matching your filters. Try adjusting them.")
            else:
                if filtered_announcements:
                    st.success(f"✅ {len(filtered_announcements)} open procedures match your filters")
                else:
                    st.warning(f"⚠️ No open procedures found matching your filters. Try adjusting them.")
    
    # Display results
    if st.session_state.filtered_contracts or st.session_state.filtered_announcements:
        # Determine which type of results to show
        if st.session_state.search_type == 'contracts' and st.session_state.filtered_contracts:
            contracts = st.session_state.filtered_contracts
            announcements = []
            
            # Toggle for Data Highlights
            show_highlights = st.checkbox("📊 Show Data Highlights", value=True)
            
            if show_highlights:
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                total_value = sum(format_price(c.get('precoContratual', '0')) for c in contracts)
                
                with col1:
                    st.metric("Total Contracts", len(contracts))
                with col2:
                    st.metric("Total Value", f"€{total_value:,.2f}")
                with col3:
                    avg_value = total_value / len(contracts) if contracts else 0
                    st.metric("Average Value", f"€{avg_value:,.2f}")
                with col4:
                    unique_entities = len(set(
                        entity
                        for c in contracts
                        for entity in (c.get('adjudicante', []) if isinstance(c.get('adjudicante'), list) else [])
                    ))
                    st.metric("Unique Entities", unique_entities)
            
            st.markdown("---")
            
            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Contratos", "📢 Procedimentos Abertos", "📈 Analytics", "📄 Detailed View"])
            
            with tab1:
                # Convert to DataFrame
                df = contracts_to_dataframe(contracts)
                
                # Display table with clickable links
                st.dataframe(
                df,
                use_container_width=True,
                height=600,
                column_config={
                    "View Contract": st.column_config.LinkColumn(
                        "🔗 Contract",
                        help="Click to view full contract on Base.gov.pt",
                        display_text="View"
                    ),
                    "Price (€)": st.column_config.NumberColumn(
                        "Price (€)",
                        format="€%.2f"
                    )
                },
                hide_index=True
            )
            
            # Download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
            with tab2:
                # Announcements/Open Procedures Tab (for contracts view - shows empty if searching contracts)
                if announcements:
                    st.subheader(f"📢 {len(announcements)} Open Procedures Found")
                    
                    # Convert to DataFrame and display
                    df_announcements = announcements_to_dataframe(announcements)
                    
                    # Display the table with clickable links
                    st.dataframe(
                        df_announcements,
                        use_container_width=True,
                        height=600,
                        column_config={
                            "View": st.column_config.LinkColumn(
                                "🔗 Ver",
                                help="Click to view announcement on Base.gov.pt",
                                display_text="Ver"
                            ),
                            "Docs": st.column_config.LinkColumn(
                                "📄 Docs",
                                help="Click to download procedure documents",
                                display_text="Docs"
                            ),
                            "Preço Base (€)": st.column_config.NumberColumn(
                                "Preço Base (€)",
                                format="€%.2f"
                            )
                        },
                        hide_index=True,
                    )
                    
                    # Download button
                    csv_announcements = df_announcements.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv_announcements,
                        file_name=f"announcements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )
                    
                    # Summary statistics
                    st.markdown("---")
                    st.subheader("📊 Procedure Statistics")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        total_base_price = sum(format_price(a.get('PrecoBase', '0')) for a in announcements)
                        st.metric("Total Base Price", f"€{total_base_price:,.2f}")
                    
                    with col2:
                        unique_entities = len(set(a.get('designacaoEntidade', 'N/A') for a in announcements))
                        st.metric("Unique Entities", unique_entities)
                    
                    with col3:
                        avg_base_price = total_base_price / len(announcements) if announcements else 0
                        st.metric("Average Base Price", f"€{avg_base_price:,.2f}")
                else:
                    st.info("No open procedures found. Try adjusting your search filters or date range.")
            
            with tab3:
                col1, col2 = st.columns(2)
            
            with col1:
                # Contract types distribution
                st.subheader("Contract Types Distribution")
                type_counts = {}
                for c in contracts:
                    tipos = c.get('tipoContrato', ['Unknown'])
                    if not isinstance(tipos, list):
                        tipos = [str(tipos)]
                    for ctype in tipos:
                        type_counts[ctype] = type_counts.get(ctype, 0) + 1
                
                if type_counts:
                    type_df = pd.DataFrame(
                        list(type_counts.items()),
                        columns=['Type', 'Count']
                    ).sort_values('Count', ascending=False)
                    
                    st.bar_chart(type_df.set_index('Type'))
                else:
                    st.info("No contract type data available")
            
            with col2:
                # Top contracting entities
                st.subheader("Top 10 Contracting Entities")
                entity_counts = {}
                for c in contracts:
                    entities = c.get('adjudicante', [])
                    if not isinstance(entities, list):
                        entities = [str(entities)] if entities else []
                    for entity in entities:
                        if entity:  # Skip empty strings
                            entity_counts[entity] = entity_counts.get(entity, 0) + 1
                
                if entity_counts:
                    top_entities = sorted(
                        entity_counts.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]
                    
                    entity_df = pd.DataFrame(top_entities, columns=['Entity', 'Contracts'])
                    st.dataframe(entity_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No entity data available")
            
                # Price distribution
                st.subheader("Price Distribution")
                prices = [format_price(c.get('precoContratual', '0')) for c in contracts]
                prices = [p for p in prices if p > 0]  # Remove zero prices
                
                if prices:
                    price_df = pd.DataFrame({'Price (€)': prices})
                    st.bar_chart(price_df['Price (€)'])
                    
                    st.write(f"**Min Price:** €{min(prices):,.2f}")
                    st.write(f"**Max Price:** €{max(prices):,.2f}")
                    st.write(f"**Median Price:** €{sorted(prices)[len(prices)//2]:,.2f}")
                else:
                    st.info("No price data available")
            
            with tab4:
                # Detailed view of each contract
                st.subheader("Contract Details")
            
            # Pagination
            items_per_page = 10
            total_pages = (len(contracts) - 1) // items_per_page + 1
            
            page = st.number_input(
                "Page",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1
            )
            
            start_idx = (page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, len(contracts))
            
            st.write(f"Showing contracts {start_idx + 1} to {end_idx} of {len(contracts)}")
            
            for i, contract in enumerate(contracts[start_idx:end_idx], start=start_idx + 1):
                with st.expander(f"**{i}. {contract.get('objectoContrato', 'N/A')}** - €{format_price(contract.get('precoContratual', '0')):,.2f}"):
                    # Basic Information Table
                    st.markdown("**📋 Basic Information**")
                    basic_info = pd.DataFrame({
                        'Field': ['Contract ID', 'Publication Date', 'Celebration Date', 'Contract Price', 'Announcement ID'],
                        'Value': [
                            contract.get('idcontrato') or contract.get('idContrato', 'N/A'),
                            contract.get('dataPublicacao', 'N/A'),
                            contract.get('dataCelebracaoContrato', 'N/A'),
                            f"€{format_price(contract.get('precoContratual', '0')):,.2f}",
                            contract.get('nAnuncio', 'N/A')
                        ]
                    })
                    st.dataframe(basic_info, hide_index=True, use_container_width=True)
                    
                    # Contract Type and Procedure Table
                    st.markdown("**📝 Type & Procedure**")
                    tipo_contrato = contract.get('tipoContrato', ['N/A'])
                    if not isinstance(tipo_contrato, list):
                        tipo_contrato = [str(tipo_contrato)]
                    type_info = pd.DataFrame({
                        'Field': ['Contract Type', 'Procedure Type', 'Framework Agreement'],
                        'Value': [
                            ', '.join(str(x) for x in tipo_contrato),
                            contract.get('tipoprocedimento', 'N/A'),
                            contract.get('acordoQuadro', 'N/A')
                        ]
                    })
                    st.dataframe(type_info, hide_index=True, use_container_width=True)
                    
                    # Entities Table
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🏢 Contracting Entities**")
                        adjudicante = contract.get('adjudicante', ['N/A'])
                        if not isinstance(adjudicante, list):
                            adjudicante = [str(adjudicante)]
                        entities_df = pd.DataFrame({
                            'Entity': adjudicante
                        })
                        st.dataframe(entities_df, hide_index=True, use_container_width=True)
                    
                    with col2:
                        st.markdown("**👔 Contractors**")
                        adjudicatarios = contract.get('adjudicatarios', ['N/A'])
                        if not isinstance(adjudicatarios, list):
                            adjudicatarios = [str(adjudicatarios)]
                        contractors_df = pd.DataFrame({
                            'Contractor': adjudicatarios
                        })
                        st.dataframe(contractors_df, hide_index=True, use_container_width=True)
                    
                    # CPV Codes Table
                    cpv_codes = contract.get('cpv', [])
                    if cpv_codes:
                        if not isinstance(cpv_codes, list):
                            cpv_codes = [str(cpv_codes)]
                        st.markdown("**🏷️ CPV Codes (Classification)**")
                        cpv_df = pd.DataFrame({
                            'CPV Code': cpv_codes
                        })
                        st.dataframe(cpv_df, hide_index=True, use_container_width=True)
                    
                    # Location Information
                    locations = contract.get('localExecucao', [])
                    if locations:
                        if not isinstance(locations, list):
                            locations = [str(locations)]
                        st.markdown("**📍 Execution Locations**")
                        location_df = pd.DataFrame({
                            'Location': locations
                        })
                        st.dataframe(location_df, hide_index=True, use_container_width=True)
                    
                    # Description
                    if contract.get('descContrato'):
                        st.markdown("**📄 Description**")
                        st.info(contract.get('descContrato'))
                    
                    # Object (always present)
                    if contract.get('objectoContrato'):
                        st.markdown("**🎯 Contract Object**")
                        st.success(contract.get('objectoContrato'))
        
        elif st.session_state.search_type == 'announcements' and st.session_state.filtered_announcements:
            # Show only announcements (open procedures)
            announcements = st.session_state.filtered_announcements
            
            # Toggle for Data Highlights
            show_highlights = st.checkbox("📊 Show Data Highlights", value=True)
            
            if show_highlights:
                # Summary metrics for announcements
                col1, col2, col3, col4 = st.columns(4)
                
                total_base_price = sum(format_price(a.get('PrecoBase', '0')) for a in announcements)
                
                with col1:
                    st.metric("Total Open Procedures", len(announcements))
                with col2:
                    st.metric("Total Base Price", f"€{total_base_price:,.2f}")
                with col3:
                    avg_price = total_base_price / len(announcements) if announcements else 0
                    st.metric("Average Base Price", f"€{avg_price:,.2f}")
                with col4:
                    unique_entities = len(set(
                        a.get('nifEntidade', '') for a in announcements if a.get('nifEntidade')
                    ))
                    st.metric("Unique Entities", unique_entities)
            
            st.markdown("---")
            
            # Tabs for announcements view
            tab1, tab2, tab3 = st.tabs(["📢 Procedimentos Abertos", "📈 Analytics", "📄 Detailed View"])
            
            with tab1:
                # Convert to DataFrame and display
                df_announcements = announcements_to_dataframe(announcements)
                
                # Display the table with clickable links
                st.dataframe(
                    df_announcements,
                    use_container_width=True,
                    height=600,
                    column_config={
                        "View": st.column_config.LinkColumn(
                            "🔗 Ver",
                            help="Click to view announcement on Base.gov.pt",
                            display_text="Ver"
                        ),
                        "Docs": st.column_config.LinkColumn(
                            "📄 Docs",
                            help="Click to download procedure documents",
                            display_text="Docs"
                        ),
                        "Preço Base (€)": st.column_config.NumberColumn(
                            "Preço Base (€)",
                            format="€%.2f"
                        )
                    },
                    hide_index=True,
                )
                
                # Download button
                csv_announcements = df_announcements.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv_announcements,
                    file_name=f"announcements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
            
            with tab2:
                st.subheader("📊 Announcement Analytics")
                st.info("Analytics for announcements coming soon!")
            
            with tab3:
                st.subheader("📄 Announcement Details")
                st.info("Detailed view for announcements coming soon!")
    
    else:
        # Only show sample table if no search has been performed yet
        if not st.session_state.search_performed:
            # Welcome message
            st.info("👈 Use the filters in the sidebar to search for contracts")
            
            # Quick stats
            stats = st.session_state.client.get_cache_stats()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Contracts in Cache", f"{stats['total_contracts']:,}")
            with col2:
                st.metric("Total Announcements in Cache", f"{stats['total_announcements']:,}")
            
            # Show recent contracts sample
            st.markdown("### 📋 Recent Contracts Sample")
            st.markdown("*Showing a preview of recent contracts. Use filters to search for specific contracts.*")
            
            try:
                # Get yesterday's contracts as a sample
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
                sample_contracts = st.session_state.client.get_contracts_by_date(yesterday)
                
                if sample_contracts:
                    # Limit to first 20 for preview
                    sample_contracts = sample_contracts[:20]
                    
                    # Show in table format
                    df = contracts_to_dataframe(sample_contracts)
                    st.dataframe(
                        df,
                        use_container_width=True,
                        height=400,
                        column_config={
                            "View Contract": st.column_config.LinkColumn(
                                "🔗 Contract",
                                display_text="View"
                            ),
                            "Price (€)": st.column_config.NumberColumn(
                                "Price (€)",
                                format="€%.2f"
                            )
                        },
                        hide_index=True
                    )
                    
                    st.info(f"📊 Showing {len(sample_contracts)} contracts from {yesterday}. Click 🔎 Search to see more or filter.")
                else:
                    st.warning("No recent contracts found. Use the search filters to load data.")
            except Exception as e:
                st.warning(f"Unable to load sample data. Use the filters to search for contracts.")
        else:
            # Search was performed but returned no results
            st.warning("⚠️ No contracts found matching your filters. Try adjusting them.")


if __name__ == "__main__":
    main()

