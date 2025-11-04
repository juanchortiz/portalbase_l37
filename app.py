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

# Initialize session state
if 'client' not in st.session_state:
    try:
        ACCESS_TOKEN = get_api_key()
        st.session_state.client = CachedBaseAPIClient(ACCESS_TOKEN)
    except ValueError as e:
        st.error(f"❌ {str(e)}")
        st.stop()

if 'filtered_contracts' not in st.session_state:
    st.session_state.filtered_contracts = []

if 'filtered_announcements' not in st.session_state:
    st.session_state.filtered_announcements = []


def format_price(price_str):
    """Convert Portuguese price format to float."""
    try:
        if not price_str or price_str == "N/A":
            return 0.0
        return float(str(price_str).replace(".", "").replace(",", "."))
    except (ValueError, AttributeError):
        return 0.0


def filter_contracts(contracts, filters):
    """Apply filters to contracts."""
    filtered = contracts
    
    # Keyword filter (supports comma-separated keywords)
    if filters['keyword']:
        keywords = [kw.strip().lower() for kw in filters['keyword'].split(',') if kw.strip()]
        filtered = [
            c for c in filtered
            if any(
                keyword in c.get('objectoContrato', '').lower() or
                keyword in c.get('descContrato', '').lower() or
                keyword in ' '.join(c.get('cpv', [])).lower()
                for keyword in keywords
            )
        ]
    
    # Entity NIF filter
    if filters['entity_nif']:
        nif = filters['entity_nif'].strip()
        filtered = [
            c for c in filtered
            if nif in ' '.join(c.get('adjudicante', [])) or
               nif in ' '.join(c.get('adjudicatarios', []))
        ]
    
    # Location filter (multiple selection)
    if filters.get('location') and filters['location']:
        location_list = filters['location'] if isinstance(filters['location'], list) else [filters['location']]
        filtered = [
            c for c in filtered
            if any(
                any(filter_loc.lower() in loc.lower() for filter_loc in location_list)
                for loc in c.get('localExecucao', [])
            )
        ]
    
    # CPV codes filter (multiple selection)
    if filters.get('cpv_codes') and filters['cpv_codes']:
        cpv_list = filters['cpv_codes']
        # Match CPV codes - check if any selected CPV code is in any contract CPV
        filtered = [
            c for c in filtered
            if c.get('cpv') and any(
                any(cpv_filter.split('-')[0] in str(cpv_item) for cpv_filter in cpv_list)
                for cpv_item in c.get('cpv', [])
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
        
        data.append({
            'View Contract': contract_url,  # New column with link
            'ID': contract_id,
            'Publication Date': contract.get('dataPublicacao', 'N/A'),
            'Object': contract.get('objectoContrato', 'N/A'),
            'Type': ', '.join(contract.get('tipoContrato', ['N/A'])),
            'Price (€)': format_price(contract.get('precoContratual', '0')),
            'CPV Codes': ', '.join(contract.get('cpv', ['N/A'])[:3]),
            'Contracting Entity': ', '.join(contract.get('adjudicante', ['N/A'])),
            'Contractors': ', '.join(contract.get('adjudicatarios', ['N/A'])),
            'Location': ', '.join(contract.get('localExecucao', ['N/A'])),
        })
    
    return pd.DataFrame(data)


def main():
    # Hero section with gradient background
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
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
            <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #ffffff;">Powered by Link37</p>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 60px; font-weight: bold; color: #FFFFFF; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">link</span><span style="font-size: 60px; font-weight: bold; color: #E31E26; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">37</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Sidebar - Filters
    st.sidebar.header("🔍 Filtros")
    
    # Date range selection
    st.sidebar.subheader("Datas")
    
    # Show cache info
    stats = st.session_state.client.get_cache_stats()
    if stats['years_cached']:
        last_update = stats['years_cached'][0]['last_fetched'][:10] if stats['years_cached'] else 'Unknown'
        st.sidebar.caption(f"📅 Cache last updated: {last_update}")
    
    date_option = st.sidebar.radio(
        "Select period:",
        ["Last 30 days", "Last 90 days", "Custom range", "Today", "Yesterday"],
        index=0  # Default to Last 30 days
    )
    
    if date_option == "Custom range":
        st.sidebar.markdown("**Data Inicial**")
        start_date = st.sidebar.date_input(
            "Escolher data inicial:",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now(),
            format="DD/MM/YYYY",
            label_visibility="collapsed"
        )
        
        st.sidebar.markdown("**Data Final**")
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            end_date = st.date_input(
                "Escolher data final:",
                value=datetime.now() - timedelta(days=1),
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
    keyword = st.sidebar.text_input(
        "Search keywords (comma-separated):",
        help="Enter keywords separated by commas. Example: 'reagentes, laboratório, análises'"
    )
    
    # Entity filter
    st.sidebar.subheader("Entity Filter")
    entity_nif = st.sidebar.text_input(
        "Entity NIF:",
        help="Filter by contracting entity or contractor NIF"
    )
    
    # Location filter
    st.sidebar.subheader("Location")
    selected_locations = st.sidebar.multiselect(
        "Select Locations:",
        options=[loc for loc in COMMON_LOCATIONS if loc != "All"],
        help="Filter by execution location (select multiple)"
    )
    # Convert list to filter format
    location = selected_locations if selected_locations else []
    
    # CPV filter
    st.sidebar.subheader("CPV Classification")
    cpv_options = get_cpv_display_options()
    selected_cpvs = st.sidebar.multiselect(
        "Select CPV Categories:",
        options=cpv_options,
        default=None,
        help="Select one or more CPV categories. Use the search to find specific categories.",
        placeholder="Search and select CPV codes..."
    )
    cpv_codes = extract_cpv_codes_from_selection(selected_cpvs)
    
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
        with st.spinner('Searching contracts...'):
            # Convert dates to Portuguese format
            start_str = start_date.strftime("%d/%m/%Y")
            end_str = end_date.strftime("%d/%m/%Y")
            
            # Get contracts
            if start_date == end_date:
                contracts = st.session_state.client.get_contracts_by_date(start_str)
            else:
                contracts = st.session_state.client.get_contracts_by_date_range(start_str, end_str)
            
            # Debug: Show initial results
            st.info(f"📊 Found {len(contracts)} contracts in date range")
            
            # Apply filters
            filters = {
                'keyword': keyword,
                'entity_nif': entity_nif,
                'location': location,
                'cpv_codes': cpv_codes
            }
            
            # Debug: Show active filters
            active_filters = []
            if keyword: active_filters.append(f"Keywords: {keyword}")
            if entity_nif: active_filters.append(f"NIF: {entity_nif}")
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
            
            filtered = filter_contracts(contracts, filters)
            st.session_state.filtered_contracts = filtered
            
            # Debug: Show filtered results
            if filtered:
                st.success(f"✅ {len(filtered)} contracts match your filters")
            else:
                st.warning(f"⚠️ No contracts found matching your filters. Try adjusting them.")
    
    # Display results
    if st.session_state.filtered_contracts:
        contracts = st.session_state.filtered_contracts
        
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
                for entity in c.get('adjudicante', [])
            ))
            st.metric("Unique Entities", unique_entities)
        
        st.markdown("---")
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Table View", "📈 Analytics", "📄 Detailed View"])
        
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
            col1, col2 = st.columns(2)
            
            with col1:
                # Contract types distribution
                st.subheader("Contract Types Distribution")
                type_counts = {}
                for c in contracts:
                    for ctype in c.get('tipoContrato', ['Unknown']):
                        type_counts[ctype] = type_counts.get(ctype, 0) + 1
                
                type_df = pd.DataFrame(
                    list(type_counts.items()),
                    columns=['Type', 'Count']
                ).sort_values('Count', ascending=False)
                
                st.bar_chart(type_df.set_index('Type'))
            
            with col2:
                # Top contracting entities
                st.subheader("Top 10 Contracting Entities")
                entity_counts = {}
                for c in contracts:
                    for entity in c.get('adjudicante', []):
                        entity_counts[entity] = entity_counts.get(entity, 0) + 1
                
                top_entities = sorted(
                    entity_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
                
                entity_df = pd.DataFrame(top_entities, columns=['Entity', 'Contracts'])
                st.dataframe(entity_df, use_container_width=True, hide_index=True)
            
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
        
        with tab3:
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
                    type_info = pd.DataFrame({
                        'Field': ['Contract Type', 'Procedure Type', 'Framework Agreement'],
                        'Value': [
                            ', '.join(contract.get('tipoContrato', ['N/A'])),
                            contract.get('tipoprocedimento', 'N/A'),
                            contract.get('acordoQuadro', 'N/A')
                        ]
                    })
                    st.dataframe(type_info, hide_index=True, use_container_width=True)
                    
                    # Entities Table
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🏢 Contracting Entities**")
                        entities_df = pd.DataFrame({
                            'Entity': contract.get('adjudicante', ['N/A'])
                        })
                        st.dataframe(entities_df, hide_index=True, use_container_width=True)
                    
                    with col2:
                        st.markdown("**👔 Contractors**")
                        contractors_df = pd.DataFrame({
                            'Contractor': contract.get('adjudicatarios', ['N/A'])
                        })
                        st.dataframe(contractors_df, hide_index=True, use_container_width=True)
                    
                    # CPV Codes Table
                    if contract.get('cpv'):
                        st.markdown("**🏷️ CPV Codes (Classification)**")
                        cpv_df = pd.DataFrame({
                            'CPV Code': contract.get('cpv', [])
                        })
                        st.dataframe(cpv_df, hide_index=True, use_container_width=True)
                    
                    # Location Information
                    if contract.get('localExecucao'):
                        st.markdown("**📍 Execution Locations**")
                        location_df = pd.DataFrame({
                            'Location': contract.get('localExecucao', [])
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
    
    else:
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


if __name__ == "__main__":
    main()

