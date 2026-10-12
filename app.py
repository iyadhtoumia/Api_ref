"""
Flask API for Macfax Research
After deployment, call this API from anywhere
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from macfax_client import MacfaxClient, MacfaxAPIError, RateLimitError, CreditsExhaustedError
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
client = MacfaxClient()

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
