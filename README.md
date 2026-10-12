# Macfax API Client

Production-ready Python client for the Macfax API - device lookup, pricing data, and marketplace listings for Mac, iPad, and iPhone.

## Features

- ✅ Complete API coverage (lookup, pricing, listings, reports)
- ✅ Automatic retry logic with exponential backoff
- ✅ Rate limit handling with automatic delays
- ✅ Error handling and custom exceptions
- ✅ Bulk operations support
- ✅ Environment-based configuration
- ✅ Session management for performance

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment template:
```bash
copy .env.example .env
```

3. (Optional) Add your API key to `.env`:
```
MACFAX_API_KEY=mfx_your_key_here
```

## Quick Start

```python
from macfax_client import MacfaxClient

# Initialize client
client = MacfaxClient()

# Look up a serial
result = client.lookup_serial("C02P73J9G8WP")
if result['success']:
    print(result['data']['model'])

# Get price statistics
result = client.get_price_stats("macbook-pro-14-m3pro-2023")
if result['success']:
    print(result['data']['sold']['estimated_sale'])

# Find listings
result = client.get_listings("macbook-pro-14-m3pro-2023", max_price=1500)
if result['success']:
    for listing in result['data']['listings']:
        print(f"{listing['ask_usd']} - {listing['platform']}")
```

## Usage Examples

Run the example script:
```bash
python api_example.py
```

## API Methods

### Device Lookup
```python
client.lookup_serial(serial, context=None, run_id=None)
```

### Pricing
```python
client.get_price_stats(config)
client.get_market_value(model)
```

### Listings
```python
client.get_listings(config, max_price=None, sort='price_asc', limit=None)
client.check_listing(url)
```

### Reports & Data
```python
client.get_report(report_id)
client.get_config_data(config)
```

### Alerts & Management
```python
client.create_alert(config, email, max_price=None)
client.get_api_key()
client.get_credits()
```

### Bulk Operations
```python
client.bulk_lookup(serials, context='inventory', run_id=None)
```

## Error Handling

```python
from macfax_client import MacfaxAPIError, RateLimitError, CreditsExhaustedError

try:
    result = client.lookup_serial("SERIAL123")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except CreditsExhaustedError:
    print("Out of credits. Please top up.")
except MacfaxAPIError as e:
    print(f"API error: {e}")
```

## Configuration

Edit `.env` file:
```
MACFAX_API_KEY=mfx_your_key_here
MACFAX_BASE_URL=https://macfax.com/api/v1
MACFAX_TIMEOUT=30
```

## Getting an API Key

Anonymous usage works with lower rate limits. Get a free key for 10x higher limits:

```python
client = MacfaxClient()
result = client.get_api_key()
print(result['data']['key'])
```

Or via PowerShell:
```powershell
Invoke-RestMethod -Method Post -Uri 'https://macfax.com/api/v1/keys'
```

## Rate Limits

| Endpoint | Anonymous | With Key |
|----------|-----------|----------|
| lookup | 10/min · 200/day | 100/min · 2000/day |
| price-stats | 30/min · 1000/day | 300/min · 10000/day |
| listings | 20/min · 500/day | 200/min · 5000/day |

## Documentation

- API Docs: https://macfax.com/developers
- OpenAPI Spec: https://macfax.com/api/v1/openapi.json
- MCP Server: https://macfax.com/mcp

## Support

Email: support@macfax.com
