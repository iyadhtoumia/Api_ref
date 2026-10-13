# Macfax API + iFixit Repair Service

Production-ready REST API combining Mac/iPad/iPhone device lookup with real repair guides and parts from iFixit.

## Features

- 🔍 **Device lookup by serial number** - Macfax API integration
- 🔧 **Real repair guides** - iFixit API integration
- 🛠️ **Parts identification** - Tools and components needed
- 💰 **Real-time pricing statistics** - Market data
- 📊 **Market value estimation** - Device valuation
- 🛒 **Live marketplace listings** - Find deals
- ✅ **Listing trust verification** - Safety checks
- 🔄 **Bulk operations support** - Process multiple devices

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

### Device & Repair Endpoints

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/` | GET | - | API documentation |
| `/api/lookup` | GET | `serial` | Look up device by serial |
| `/api/parts` | GET | `serial`, `repair_type`, `model`, `device_type` | Get repair guides & parts from iFixit |
| `/api/repair-types` | GET | - | List available repair types |
| `/api/price` | GET | `config` | Get price statistics |
| `/api/market` | GET | `model` | Get market value |
| `/api/listings` | GET | `config`, `max_price` | Find marketplace listings |
| `/api/check` | GET | `url` | Check listing trust |
| `/api/bulk` | POST | `{"serials": [...]}` | Bulk lookups |
| `/health` | GET | - | Health check |

### Repair Types

- `screen` - Display replacement
- `battery` - Battery replacement
- `keyboard` - Keyboard repair/replacement
- `trackpad` - Trackpad replacement
- `camera` - Camera module replacement
- `speaker` - Speaker replacement
- `charging_port` - Charging port repair
- `logic_board` - Logic board repair

## Usage Examples

### Get Repair Parts & Guides
```bash
# Get repair guides and parts for a device
curl "https://your-app.onrender.com/api/parts?serial=C02P73J9G8WP&repair_type=battery&model=MacBook%20Pro&device_type=Mac%20laptops"
```

Response:
```json
{
  "success": true,
  "data": {
    "device_model": "MacBook Pro (Retina, 15-inch, Mid 2015)",
    "repair_type": "battery",
    "repair_display_name": "Battery",
    "source": "ifixit",
    "guides": [
      {
        "title": "MacBook Pro Battery Replacement",
        "url": "https://www.ifixit.com/Guide/...",
        "difficulty": "Moderate",
        "time_required": "30 minutes - 1 hour",
        "image": "https://..."
      }
    ],
    "parts": [
      {
        "name": "MacBook Pro 15\" Retina Battery",
        "url": "https://www.ifixit.com/products/...",
        "notes": "Replacement battery pack"
      }
    ]
  }
}
```

### Device Lookup
```bash
# Look up device
curl "https://your-app.onrender.com/api/lookup?serial=C02P73J9G8WP"
```

### JavaScript
```javascript
// Look up device
const deviceResponse = await fetch('https://your-app.onrender.com/api/lookup?serial=C02P73J9G8WP');
const deviceData = await deviceResponse.json();

// Get repair guides
const partsResponse = await fetch(`https://your-app.onrender.com/api/parts?serial=C02P73J9G8WP&repair_type=battery&model=${encodeURIComponent(deviceData.data.model)}&device_type=${encodeURIComponent(deviceData.data.device_type)}`);
const partsData = await partsResponse.json();

console.log('Repair guides:', partsData.data.guides);
console.log('Required parts:', partsData.data.parts);
```

### Python
```python
import requests

# Look up device
response = requests.get('https://your-app.onrender.com/api/lookup', 
                       params={'serial': 'C02P73J9G8WP'})
device = response.json()

# Get repair parts
parts_response = requests.get('https://your-app.onrender.com/api/parts', params={
    'serial': 'C02P73J9G8WP',
    'repair_type': 'battery',
    'model': device['data']['model'],
    'device_type': device['data']['device_type']
})
parts = parts_response.json()
print(f"Found {len(parts['data']['guides'])} repair guides")
```

## Demo Page

Open `demo.html` in your browser to test the complete repair workflow:
1. Enter device serial number
2. Select repair type (screen, battery, etc.)
3. View iFixit repair guides with step-by-step instructions
4. See required parts and tools
5. Fallback to Apple Self Service Repair if needed

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

## Rate Limits & APIs Used

- **Macfax API**: 2000 lookups/day (free tier)
- **iFixit API**: Public API, no key required
- **Your API**: No limits (you control it)
- **Render Free Tier**: 750 hours/month

## How It Works

1. **Device Identification**: Uses Macfax API to identify device by serial number
2. **Repair Guide Search**: Searches iFixit's database for matching repair guides
3. **Parts Extraction**: Extracts required parts and tools from repair guides
4. **Fallback**: If no iFixit guides found, directs to Apple Self Service Repair

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python app.py
```

Visit: http://localhost:5000

Open `demo.html` in browser to test the UI

## Documentation

- Macfax API docs: https://macfax.com/developers
- iFixit API docs: https://www.ifixit.com/api/2.0/doc
- Full deployment guide: [RENDER_DEPLOY.md](RENDER_DEPLOY.md)

## Support

- Macfax API: support@macfax.com
- iFixit API: https://www.ifixit.com/api
- This service: [GitHub Issues](https://github.com/iyadhtoumia/Api_ref/issues)

## License

MIT
