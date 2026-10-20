"""
Telegram Bot — mirrors the website exactly.
Users are linked to DB accounts by telegram_id.
Supports all services, balance checks, top-up links, and lookup history.
"""

import os
import logging
import sqlite3
import stripe
import threading
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)
from sickw_client import SickwClient
from apple_scraper import AppleScraper
from cache import cache
import services as service_registry

APPLE_SCRAPER_SERVICES = {999}
scraper = None
scraper_lock = threading.Lock()

def get_scraper():
    global scraper
    if scraper is None:
        with scraper_lock:
            if scraper is None:
                scraper = AppleScraper(headless=True, max_browsers=2)
    return scraper

load_dotenv('.env.dev')

stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')
DATABASE = os.getenv('DATABASE', 'users.db')
CACHE_EXPIRY = 3600

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

sickw_client = SickwClient()

# Conversation states
AWAITING_SERIAL = 1

# ── Database helpers ──────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    return conn


def _ensure_telegram_column():
    """Add telegram_id column to users table if it doesn't exist yet."""
    conn = get_db()
    try:
        conn.execute('ALTER TABLE users ADD COLUMN telegram_id INTEGER')
        conn.commit()
    except Exception:
        pass  # already exists
    finally:
        conn.close()


def get_or_create_user(telegram_id: int, username: str | None) -> dict:
    """Return DB user linked to this Telegram ID, creating one if needed."""
    conn = get_db()
    try:
        user = conn.execute(
            'SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)
        ).fetchone()
        if user:
            return dict(user)

        # Create a new account — no password, linked by telegram_id only
        email = f"tg_{telegram_id}@telegram.local"
        conn.execute(
            'INSERT OR IGNORE INTO users (email, password_hash, balance_eur, verified, telegram_id) '
            'VALUES (?, ?, 0, 1, ?)',
            (email, '', telegram_id)
        )
        conn.commit()
        user = conn.execute(
            'SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)
        ).fetchone()
        return dict(user)
    finally:
        conn.close()


def get_services_by_category() -> dict[str, list[dict]]:
    """Return all active services grouped by category."""
    conn = get_db()
    rows = conn.execute(
        'SELECT id, name, category, price FROM services WHERE active = 1 ORDER BY category, name'
    ).fetchall()
    conn.close()
    grouped: dict[str, list[dict]] = {}
    for r in rows:
        grouped.setdefault(r['category'], []).append(dict(r))
    return grouped


def get_service(service_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute(
        'SELECT id, name, category, price FROM services WHERE id = ? AND active = 1',
        (service_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def deduct_and_record(user_id: int, serial: str, result: str,
                      amount_cents: int, service: dict) -> bool:
    """Atomically deduct balance and record lookup. Returns False if insufficient."""
    conn = get_db()
    try:
        cur = conn.execute(
            'UPDATE users SET balance_eur = balance_eur - ?, total_lookups = total_lookups + 1 '
            'WHERE id = ? AND balance_eur >= ?',
            (amount_cents, user_id, amount_cents)
        )
        if cur.rowcount == 0:
            return False
        conn.execute(
            'INSERT INTO lookups (user_id, serial, config, coins_spent, amount_eur, service_id, service_name) '
            'VALUES (?, ?, ?, 0, ?, ?, ?)',
            (user_id, serial, result, amount_cents, service['id'], service['name'])
        )
        conn.commit()
        return True
    finally:
        conn.close()


# ── Keyboards ─────────────────────────────────────────────────────────────────

def category_keyboard(grouped: dict) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(cat, callback_data=f"cat:{cat}")]
        for cat in grouped
    ]
    return InlineKeyboardMarkup(buttons)


def services_keyboard(services: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for svc in services:
        label = f"{svc['name']}  —  €{svc['price']:.3f}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"svc:{svc['id']}")])
    buttons.append([InlineKeyboardButton("« Back to categories", callback_data="cat:__back__")])
    return InlineKeyboardMarkup(buttons)


# ── Command handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    user = get_or_create_user(tg.id, tg.username)
    balance = user['balance_eur'] / 100
    linked = bool(user.get('telegram_id') and not user['email'].endswith('@telegram.local'))
    link_hint = "" if linked else "\n💡 Have a website account? /link <token> to share your balance."
    await update.message.reply_text(
        f"👋 Welcome{' back' if user['total_lookups'] else ''}, {tg.first_name}!\n\n"
        f"💶 Balance: €{balance:.2f}\n\n"
        "Commands:\n"
        "/services — browse & run a service\n"
        "/balance  — check your balance\n"
        "/topup    — add funds\n"
        "/history  — recent lookups\n"
        "/link     — connect your website account\n"
        "/cancel   — cancel current operation"
        f"{link_hint}"
    )


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_or_create_user(update.effective_user.id, update.effective_user.username)
    balance = user['balance_eur'] / 100
    await update.message.reply_text(f"💶 Your balance: €{balance:.2f}")


async def cmd_topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_or_create_user(update.effective_user.id, update.effective_user.username)

    # Create a Stripe Checkout session for €10 default
    amount_cents = 1000  # €10
    try:
        session = stripe.checkout.Session.create(
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': amount_cents,
                    'product_data': {'name': 'Balance Top-up (Telegram)'},
                },
                'quantity': 1,
            }],
            metadata={
                'user_id': str(user['id']),
                'source': 'telegram',
            },
            success_url=f"{FRONTEND_URL}/dashboard?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/dashboard?payment=cancel",
        )
        # Record pending payment
        conn = get_db()
        try:
            conn.execute(
                'INSERT OR IGNORE INTO payments (user_id, stripe_session_id, amount_eur, status) '
                'VALUES (?, ?, ?, ?)',
                (user['id'], session.id, amount_cents, 'pending')
            )
            conn.commit()
        finally:
            conn.close()

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("💳 Pay €10.00", url=session.url)
        ]])
        await update.message.reply_text(
            "Click below to top up €10.00 via Stripe.\n"
            "Your balance will be credited automatically once the payment completes.",
            reply_markup=keyboard
        )
    except stripe.error.StripeError as e:
        await update.message.reply_text(f"❌ Payment link failed: {e.user_message}")


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_or_create_user(update.effective_user.id, update.effective_user.username)
    conn = get_db()
    rows = conn.execute(
        'SELECT serial, service_name, config, amount_eur, created_at '
        'FROM lookups WHERE user_id = ? ORDER BY created_at DESC LIMIT 10',
        (user['id'],)
    ).fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No lookups yet.")
        return

    lines = ["📋 Last 10 lookups:\n"]
    for r in rows:
        cost = r['amount_eur'] / 100
        lines.append(
            f"• {r['serial']}  [{r['service_name']}]\n"
            f"  {r['config'][:120]}{'…' if len(r['config']) > 120 else ''}\n"
            f"  Cost €{cost:.3f}  —  {r['created_at'][:16]}\n"
        )
    await update.message.reply_text("\n".join(lines))


# ── Service selection conversation ────────────────────────────────────────────

async def cmd_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grouped = get_services_by_category()
    if not grouped:
        await update.message.reply_text("No services available right now.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Select a category:",
        reply_markup=category_keyboard(grouped)
    )
    return AWAITING_SERIAL


async def cb_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cat = query.data.split(":", 1)[1]
    if cat == "__back__":
        grouped = get_services_by_category()
        await query.edit_message_text(
            "Select a category:",
            reply_markup=category_keyboard(grouped)
        )
        return AWAITING_SERIAL

    grouped = get_services_by_category()
    services = grouped.get(cat, [])
    if not services:
        await query.edit_message_text("No services in this category.")
        return ConversationHandler.END

    context.user_data['category'] = cat
    await query.edit_message_text(
        f"📂 {cat}\n\nPick a service:",
        reply_markup=services_keyboard(services)
    )
    return AWAITING_SERIAL


async def cb_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    service_id = int(query.data.split(":", 1)[1])
    service = get_service(service_id)
    if not service:
        await query.edit_message_text("Service not found or inactive.")
        return ConversationHandler.END

    context.user_data['selected_service'] = service
    await query.edit_message_text(
        f"✅ Selected: {service['name']}\n"
        f"💶 Cost: €{service['price']:.3f}\n\n"
        "Enter the IMEI or serial number:"
    )
    return AWAITING_SERIAL


async def handle_serial_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = context.user_data.get('selected_service')
    if not service:
        await update.message.reply_text("Please use /services to pick a service first.")
        return ConversationHandler.END

    serial = update.message.text.strip().upper()
    if len(serial) < 4 or len(serial) > 20:
        await update.message.reply_text("⚠️ That doesn't look like a valid IMEI/serial. Try again or /cancel.")
        return AWAITING_SERIAL

    tg = update.effective_user
    user = get_or_create_user(tg.id, tg.username)
    amount_cents = round(service['price'] * 100)

    if user['balance_eur'] < amount_cents:
        needed = service['price']
        balance = user['balance_eur'] / 100
        await update.message.reply_text(
            f"❌ Insufficient balance.\n"
            f"Need €{needed:.3f}, you have €{balance:.2f}.\n"
            f"Use /topup to add funds."
        )
        return ConversationHandler.END

    await update.message.reply_text(f"🔍 Running {service['name']} for {serial}…")

    # Run the lookup
    result_text, success, err = _run_service(serial, service['id'])

    if not success:
        await update.message.reply_text(f"❌ Lookup failed: {err}")
        return ConversationHandler.END

    credited = deduct_and_record(user['id'], serial, result_text, amount_cents, service)
    if not credited:
        await update.message.reply_text(
            f"❌ Insufficient balance.\nUse /topup to add funds."
        )
        return ConversationHandler.END

    # Refresh balance
    conn = get_db()
    updated = conn.execute('SELECT balance_eur FROM users WHERE id = ?', (user['id'],)).fetchone()
    conn.close()
    new_balance = updated['balance_eur'] / 100 if updated else (user['balance_eur'] - amount_cents) / 100

    await update.message.reply_text(
        f"✅ Result for {serial}\n"
        f"📋 Service: {service['name']}\n\n"
        f"`{result_text}`\n\n"
        f"💶 Cost: €{service['price']:.3f}  |  Balance: €{new_balance:.2f}",
        parse_mode='Markdown'
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


async def cmd_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /link <token>
    Links this Telegram account to an existing website account.
    The token is generated on the website under Account → Connect Telegram.
    """
    tg = update.effective_user

    if not context.args:
        await update.message.reply_text(
            "Usage: /link <token>\n\n"
            "Get your token from the website:\n"
            "Dashboard → Account → Connect Telegram"
        )
        return

    token = context.args[0].strip()
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/auth/telegram-claim",
            json={'token': token, 'telegram_id': tg.id},
            timeout=10
        )
        data = resp.json()
    except Exception as e:
        await update.message.reply_text(f"❌ Could not reach server: {e}")
        return

    if resp.status_code == 200:
        email = data.get('email', '')
        await update.message.reply_text(
            f"✅ Linked! This Telegram account is now connected to {email}.\n"
            "Your balance and history are shared across the website and this bot."
        )
    else:
        await update.message.reply_text(f"❌ {data.get('error', 'Link failed')}")


async def cmd_unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /unlink
    Disconnects this Telegram account from the linked website account.
    The bot account reverts to standalone (balance is kept).
    """
    tg = update.effective_user
    user = get_or_create_user(tg.id, tg.username)

    conn = get_db()
    try:
        linked = conn.execute(
            'SELECT email FROM users WHERE id = ? AND telegram_id IS NOT NULL',
            (user['id'],)
        ).fetchone()

        if not linked:
            await update.message.reply_text("No linked website account found.")
            return

        conn.execute('UPDATE users SET telegram_id = NULL WHERE id = ?', (user['id'],))
        conn.commit()
    finally:
        conn.close()

    await update.message.reply_text(
        f"✅ Unlinked from {linked['email']}.\n"
        "Your Telegram account is now standalone."
    )


# ── Lookup routing (mirrors backend_app._run_sickw) ──────────────────────────

def _run_service(serial: str, service_id: int) -> tuple[str, bool, str | None]:
    # Apple scraper services — no sickw token needed
    if service_id in APPLE_SCRAPER_SERVICES:
        cached = cache.get(serial, ttl=CACHE_EXPIRY)
        if cached:
            return cached, True, None
        with cache.lock_for(serial):
            cached = cache.get(serial, ttl=CACHE_EXPIRY)
            if cached:
                return cached, True, None
            try:
                result = get_scraper().get_logic_board_config(serial)
                if not result or not result.get('success'):
                    return '', False, result.get('error', 'Configuration not found')
                config = result.get('config', '')
                if not config:
                    return '', False, 'Configuration text is empty'
                cache.set(serial, config)
                return config, True, None
            except Exception as e:
                return '', False, str(e)

    # Registered service handler
    handler = service_registry.get(service_id)
    if handler:
        try:
            result = handler.run(serial)
            if not result['success']:
                return '', False, result.get('error', 'Check failed')
            return result['result'], True, None
        except Exception as e:
            return '', False, str(e)

    # Fallback: direct sickw call
    result = sickw_client.check(imei=serial, service_id=service_id)
    if not result['success']:
        return '', False, result.get('error', 'Check failed')
    return result['text'] or str(result['data']), True, None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return

    _ensure_telegram_column()

    app = Application.builder().token(token).build()

    # Service selection conversation
    conv = ConversationHandler(
        entry_points=[CommandHandler('services', cmd_services)],
        states={
            AWAITING_SERIAL: [
                CallbackQueryHandler(cb_category, pattern=r'^cat:'),
                CallbackQueryHandler(cb_service, pattern=r'^svc:'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_serial_input),
            ],
        },
        fallbacks=[CommandHandler('cancel', cmd_cancel)],
    )

    app.add_handler(CommandHandler('start',   cmd_start))
    app.add_handler(CommandHandler('balance', cmd_balance))
    app.add_handler(CommandHandler('topup',   cmd_topup))
    app.add_handler(CommandHandler('history', cmd_history))
    app.add_handler(CommandHandler('link',    cmd_link))
    app.add_handler(conv)

    logger.info("Bot starting…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
