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


# Page configuration
st.set_page_config(
    page_title="Portal Base - Public Procurement",
    page_icon="📋",
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
    
    # Keyword filter
    if filters['keyword']:
        keyword = filters['keyword'].lower()
        filtered = [
            c for c in filtered
            if keyword in c.get('objectoContrato', '').lower() or
               keyword in c.get('descContrato', '').lower() or
               keyword in ' '.join(c.get('cpv', [])).lower()
        ]
    
    # Entity NIF filter
    if filters['entity_nif']:
        nif = filters['entity_nif'].strip()
        filtered = [
            c for c in filtered
            if nif in ' '.join(c.get('adjudicante', [])) or
               nif in ' '.join(c.get('adjudicatarios', []))
        ]
    
    # Location filter
    if filters['location']:
        location = filters['location'].lower()
        filtered = [
            c for c in filtered
            if any(location in loc.lower() for loc in c.get('localExecucao', []))
        ]
    
    # CPV codes filter (multiple selection)
    if filters.get('cpv_codes'):
        cpv_list = filters['cpv_codes']
        filtered = [
            c for c in filtered
            if any(
                any(cpv_filter in cpv_item for cpv_filter in cpv_list)
                for cpv_item in c.get('cpv', [])
            )
        ]
    
    return filtered


def contracts_to_dataframe(contracts):
    """Convert contracts to a pandas DataFrame."""
    if not contracts:
        return pd.DataFrame()
    
    data = []
    for contract in contracts:
        data.append({
            'ID': contract.get('idContrato', 'N/A'),
            'Publication Date': contract.get('dataPublicacao', 'N/A'),
            'Object': contract.get('objectoContrato', 'N/A'),
            'Type': ', '.join(contract.get('tipoContrato', ['N/A'])),
            'Price (€)': format_price(contract.get('precoContratual', '0')),
            'CPV Codes': ', '.join(contract.get('cpv', ['N/A'])[:3]),  # Show first 3 CPV codes
            'Contracting Entity': ', '.join(contract.get('adjudicante', ['N/A'])),
            'Contractors': ', '.join(contract.get('adjudicatarios', ['N/A'])),
            'Location': ', '.join(contract.get('localExecucao', ['N/A'])),
            'Announcement': contract.get('nAnuncio', 'N/A')
        })
    
    return pd.DataFrame(data)


def main():
    # Header
    st.title("📋 Portal Base - Concursos e Contratos Públicos - Link37 App")
    st.markdown("Filtrar e buscar. Ver infromação de caché")
    
    # Sidebar - Filters
    st.sidebar.header("🔍 Filtros")
    
    # Date range selection
    st.sidebar.subheader("Datas")
    date_option = st.sidebar.radio(
        "Select period:",
        ["Today", "Yesterday", "Last 7 days", "Last 30 days", "Custom range"]
    )
    
    if date_option == "Custom range":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input(
                "Start date",
                value=datetime.now() - timedelta(days=7),
                max_value=datetime.now()
            )
        with col2:
            end_date = st.date_input(
                "End date",
                value=datetime.now(),
                max_value=datetime.now()
            )
    else:
        if date_option == "Today":
            start_date = end_date = datetime.now().date()
        elif date_option == "Yesterday":
            start_date = end_date = (datetime.now() - timedelta(days=1)).date()
        elif date_option == "Last 7 days":
            start_date = (datetime.now() - timedelta(days=7)).date()
            end_date = datetime.now().date()
        else:  # Last 30 days
            start_date = (datetime.now() - timedelta(days=30)).date()
            end_date = datetime.now().date()
    
    st.sidebar.markdown("---")
    
    # Keyword filter
    st.sidebar.subheader("Keyword Search")
    keyword = st.sidebar.text_input(
        "Search in object/description:",
        help="Search for keywords in contract object, description, or CPV codes"
    )
    
    # Entity filter
    st.sidebar.subheader("Entity Filter")
    entity_nif = st.sidebar.text_input(
        "Entity NIF:",
        help="Filter by contracting entity or contractor NIF"
    )
    
    # Location filter
    st.sidebar.subheader("Location")
    location = st.sidebar.text_input(
        "Location:",
        help="Filter by execution location (e.g., 'Lisboa', 'Porto')"
    )
    
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
            
            # Apply filters
            filters = {
                'keyword': keyword,
                'entity_nif': entity_nif,
                'location': location,
                'cpv_codes': cpv_codes
            }
            
            filtered = filter_contracts(contracts, filters)
            st.session_state.filtered_contracts = filtered
    
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
            
            # Display table
            st.dataframe(
                df,
                use_container_width=True,
                height=600,
                column_config={
                    "Price (€)": st.column_config.NumberColumn(
                        "Price (€)",
                        format="€%.2f"
                    )
                }
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
                            contract.get('idContrato', 'N/A'),
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
                        "Price (€)": st.column_config.NumberColumn(
                            "Price (€)",
                            format="€%.2f"
                        )
                    }
                )
                
                st.info(f"📊 Showing {len(sample_contracts)} contracts from {yesterday}. Click 🔎 Search to see more or filter.")
            else:
                st.warning("No recent contracts found. Use the search filters to load data.")
        except Exception as e:
            st.warning(f"Unable to load sample data. Use the filters to search for contracts.")
        
        # Example searches
        st.markdown("### 💡 Example Searches")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🏥 Healthcare Contracts**
            - Keywords: "saúde", "hospital", "médico"
            - Filter by health entities
            """)
        
        with col2:
            st.markdown("""
            **🏗️ Construction Projects**
            - Type: "Empreitadas de obras públicas"
            - Location: Your city
            - Price range: Set minimum
            """)
        
        with col3:
            st.markdown("""
            **💻 IT Services**
            - Keywords: "informática", "software"
            - Type: "Aquisição de serviços"
            """)


if __name__ == "__main__":
    main()

