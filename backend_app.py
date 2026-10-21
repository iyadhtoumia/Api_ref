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
import secrets
import stripe
import paypalrestsdk
from functools import wraps
from apple_scraper import AppleScraper
from macfax_client import MacfaxClient, MacfaxAPIError
from sickw_client import SickwClient
from cache import cache
import services as service_registry
from mailer import send_verification_email, send_resend_verification_email, send_otp_email, _send
from sync_services import sync_all, import_services
import time
import threading

app = Flask(__name__)
CORS(app)

# Configuration
SECRET_KEY = os.getenv('SECRET_KEY', '')
if not SECRET_KEY:
    raise RuntimeError(
        'SECRET_KEY environment variable is not set. '
        'Generate one with: python -c "import secrets; print(secrets.token_hex(64))"'
    )
DATABASE = os.getenv('DATABASE', 'users.db')

stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

paypalrestsdk.configure({
    'mode': os.getenv('PAYPAL_MODE', 'sandbox'),
    'client_id': os.getenv('PAYPAL_CLIENT_ID', ''),
    'client_secret': os.getenv('PAYPAL_CLIENT_SECRET', ''),
})

# Initialize clients (same as telegram_bot.py)
macfax_client = MacfaxClient()
sickw_client = SickwClient()

# Services handled by the Apple scraper
APPLE_SCRAPER_SERVICES = {999}

# All service IDs are forwarded to sickw

# Single thread-safe scraper instance. Each worker thread gets its own
# Chrome driver internally (capped at MAX_BROWSERS).
MAX_BROWSERS = 2
scraper = None
scraper_lock = threading.Lock()
CACHE_EXPIRY = 3600  # 1 hour

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    return conn

def init_db():
    """Initialize database"""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            coins INTEGER DEFAULT 0,
            balance_eur INTEGER NOT NULL DEFAULT 0,
            total_lookups INTEGER DEFAULT 0,
            verified INTEGER NOT NULL DEFAULT 0,
            verify_token TEXT,
            verify_token_expires TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Migrate existing users table if needed
    for col, definition in [
        ('verified',               'INTEGER NOT NULL DEFAULT 0'),
        ('verify_token',           'TEXT'),
        ('verify_token_expires',   'TIMESTAMP'),
        ('balance_eur',            'INTEGER NOT NULL DEFAULT 0'),
        ('telegram_id',            'INTEGER UNIQUE'),
        ('tg_link_token',          'TEXT'),
        ('tg_link_token_expires',  'TIMESTAMP'),
        ('otp_code',               'TEXT'),
        ('otp_expires',            'TIMESTAMP'),
    ]:
        try:
            conn.execute(f'ALTER TABLE users ADD COLUMN {col} {definition}')
        except Exception:
            pass
    conn.execute('''
        CREATE TABLE IF NOT EXISTS lookups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            serial TEXT NOT NULL,
            config TEXT NOT NULL,
            coins_spent INTEGER NOT NULL DEFAULT 0,
            amount_eur INTEGER NOT NULL DEFAULT 0,
            service_id INTEGER,
            service_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    # Migrate: add columns if they don't exist yet
    for col, definition in [
        ('service_id',  'INTEGER'),
        ('service_name', 'TEXT'),
        ('amount_eur',  'INTEGER NOT NULL DEFAULT 0'),
    ]:
        try:
            conn.execute(f'ALTER TABLE lookups ADD COLUMN {col} {definition}')
        except Exception:
            pass
    conn.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id           INTEGER PRIMARY KEY,
            name         TEXT    NOT NULL,
            category     TEXT    NOT NULL,
            price        REAL    NOT NULL,
            active       INTEGER NOT NULL DEFAULT 1,
            last_checked TIMESTAMP,
            last_status  TEXT    DEFAULT 'unknown'
        )
    ''')
    for col, definition in [
        ('last_checked', 'TIMESTAMP'),
        ('last_status',  "TEXT DEFAULT 'unknown'"),
    ]:
        try:
            conn.execute(f'ALTER TABLE services ADD COLUMN {col} {definition}')
        except Exception:
            pass
    conn.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id               INTEGER NOT NULL,
            stripe_session_id     TEXT UNIQUE NOT NULL,
            stripe_payment_intent TEXT,
            amount_eur            INTEGER NOT NULL,
            status                TEXT NOT NULL DEFAULT 'pending',
            provider              TEXT NOT NULL DEFAULT 'stripe',
            created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    # Migrate: add provider column if missing
    try:
        conn.execute("ALTER TABLE payments ADD COLUMN provider TEXT NOT NULL DEFAULT 'stripe'")
    except Exception:
        pass
    # Migrate: add refunded_at column if missing
    try:
        conn.execute("ALTER TABLE payments ADD COLUMN refunded_at TIMESTAMP")
    except Exception:
        pass
    # Migrate: add is_admin and banned columns to users if missing
    for col, definition in [
        ('is_admin',      'INTEGER NOT NULL DEFAULT 0'),
        ('banned',        'INTEGER NOT NULL DEFAULT 0'),
        ('totp_secret',   'TEXT'),
        ('totp_enabled',  'INTEGER NOT NULL DEFAULT 0'),
        ('otp_attempts',  'INTEGER NOT NULL DEFAULT 0'),
        ('otp_locked_until', 'TIMESTAMP'),
    ]:
        try:
            conn.execute(f'ALTER TABLE users ADD COLUMN {col} {definition}')
        except Exception:
            pass
    
    # FAQ table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    _bootstrap_admin()

def _bootstrap_admin():
    """Create the hardcoded admin account from env vars if it doesn't exist yet."""
    admin_email    = os.getenv('ADMIN_EMAIL', '').strip().lower()
    admin_password = os.getenv('ADMIN_PASSWORD', '').strip()
    if not admin_email or not admin_password:
        return  # not configured — skip
    conn = get_db()
    try:
        existing = conn.execute('SELECT id, is_admin FROM users WHERE email = ?', (admin_email,)).fetchone()
        if existing:
            # Ensure the flag is set even if the account already existed
            if not existing['is_admin']:
                conn.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (existing['id'],))
                conn.commit()
            return
        pw_hash = generate_password_hash(admin_password)
        conn.execute(
            'INSERT INTO users (email, password_hash, balance_eur, verified, is_admin) VALUES (?, ?, 0, 1, 1)',
            (admin_email, pw_hash)
        )
        conn.commit()
        print(f'[Admin] Bootstrap account created: {admin_email}')
    finally:
        conn.close()


def get_scraper():
    """Get or create the shared thread-safe scraper instance"""
    global scraper
    if scraper is None:
        with scraper_lock:
            if scraper is None:
                scraper = AppleScraper(headless=True, max_browsers=MAX_BROWSERS)
    return scraper

def _startup_prewarm():
    """Warm the Apple token/DeviceTypes cache so the first lookup is fast."""
    try:
        get_scraper()._get_api_client().prewarm()
    except Exception as e:
        print(f"[Startup] Prewarm skipped: {e}")

threading.Thread(target=_startup_prewarm, name='startup-prewarm', daemon=True).start()

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
            
            # Enforce suspension
            if user.get('banned'):
                return jsonify({'error': 'Account is suspended'}), 403
            
            return f(dict(user), *args, **kwargs)
        
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
    
    return decorated


def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            conn = get_db()
            user = conn.execute('SELECT * FROM users WHERE id = ?', (data['user_id'],)).fetchone()
            conn.close()
            if not user:
                return jsonify({'error': 'User not found'}), 401
            if not user['is_admin']:
                return jsonify({'error': 'Admin access required'}), 403
            return f(dict(user), *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
    return decorated

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """Create new user account — sends verification email before allowing login"""
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    conn = get_db()
    existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        conn.close()
        # Don't reveal that email exists
        return jsonify({
            'message': 'If this email is not already registered, you will receive a verification link.'
        }), 201

    password_hash = generate_password_hash(password)
    token = secrets.token_urlsafe(32)
    expires = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

    conn.execute(
        'INSERT INTO users (email, password_hash, balance_eur, verified, verify_token, verify_token_expires) '
        'VALUES (?, ?, ?, 0, ?, ?)',
        (email, password_hash, 0, token, expires.isoformat())
    )
    conn.commit()
    conn.close()

    # Send verification email (non-blocking — failure doesn't break signup)
    try:
        send_verification_email(email, token)
    except Exception as e:
        print(f"[Mail] Failed to send verification email to {email}: {e}")

    return jsonify({
        'message': 'Account created. Please check your email to verify your account before signing in.'
    }), 201


@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Sign in or register with Google ID token."""
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests

    data = request.json or {}
    credential = data.get('credential', '')
    if not credential:
        return jsonify({'error': 'Missing Google credential'}), 400

    google_client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    if not google_client_id:
        return jsonify({'error': 'Google auth not configured'}), 500

    try:
        info = id_token.verify_oauth2_token(credential, google_requests.Request(), google_client_id)
    except Exception as e:
        return jsonify({'error': f'Invalid Google token: {e}'}), 401

    email = info.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'No email in Google account'}), 400

    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if not user:
            # Auto-register — no password, pre-verified
            conn.execute(
                'INSERT INTO users (email, password_hash, balance_eur, verified) VALUES (?, ?, 0, 1)',
                (email, generate_password_hash(secrets.token_hex(32)))
            )
            conn.commit()
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        elif user['banned']:
            return jsonify({'error': 'Account is banned'}), 403
    finally:
        conn.close()

    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, SECRET_KEY, algorithm='HS256')

    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'balance_eur': user['balance_eur'],
            'total_lookups': user['total_lookups'],
            'is_admin': bool(user['is_admin']),
            'verified': True,
        }
    })


@app.route('/api/auth/signin', methods=['POST'])
def signin():
    """Sign in step 1 — validate credentials and send OTP email."""
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if not user or not check_password_hash(user['password_hash'], password):
        conn.close()
        return jsonify({'error': 'Invalid email or password'}), 401

    if not user['verified']:
        conn.close()
        return jsonify({
            'error': 'Please verify your email before signing in.',
            'unverified': True
        }), 403
    
    # Enforce suspension at sign-in
    if user.get('banned'):
        conn.close()
        return jsonify({'error': 'Account is suspended'}), 403

    # Skip OTP for admin accounts (for easier access)
    if user.get('is_admin'):
        conn.close()
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }, SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'balance_eur': user['balance_eur'],
                'total_lookups': user['total_lookups'],
                'is_admin': True,
            }
        })

    # Generate 6-digit OTP for regular users
    otp = str(secrets.randbelow(900000) + 100000)
    otp_expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    conn.execute(
        'UPDATE users SET otp_code = ?, otp_expires = ? WHERE id = ?',
        (otp, otp_expires.isoformat(), user['id'])
    )
    conn.commit()
    conn.close()

    try:
        send_otp_email(email, otp)
    except Exception as e:
        print(f"[Mail] Failed to send OTP to {email}: {e}")
        return jsonify({'error': 'Failed to send verification code. Please try again.'}), 500

    return jsonify({'otp_required': True, 'email': email}), 200


@app.route('/api/auth/signin/verify-otp', methods=['POST'])
def signin_verify_otp():
    """Sign in step 2 — verify OTP and return JWT."""
    data = request.json
    email = data.get('email', '').strip().lower()
    otp = data.get('otp', '').strip()
    use_totp = data.get('use_totp', False)

    if not email or not otp:
        return jsonify({'error': 'Email and code are required'}), 400

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if not user:
        conn.close()
        return jsonify({'error': 'Invalid request'}), 400

    # Check rate limit
    otp_locked_until = user.get('otp_locked_until')
    if otp_locked_until:
        try:
            locked_until = datetime.datetime.fromisoformat(otp_locked_until)
            if datetime.datetime.utcnow() < locked_until:
                conn.close()
                return jsonify({'error': 'Too many failed attempts. Please try again later.'}), 429
        except Exception:
            pass

    if use_totp:
        # Verify against Google Authenticator TOTP
        import pyotp
        if not user['totp_enabled'] or not user['totp_secret']:
            conn.close()
            return jsonify({'error': 'Authenticator app is not set up for this account'}), 400
        totp = pyotp.TOTP(user['totp_secret'])
        if not totp.verify(otp, valid_window=1):
            conn.close()
            return jsonify({'error': 'Invalid authenticator code'}), 401
    else:
        # Verify email OTP
        if not user['otp_code'] or user['otp_code'] != otp:
            # Increment failed attempts
            attempts = user.get('otp_attempts', 0) + 1
            if attempts >= 5:
                # Lock for 15 minutes after 5 failed attempts
                locked_until = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
                conn.execute(
                    'UPDATE users SET otp_attempts = 0, otp_locked_until = ? WHERE id = ?',
                    (locked_until.isoformat(), user['id'])
                )
                conn.commit()
                conn.close()
                return jsonify({'error': 'Too many failed attempts. Account locked for 15 minutes.'}), 429
            else:
                conn.execute(
                    'UPDATE users SET otp_attempts = ? WHERE id = ?',
                    (attempts, user['id'])
                )
                conn.commit()
                conn.close()
                return jsonify({'error': 'Invalid verification code'}), 401
        try:
            expires = datetime.datetime.fromisoformat(user['otp_expires'])
            if datetime.datetime.utcnow() > expires:
                conn.close()
                return jsonify({'error': 'Verification code has expired. Please sign in again.', 'expired': True}), 401
        except Exception:
            conn.close()
            return jsonify({'error': 'Invalid code'}), 400
        # Clear email OTP and reset attempts
        conn.execute(
            'UPDATE users SET otp_code = NULL, otp_expires = NULL, otp_attempts = 0, otp_locked_until = NULL WHERE id = ?',
            (user['id'],)
        )
        conn.commit()

    conn.close()

    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, SECRET_KEY, algorithm='HS256')

    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'balance_eur': user['balance_eur'],
            'total_lookups': user['total_lookups'],
            'is_admin': bool(user['is_admin']),
        }
    })

@app.route('/api/auth/verify', methods=['GET'])
def verify_email():
    """Verify email with token from link"""
    token = request.args.get('token', '').strip()
    if not token:
        return jsonify({'error': 'Token is required'}), 400

    conn = get_db()
    user = conn.execute(
        'SELECT * FROM users WHERE verify_token = ?', (token,)
    ).fetchone()

    if not user:
        conn.close()
        return jsonify({'error': 'Invalid or expired verification link'}), 400

    # Check expiry
    try:
        expires = datetime.datetime.fromisoformat(user['verify_token_expires'])
        if datetime.datetime.utcnow() > expires:
            conn.close()
            return jsonify({'error': 'Verification link has expired. Please request a new one.', 'expired': True}), 400
    except Exception:
        conn.close()
        return jsonify({'error': 'Invalid token'}), 400

    # Mark verified
    conn.execute(
        'UPDATE users SET verified = 1, verify_token = NULL, verify_token_expires = NULL WHERE id = ?',
        (user['id'],)
    )
    conn.commit()
    conn.close()

    # Auto-login: return JWT
    jwt_token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, SECRET_KEY, algorithm='HS256')

    return jsonify({
        'message': 'Email verified successfully.',
        'token': jwt_token,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'balance_eur': user['balance_eur'],
            'total_lookups': user['total_lookups'],
            'is_admin': bool(user['is_admin']) if user['is_admin'] else False,
        }
    })


@app.route('/api/auth/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    data = request.json
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if not user:
        conn.close()
        # Don't reveal whether email exists
        return jsonify({'message': 'If that email exists, a verification link has been sent.'}), 200

    if user['verified']:
        conn.close()
        return jsonify({'error': 'This account is already verified.'}), 400

    token = secrets.token_urlsafe(32)
    expires = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    conn.execute(
        'UPDATE users SET verify_token = ?, verify_token_expires = ? WHERE id = ?',
        (token, expires.isoformat(), user['id'])
    )
    conn.commit()
    conn.close()

    try:
        send_resend_verification_email(email, token)
    except Exception as e:
        print(f"[Mail] Resend failed for {email}: {e}")

    return jsonify({'message': 'Verification email sent. Please check your inbox.'})


@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_me(current_user):
    """Get current user info"""
    return jsonify({
        'user': {
            'id': current_user['id'],
            'email': current_user['email'],
            'balance_eur': current_user['balance_eur'],
            'total_lookups': current_user['total_lookups'],
            'telegram_linked': bool(current_user.get('telegram_id')),
            'is_admin': bool(current_user.get('is_admin')),
            'verified': bool(current_user.get('verified')),
            'created_at': current_user.get('created_at'),
            'totp_enabled': bool(current_user.get('totp_enabled')),
        }
    })


@app.route('/api/auth/telegram-link-token', methods=['POST'])
@token_required
def generate_telegram_link_token(current_user):
    """
    Generate a short-lived token the user pastes into the Telegram bot via /link <token>.
    The bot calls /api/auth/telegram-claim to bind its telegram_id to this account.
    """
    token = secrets.token_urlsafe(16)
    expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    conn = get_db()
    try:
        conn.execute(
            'UPDATE users SET tg_link_token = ?, tg_link_token_expires = ? WHERE id = ?',
            (token, expires.isoformat(), current_user['id'])
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({'token': token, 'expires_in': 900})


@app.route('/api/auth/telegram-claim', methods=['POST'])
def telegram_claim():
    """
    Called by the Telegram bot with the token the user typed.
    Binds the telegram_id to the matching website account.
    Body: { token, telegram_id }
    This endpoint is internal — only reachable from the bot (no user JWT needed).
    Protect with a shared secret if exposed publicly.
    """
    data = request.json or {}
    token = data.get('token', '').strip()
    telegram_id = data.get('telegram_id')

    if not token or not telegram_id:
        return jsonify({'error': 'token and telegram_id are required'}), 400

    conn = get_db()
    try:
        user = conn.execute(
            'SELECT * FROM users WHERE tg_link_token = ?', (token,)
        ).fetchone()

        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 400

        try:
            expires = datetime.datetime.fromisoformat(user['tg_link_token_expires'])
            if datetime.datetime.utcnow() > expires:
                return jsonify({'error': 'Token has expired. Generate a new one from the website.'}), 400
        except Exception:
            return jsonify({'error': 'Invalid token'}), 400

        # Check if this telegram_id is already attached to a bot-only account — merge balances
        existing_bot_account = conn.execute(
            'SELECT * FROM users WHERE telegram_id = ? AND id != ?',
            (telegram_id, user['id'])
        ).fetchone()

        if existing_bot_account:
            # Merge: add bot account's balance to the real account, reassign lookups
            conn.execute(
                'UPDATE users SET balance_eur = balance_eur + ? WHERE id = ?',
                (existing_bot_account['balance_eur'], user['id'])
            )
            conn.execute(
                'UPDATE lookups SET user_id = ? WHERE user_id = ?',
                (user['id'], existing_bot_account['id'])
            )
            conn.execute(
                'UPDATE payments SET user_id = ? WHERE user_id = ?',
                (user['id'], existing_bot_account['id'])
            )
            conn.execute('DELETE FROM users WHERE id = ?', (existing_bot_account['id'],))

        conn.execute(
            'UPDATE users SET telegram_id = ?, tg_link_token = NULL, tg_link_token_expires = NULL WHERE id = ?',
            (telegram_id, user['id'])
        )
        conn.commit()
        return jsonify({'status': 'linked', 'email': user['email']})
    finally:
        conn.close()


@app.route('/api/auth/telegram-unlink', methods=['POST'])
@token_required
def telegram_unlink(current_user):
    """Remove the telegram_id binding from the current account."""
    conn = get_db()
    try:
        conn.execute('UPDATE users SET telegram_id = NULL WHERE id = ?', (current_user['id'],))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'status': 'unlinked'})


@app.route('/api/auth/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Change password — requires current password verification."""
    data = request.json or {}
    current_pw = data.get('current_password', '')
    new_pw = data.get('new_password', '')

    if not current_pw or not new_pw:
        return jsonify({'error': 'Both current and new password are required'}), 400
    if len(new_pw) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400

    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user['id'],)).fetchone()
        if not check_password_hash(user['password_hash'], current_pw):
            return jsonify({'error': 'Current password is incorrect'}), 401
        new_hash = generate_password_hash(new_pw)
        conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, current_user['id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'status': 'password updated'})


@app.route('/api/auth/change-email', methods=['POST'])
@token_required
def change_email(current_user):
    """Change email — requires password verification, sends verification to new address."""
    data = request.json or {}
    new_email = data.get('new_email', '').strip().lower()
    password  = data.get('password', '')

    if not new_email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    if new_email == current_user['email']:
        return jsonify({'error': 'That is already your current email'}), 400

    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user['id'],)).fetchone()
        if not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Password is incorrect'}), 401
        existing = conn.execute('SELECT id FROM users WHERE email = ?', (new_email,)).fetchone()
        if existing:
            return jsonify({'error': 'Email already in use'}), 400
        conn.execute('UPDATE users SET email = ? WHERE id = ?', (new_email, current_user['id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'status': 'email updated', 'email': new_email})


@app.route('/api/auth/totp/setup', methods=['POST'])
@token_required
def totp_setup(current_user):
    """Generate a new TOTP secret and return the QR code URI."""
    import pyotp, qrcode, io, base64
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user['email'], issuer_name='RepairAPI')

    # Generate QR code as base64 PNG
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    # Store secret temporarily (not enabled yet — user must verify first)
    conn = get_db()
    try:
        conn.execute('UPDATE users SET totp_secret = ? WHERE id = ?', (secret, current_user['id']))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'secret': secret, 'qr': f'data:image/png;base64,{qr_b64}', 'uri': uri})


@app.route('/api/auth/totp/enable', methods=['POST'])
@token_required
def totp_enable(current_user):
    """Verify the TOTP code and enable authenticator 2FA."""
    import pyotp
    data = request.json or {}
    code = data.get('code', '').strip()

    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user['id'],)).fetchone()
        if not user['totp_secret']:
            return jsonify({'error': 'No TOTP setup in progress'}), 400
        totp = pyotp.TOTP(user['totp_secret'])
        if not totp.verify(code, valid_window=1):
            return jsonify({'error': 'Invalid code — check your authenticator app'}), 401
        conn.execute('UPDATE users SET totp_enabled = 1 WHERE id = ?', (current_user['id'],))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'status': 'totp enabled'})


@app.route('/api/auth/totp/disable', methods=['POST'])
@token_required
def totp_disable(current_user):
    """Disable TOTP — requires password confirmation."""
    import pyotp
    data = request.json or {}
    password = data.get('password', '')

    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user['id'],)).fetchone()
        if not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Password is incorrect'}), 401
        conn.execute('UPDATE users SET totp_enabled = 0, totp_secret = NULL WHERE id = ?', (current_user['id'],))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'status': 'totp disabled'})


@app.route('/api/support', methods=['POST'])
@token_required
def submit_support(current_user):
    """Send a support request email from the logged-in user."""
    try:
        import html
        data = request.json or {}
        subject = data.get('subject', '').strip()
        description = data.get('description', '').strip()

        if not description:
            return jsonify({'error': 'Description is required'}), 400

        # Escape user content to prevent HTML injection
        subject_escaped = html.escape(subject)
        description_escaped = html.escape(description)
        email_escaped = html.escape(current_user['email'])

        email_subject = f"[Support] {subject_escaped}" if subject else "[Support] New request"
        subject_row = (
            f'<tr><td style="padding:8px 0;color:#555;font-size:13px;">Subject</td>'
            f'<td style="padding:8px 0;font-size:14px;color:#111;">{subject_escaped}</td></tr>'
            if subject else ''
        )
        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:32px 24px;background:#fff;border-radius:12px;">
          <h2 style="color:#111;margin-bottom:4px;">Support Request</h2>
          <p style="color:#999;font-size:13px;margin-bottom:24px;">Submitted via the dashboard</p>
          <table style="width:100%;border-collapse:collapse;margin-bottom:24px;">
            <tr><td style="padding:8px 0;color:#555;font-size:13px;width:100px;">From</td><td style="padding:8px 0;font-size:14px;color:#111;">{email_escaped}</td></tr>
            <tr><td style="padding:8px 0;color:#555;font-size:13px;">User ID</td><td style="padding:8px 0;font-size:14px;color:#111;">#{current_user['id']}</td></tr>
            {subject_row}
          </table>
          <div style="background:#f9f9f9;border-radius:8px;padding:16px 20px;font-size:14px;color:#333;line-height:1.7;white-space:pre-wrap;">{description_escaped}</div>
        </div>
        """
        subject_line = f"Subject: {subject}\n" if subject else ''
        text = f"Support request from {current_user['email']} (#{current_user['id']})\n\n{subject_line}{description}"

        _send(os.getenv('MAIL_FROM'), email_subject, html_body, text)
        return jsonify({'status': 'sent'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── FAQ Routes ────────────────────────────────────────────────────────────────

@app.route('/api/faqs', methods=['GET'])
def get_faqs():
    """Get all active FAQs (public endpoint)."""
    conn = get_db()
    faqs = conn.execute(
        'SELECT id, question, answer, position FROM faqs WHERE active = 1 ORDER BY position ASC, id ASC'
    ).fetchall()
    conn.close()
    return jsonify({'faqs': [dict(f) for f in faqs]})


@app.route('/api/admin/faqs', methods=['GET'])
@admin_required
def admin_get_faqs(_admin):
    """Get all FAQs including inactive ones."""
    conn = get_db()
    faqs = conn.execute(
        'SELECT id, question, answer, position, active, created_at, updated_at FROM faqs ORDER BY position ASC, id ASC'
    ).fetchall()
    conn.close()
    return jsonify({'faqs': [dict(f) for f in faqs]})


@app.route('/api/admin/faqs', methods=['POST'])
@admin_required
def admin_create_faq(_admin):
    """Create a new FAQ."""
    data = request.json or {}
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    position = int(data.get('position', 0))
    active = 1 if data.get('active', True) else 0
    
    if not question or not answer:
        return jsonify({'error': 'Question and answer are required'}), 400
    
    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO faqs (question, answer, position, active) VALUES (?, ?, ?, ?)',
        (question, answer, position, active)
    )
    faq_id = cursor.lastrowid
    conn.commit()
    
    faq = conn.execute('SELECT * FROM faqs WHERE id = ?', (faq_id,)).fetchone()
    conn.close()
    return jsonify({'faq': dict(faq)}), 201


@app.route('/api/admin/faqs/<int:faq_id>', methods=['PATCH'])
@admin_required
def admin_update_faq(_admin, faq_id):
    """Update an existing FAQ."""
    data = request.json or {}
    conn = get_db()
    
    faq = conn.execute('SELECT id FROM faqs WHERE id = ?', (faq_id,)).fetchone()
    if not faq:
        conn.close()
        return jsonify({'error': 'FAQ not found'}), 404
    
    updates, params = [], []
    if 'question' in data:
        updates.append('question = ?')
        params.append(data['question'].strip())
    if 'answer' in data:
        updates.append('answer = ?')
        params.append(data['answer'].strip())
    if 'position' in data:
        updates.append('position = ?')
        params.append(int(data['position']))
    if 'active' in data:
        updates.append('active = ?')
        params.append(1 if data['active'] else 0)
    
    if not updates:
        conn.close()
        return jsonify({'error': 'Nothing to update'}), 400
    
    updates.append('updated_at = CURRENT_TIMESTAMP')
    params.append(faq_id)
    
    conn.execute(f'UPDATE faqs SET {", ".join(updates)} WHERE id = ?', params)
    conn.commit()
    
    updated = conn.execute('SELECT * FROM faqs WHERE id = ?', (faq_id,)).fetchone()
    conn.close()
    return jsonify({'faq': dict(updated)})


@app.route('/api/admin/faqs/<int:faq_id>', methods=['DELETE'])
@admin_required
def admin_delete_faq(_admin, faq_id):
    """Delete an FAQ."""
    conn = get_db()
    faq = conn.execute('SELECT id FROM faqs WHERE id = ?', (faq_id,)).fetchone()
    if not faq:
        conn.close()
        return jsonify({'error': 'FAQ not found'}), 404
    
    conn.execute('DELETE FROM faqs WHERE id = ?', (faq_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'FAQ deleted'})


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
    Unified lookup dispatcher.
    Routes to sickw for most services, Apple scraper for scraper-only services.
    Accepts service_id; cost is taken from the services table (in EUR).
    """
    data = request.json
    serial = data.get('serial', '').strip().upper()
    service_id = data.get('service_id')

    if not serial:
        return jsonify({'error': 'Serial number required'}), 400
    if len(serial) < 4 or len(serial) > 20:
        return jsonify({'error': 'Invalid serial number format'}), 400
    if not service_id:
        return jsonify({'error': 'service_id is required'}), 400

    # Resolve service — price is always read from DB, never trusted from client
    conn = get_db()
    service = conn.execute(
        'SELECT id, name, price FROM services WHERE id = ? AND active = 1',
        (service_id,)
    ).fetchone()
    conn.close()

    if not service:
        return jsonify({'error': 'Invalid or inactive service'}), 400

    amount_cents = round(service['price'] * 100)  # convert EUR price to cents
    
    # Validate price is non-negative (defense in depth)
    if amount_cents < 0:
        return jsonify({'error': 'Invalid service price'}), 500

    if current_user['balance_eur'] < amount_cents:
        return jsonify({'error': f'Insufficient balance. Need €{service["price"]:.3f}'}), 400

    # ── Route to the right backend ───────────────────────────────────────
    if service_id in APPLE_SCRAPER_SERVICES:
        result_text, success, err = _run_apple_scraper(serial, amount_cents)
    else:
        result_text, success, err = _run_sickw(serial, service_id)

    if not success:
        return jsonify({'success': False, 'error': err}), 404

    # Deduct balance and record atomically
    conn = get_db()
    try:
        cur = conn.execute(
            'UPDATE users SET balance_eur = balance_eur - ?, total_lookups = total_lookups + 1 '
            'WHERE id = ? AND balance_eur >= ?',
            (amount_cents, current_user['id'], amount_cents)
        )
        if cur.rowcount == 0:
            conn.rollback()
            return jsonify({'error': f'Insufficient balance. Need €{service["price"]:.3f}'}), 400
        conn.execute(
            'INSERT INTO lookups (user_id, serial, config, coins_spent, amount_eur, service_id, service_name) '
            'VALUES (?, ?, ?, 0, ?, ?, ?)',
            (current_user['id'], serial, result_text, amount_cents, service['id'], service['name'])
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        'success': True,
        'serial': serial,
        'config': result_text,
        'cached': False,
        'amount_eur': amount_cents,
        'service_id': service['id'],
        'service_name': service['name'],
    })


def _run_sickw(serial: str, service_id: int):
    """Dispatch to registered service handler, return (result_text, success, error)."""
    handler = service_registry.get(service_id)
    if not handler:
        # Fallback: call sickw directly for unregistered IDs
        result = sickw_client.check(imei=serial, service_id=service_id)
        if not result['success']:
            return None, False, result.get('error', 'Check failed')
        return result['text'] or str(result['data']), True, None

    try:
        result = handler.run(serial)
        if not result['success']:
            return None, False, result.get('error', 'Check failed')
        return result['result'], True, None
    except Exception as e:
        return None, False, str(e)


def _run_apple_scraper(serial: str, amount_cents: int):
    """Call Apple scraper and return (result_text, success, error)."""
    cached = cache.get(serial, ttl=CACHE_EXPIRY)
    if cached:
        return cached, True, None
    with cache.lock_for(serial):
        cached = cache.get(serial, ttl=CACHE_EXPIRY)
        if cached:
            return cached, True, None
        try:
            apple_scraper = get_scraper()
            result = apple_scraper.get_logic_board_config(serial)
            if not result or not result.get('success'):
                return None, False, result.get('error', 'Configuration not found')
            config = result.get('config', '')
            if not config:
                return None, False, 'Configuration text is empty'
            cache.set(serial, config)
            return config, True, None
        except Exception as e:
            return None, False, str(e)

@app.route('/api/history', methods=['GET'])
@token_required
def get_history(current_user):
    """Get user's lookup history with filtering and pagination"""
    year = request.args.get('year')
    search = request.args.get('search', '').strip().upper()
    page = max(1, int(request.args.get('page', 1)))
    per_page = 250

    conn = get_db()

    # Build query
    conditions = ['user_id = ?']
    params = [current_user['id']]

    if year:
        conditions.append("strftime('%Y', created_at) = ?")
        params.append(str(year))

    if search:
        conditions.append('(serial LIKE ? OR config LIKE ?)')
        params.extend([f'%{search}%', f'%{search}%'])

    where = ' AND '.join(conditions)

    total = conn.execute(
        f'SELECT COUNT(*) FROM lookups WHERE {where}', params
    ).fetchone()[0]

    offset = (page - 1) * per_page
    rows = conn.execute(
        f'SELECT id, serial, config, coins_spent, amount_eur, service_id, service_name, created_at FROM lookups WHERE {where} ORDER BY created_at DESC LIMIT ? OFFSET ?',
        params + [per_page, offset]
    ).fetchall()

    # Compute running balance snapshot per row
    history = []
    conn.close()

    for i, row in enumerate(rows):
        r = dict(row)
        r['ip'] = request.remote_addr or '—'
        r['service'] = 'Service 3'
        history.append(r)

    return jsonify({
        'history': history,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': max(1, (total + per_page - 1) // per_page),
        'current_balance': current_user['balance_eur'],
    })

@app.route('/api/payments/create-checkout', methods=['POST'])
@token_required
def create_checkout(current_user):
    """Create a Stripe Checkout session to top up balance."""
    data = request.json or {}
    try:
        amount_eur_float = float(data.get('amount_eur', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid amount'}), 400

    if amount_eur_float < 1.0:
        return jsonify({'error': 'Minimum top-up is €1.00'}), 400

    amount_cents = round(amount_eur_float * 100)

    try:
        session = stripe.checkout.Session.create(
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': amount_cents,
                    'product_data': {'name': 'Balance Top-up'},
                },
                'quantity': 1,
            }],
            metadata={'user_id': str(current_user['id'])},
            success_url=f"{FRONTEND_URL}/dashboard?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/dashboard?payment=cancel",
        )
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e.user_message)}), 502

    # Record pending payment
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO payments (user_id, stripe_session_id, amount_eur, status) VALUES (?, ?, ?, ?)',
            (current_user['id'], session.id, amount_cents, 'pending')
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({'checkout_url': session.url})


@app.route('/api/payments/verify-session', methods=['POST'])
@token_required
def verify_payment_session(current_user):
    """
    Called by the frontend after returning from Stripe's success URL.
    Fallback in case the webhook was delayed or missed.
    """
    data = request.json or {}
    session_id = data.get('session_id', '').strip()
    if not session_id:
        return jsonify({'error': 'session_id required'}), 400

    conn = get_db()
    try:
        payment = conn.execute(
            'SELECT * FROM payments WHERE stripe_session_id = ? AND user_id = ?',
            (session_id, current_user['id'])
        ).fetchone()

        if not payment:
            return jsonify({'error': 'Payment not found'}), 404

        if payment['status'] == 'paid':
            return jsonify({'status': 'already_credited'}), 200

        # Verify with Stripe
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.error.StripeError as e:
            return jsonify({'error': str(e.user_message)}), 502

        if session.payment_status != 'paid':
            return jsonify({'status': 'not_paid'}), 200

        payment_intent = session.payment_intent or ''
        
        # Atomic update: only credit if still pending
        updated = conn.execute(
            'UPDATE payments SET status = ?, stripe_payment_intent = ? WHERE stripe_session_id = ? AND status = ?',
            ('paid', payment_intent, session_id, 'pending')
        ).rowcount
        
        if updated == 0:
            return jsonify({'status': 'already_credited'}), 200
            
        conn.execute(
            'UPDATE users SET balance_eur = balance_eur + ? WHERE id = ?',
            (payment['amount_eur'], current_user['id'])
        )
        conn.commit()
        return jsonify({'status': 'credited', 'amount_eur': payment['amount_eur']}), 200
    finally:
        conn.close()


@app.route('/api/payments/webhook', methods=['POST'])
def stripe_webhook():
    """Stripe webhook — verifies signature and credits user balance on payment completion."""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception:
        return jsonify({'error': 'Webhook error'}), 400

    if event['type'] == 'checkout.session.completed':
        session_id = event['data']['object']['id']

        # Re-retrieve from Stripe to confirm payment status
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status != 'paid':
            return jsonify({'status': 'ignored'}), 200

        conn = get_db()
        try:
            payment = conn.execute(
                'SELECT * FROM payments WHERE stripe_session_id = ?', (session_id,)
            ).fetchone()

            if not payment or payment['status'] == 'paid':
                # Already processed or unknown — idempotent
                return jsonify({'status': 'ok'}), 200

            amount_cents = payment['amount_eur']
            user_id = payment['user_id']
            payment_intent = session.payment_intent or ''

            # Atomic update: only credit if still pending
            updated = conn.execute(
                'UPDATE payments SET status = ?, stripe_payment_intent = ? WHERE stripe_session_id = ? AND status = ?',
                ('paid', payment_intent, session_id, 'pending')
            ).rowcount
            
            if updated > 0:
                conn.execute(
                    'UPDATE users SET balance_eur = balance_eur + ? WHERE id = ?',
                    (amount_cents, user_id)
                )
            conn.commit()
        finally:
            conn.close()

    return jsonify({'status': 'ok'}), 200


@app.route('/api/payments/paypal/create-order', methods=['POST'])
@token_required
def paypal_create_order(current_user):
    """Create a PayPal order and return the approval URL."""
    data = request.json or {}
    try:
        amount_eur_float = float(data.get('amount_eur', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid amount'}), 400

    if amount_eur_float < 1.0:
        return jsonify({'error': 'Minimum top-up is €1.00'}), 400

    amount_cents = round(amount_eur_float * 100)
    amount_str = f'{amount_eur_float:.2f}'

    payment = paypalrestsdk.Payment({
        'intent': 'sale',
        'payer': {'payment_method': 'paypal'},
        'redirect_urls': {
            'return_url': f"{FRONTEND_URL}/dashboard?payment=success&provider=paypal",
            'cancel_url': f"{FRONTEND_URL}/dashboard?payment=cancel",
        },
        'transactions': [{
            'amount': {'total': amount_str, 'currency': 'EUR'},
            'description': 'Balance Top-up',
        }],
    })

    if not payment.create():
        error_msg = payment.error.get('message', 'PayPal error') if payment.error else 'PayPal error'
        return jsonify({'error': error_msg}), 502

    # Find the approval URL
    approve_url = next(
        (link.href for link in payment.links if link.rel == 'approval_url'),
        None
    )
    if not approve_url:
        return jsonify({'error': 'Could not get PayPal approval URL'}), 502

    # Store pending payment — reuse payments table, store paypal payment id in stripe_session_id column
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO payments (user_id, stripe_session_id, amount_eur, status, provider) VALUES (?, ?, ?, ?, ?)',
            (current_user['id'], payment.id, amount_cents, 'pending', 'paypal')
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({'approve_url': approve_url, 'paypal_payment_id': payment.id})


@app.route('/api/payments/paypal/capture-order', methods=['POST'])
@token_required
def paypal_capture_order(current_user):
    """
    Called by the frontend after PayPal redirects back with paymentId + PayerID.
    Executes the payment and credits the user's balance.
    """
    data = request.json or {}
    paypal_payment_id = data.get('paymentId', '').strip()
    payer_id = data.get('PayerID', '').strip()

    if not paypal_payment_id or not payer_id:
        return jsonify({'error': 'paymentId and PayerID are required'}), 400

    conn = get_db()
    try:
        # stripe_session_id column stores the paypal payment id for paypal payments
        record = conn.execute(
            'SELECT * FROM payments WHERE stripe_session_id = ? AND user_id = ? AND provider = ?',
            (paypal_payment_id, current_user['id'], 'paypal')
        ).fetchone()

        if not record:
            return jsonify({'error': 'Payment not found'}), 404

        if record['status'] == 'paid':
            return jsonify({'status': 'already_credited'}), 200

        # Execute the payment with PayPal
        payment = paypalrestsdk.Payment.find(paypal_payment_id)
        if not payment.execute({'payer_id': payer_id}):
            error_msg = payment.error.get('message', 'Execution failed') if payment.error else 'Execution failed'
            return jsonify({'error': error_msg}), 502

        amount_cents = record['amount_eur']
        
        # Atomic update: only credit if still pending
        updated = conn.execute(
            'UPDATE payments SET status = ? WHERE stripe_session_id = ? AND status = ?',
            ('paid', paypal_payment_id, 'pending')
        ).rowcount
        
        if updated == 0:
            return jsonify({'status': 'already_credited'}), 200
            
        conn.execute(
            'UPDATE users SET balance_eur = balance_eur + ? WHERE id = ?',
            (amount_cents, current_user['id'])
        )
        conn.commit()
        return jsonify({'status': 'credited', 'amount_eur': amount_cents}), 200
    finally:
        conn.close()


@app.route('/api/payments/paypal/webhook', methods=['POST'])
def paypal_webhook():
    """
    PayPal IPN / webhook listener with signature verification.
    Handles PAYMENT.SALE.COMPLETED as a fallback in case the capture endpoint was missed.
    """
    # Get the raw POST body and headers for verification
    transmission_id = request.headers.get('Paypal-Transmission-Id')
    transmission_time = request.headers.get('Paypal-Transmission-Time')
    cert_url = request.headers.get('Paypal-Cert-Url')
    auth_algo = request.headers.get('Paypal-Auth-Algo')
    transmission_sig = request.headers.get('Paypal-Transmission-Sig')
    webhook_id = os.getenv('PAYPAL_WEBHOOK_ID', '')

    if not webhook_id:
        # Fail closed if webhook verification is not configured
        return jsonify({'error': 'PayPal webhook not configured'}), 500

    # Verify the webhook signature
    try:
        webhook_event = paypalrestsdk.WebhookEvent(request.json or {})
        if not webhook_event.verify(
            transmission_id, transmission_time, webhook_id,
            request.get_data(as_text=True), cert_url, auth_algo, transmission_sig
        ):
            return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        print(f'[PayPal] Webhook verification failed: {e}')
        return jsonify({'error': 'Verification failed'}), 400

    data = request.json or {}
    event_type = data.get('event_type', '')

    if event_type != 'PAYMENT.SALE.COMPLETED':
        return jsonify({'status': 'ignored'}), 200

    resource = data.get('resource', {})
    parent_payment_id = resource.get('parent_payment', '')
    if not parent_payment_id:
        return jsonify({'status': 'ignored'}), 200

    conn = get_db()
    try:
        record = conn.execute(
            'SELECT * FROM payments WHERE stripe_session_id = ? AND provider = ? AND status = ?',
            (parent_payment_id, 'paypal', 'pending')
        ).fetchone()

        if not record:
            # Not found or already processed
            return jsonify({'status': 'ok'}), 200

        # Atomic update: only credit if still pending
        updated = conn.execute(
            'UPDATE payments SET status = ? WHERE stripe_session_id = ? AND status = ?',
            ('paid', parent_payment_id, 'pending')
        ).rowcount

        if updated > 0:
            conn.execute(
                'UPDATE users SET balance_eur = balance_eur + ? WHERE id = ?',
                (record['amount_eur'], record['user_id'])
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({'status': 'ok'}), 200


@app.route('/api/payments/history', methods=['GET'])
@token_required
def payment_history(current_user):
    """Return the current user's top-up payment history."""
    conn = get_db()
    rows = conn.execute(
        'SELECT id, amount_eur, status, created_at FROM payments '
        'WHERE user_id = ? ORDER BY created_at DESC LIMIT 100',
        (current_user['id'],)
    ).fetchall()
    conn.close()
    return jsonify({'payments': [dict(r) for r in rows]})


@app.route('/api/services', methods=['GET'])
def get_services():
    """Return all active services, optionally filtered by category or search query."""
    category = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip().upper()

    conditions = ['active = 1']
    params = []

    if category:
        conditions.append('category = ?')
        params.append(category)

    if search:
        conditions.append('(UPPER(name) LIKE ? OR CAST(id AS TEXT) LIKE ?)')
        params.extend([f'%{search}%', f'%{search}%'])

    where = ' AND '.join(conditions)
    conn = get_db()
    rows = conn.execute(
        f'SELECT id, name, category, price FROM services WHERE {where} ORDER BY category, name',
        params
    ).fetchall()
    conn.close()

    return jsonify({'services': [dict(r) for r in rows]})


@app.route('/api/admin/sync-services', methods=['POST'])
@admin_required
def admin_sync_services(_admin):
    """Manually trigger a service sync."""
    def _run():
        sync_all(verbose=True)
    threading.Thread(target=_run, daemon=True, name='manual-sync').start()
    return jsonify({'message': 'Sync started in background. Check server logs for progress.'})


@app.route('/api/admin/import-services', methods=['POST'])
@admin_required
def admin_import_services(_admin):
    """
    Bulk upsert services. Body: { "services": [{id, name, category, price}, ...] }
    Use this to update prices or add new services manually.
    """
    data = request.json or {}
    rows = data.get('services', [])

    if not rows or not isinstance(rows, list):
        return jsonify({'error': 'services array is required'}), 400

    # Validate each row
    valid = []
    for r in rows:
        if not all(k in r for k in ('id', 'name', 'category', 'price')):
            continue
        try:
            valid.append({
                'id':       int(r['id']),
                'name':     str(r['name']).strip(),
                'category': str(r['category']).strip(),
                'price':    float(r['price']),
            })
        except (ValueError, TypeError):
            continue

    if not valid:
        return jsonify({'error': 'No valid service rows found'}), 400

    result = import_services(valid)
    return jsonify({'imported': result['imported'], 'submitted': len(rows)})


@app.route('/api/admin/services-status', methods=['GET'])
@admin_required
def admin_services_status(_admin):
    """Return all services with their sync status."""
    conn = get_db()
    rows = conn.execute(
        'SELECT id, name, category, price, active, last_checked, last_status '
        'FROM services ORDER BY category, name'
    ).fetchall()
    conn.close()
    return jsonify({'services': [dict(r) for r in rows]})


# ── Admin Routes ─────────────────────────────────────────────────────────────

@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def admin_stats(_admin):
    """Dashboard stats: users, revenue, lookups, top services."""
    conn = get_db()
    total_users   = conn.execute('SELECT COUNT(*) FROM users WHERE is_admin = 0').fetchone()[0]
    total_revenue = conn.execute("SELECT COALESCE(SUM(amount_eur),0) FROM payments WHERE status='paid'").fetchone()[0]
    total_lookups = conn.execute('SELECT COALESCE(SUM(total_lookups),0) FROM users').fetchone()[0]
    today = datetime.date.today().isoformat()
    lookups_today = conn.execute(
        "SELECT COUNT(*) FROM lookups WHERE DATE(created_at)=?", (today,)
    ).fetchone()[0]
    revenue_today = conn.execute(
        "SELECT COALESCE(SUM(amount_eur),0) FROM payments WHERE status='paid' AND DATE(created_at)=?", (today,)
    ).fetchone()[0]
    new_users_today = conn.execute(
        "SELECT COUNT(*) FROM users WHERE DATE(created_at)=? AND is_admin=0", (today,)
    ).fetchone()[0]
    top_services = conn.execute(
        '''SELECT service_name, COUNT(*) as uses, COALESCE(SUM(amount_eur),0) as revenue
           FROM lookups WHERE service_name IS NOT NULL
           GROUP BY service_name ORDER BY uses DESC LIMIT 5'''
    ).fetchall()
    conn.close()
    return jsonify({
        'total_users':     total_users,
        'total_revenue':   total_revenue,
        'total_lookups':   total_lookups,
        'lookups_today':   lookups_today,
        'revenue_today':   revenue_today,
        'new_users_today': new_users_today,
        'top_services':    [dict(r) for r in top_services],
    })


@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_list_users(_admin):
    """Paginated user list with optional search."""
    search   = request.args.get('search', '').strip()
    page     = max(1, int(request.args.get('page', 1)))
    per_page = 50
    conditions, params = ['is_admin = 0'], []
    if search:
        conditions.append('(email LIKE ?)')
        params.append(f'%{search}%')
    where = ' AND '.join(conditions)
    conn = get_db()
    total = conn.execute(f'SELECT COUNT(*) FROM users WHERE {where}', params).fetchone()[0]
    rows  = conn.execute(
        f'''SELECT id, email, balance_eur, total_lookups, verified, banned, created_at
            FROM users WHERE {where} ORDER BY created_at DESC LIMIT ? OFFSET ?''',
        params + [per_page, (page - 1) * per_page]
    ).fetchall()
    conn.close()
    return jsonify({
        'users': [dict(r) for r in rows],
        'total': total, 'page': page,
        'pages': max(1, (total + per_page - 1) // per_page),
    })


@app.route('/api/admin/users/<int:user_id>', methods=['PATCH'])
@admin_required
def admin_update_user(_admin, user_id):
    """Adjust balance, toggle ban, manually verify a user."""
    data = request.json or {}
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ? AND is_admin = 0', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    updates, params = [], []

    if 'balance_eur' in data:
        try:
            updates.append('balance_eur = ?')
            params.append(int(data['balance_eur']))
        except (ValueError, TypeError):
            conn.close()
            return jsonify({'error': 'balance_eur must be an integer (cents)'}), 400

    if 'add_balance' in data:
        try:
            updates.append('balance_eur = balance_eur + ?')
            params.append(int(data['add_balance']))
        except (ValueError, TypeError):
            conn.close()
            return jsonify({'error': 'add_balance must be an integer (cents)'}), 400

    if 'banned' in data:
        updates.append('banned = ?')
        params.append(1 if data['banned'] else 0)

    if 'verified' in data:
        updates.append('verified = ?')
        params.append(1 if data['verified'] else 0)

    if not updates:
        conn.close()
        return jsonify({'error': 'Nothing to update'}), 400

    params.append(user_id)
    conn.execute(f'UPDATE users SET {", ".join(updates)} WHERE id = ?', params)
    conn.commit()
    updated = conn.execute(
        'SELECT id, email, balance_eur, total_lookups, verified, banned FROM users WHERE id = ?', (user_id,)
    ).fetchone()
    conn.close()
    return jsonify({'user': dict(updated)})


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(_admin, user_id):
    """Delete a user account and all associated data."""
    conn = get_db()
    user = conn.execute('SELECT id FROM users WHERE id = ? AND is_admin = 0', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    conn.execute('DELETE FROM lookups  WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM payments WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM users    WHERE id = ?',      (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User deleted'})


@app.route('/api/admin/services', methods=['GET'])
@admin_required
def admin_list_services(_admin):
    """All services including inactive ones."""
    conn = get_db()
    rows = conn.execute(
        'SELECT id, name, category, price, active, last_checked, last_status FROM services ORDER BY category, name'
    ).fetchall()
    conn.close()
    return jsonify({'services': [dict(r) for r in rows]})


@app.route('/api/admin/services', methods=['POST'])
@admin_required
def admin_create_service(_admin):
    """Add a new service."""
    data = request.json or {}
    try:
        svc_id   = int(data['id'])
        name     = str(data['name']).strip()
        category = str(data['category']).strip()
        price    = float(data['price'])
        if price < 0 or not float('inf') > price:
            return jsonify({'error': 'Price must be non-negative and finite'}), 400
    except (KeyError, ValueError, TypeError):
        return jsonify({'error': 'id, name, category, price are required'}), 400
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO services (id, name, category, price, active) VALUES (?, ?, ?, ?, 1)',
            (svc_id, name, category, price)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': f'Service ID {svc_id} already exists'}), 409
    conn.close()
    return jsonify({'message': 'Service created', 'id': svc_id}), 201


@app.route('/api/admin/services/<int:service_id>', methods=['PATCH'])
@admin_required
def admin_update_service(_admin, service_id):
    """Edit name, price, category, or active flag."""
    data = request.json or {}
    conn = get_db()
    svc = conn.execute('SELECT id FROM services WHERE id = ?', (service_id,)).fetchone()
    if not svc:
        conn.close()
        return jsonify({'error': 'Service not found'}), 404

    updates, params = [], []
    if 'name'     in data: updates.append('name = ?');     params.append(str(data['name']).strip())
    if 'category' in data: updates.append('category = ?'); params.append(str(data['category']).strip())
    if 'price'    in data:
        try:
            price = float(data['price'])
            if price < 0 or not float('inf') > price:
                conn.close()
                return jsonify({'error': 'Price must be non-negative and finite'}), 400
            updates.append('price = ?')
            params.append(price)
        except:
            conn.close()
            return jsonify({'error': 'Invalid price'}), 400
    if 'active'   in data: updates.append('active = ?');   params.append(1 if data['active'] else 0)

    if not updates:
        conn.close()
        return jsonify({'error': 'Nothing to update'}), 400

    params.append(service_id)
    conn.execute(f'UPDATE services SET {", ".join(updates)} WHERE id = ?', params)
    conn.commit()
    updated = conn.execute('SELECT * FROM services WHERE id = ?', (service_id,)).fetchone()
    conn.close()
    return jsonify({'service': dict(updated)})


@app.route('/api/admin/services/<int:service_id>', methods=['DELETE'])
@admin_required
def admin_delete_service(_admin, service_id):
    """Remove a service."""
    conn = get_db()
    svc = conn.execute('SELECT id FROM services WHERE id = ?', (service_id,)).fetchone()
    if not svc:
        conn.close()
        return jsonify({'error': 'Service not found'}), 404
    conn.execute('DELETE FROM services WHERE id = ?', (service_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Service deleted'})


@app.route('/api/admin/transactions', methods=['GET'])
@admin_required
def admin_transactions(_admin):
    """Unified paginated ledger: payments (top-ups) + lookups (service usage)."""
    page     = max(1, int(request.args.get('page', 1)))
    per_page = 50
    type_filter   = request.args.get('type', '')    # 'payment' | 'lookup' | ''
    status_filter = request.args.get('status', '')  # 'paid' | 'pending' | 'refunded' | ''
    search        = request.args.get('search', '').strip()

    conn = get_db()

    # Payments sub-query
    pay_conditions = ["'payment' as type"]
    pay_where, pay_params = [], []
    if status_filter and type_filter in ('', 'payment'):
        pay_where.append('p.status = ?')
        pay_params.append(status_filter)
    if search:
        pay_where.append('(u.email LIKE ?)')
        pay_params.append(f'%{search}%')

    pay_sql = f'''
        SELECT p.id, p.user_id, u.email, 'payment' as type,
               NULL as serial, NULL as service_name,
               p.amount_eur, p.status, p.provider, p.created_at,
               p.refunded_at
        FROM payments p JOIN users u ON u.id = p.user_id
        {("WHERE " + " AND ".join(pay_where)) if pay_where else ""}
    '''

    # Lookups sub-query
    lkp_where, lkp_params = [], []
    if search:
        lkp_where.append('(u.email LIKE ? OR l.serial LIKE ?)')
        lkp_params.extend([f'%{search}%', f'%{search}%'])

    lkp_sql = f'''
        SELECT l.id, l.user_id, u.email, 'lookup' as type,
               l.serial, l.service_name,
               l.amount_eur, 'completed' as status, NULL as provider,
               l.created_at, NULL as refunded_at
        FROM lookups l JOIN users u ON u.id = l.user_id
        {("WHERE " + " AND ".join(lkp_where)) if lkp_where else ""}
    '''

    if type_filter == 'payment':
        union_sql = pay_sql
        all_params = pay_params
    elif type_filter == 'lookup':
        union_sql = lkp_sql
        all_params = lkp_params
    else:
        union_sql = f'({pay_sql}) UNION ALL ({lkp_sql})'
        all_params = pay_params + lkp_params

    total = conn.execute(f'SELECT COUNT(*) FROM ({union_sql})', all_params).fetchone()[0]
    rows  = conn.execute(
        f'SELECT * FROM ({union_sql}) ORDER BY created_at DESC LIMIT ? OFFSET ?',
        all_params + [per_page, (page - 1) * per_page]
    ).fetchall()
    conn.close()
    return jsonify({
        'transactions': [dict(r) for r in rows],
        'total': total, 'page': page,
        'pages': max(1, (total + per_page - 1) // per_page),
    })


@app.route('/api/admin/transactions/refund/<int:payment_id>', methods=['POST'])
@admin_required
def admin_refund(_admin, payment_id):
    """Credit the user's balance and mark payment as refunded."""
    conn = get_db()
    payment = conn.execute(
        'SELECT * FROM payments WHERE id = ?', (payment_id,)
    ).fetchone()
    if not payment:
        conn.close()
        return jsonify({'error': 'Payment not found'}), 404
    if payment['status'] == 'refunded':
        conn.close()
        return jsonify({'error': 'Already refunded'}), 409
    if payment['status'] != 'paid':
        conn.close()
        return jsonify({'error': 'Only paid payments can be refunded'}), 400

    refunded_at = datetime.datetime.utcnow().isoformat()
    
    # Atomic update: only refund if still paid
    updated = conn.execute(
        'UPDATE payments SET status = ?, refunded_at = ? WHERE id = ? AND status = ?',
        ('refunded', refunded_at, payment_id, 'paid')
    ).rowcount
    
    if updated == 0:
        conn.close()
        return jsonify({'error': 'Already refunded'}), 409
        
    conn.execute(
        'UPDATE users SET balance_eur = balance_eur + ? WHERE id = ?',
        (payment['amount_eur'], payment['user_id'])
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Refund issued', 'amount_eur': payment['amount_eur']})


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy'})

# Ensure schema exists for WSGI servers (gunicorn) as well as direct runs
init_db()

# ── Service sync scheduler (3x per day = every 8 hours) ──────────────────────
def _start_scheduler():
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler(daemon=True)
        # Run at 06:00, 14:00, 22:00 UTC
        scheduler.add_job(sync_all, 'cron', hour='6,14,22', minute=0,
                          id='service_sync', replace_existing=True)
        scheduler.start()
        print('[Scheduler] Service sync scheduled at 06:00, 14:00, 22:00 UTC')
    except Exception as e:
        print(f'[Scheduler] Failed to start: {e}')

threading.Thread(target=_start_scheduler, daemon=True, name='scheduler-init').start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Increase timeout for long-running scraper operations
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
