# Portal Base API Client 🇵🇹

A Python client and web application for accessing and analyzing Portuguese public procurement data from Base.gov.pt.

## 🌟 Features

### Python API Client
- ✅ Complete Base.gov.pt REST API wrapper
- ✅ SQLite-based local caching for instant queries
- ✅ Automatic daily data refresh
- ✅ Support for contracts, announcements, and entities
- ✅ Date-based filtering and search

### Interactive Web Application
- 📊 Beautiful Streamlit interface
- 🔍 Advanced filtering (keywords, entities, price, location, type)
- 📈 Analytics dashboard with charts and statistics
- 📥 CSV export functionality
- ⚡ Real-time search with cached data

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/portal-base-client.git
cd portal-base-client
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

**Option A: Environment Variable (Recommended for production)**

```bash
export BASE_API_KEY="your_api_key_here"
```

**Option B: Secrets File (Good for local development)**

Create a file named `Secrets` in the project root:

```
BASE_API_KEY:"your_api_key_here"
```

> ⚠️ **Important**: Never commit your API key to Git! The `.gitignore` file is configured to exclude the `Secrets` file and `.env` files.

### 4. Run the Web Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 Usage Examples

### Command Line Scripts

#### Get Yesterday's Contracts
```bash
python get_yesterday_cached.py
```

#### Get Contracts for Specific Date
```bash
python get_date.py 31/10/2025
```

#### Sync Data for a Year
```bash
python sync_year_data.py 2025
```

#### Force Refresh Cache
```bash
python sync_year_data.py 2025 --force
```

### Python API

```python
from cached_api_client import CachedBaseAPIClient
from config import get_api_key

# Initialize client
client = CachedBaseAPIClient(get_api_key())

# Get contracts for a specific date
contracts = client.get_contracts_by_date("31/10/2025")

# Get contracts for date range
contracts = client.get_contracts_by_date_range("01/10/2025", "31/10/2025")

# Get announcements
announcements = client.get_announcements_by_date("31/10/2025")
```

## 🗄️ Project Structure

```
portal-base-client/
├── app.py                      # Streamlit web application
├── base_api_client.py          # Direct API client
├── cached_api_client.py        # Cached API client with SQLite
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore file
├── README.md                  # This file
│
├── Scripts/
│   ├── get_yesterday_cached.py # Get yesterday's data
│   ├── get_date.py            # Get specific date data
│   ├── sync_year_data.py      # Manual cache sync
│   ├── cached_examples.py     # Usage examples
│   └── example_usage.py       # Basic examples
│
└── APP_GUIDE.md               # Detailed app documentation
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BASE_API_KEY` | Your Base.gov.pt API access token | Yes |

### Cache Configuration

The client automatically caches data in a local SQLite database (`base_cache.db`). The cache:
- Refreshes daily (date-based, not time-based)
- Stores full contract and announcement data
- Enables instant queries without API calls

## 📊 Web Application Features

### Filters Available

1. **Date Range**
   - Today, Yesterday, Last 7/30 days, Custom range

2. **Keyword Search**
   - Search in contract titles, descriptions, CPV codes

3. **Entity Filter**
   - Filter by contracting entity or contractor NIF

4. **Contract Type**
   - Acquisition of goods, services, public works, leasing

5. **Price Range**
   - Set minimum and maximum price filters

6. **Location**
   - Filter by execution location

### View Modes

- **Table View**: Sortable, searchable with CSV export
- **Analytics View**: Charts and statistics
- **Detailed View**: Full contract information

## 🔐 Security Best Practices

1. **Never commit API keys** to Git
2. **Use environment variables** in production
3. **Use the Secrets file** only for local development
4. **Rotate keys regularly** if compromised
5. **Review `.gitignore`** before pushing

The `.gitignore` file protects:
- `Secrets` file
- `.env` files
- Database files (`*.db`)
- Python cache files
- IDE configurations

## 🛠️ Development

### Running Tests
```bash
python -m pytest
```

### Updating Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 API Reference

### BaseAPIClient Methods

- `get_contract_info()` - Get contract information
- `get_announcement_info()` - Get announcement information
- `get_contract_modification_info()` - Get contract modifications
- `get_entity_info()` - Get entity information
- `search_contracts_by_year()` - Search contracts by year
- `search_contracts_by_entity()` - Search contracts by entity

### CachedBaseAPIClient Methods

All `BaseAPIClient` methods plus:
- `get_contracts_by_date()` - Get contracts for specific date
- `get_announcements_by_date()` - Get announcements for specific date
- `get_contracts_by_date_range()` - Get contracts for date range
- `get_cache_stats()` - View cache statistics
- `sync_year()` - Manually sync data for a year

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Acknowledgments

- Base.gov.pt for providing the public procurement API
- Streamlit for the amazing web framework
- The Python community

## 📧 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the [APP_GUIDE.md](APP_GUIDE.md) for detailed documentation

## 🗺️ Roadmap

- [ ] Add more visualization options
- [ ] Export to Excel with formatting
- [ ] Email notifications for new contracts
- [ ] Advanced analytics (trends, patterns)
- [ ] API rate limiting handling
- [ ] Multi-year comparison views

---

**Made with ❤️ for transparency in public procurement**
