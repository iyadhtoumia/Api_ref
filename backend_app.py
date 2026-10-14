"""
Flask API with Authentication and Coin System
Behaves exactly like Telegram bot
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import sqlite3
import os
from functools import wraps
from apple_scraper import AppleScraper
from macfax_client import MacfaxClient, MacfaxAPIError
import time

app = Flask(__name__)
CORS(app)

# Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
DATABASE = 'users.db'

# Initialize clients (same as telegram_bot.py)
macfax_client = MacfaxClient()
scraper = None
config_cache = {}
CACHE_EXPIRY = 3600  # 1 hour

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database"""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            coins INTEGER DEFAULT 100,
            total_lookups INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS lookups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            serial TEXT NOT NULL,
            config TEXT NOT NULL,
            coins_spent INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def get_scraper():
    """Get or create scraper instance"""
    global scraper
    if scraper is None:
        scraper = AppleScraper(headless=True)
    return scraper

def token_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['user_id']
            
            conn = get_db()
            user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user_id,)).fetchone()
            conn.close()
            
            if not user:
                return jsonify({'error': 'User not found'}), 401
            
            return f(dict(user), *args, **kwargs)
        
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
    
    return decorated

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """Create new user account"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    conn = get_db()
    
    existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'Email already registered'}), 400
    
    password_hash = generate_password_hash(password)
    
    cursor = conn.execute(
        'INSERT INTO users (email, password_hash, coins) VALUES (?, ?, ?)',
        (email, password_hash, 100)
    )
    user_id = cursor.lastrowid
    conn.commit()
    
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, SECRET_KEY, algorithm='HS256')
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'coins': user['coins'],
            'total_lookups': user['total_lookups']
        }
    }), 201

@app.route('/api/auth/signin', methods=['POST'])
def signin():
    """Sign in user"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, SECRET_KEY, algorithm='HS256')
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'coins': user['coins'],
            'total_lookups': user['total_lookups']
        }
    })

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_me(current_user):
    """Get current user info"""
    return jsonify({
        'user': {
            'id': current_user['id'],
            'email': current_user['email'],
            'coins': current_user['coins'],
            'total_lookups': current_user['total_lookups']
        }
    })

@app.route('/api/lookup', methods=['POST'])
@token_required
def lookup_device(current_user):
    """Lookup device info using Macfax API (same as telegram bot /lookup command)"""
    data = request.json
    serial = data.get('serial', '').strip().upper()
    
    if not serial:
        return jsonify({'error': 'Serial number required'}), 400
    
    try:
        result = macfax_client.lookup_serial(serial)
        
        if result.get('success') and result.get('data'):
            device_data = result['data']
            return jsonify({
                'success': True,
                'model': device_data.get('model', 'N/A'),
                'device_type': device_data.get('device_type', 'N/A'),
                'data': device_data
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 404
    
    except MacfaxAPIError as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lookup-config', methods=['POST'])
@token_required
def lookup_config(current_user):
    """
    Lookup configuration using Apple Scraper - costs 10 coins
    Behaves exactly like telegram bot /config command
    """
    data = request.json
    serial = data.get('serial', '').strip().upper()
    
    if not serial:
        return jsonify({'error': 'Serial number required'}), 400
    
    # Validate serial format (basic check)
    if len(serial) < 4 or len(serial) > 20:
        return jsonify({'error': 'Invalid serial number format'}), 400
    
    # Check cache first (FREE - same as telegram bot)
    cache_key = serial
    if cache_key in config_cache:
        cached_data = config_cache[cache_key]
        if time.time() - cached_data['timestamp'] < CACHE_EXPIRY:
            print(f"[API] Cache hit for {serial}")
            return jsonify({
                'success': True,
                'serial': serial,
                'config': cached_data['config'],
                'cached': True,
                'coins_spent': 0,
                'message': 'Retrieved instantly from cache'
            })
        else:
            del config_cache[cache_key]
    
    # Check if user has enough coins
    if current_user['coins'] < 10:
        return jsonify({'error': 'Insufficient coins. You need 10 coins.'}), 400
    
    print(f"[API] Starting lookup for serial: {serial}")
    
    # Perform lookup using Apple Scraper (same as telegram bot - NO TIMEOUT!)
    try:
        apple_scraper = get_scraper()
        print(f"[API] Scraper initialized, calling get_logic_board_config...")
        
        # Call scraper directly without timeout (same as Telegram bot)
        result = apple_scraper.get_logic_board_config(serial)
        
        print(f"[API] Scraper returned: success={result.get('success')}")
        
        if not result or not isinstance(result, dict):
            return jsonify({
                'success': False,
                'error': 'Invalid response from scraper'
            }), 500
        
        if not result.get('success'):
            error_msg = result.get('error', 'Configuration not found')
            print(f"[API] Scraper failed: {error_msg}")
            
            # Don't charge coins for scraper errors
            return jsonify({
                'success': False,
                'error': error_msg,
                'debug': 'Serial may be invalid or configuration not available on Apple\'s website.'
            }), 404
        
        config = result.get('config')
        if not config:
            return jsonify({
                'success': False,
                'error': 'Configuration text is empty'
            }), 404
        
        print(f"[API] Success! Config: {config}")
        
        # Deduct coins and update user
        conn = get_db()
        conn.execute(
            'UPDATE users SET coins = coins - 10, total_lookups = total_lookups + 1 WHERE id = ?',
            (current_user['id'],)
        )
        
        # Record lookup
        conn.execute(
            'INSERT INTO lookups (user_id, serial, config, coins_spent) VALUES (?, ?, ?, ?)',
            (current_user['id'], serial, config, 10)
        )
        
        conn.commit()
        conn.close()
        
        # Cache the result
        config_cache[cache_key] = {
            'config': config,
            'timestamp': time.time()
        }
        
        print(f"[API] Cached result for {serial}")
        
        return jsonify({
            'success': True,
            'serial': serial,
            'config': config,
            'cached': False,
            'coins_spent': 10,
            'message': 'Configuration retrieved successfully'
        })
    
    except Exception as e:
        print(f"[API] Lookup error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'System error: {str(e)}'
        }), 500

@app.route('/api/history', methods=['GET'])
@token_required
def get_history(current_user):
    """Get user's lookup history"""
    conn = get_db()
    lookups = conn.execute(
        'SELECT serial, config, coins_spent, created_at FROM lookups WHERE user_id = ? ORDER BY created_at DESC LIMIT 50',
        (current_user['id'],)
    ).fetchall()
    conn.close()
    
    return jsonify({
        'history': [dict(lookup) for lookup in lookups]
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    # Increase timeout for long-running scraper operations
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
