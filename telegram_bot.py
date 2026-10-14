"""
Telegram Bot for Apple Configuration Lookup
Returns configuration data based on serial number reference
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from macfax_client import MacfaxClient, MacfaxAPIError
from apple_scraper import AppleScraper
from cache import cache
import time
import threading

# Load environment variables
load_dotenv('.env.dev')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize clients
macfax_client = MacfaxClient()
MAX_BROWSERS = 2
scraper = None
scraper_lock = threading.Lock()

# Shared cache TTL (1 hour)
CACHE_EXPIRY = 3600

def get_scraper():
    """Get or create the shared thread-safe scraper instance"""
    global scraper
    if scraper is None:
        with scraper_lock:
            if scraper is None:
                scraper = AppleScraper(headless=True, max_browsers=MAX_BROWSERS)
            scraper._get_api_client().prewarm()
    return scraper

async def send_config_response(update: Update, serial: str, from_cache: bool = False):
    """Helper function to send configuration response"""
    cached_config = cache.get(serial, ttl=CACHE_EXPIRY)
    if cached_config:
        response = (
            f"✅ Configuration (from cache)\n\n"
            f"🏷️ Serial: {serial}\n"
            f"🔧 Config: `{cached_config}`\n\n"
            f"⚡ Retrieved instantly from cache"
        )
        await update.message.reply_text(response, parse_mode='Markdown')
        return True

    return False

async def fetch_and_cache_config(update: Update, serial: str):
    """Fetch configuration from Apple and cache it"""
    try:
        with cache.lock_for(serial):
            cached_config = cache.get(serial, ttl=CACHE_EXPIRY)
            if cached_config:
                await send_config_response(update, serial, from_cache=True)
                return

            apple_scraper = get_scraper()
            result = apple_scraper.get_logic_board_config(serial)

            if result['success']:
                config = result['config']
                cache.set(serial, config)

                response = (
                    f"✅ Configuration Retrieved!\n\n"
                    f"🏷️ Serial: {serial}\n"
                    f"🔧 Config: `{config}`\n\n"
                            )
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ Error: {result.get('error', 'Configuration not found')}")
    except Exception as e:
        logger.error(f"Config fetch error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Welcome to Apple Configuration Lookup Bot!\n\n"
        "Send me a serial number to get device configuration.\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/help - Get help\n"
        "/lookup <serial> - Get device info\n"
        "/config <serial> - Get logic board configuration\n\n"
        "Or simply send a serial number directly!"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = (
        "📖 How to use:\n\n"
        "1️⃣ Send a serial number: C02P73J9G8WP\n"
        "2️⃣ Use /lookup command: /lookup C02P73J9G8WP\n"
        "3️⃣ Use /config command: /config C02P73J9G8WP\n\n"
        "The bot will return device information and configuration data."
    )
    await update.message.reply_text(help_text)

async def lookup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /lookup command"""
    if not context.args:
        await update.message.reply_text("❌ Please provide a serial number.\nExample: /lookup C02P73J9G8WP")
        return
    
    serial = context.args[0].strip().upper()
    await update.message.reply_text(f"🔍 Looking up serial: {serial}...")
    
    try:
        result = macfax_client.lookup_serial(serial)
        
        if result.get('success') and result.get('data'):
            data = result['data']
            model = data.get('model', 'N/A')
            device_type = data.get('device_type', 'N/A')
            response = f"'model': '{model}', 'device_type': '{device_type}'"
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(f"❌ Error: {result.get('error', 'Unknown error')}")
    except MacfaxAPIError as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    except Exception as e:
        logger.error(f"Lookup error: {e}")
        await update.message.reply_text(f"❌ Unexpected error: {str(e)}")

async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /config command"""
    if not context.args:
        await update.message.reply_text("❌ Please provide a serial number.\nExample: /config C02P73J9G8WP")
        return
    
    serial = context.args[0].strip().upper()
    
    if await send_config_response(update, serial):
        return
    
    await update.message.reply_text(f"🔍 Fetching configuration for: {serial}\n⏳ This may take 15-30 seconds...")
    await fetch_and_cache_config(update, serial)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages (treat as serial number lookup)"""
    text = update.message.text.strip().upper()
    
    if len(text) < 8 or len(text) > 20:
        await update.message.reply_text(
            "❓ That doesn't look like a valid serial number.\n"
            "Please send a valid serial number or use /help for more info."
        )
        return
    
    serial = text
    
    if await send_config_response(update, serial):
        return
    
    await update.message.reply_text(f"🔍 Processing: {serial}\n⏳ Getting configuration...")
    await fetch_and_cache_config(update, serial)

def main():
    """Start the bot"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("lookup", lookup_command))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the Bot
    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
