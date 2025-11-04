# Portal Base Web Application Guide

## 🚀 Quick Start

### Launch the App

```bash
cd "/Users/juanortiz/Desktop/Portal Base"
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

---

## 📋 Features

### 1. **Date Range Selection**
- **Today**: View contracts published today
- **Yesterday**: View contracts published yesterday  
- **Last 7 days**: View contracts from the past week
- **Last 30 days**: View contracts from the past month
- **Custom range**: Select any date range

### 2. **Keyword Search**
Search for keywords in:
- Contract object/title
- Contract description
- CPV codes (classification)

**Examples:**
- "saúde" - Find healthcare contracts
- "informática" - Find IT contracts
- "construção" - Find construction contracts

### 3. **Entity Filter**
Filter by contracting entity or contractor NIF (tax ID number):
- Enter the full or partial NIF
- Searches in both contracting entities and contractors

**Example:**
- `509540716` - SPMS (Health services)
- `500122237` - Fund INATEL

### 4. **Contract Type Filter**
Filter by contract type:
- **Aquisição de bens móveis** - Acquisition of movable goods
- **Aquisição de serviços** - Acquisition of services
- **Empreitadas de obras públicas** - Public works contracts
- **Locação de bens móveis** - Leasing of movable goods

### 5. **Price Range Filter**
Set minimum and maximum price thresholds:
- Find high-value contracts (e.g., > €100,000)
- Find specific price ranges

### 6. **Location Filter**
Filter by execution location:
- "Lisboa" - Contracts in Lisbon
- "Porto" - Contracts in Porto
- Any location name

---

## 📊 Views

### Table View
- Sortable columns
- Searchable data
- Download results as CSV

### Analytics View
- **Contract Types Distribution** - Bar chart showing distribution by type
- **Top 10 Contracting Entities** - Most active entities
- **Price Distribution** - Overview of contract values
- Statistical summary (min, max, median prices)

### Detailed View
- Full contract details
- Paginated (10 per page)
- Expandable cards for each contract
- Complete information including:
  - Contract ID
  - Publication and celebration dates
  - Price
  - Type and procedure type
  - Contracting entity and contractors
  - Description
  - CPV codes
  - Execution location

---

## 💡 Example Use Cases

### 1. Healthcare Contracts in Lisbon
```
Date Range: Last 30 days
Keyword: saúde
Location: Lisboa
```

### 2. High-Value Construction Projects
```
Contract Type: Empreitadas de obras públicas
Min Price: 100000
```

### 3. IT Services for Specific Entity
```
Keyword: informática
Contract Type: Aquisição de serviços
Entity NIF: 509540716
```

### 4. All Contracts from Yesterday
```
Date Range: Yesterday
(No other filters)
```

---

## 🗄️ Cache Information

The app uses a local SQLite database (`base_cache.db`) to:
- Store all contract data locally
- Enable instant queries without API calls
- Auto-refresh daily (once per calendar day)

View cache statistics in the sidebar:
- Total contracts cached
- Total announcements cached
- Years in cache with last update time

---

## ⚡ Performance

- **First search of the day**: May take a moment (fetching from API)
- **Subsequent searches**: Instant (uses local cache)
- **189,342+ contracts** from 2025 already cached!

---

## 🔧 Troubleshooting

### App won't start
```bash
# Make sure streamlit is installed
pip3 install streamlit pandas

# Try running with full path
/Users/juanortiz/Library/Python/3.14/bin/streamlit run app.py
```

### Cache issues
```bash
# Force refresh cache
python3 sync_year_data.py 2025 --force
```

### Port already in use
```bash
# Run on different port
streamlit run app.py --server.port 8502
```

---

## 📝 Tips

1. **Combine filters** for precise results
2. **Use Analytics view** to understand data distribution
3. **Download CSV** for further analysis in Excel/Google Sheets
4. **Check cache info** to see data freshness
5. **No filters** = view all contracts for the date range

---

## 🎯 Common Queries

| What you want | Filters to use |
|---------------|----------------|
| All yesterday's contracts | Date: Yesterday |
| Healthcare contracts | Keyword: "saúde" or "hospital" |
| Contracts > €1M | Min Price: 1000000 |
| SPMS contracts | Entity NIF: 509540716 |
| IT services | Type: Aquisição de serviços + Keyword: "informática" |
| Porto construction | Location: Porto + Type: Empreitadas de obras públicas |

---

## 📧 Support

For issues or questions:
1. Check the cache statistics
2. Try force refreshing: `python3 sync_year_data.py 2025 --force`
3. Restart the app

Enjoy browsing Portuguese public procurement data! 🇵🇹

