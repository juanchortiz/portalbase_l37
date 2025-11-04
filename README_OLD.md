# Base.gov.pt API Client

A Python client for interacting with the Portuguese public procurement API (Base.gov.pt). This client provides easy access to contracts, announcements, contract modifications, and entity data.

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from base_api_client import BaseAPIClient

# Initialize the client with your access token
client = BaseAPIClient("your_access_token_here")

# Get contract information
contract = client.get_contract_info(id_contrato="12345")
print(contract)

# Get announcement information
announcement = client.get_announcement_info(n_anuncio="1234/2015")
print(announcement)

# Get contract modifications
modification = client.get_contract_modification_info(id_contrato="12345")
print(modification)

# Get entity information
entity = client.get_entity_info(nif_entidade="654123987")
print(entity)
```

## API Methods

### `get_contract_info()`

Retrieve contract information. At least one parameter is required.

**Parameters:**
- `id_contrato` (str, optional): Contract ID
- `id_procedimento` (str, optional): Procedure ID
- `nif_entidade` (str, optional): Entity NIF (tax ID)
- `n_anuncio` (str, optional): Announcement number
- `ano` (str, optional): Year

**Example:**
```python
# Search by contract ID
contract = client.get_contract_info(id_contrato="12345")

# Search by entity and year
contracts = client.get_contract_info(nif_entidade="654123987", ano="2015")
```

### `get_announcement_info()`

Retrieve announcement information. At least one parameter is required.

**Parameters:**
- `n_anuncio` (str, optional): Announcement number
- `nif_entidade` (str, optional): Entity NIF
- `id_incm` (str, optional): INCM ID
- `ano` (str, optional): Year

**Example:**
```python
announcement = client.get_announcement_info(n_anuncio="1234/2015")
```

### `get_contract_modification_info()`

Retrieve contract modification information. At least one parameter is required.

**Parameters:**
- `id_contrato` (str, optional): Contract ID
- `ano` (str, optional): Year

**Example:**
```python
modification = client.get_contract_modification_info(id_contrato="12345")
```

### `get_entity_info()`

Retrieve entity information.

**Parameters:**
- `nif_entidade` (str, required): Entity NIF

**Example:**
```python
entity = client.get_entity_info(nif_entidade="654123987")
```

### Helper Methods

#### `search_contracts_by_year()`

Search all contracts for a given year.

```python
contracts_2015 = client.search_contracts_by_year("2015")
```

#### `search_contracts_by_entity()`

Search contracts for a specific entity.

```python
entity_contracts = client.search_contracts_by_entity("654123987", "2015")
```

## Response Example

Contract information response:

```python
{
    "idContrato": "12345",
    "nAnuncio": "1234/2015",
    "TipoAnuncio": "Anúncio de procedimento",
    "idINCM": "123456789",
    "tipoContrato": ["Empreitadas de obras públicas"],
    "idprocedimento": "355455",
    "tipoprocedimento": "Concurso público",
    "objectoContrato": "Contrato de teste",
    "descContrato": "Contrato de teste",
    "adjudicante": ["654123987 - Entidade de Exemplo"],
    "adjudicatarios": [
        "500045698 - Empresa de Testes",
        "500123698 - Outra Empresa de Testes"
    ],
    "dataPublicacao": "12/05/2015",
    "dataCelebracaoContrato": "18/04/2015",
    "precoContratual": "105000,00",
    "cpv": ["45212410-3 - Obras de construção de edifícios relacionados com alojamento"],
    "prazoExecucao": "365",
    "localExecucao": ["Portugal, Lisboa, Lisboa", "Portugal, Porto, Porto"],
    "fundamentacao": "Artigo 19.º, alínea b) do Código dos Contratos Públicos",
    "ProcedimentoCentralizado": "Não",
    "precoBaseProcedimento": "110000,00",
    "dataDecisaoAdjudicacao": "15/03/2015",
    "regime": "Código dos Contratos Públicos (DL 18/2008)",
    "Ano": "2015"
}
```

## Error Handling

The client handles various error scenarios:

```python
try:
    contract = client.get_contract_info(id_contrato="12345")
except ValueError as e:
    # Handle missing parameters, invalid token, etc.
    print(f"Validation error: {e}")
except requests.exceptions.HTTPError as e:
    # Handle HTTP errors
    print(f"HTTP error: {e}")
except Exception as e:
    # Handle other errors
    print(f"Error: {e}")
```

## Advanced Usage

### Custom Session Configuration

You can access the underlying `requests.Session` for advanced configuration:

```python
client = BaseAPIClient("your_token")

# Add custom headers
client.session.headers.update({"User-Agent": "MyApp/1.0"})

# Configure timeout
client.session.timeout = 30

# Use proxies
client.session.proxies = {"http": "http://proxy.example.com:8080"}
```

### Analyzing Contract Data

```python
# Get all contracts for an entity in 2015
contracts = client.search_contracts_by_entity("654123987", "2015")

# Calculate total contract value
total_value = 0
for contract in contracts:
    price_str = contract.get("precoContratual", "0")
    # Remove thousands separator and replace decimal comma
    price = float(price_str.replace(".", "").replace(",", "."))
    total_value += price

print(f"Total contract value: €{total_value:,.2f}")
```

### Filtering by Contract Type

```python
contracts = client.search_contracts_by_year("2015")

# Filter for public works contracts
public_works = [
    c for c in contracts 
    if "Empreitadas de obras públicas" in c.get("tipoContrato", [])
]

print(f"Found {len(public_works)} public works contracts")
```

## Authentication

To use this API, you need an access token from Base.gov.pt. Contact the platform administrators for access credentials.

## API Documentation

For full API documentation, visit: https://www.base.gov.pt/APIBase2

## License

This client is provided as-is for interacting with the Base.gov.pt public API.
