"""
Flask API for Macfax Research + iFixit Parts Integration
Fetches real parts data from iFixit API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from macfax_client import MacfaxClient, MacfaxAPIError, RateLimitError, CreditsExhaustedError
import os
import requests
import json
import re

app = Flask(__name__)
CORS(app)
client = MacfaxClient()

IFIXIT_API_BASE = "https://www.ifixit.com/api/2.0"
APPLE_REPAIR_URL = "https://selfservicerepair.com"

def get_ifixit_device_name(model, device_type):
    """Convert Macfax device info to iFixit search query"""
    # Clean up model name for iFixit search
    model_clean = model
    
    # Remove year info in parentheses for better matching
    model_clean = re.sub(r'\s*\([^)]*\)', '', model_clean)
    
    # iFixit uses simpler names
    if 'MacBook Pro' in model:
        return 'MacBook Pro'
    elif 'MacBook Air' in model:
        return 'MacBook Air'
    elif 'MacBook' in model:
        return 'MacBook'
    elif 'iPhone' in model:
        # Extract iPhone model (e.g., "iPhone 13 Pro")
        match = re.search(r'iPhone\s+[\d\w\s]+', model)
        if match:
            return match.group(0).strip()
        return 'iPhone'
    elif 'iPad' in model:
        match = re.search(r'iPad\s+[\w\s]+', model)
        if match:
            return match.group(0).strip()
        return 'iPad'
    
    return model_clean

def search_ifixit_device(device_name):
    """Search for device on iFixit"""
    try:
        # Use iFixit suggest API for device search
        url = f"{IFIXIT_API_BASE}/suggest/{requests.utils.quote(device_name)}"
        params = {'doctypes': 'device'}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and 'results' in data and len(data['results']) > 0:
                return data['results'][0]
        
        return None
    except Exception as e:
        print(f"iFixit search error: {e}")
        return None

def get_ifixit_guides(device_name, repair_type):
    """Get repair guides from iFixit for specific repair type"""
    try:
        # Search for guides related to the repair
        search_query = f"{device_name} {repair_type} replacement"
        url = f"{IFIXIT_API_BASE}/search/{requests.utils.quote(search_query)}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and 'results' in data:
                guides = []
                for result in data['results'][:5]:  # Top 5 results
                    if result.get('dataType') == 'guide':
                        guides.append({
                            'title': result.get('title', ''),
                            'url': result.get('url', ''),
                            'guide_id': result.get('guideid'),
                            'image': result.get('image', {}).get('standard') if result.get('image') else None,
                            'difficulty': result.get('difficulty', 'Unknown'),
                            'time_required': result.get('time_required', 'Unknown')
                        })
                return guides
        
        return []
    except Exception as e:
        print(f"iFixit guides error: {e}")
        return []

def get_ifixit_parts_from_guide(guide_id):
    """Fetch parts list from a specific guide"""
    try:
        url = f"{IFIXIT_API_BASE}/guides/{guide_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and 'parts' in data:
                parts = []
                for part in data['parts']:
                    parts.append({
                        'name': part.get('text', 'Unknown Part'),
                        'url': part.get('url', ''),
                        'thumbnail': part.get('thumbnail', ''),
                        'notes': part.get('notes', '')
                    })
                return parts
            elif data and 'tools' in data:
                # Sometimes parts are listed as tools
                parts = []
                for tool in data['tools']:
                    parts.append({
                        'name': tool.get('text', 'Unknown Tool'),
                        'url': tool.get('url', ''),
                        'thumbnail': tool.get('thumbnail', ''),
                        'notes': 'Tool required for repair'
                    })
                return parts
        
        return []
    except Exception as e:
        print(f"iFixit parts fetch error: {e}")
        return []

def get_device_category(device_type):
    """Map device type to category"""
    if not device_type:
        return None
    
    device_lower = device_type.lower()
    
    if 'macbook pro' in device_lower or 'mac pro' in device_lower:
        return 'MacBook Pro'
    elif 'macbook air' in device_lower or 'mac air' in device_lower:
        return 'MacBook Air'
    elif 'macbook' in device_lower or 'mac laptop' in device_lower:
        return 'MacBook Pro'
    elif 'iphone' in device_lower or 'phone' in device_lower:
        return 'iPhone'
    elif 'ipad' in device_lower or 'tablet' in device_lower:
        return 'iPad'
    elif 'laptop' in device_lower:
        return 'MacBook Pro'
    elif 'mobile' in device_lower:
        return 'iPhone'
    
    return None

@app.route('/api/parts', methods=['GET'])
def get_parts():
    """Fetch parts from iFixit API"""
    serial = request.args.get('serial')
    repair_type = request.args.get('repair_type')
    model = request.args.get('model', '')
    device_type = request.args.get('device_type', '')
    
    if not serial or not repair_type:
        return jsonify({'error': 'Missing serial or repair_type parameter'}), 400
    
    try:
        # Map repair type to user-friendly name
        repair_names = {
            'screen': 'Display',
            'battery': 'Battery',
            'keyboard': 'Keyboard',
            'trackpad': 'Trackpad',
            'camera': 'Camera',
            'speaker': 'Speaker',
            'charging_port': 'Charging Port',
            'logic_board': 'Logic Board'
        }
        
        repair_display_name = repair_names.get(repair_type, repair_type.title())
        
        # Convert device model to iFixit search format
        device_name = get_ifixit_device_name(model, device_type)
        print(f"Searching iFixit for: {device_name} - {repair_display_name}")
        
        # Search for repair guides on iFixit
        guides = get_ifixit_guides(device_name, repair_display_name)
        
        if not guides:
            # Fallback to Apple Self Service Repair
            return jsonify({
                'success': True,
                'data': {
                    'device_model': model,
                    'device_type': device_type,
                    'repair_type': repair_type,
                    'repair_display_name': repair_display_name,
                    'serial': serial,
                    'source': 'apple',
                    'apple_repair_url': f"{APPLE_REPAIR_URL}/order",
                    'guides': [],
                    'parts': [],
                    'message': f'No iFixit guides found. Visit Apple Self Service Repair for genuine parts.'
                }
            })
        
        # Get parts from the first guide
        parts = []
        if guides and len(guides) > 0:
            guide_id = guides[0].get('guide_id')
            if guide_id:
                parts = get_ifixit_parts_from_guide(guide_id)
        
        return jsonify({
            'success': True,
            'data': {
                'device_model': model,
                'device_type': device_type,
                'repair_type': repair_type,
                'repair_display_name': repair_display_name,
                'serial': serial,
                'source': 'ifixit',
                'device_name': device_name,
                'guides': guides,
                'parts': parts,
                'apple_repair_url': f"{APPLE_REPAIR_URL}/order",
                'message': f'Found {len(guides)} repair guide(s) for {device_name}'
            }
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/repair-types', methods=['GET'])
def get_repair_types():
    """Get available repair types"""
    repair_types = [
        {'id': 'screen', 'name': 'Screen', 'available': True},
        {'id': 'battery', 'name': 'Battery', 'available': True},
        {'id': 'keyboard', 'name': 'Keyboard', 'available': True},
        {'id': 'trackpad', 'name': 'Trackpad', 'available': True},
        {'id': 'camera', 'name': 'Camera', 'available': True},
        {'id': 'speaker', 'name': 'Speaker', 'available': True},
        {'id': 'charging_port', 'name': 'Charging Port', 'available': True},
        {'id': 'logic_board', 'name': 'Logic Board', 'available': True}
    ]
    
    return jsonify({
        'success': True,
        'data': {
            'repair_types': repair_types
        }
    })

@app.route('/')
def home():
    """API documentation"""
    return jsonify({
        'service': 'Macfax API Research',
        'version': '1.0.0',
        'endpoints': {
            'lookup': '/api/lookup?serial=SERIAL_NUMBER',
            'price': '/api/price?config=CONFIG_NAME',
            'market': '/api/market?model=MODEL_NAME',
            'listings': '/api/listings?config=CONFIG_NAME&max_price=PRICE',
            'check': '/api/check?url=LISTING_URL',
            'bulk': '/api/bulk (POST with JSON body: {"serials": ["SERIAL1", "SERIAL2"]})'
        },
        'examples': {
            'lookup': '/api/lookup?serial=C02P73J9G8WP',
            'price': '/api/price?config=macbook-pro-14-m3pro-2023',
            'market': '/api/market?model=MacBook Air (13-inch, M4, 2025)',
            'listings': '/api/listings?config=macbook-pro-14-m3pro-2023&max_price=1500'
        }
    })

@app.route('/api/lookup', methods=['GET'])
def lookup():
    """Look up device by serial number"""
    serial = request.args.get('serial')
    if not serial:
        return jsonify({'error': 'Missing serial parameter'}), 400
    
    try:
        result = client.lookup_serial(serial)
        return jsonify(result)
    except MacfaxAPIError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/price', methods=['GET'])
def price():
    """Get price statistics"""
    config = request.args.get('config')
    if not config:
        return jsonify({'error': 'Missing config parameter'}), 400
    
    try:
        result = client.get_price_stats(config)
        return jsonify(result)
    except MacfaxAPIError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market', methods=['GET'])
def market():
    """Get market value"""
    model = request.args.get('model')
    if not model:
        return jsonify({'error': 'Missing model parameter'}), 400
    
    try:
        result = client.get_market_value(model)
        return jsonify(result)
    except MacfaxAPIError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/listings', methods=['GET'])
def listings():
    """Get marketplace listings"""
    config = request.args.get('config')
    if not config:
        return jsonify({'error': 'Missing config parameter'}), 400
    
    max_price = request.args.get('max_price', type=int)
    
    try:
        result = client.get_listings(config, max_price=max_price)
        return jsonify(result)
    except MacfaxAPIError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check', methods=['GET'])
def check():
    """Check listing trust score"""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400
    
    try:
        result = client.check_listing(url)
        return jsonify(result)
    except MacfaxAPIError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bulk', methods=['POST'])
def bulk():
    """Bulk lookup serials"""
    data = request.get_json()
    if not data or 'serials' not in data:
        return jsonify({'error': 'Missing serials in JSON body'}), 400
    
    serials = data['serials']
    if not isinstance(serials, list):
        return jsonify({'error': 'serials must be an array'}), 400
    
    try:
        results = client.bulk_lookup(serials)
        return jsonify({'results': results})
    except RateLimitError as e:
        return jsonify({'error': f'Rate limit: {str(e)}'}), 429
    except CreditsExhaustedError as e:
        return jsonify({'error': str(e)}), 402
    except MacfaxAPIError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'macfax-api'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
