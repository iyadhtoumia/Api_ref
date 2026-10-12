"""Configuration for Macfax API"""
import os
from dotenv import load_dotenv

load_dotenv('.env.dev')

class Config:
    MACFAX_API_KEY = os.getenv('MACFAX_API_KEY', None)
    MACFAX_BASE_URL = os.getenv('MACFAX_BASE_URL', 'https://macfax.com/api/v1')
    MACFAX_TIMEOUT = int(os.getenv('MACFAX_TIMEOUT', '30'))
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.MACFAX_API_KEY and not cls.MACFAX_API_KEY.startswith('mfx_'):
            raise ValueError("Invalid API key format. Should start with 'mfx_'")
        return True
