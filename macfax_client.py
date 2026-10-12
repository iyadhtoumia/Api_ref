"""
Macfax API Client
Production-ready wrapper for Macfax API
"""

import requests
import time
from typing import Optional, Dict, Any, List
from config import Config

class MacfaxAPIError(Exception):
    """Base exception for Macfax API errors"""
    pass

class RateLimitError(MacfaxAPIError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after

class CreditsExhaustedError(MacfaxAPIError):
    """Raised when API credits are exhausted"""
    pass

class MacfaxClient:
    """Production-ready Macfax API client"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or Config.MACFAX_API_KEY
        self.base_url = base_url or Config.MACFAX_BASE_URL
        self.timeout = Config.MACFAX_TIMEOUT
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
    
    def _request(self, endpoint: str, params: Optional[Dict] = None, method: str = 'GET') -> Dict[Any, Any]:
        """Make API request with error handling and retry logic"""
        url = f"{self.base_url}/{endpoint}"
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if method == 'GET':
                    response = self.session.get(url, params=params, timeout=self.timeout)
                elif method == 'POST':
                    response = self.session.post(url, json=params, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    if retry_count < max_retries - 1:
                        time.sleep(retry_after)
                        retry_count += 1
                        continue
                    raise RateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after} seconds",
                        retry_after
                    )
                
                # Handle credits exhausted
                if response.status_code == 402:
                    raise CreditsExhaustedError("API credits exhausted. Please top up.")
                
                # Handle invalid input
                if response.status_code == 400:
                    error_data = response.json()
                    return {
                        'success': False,
                        'error': error_data.get('error', 'Invalid input'),
                        'data': None
                    }
                
                response.raise_for_status()
                result = response.json()
                
                return {
                    'success': True,
                    'data': result.get('data'),
                    'meta': result.get('meta'),
                    'headers': dict(response.headers)
                }
                
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count >= max_retries:
                    raise MacfaxAPIError(f"Request timeout after {max_retries} retries")
                time.sleep(2 ** retry_count)
                
            except requests.exceptions.RequestException as e:
                raise MacfaxAPIError(f"Request failed: {str(e)}")
        
        raise MacfaxAPIError("Max retries exceeded")
    
    def lookup_serial(self, serial: str, context: Optional[str] = None, run_id: Optional[str] = None) -> Dict:
        """Look up device by serial number"""
        params = {'serial': serial}
        if context:
            params['context'] = context
        if run_id:
            params['run_id'] = run_id
        
        return self._request('lookup', params)
    
    def get_price_stats(self, config: str) -> Dict:
        """Get price statistics for a configuration"""
        return self._request('price-stats', {'config': config})
    
    def get_market_value(self, model: str) -> Dict:
        """Get market value by model name"""
        return self._request('market', {'model': model})
    
    def get_listings(self, config: str, max_price: Optional[int] = None, 
                     sort: str = 'price_asc', limit: Optional[int] = None) -> Dict:
        """Get live listings for a configuration"""
        params = {'config': config, 'sort': sort}
        if max_price:
            params['max_price_usd'] = max_price
        if limit:
            params['limit'] = limit
        
        return self._request('listings', params)
    
    def check_listing(self, url: str) -> Dict:
        """Check trust score for a specific listing"""
        return self._request('check-listing', {'url': url})
    
    def get_report(self, report_id: str) -> Dict:
        """Get a verified Macfax report"""
        return self._request(f'reports/{report_id}')
    
    def get_config_data(self, config: str) -> Dict:
        """Get configuration page data"""
        return self._request(f'configs/{config}')
    
    def create_alert(self, config: str, email: str, max_price: Optional[int] = None) -> Dict:
        """Create a standing alert for new listings"""
        params = {'config': config, 'email': email}
        if max_price:
            params['max_price_usd'] = max_price
        
        return self._request('alerts', params, method='POST')
    
    def get_api_key(self) -> Dict:
        """Request a new API key"""
        return self._request('keys', method='POST')
    
    def get_credits(self) -> Dict:
        """Check API credit balance and pricing"""
        return self._request('credits')
    
    def bulk_lookup(self, serials: List[str], context: str = 'inventory', 
                    run_id: Optional[str] = None) -> List[Dict]:
        """Perform bulk serial lookups with rate limiting"""
        import uuid
        if not run_id:
            run_id = str(uuid.uuid4())
        
        results = []
        for serial in serials:
            try:
                result = self.lookup_serial(serial, context=context, run_id=run_id)
                results.append({
                    'serial': serial,
                    'result': result
                })
            except RateLimitError as e:
                print(f"Rate limit hit. Waiting {e.retry_after} seconds...")
                time.sleep(e.retry_after)
                result = self.lookup_serial(serial, context=context, run_id=run_id)
                results.append({
                    'serial': serial,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'serial': serial,
                    'error': str(e)
                })
        
        return results
