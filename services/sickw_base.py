"""
Mixin for services that delegate directly to sickw.com.
Subclass this and set `service_id` — no other code needed.
"""
from services.base import BaseService
from sickw_client import SickwClient

_client = SickwClient()   # shared across all sickw services


class SickwService(BaseService):
    service_id: int = 0   # must be set in subclass

    def run(self, identifier: str) -> dict:
        result = _client.check(imei=identifier, service_id=self.service_id)
        return {
            'success': result['success'],
            'result':  result.get('text') or '',
            'raw':     result.get('data') or {},
            'error':   result.get('error'),
        }
