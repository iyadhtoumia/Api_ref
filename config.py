"""Configuration for Macfax API"""
import os
from dotenv import load_dotenv

load_dotenv('.env.dev')

class Config:
    MACFAX_API_KEY = os.getenv('MACFAX_API_KEY', None)
    MACFAX_BASE_URL = os.getenv('MACFAX_BASE_URL', 'https://macfax.com/api/v1')
    MACFAX_TIMEOUT = int(os.getenv('MACFAX_TIMEOUT', '30'))

    SICKW_API_KEY = os.getenv('SICKW_API_KEY', None)
    SICKW_BASE_URL = os.getenv('SICKW_BASE_URL', 'https://sickw.com/api.php')

    # Mail
    MAIL_FROM        = os.getenv('MAIL_FROM', 'noreply@example.com')
    MAIL_SMTP_HOST   = os.getenv('MAIL_SMTP_HOST', 'smtp.gmail.com')
    MAIL_SMTP_PORT   = int(os.getenv('MAIL_SMTP_PORT', '587'))
    MAIL_SMTP_USER   = os.getenv('MAIL_SMTP_USER', '')
    MAIL_SMTP_PASSWORD = os.getenv('MAIL_SMTP_PASSWORD', '')

    # Frontend
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

    # PayPal
    PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID', '')
    PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET', '')
    PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')  # 'sandbox' or 'live'
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.MACFAX_API_KEY and not cls.MACFAX_API_KEY.startswith('mfx_'):
            raise ValueError("Invalid API key format. Should start with 'mfx_'")
        return True
