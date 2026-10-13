"""
Flask API for Macfax Research + iFixit Parts Integration
Fetches real parts data from iFixit API
"""

from flask import Flask, request, jsonify, send_file
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
    """Fetch replacement parts list from a specific guide (exclude tools)"""
    try:
        url = f"{IFIXIT_API_BASE}/guides/{guide_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            parts_list = []
            
            # Extract ONLY replacement parts from guide (not tools)
            if data and 'parts' in data:
                for part in data['parts']:
                    part_info = {
                        'name': part.get('text', 'Unknown Part'),
                        'url': part.get('url', ''),
                        'thumbnail': part.get('thumbnail', ''),
                        'notes': part.get('notes', ''),
                        'type': 'replacement_part'
                    }
                    
                    # Try to get price and SKU from URL if available
                    part_url = part.get('url', '')
                    if part_url:
                        part_info['sku'] = extract_sku_from_url(part_url)
                    
                    parts_list.append(part_info)
            
            # DO NOT include tools - we only want replacement parts
            
            return parts_list
        
        return []
    except Exception as e:
        print(f"iFixit parts fetch error: {e}")
        return []

def extract_sku_from_url(url):
    """Extract SKU/product ID from iFixit URL"""
    try:
        # iFixit URLs often end with product codes
        parts = url.rstrip('/').split('/')
        if len(parts) > 0:
            return parts[-1]
    except:
        pass
    return None

def search_ifixit_parts_direct(device_name, repair_type):
    """Search for replacement parts directly in iFixit store (exclude tools)"""
    try:
        # Build search query for replacement parts only
        search_query = f"{device_name} {repair_type} replacement"
        url = f"{IFIXIT_API_BASE}/search/{requests.utils.quote(search_query)}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            parts = []
            
            # Filter keywords for tools to exclude
            tool_keywords = ['screwdriver', 'opener', 'pry', 'spudger', 'tweezers', 'suction', 
                           'pick', 'driver', 'bit set', 'toolkit', 'repair kit', 'tool']
            
            if data and 'results' in data:
                for result in data['results']:
                    # Look for product/part results only
                    if result.get('dataType') in ['product', 'item']:
                        title = result.get('title', '').lower()
                        
                        # Skip if it's a tool
                        is_tool = any(keyword in title for keyword in tool_keywords)
                        if is_tool:
                            continue
                        
                        # Only include actual replacement parts (battery, screen, etc.)
                        part_info = {
                            'name': result.get('title', 'Unknown Part'),
                            'url': result.get('url', ''),
                            'thumbnail': result.get('image', {}).get('thumbnail') if result.get('image') else None,
                            'price': result.get('price_string', 'See website'),
                            'availability': result.get('availability', 'Check availability'),
                            'type': 'replacement_part',
                            'source': 'store'
                        }
                        parts.append(part_info)
            
            return parts
        
        return []
    except Exception as e:
        print(f"iFixit parts search error: {e}")
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
    """Fetch matching parts from iFixit API"""
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
            'speaker_right': 'Right Speaker',
            'speaker_left': 'Left Speaker',
            'charging_port': 'Charging Port',
            'logic_board': 'Logic Board',
            'magsafe': 'MagSafe 3 Card',
            'usb_c': 'USB-C Cards',
            'display_hinge': 'Display Hinge Covers',
            'keys': 'Individual Keys',
            'antenna': 'Antenna',
            'bottom_case': 'Bottom Case',
            'audio_card': 'Audio Card',
            'touch_id': 'Touch ID Card',
            'lid_angle': 'Lid Angle Sensor',
            'other': 'Other Parts'
        }
        
        repair_display_name = repair_names.get(repair_type, repair_type.title())
        
        # Convert device model to iFixit search format
        device_name = get_ifixit_device_name(model, device_type)
        print(f"Searching iFixit parts for: {device_name} - {repair_display_name}")
        
        # Strategy 1: Search for repair guides to get parts lists
        guides = get_ifixit_guides(device_name, repair_display_name)
        all_parts = []
        
        # Get parts from guides
        if guides and len(guides) > 0:
            print(f"Found {len(guides)} guides, extracting parts...")
            for guide in guides[:3]:  # Top 3 guides
                guide_id = guide.get('guide_id')
                if guide_id:
                    parts = get_ifixit_parts_from_guide(guide_id)
                    all_parts.extend(parts)
        
        # Strategy 2: Direct parts search
        print(f"Searching iFixit store for parts...")
        store_parts = search_ifixit_parts_direct(device_name, repair_display_name)
        all_parts.extend(store_parts)
        
        # Remove duplicates based on name
        seen_names = set()
        unique_parts = []
        for part in all_parts:
            part_name = part.get('name', '').lower()
            if part_name and part_name not in seen_names:
                seen_names.add(part_name)
                unique_parts.append(part)
        
        if not unique_parts:
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
                    'parts': [],
                    'message': f'No parts found on iFixit. Visit Apple Self Service Repair for genuine {repair_display_name} parts.',
                    'guides': guides if guides else []
                }
            })
        
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
                'parts': unique_parts,
                'total_parts': len(unique_parts),
                'apple_repair_url': f"{APPLE_REPAIR_URL}/order",
                'message': f'Found {len(unique_parts)} replacement part(s) for {repair_display_name} repair',
                'guides': guides if guides else []
            }
        })
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/repair-types', methods=['GET'])
def get_repair_types():
    """Get available repair types"""
    repair_types = [
        {'id': 'screen', 'name': 'Screen (Écran)', 'available': True},
        {'id': 'battery', 'name': 'Battery (Batterie)', 'available': True},
        {'id': 'keyboard', 'name': 'Keyboard (Boîtier supérieur avec clavier)', 'available': True},
        {'id': 'trackpad', 'name': 'Trackpad (Trackpad et nappe)', 'available': True},
        {'id': 'logic_board', 'name': 'Logic Board (Carte logique)', 'available': True},
        {'id': 'camera', 'name': 'Camera', 'available': True},
        {'id': 'speaker_right', 'name': 'Right Speaker (Haut-parleur droit)', 'available': True},
        {'id': 'speaker_left', 'name': 'Left Speaker (Haut-parleur gauche)', 'available': True},
        {'id': 'charging_port', 'name': 'Charging Port', 'available': True},
        {'id': 'magsafe', 'name': 'MagSafe 3 Card (Carte MagSafe 3)', 'available': True},
        {'id': 'usb_c', 'name': 'USB-C Cards (Cartes USB-C)', 'available': True},
        {'id': 'display_hinge', 'name': 'Display Hinge Covers (Couvercles de charnière)', 'available': True},
        {'id': 'keys', 'name': 'Individual Keys (Touches)', 'available': True},
        {'id': 'antenna', 'name': 'Antenna (Antenne)', 'available': True},
        {'id': 'bottom_case', 'name': 'Bottom Case (Boîtier inférieur)', 'available': True},
        {'id': 'audio_card', 'name': 'Audio Card (Carte audio)', 'available': True},
        {'id': 'touch_id', 'name': 'Touch ID Card (Carte du Touch ID)', 'available': True},
        {'id': 'lid_angle', 'name': 'Lid Angle Sensor (Capteur d\'angle)', 'available': True},
        {'id': 'other', 'name': 'Other Parts (Autres pièces)', 'available': True}
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

@app.route('/demo')
@app.route('/demo.html')
def demo():
    """Serve demo HTML page"""
    return send_file('demo.html')

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
