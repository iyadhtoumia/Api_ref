# How to Use Your Deployed API

After deployment, you'll have a public URL like:
- Render: `https://macfax-api.onrender.com`
- Railway: `https://macfax-api.up.railway.app`
- Fly.io: `https://macfax-api.fly.dev`

## Use Cases & Examples

### 1. From Your Website/App (JavaScript)

```javascript
// Look up a Mac by serial number
async function lookupDevice(serial) {
    const response = await fetch(`https://YOUR-URL.onrender.com/api/lookup?serial=${serial}`);
    const data = await response.json();
    console.log(data);
}

// Get price for a specific model
async function getPrice(config) {
    const response = await fetch(`https://YOUR-URL.onrender.com/api/price?config=${config}`);
    const data = await response.json();
    return data;
}

// Search listings
async function findListings(config, maxPrice) {
    const response = await fetch(`https://YOUR-URL.onrender.com/api/listings?config=${config}&max_price=${maxPrice}`);
    const data = await response.json();
    return data;
}

// Example usage
lookupDevice('C02P73J9G8WP');
getPrice('macbook-pro-14-m3pro-2023');
findListings('macbook-pro-14-m3pro-2023', 1500);
```

### 2. From Python

```python
import requests

BASE_URL = "https://YOUR-URL.onrender.com"

# Look up serial
response = requests.get(f"{BASE_URL}/api/lookup", params={"serial": "C02P73J9G8WP"})
print(response.json())

# Get price stats
response = requests.get(f"{BASE_URL}/api/price", params={"config": "macbook-pro-14-m3pro-2023"})
print(response.json())

# Bulk lookup
response = requests.post(f"{BASE_URL}/api/bulk", json={
    "serials": ["C02P73J9G8WP", "C02XG7W9LVDT"]
})
print(response.json())
```

### 3. From PHP (Your Repair Shop Site)

```php
<?php
// Look up device
$serial = "C02P73J9G8WP";
$url = "https://YOUR-URL.onrender.com/api/lookup?serial=" . urlencode($serial);
$response = file_get_contents($url);
$data = json_decode($response, true);

echo "Device: " . $data['data']['device_type'];
echo "Model: " . $data['data']['model'];
echo "Year: " . $data['data']['year'];

// Get pricing
$config = "macbook-pro-14-m3pro-2023";
$url = "https://YOUR-URL.onrender.com/api/price?config=" . urlencode($config);
$response = file_get_contents($url);
$pricing = json_decode($response, true);

echo "Sale Estimate: $" . $pricing['data']['sold']['estimated_sale']['mid'];
?>
```

### 4. From cURL (Testing)

```bash
# Look up serial
curl "https://YOUR-URL.onrender.com/api/lookup?serial=C02P73J9G8WP"

# Get price
curl "https://YOUR-URL.onrender.com/api/price?config=macbook-pro-14-m3pro-2023"

# Get listings
curl "https://YOUR-URL.onrender.com/api/listings?config=macbook-pro-14-m3pro-2023&max_price=1500"

# Bulk lookup
curl -X POST "https://YOUR-URL.onrender.com/api/bulk" \
  -H "Content-Type: application/json" \
  -d '{"serials": ["C02P73J9G8WP", "C02XG7W9LVDT"]}'
```

### 5. From Excel/Google Sheets (Power Query)

```excel
// In Excel Power Query
let
    Source = Json.Document(Web.Contents("https://YOUR-URL.onrender.com/api/lookup?serial=C02P73J9G8WP")),
    data = Source[data],
    model = data[model]
in
    model
```

## Real-World Use Cases

### For Your Repair Shop:

**1. Customer Device Intake**
```javascript
// When customer brings device
function checkDevice(serial) {
    fetch(`/api/lookup?serial=${serial}`)
        .then(r => r.json())
        .then(data => {
            document.getElementById('device-model').value = data.data.model;
            document.getElementById('device-year').value = data.data.year;
            // Get market value for trade-in
            return fetch(`/api/market?model=${encodeURIComponent(data.data.model)}`);
        })
        .then(r => r.json())
        .then(pricing => {
            document.getElementById('trade-in-value').value = pricing.data.estimate.mid;
        });
}
```

**2. Parts Pricing Tool**
```php
<?php
// Check used market value before quoting repair
function shouldRepair($serial) {
    $device = getDeviceInfo($serial);
    $marketValue = getMarketValue($device['model']);
    $repairCost = 300; // Your repair cost
    
    if ($repairCost > $marketValue * 0.6) {
        return "Suggest replacement - repair cost too high";
    }
    return "Worth repairing";
}
?>
```

**3. Inventory Management**
```python
# Check market prices for your inventory
inventory = ["SERIAL1", "SERIAL2", "SERIAL3"]
response = requests.post("https://YOUR-URL/api/bulk", json={"serials": inventory})

for item in response.json()['results']:
    if item['result']['success']:
        model = item['result']['data']['model']
        # Get current market price
        price = get_price(model)
        print(f"{model}: ${price}")
```

**4. Customer Quote Generator**
```javascript
// Show customer what their device is worth
async function generateQuote(serial) {
    const device = await fetch(`/api/lookup?serial=${serial}`).then(r => r.json());
    const listings = await fetch(`/api/listings?config=${device.data.config}`).then(r => r.json());
    
    return {
        model: device.data.model,
        averagePrice: listings.data.median_price,
        repairRecommendation: calculateRepair(listings.data.median_price)
    };
}
```

**5. Trust Score for Buying Used Devices**
```python
# Check if a listing is legit before buying
def check_ebay_listing(url):
    response = requests.get(f"{BASE_URL}/api/check", params={"url": url})
    trust = response.json()
    
    if trust['data']['flags']:
        print(f"⚠️ Warning: {trust['data']['flags']}")
    else:
        print("✅ Listing looks good")
```

## API Endpoints Reference

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/` | GET | - | API documentation |
| `/api/lookup` | GET | `serial` | Look up device by serial |
| `/api/price` | GET | `config` | Get price statistics |
| `/api/market` | GET | `model` | Get market value |
| `/api/listings` | GET | `config`, `max_price` (optional) | Find marketplace listings |
| `/api/check` | GET | `url` | Check listing trust score |
| `/api/bulk` | POST | `{"serials": [...]}` | Bulk serial lookup |
| `/health` | GET | - | Health check |

## Integration Examples

### WordPress Plugin
```php
add_shortcode('macfax_lookup', function($atts) {
    $serial = $atts['serial'];
    $response = wp_remote_get("https://YOUR-URL/api/lookup?serial=$serial");
    $data = json_decode(wp_remote_retrieve_body($response), true);
    return $data['data']['model'];
});
// Usage: [macfax_lookup serial="C02P73J9G8WP"]
```

### Mobile App (React Native)
```javascript
import axios from 'axios';

const MacfaxAPI = {
    baseURL: 'https://YOUR-URL.onrender.com',
    
    async lookup(serial) {
        const response = await axios.get(`${this.baseURL}/api/lookup`, {
            params: { serial }
        });
        return response.data;
    },
    
    async getPrice(config) {
        const response = await axios.get(`${this.baseURL}/api/price`, {
            params: { config }
        });
        return response.data;
    }
};

export default MacfaxAPI;
```

### Automation (Zapier/Make.com)
1. Webhook trigger receives serial number
2. HTTP Request to your API
3. Parse JSON response
4. Send to Google Sheets/Airtable
5. Email notification with results

## Rate Limits & Costs

- Your API has no rate limit (you control it)
- Macfax API limits apply:
  - Free: 2000 lookups/day
  - Paid: 5000 lookups/day
- Cache results to save credits
- Same serial = free for 24 hours

## Monitoring

Check if your API is running:
```bash
curl https://YOUR-URL.onrender.com/health
```

## Next Steps

1. Deploy to Render/Railway
2. Get your deployed URL
3. Replace `YOUR-URL` in examples above
4. Test endpoints
5. Integrate into your repair shop website!
