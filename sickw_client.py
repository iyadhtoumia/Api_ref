"""
Sickw API Client
Handles all sickw.com service calls.

Usage:
    client = SickwClient()
    result = client.check(imei='350060424216123', service_id=105)
    # result['success'] True/False
    # result['data']    raw parsed dict from sickw
    # result['text']    formatted plain-text summary
"""

import requests
from config import Config


class SickwError(Exception):
    pass


class SickwClient:
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or Config.SICKW_API_KEY
        self.base_url = base_url or Config.SICKW_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})

    def check(self, imei: str, service_id: int) -> dict:
        """
        Run a sickw check.

        Returns:
            {
                'success': bool,
                'data':    dict | None,   # raw key/value pairs from sickw
                'text':    str,           # formatted result text
                'error':   str | None,
            }
        """
        if not self.api_key or self.api_key == 'YOUR-API-KEY':
            return {'success': False, 'data': None, 'text': '', 'error': 'Sickw API key not configured'}

        try:
            resp = self.session.get(
                self.base_url,
                params={
                    'format': 'json',
                    'key': self.api_key,
                    'imei': imei,
                    'service': service_id,
                },
                timeout=60,
            )
            resp.raise_for_status()
            raw = resp.json()
        except requests.exceptions.Timeout:
            return {'success': False, 'data': None, 'text': '', 'error': 'Request timed out'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'data': None, 'text': '', 'error': str(e)}
        except ValueError:
            return {'success': False, 'data': None, 'text': '', 'error': 'Invalid JSON response'}

        # Sickw returns {"success": true/false, "result": {...}} or {"error": "..."}
        if raw.get('error'):
            return {'success': False, 'data': None, 'text': '', 'error': raw['error']}

        if not raw.get('success', True) is False and 'result' not in raw and 'data' not in raw:
            # Some services return the data at the top level
            data = raw
        else:
            data = raw.get('result') or raw.get('data') or raw

        text = self._format(data)
        return {'success': True, 'data': data, 'text': text, 'error': None}

    @staticmethod
    def _format(data: dict) -> str:
        """Turn a sickw result dict into a readable string."""
        if not isinstance(data, dict):
            return str(data)
        lines = []
        for key, value in data.items():
            if value not in (None, '', 'N/A'):
                label = key.replace('_', ' ').title()
                lines.append(f"{label}: {value}")
        return '\n'.join(lines)
