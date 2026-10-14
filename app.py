"""
Flask API for Apple Self Service Repair Configuration Lookup
Scrapes logic board configuration from Apple's repair website
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from macfax_client import MacfaxClient, MacfaxAPIError, RateLimitError, CreditsExhaustedError
from apple_scraper import AppleScraper
import os
import time

app = Flask(__name__)
CORS(app)
client = MacfaxClient()

# Global scraper instance (reused for efficiency)
scraper = None

# Simple in-memory cache for configurations
config_cache = {}
CACHE_EXPIRY = 3600  # 1 hour in seconds

def get_scraper():
    """Get or create scraper instance"""
    global scraper
    if scraper is None:
        scraper = AppleScraper(headless=True)
    return scraper

@app.route('/')
def home():
    """API documentation"""
    return jsonify({
        'service': 'Apple Repair Configuration API',
        'version': '2.0.0',
        'endpoints': {
            'lookup': '/api/lookup?serial=SERIAL_NUMBER (Get device info)',
            'config': '/api/get-config?serial=SERIAL_NUMBER (Get logic board config from Apple)'
        },
        'examples': {
            'lookup': '/api/lookup?serial=C02P73J9G8WP',
            'config': '/api/get-config?serial=C02P73J9G8WP'
        }
    })



@app.route('/api/lookup', methods=['GET'])
def lookup():
    """Look up device by serial number using Macfax"""
    serial = request.args.get('serial')
    if not serial:
        return jsonify({'error': 'Missing serial parameter'}), 400
    
    try:
        result = client.lookup_serial(serial)
        return jsonify(result)
    except MacfaxAPIError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-config', methods=['GET'])
def get_config():
    """Get logic board configuration from Apple Self Service Repair website"""
    serial = request.args.get('serial')
    
    if not serial:
        return jsonify({'error': 'Missing serial parameter'}), 400
    
    try:
        # Check cache first
        cache_key = serial.upper()
        if cache_key in config_cache:
            cached_data = config_cache[cache_key]
            # Check if cache is still valid
            if time.time() - cached_data['timestamp'] < CACHE_EXPIRY:
                print(f"[API] Returning cached result for: {serial}")
                return jsonify({
                    'success': True,
                    'data': {
                        'serial': serial,
                        'config': cached_data['config'],
                        'message': 'Configuration retrieved from cache (instant)',
                        'cached': True
                    }
                })
            else:
                # Remove expired cache
                del config_cache[cache_key]
        
        print(f"[API] Getting configuration for serial: {serial}")
        
        # Get scraper and fetch config
        apple_scraper = get_scraper()
        result = apple_scraper.get_logic_board_config(serial)
        
        if result['success']:
            # Cache the result
            config_cache[cache_key] = {
                'config': result['config'],
                'timestamp': time.time()
            }
            print(f"[API] Cached result for: {serial}")
            
            return jsonify({
                'success': True,
                'data': {
                    'serial': serial,
                    'config': result['config'],
                    'message': 'Configuration retrieved successfully',
                    'cached': False
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 500
    
    except Exception as e:
        print(f"[API] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'apple-config-api'})

# Cleanup on shutdown
import atexit

def cleanup():
    """Cleanup scraper on shutdown"""
    global scraper
    if scraper:
        scraper.close()
        scraper = None

atexit.register(cleanup)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
