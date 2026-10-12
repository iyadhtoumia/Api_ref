# Macfax API Service

Production-ready REST API for Mac, iPad, and iPhone device lookup, pricing data, and marketplace listings.

## Features

- 🔍 Device lookup by serial number
- 💰 Real-time pricing statistics
- 📊 Market value estimation
- 🛒 Live marketplace listings
- ✅ Listing trust verification
- 🔄 Bulk operations support

## Quick Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Manual Deployment

1. **Fork/Clone this repo to your GitHub**

2. **Go to [render.com](https://render.com)**

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect Python

4. **Configure Environment Variable**
   - Add: `MACFAX_API_KEY`
   - Get free key: `curl -X POST https://macfax.com/api/v1/keys`

5. **Deploy!**
   - Click "Create Web Service"
   - Wait 2-3 minutes
   - Your API will be live!

## API Endpoints

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/` | GET | - | API documentation |
| `/api/lookup` | GET | `serial` | Look up device by serial |
| `/api/price` | GET | `config` | Get price statistics |
| `/api/market` | GET | `model` | Get market value |
| `/api/listings` | GET | `config`, `max_price` | Find marketplace listings |
| `/api/check` | GET | `url` | Check listing trust |
| `/api/bulk` | POST | `{"serials": [...]}` | Bulk lookups |
| `/health` | GET | - | Health check |

## Usage Examples

### cURL
```bash
# Look up device
curl "https://your-app.onrender.com/api/lookup?serial=C02P73J9G8WP"

# Get pricing
curl "https://your-app.onrender.com/api/price?config=macbook-pro-14-m3pro-2023"

# Find listings under $1500
curl "https://your-app.onrender.com/api/listings?config=macbook-pro-14-m3pro-2023&max_price=1500"
```

### JavaScript
```javascript
const response = await fetch('https://your-app.onrender.com/api/lookup?serial=C02P73J9G8WP');
const data = await response.json();
console.log(data.data.model);
```

### Python
```python
import requests
response = requests.get('https://your-app.onrender.com/api/lookup', 
                       params={'serial': 'C02P73J9G8WP'})
print(response.json())
```

### PHP
```php
$serial = "C02P73J9G8WP";
$url = "https://your-app.onrender.com/api/lookup?serial=" . urlencode($serial);
$data = json_decode(file_get_contents($url), true);
echo $data['data']['model'];
```

## Demo Page

Open `demo.html` in your browser to test the API with a visual interface.

## Configuration

Create `.env.dev` file:
```
MACFAX_API_KEY=your_key_here
MACFAX_BASE_URL=https://macfax.com/api/v1
MACFAX_TIMEOUT=30
```

Get API key:
```bash
curl -X POST https://macfax.com/api/v1/keys
```

## Rate Limits

- Macfax Free: 2000 lookups/day
- Your API: No limits (you control it)
- Render Free: 750 hours/month

## Local Development

```bash
pip install -r requirements.txt
python app.py
```

Visit: http://localhost:5000

## Documentation

- Full usage guide: [USAGE_GUIDE.md](USAGE_GUIDE.md)
- Free deployment options: [FREE_DEPLOYMENT.md](FREE_DEPLOYMENT.md)
- Macfax API docs: https://macfax.com/developers

## Support

- Macfax API: support@macfax.com
- This wrapper: [GitHub Issues](https://github.com/iyadhtoumia/Api_ref/issues)

## License

MIT
