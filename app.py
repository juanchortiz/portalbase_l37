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

# CPV Codes Dictionary - Main divisions and common categories
CPV_CODES = {
    # Main Divisions (2-digit)
    "03000000": "03 - Agricultural, farming, fishing, forestry products",
    "09000000": "09 - Petroleum products, fuel, electricity",
    "14000000": "14 - Mining, basic metals and related products",
    "15000000": "15 - Food, beverages, tobacco",
    "16000000": "16 - Agricultural machinery",
    "18000000": "18 - Clothing, footwear, luggage articles",
    "19000000": "19 - Leather and textile fabrics, plastic and rubber materials",
    "22000000": "22 - Printed matter and related products",
    "24000000": "24 - Chemical products",
    "30000000": "30 - Office and computing machinery, equipment and supplies",
    "31000000": "31 - Electrical machinery, apparatus, equipment and consumables",
    "32000000": "32 - Radio, television, communication equipment",
    "33000000": "33 - Medical equipments, pharmaceuticals and personal care products",
    "34000000": "34 - Transport equipment and auxiliary products",
    "35000000": "35 - Security, fire-fighting, police and defence equipment",
    "37000000": "37 - Musical instruments, sport goods, games, toys",
    "38000000": "38 - Laboratory, optical and precision equipments",
    "39000000": "39 - Furniture, furnishings, domestic appliances",
    "41000000": "41 - Collected and purified water",
    "42000000": "42 - Industrial machinery",
    "43000000": "43 - Mining, quarrying and construction equipment",
    "44000000": "44 - Construction structures and materials",
    "45000000": "45 - Construction work",
    "48000000": "48 - Software package and information systems",
    "50000000": "50 - Repair and maintenance services",
    "51000000": "51 - Installation services",
    "55000000": "55 - Hotel, restaurant and retail trade services",
    "60000000": "60 - Transport services",
    "63000000": "63 - Supporting and auxiliary transport services",
    "64000000": "64 - Postal and telecommunications services",
    "65000000": "65 - Public utilities",
    "66000000": "66 - Financial and insurance services",
    "70000000": "70 - Real estate services",
    "71000000": "71 - Architectural, construction, engineering and inspection services",
    "72000000": "72 - IT services: consulting, software development",
    "73000000": "73 - Research and development services",
    "75000000": "75 - Administration, defence and social security services",
    "76000000": "76 - Services related to the oil and gas industry",
    "77000000": "77 - Agricultural, forestry, horticultural, aquacultural services",
    "79000000": "79 - Business services: law, marketing, consulting",
    "80000000": "80 - Education and training services",
    "85000000": "85 - Health and social work services",
    "90000000": "90 - Sewage, refuse, cleaning and environmental services",
    "92000000": "92 - Recreational, cultural and sporting services",
    "98000000": "98 - Other community, social and personal services",
}

def get_cpv_display_options():
    """Get CPV codes formatted for display in multiselect."""
    return [f"{code} - {desc.split(' - ', 1)[1]}" for code, desc in sorted(CPV_CODES.items())]

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
    
    # Contract type filter
    if filters['contract_type'] and filters['contract_type'] != "All":
        filtered = [
            c for c in filtered
            if filters['contract_type'] in c.get('tipoContrato', [])
        ]
    
    # Price range filter
    if filters['min_price'] is not None or filters['max_price'] is not None:
        filtered_by_price = []
        for c in filtered:
            price = format_price(c.get('precoContratual', '0'))
            if filters['min_price'] is not None and price < filters['min_price']:
                continue
            if filters['max_price'] is not None and price > filters['max_price']:
                continue
            filtered_by_price.append(c)
        filtered = filtered_by_price
    
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
    
    # Contract type filter
    st.sidebar.subheader("Contract Type")
    contract_types = [
        "All",
        "Aquisição de bens móveis",
        "Aquisição de serviços",
        "Empreitadas de obras públicas",
        "Locação de bens móveis"
    ]
    contract_type = st.sidebar.selectbox("Type:", contract_types)
    
    # Price range filter
    st.sidebar.subheader("Price Range (€)")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_price = st.number_input("Min:", min_value=0, value=0, step=1000)
    with col2:
        max_price = st.number_input("Max:", min_value=0, value=0, step=1000)
    
    if max_price > 0 and max_price < min_price:
        st.sidebar.error("Max price must be greater than min price")
        max_price = None
    elif max_price == 0:
        max_price = None
    
    if min_price == 0:
        min_price = None
    
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
                'contract_type': contract_type,
                'min_price': min_price,
                'max_price': max_price,
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

