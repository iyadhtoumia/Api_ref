"""
Fast Apple configuration client.

Uses Apple Self Service Repair's own JSON API instead of driving a browser:
  1. Macfax lookup  -> model_code (e.g. "MBA15M324")
  2. DeviceTypes    -> deviceModelId (cached in memory + on disk, large list)
  3. Spares/SearchByDevice?deviceModelId=..&repairTypeId=Logic Board&sn=SERIAL
     -> the logic board item whose localized name is
        "Carte logique (M3, processeur central 8 cœurs, ...)"

No reCAPTCHA is required for this path, and round-trips are sub-second.
The Macfax lookup and the Apple token/DeviceTypes warm-up run in parallel,
and DeviceTypes is persisted to a temp file so process restarts stay fast.
"""

import os
import re
import json
import time
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from macfax_client import MacfaxClient

API_BASE = 'https://selfservicerepair.com/api'
LOGIC_BOARD_TYPE = 'Logic Board'
DEVICE_TYPES_TTL = 6 * 3600
DEVICE_MODELS_FILE = os.path.join(tempfile.gettempdir(), 'apple_device_models.json')
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)

_CONFIG_RE = re.compile(r'Carte logique\s*\((.*?)\)', re.IGNORECASE)


class AppleApiError(Exception):
    pass


class AppleApiClient:
    def __init__(self, macfax_client=None, timeout=8):
        self.macfax = macfax_client or MacfaxClient()
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept-Language': 'fr-CA',
            'Content-Type': 'application/json',
            'Origin': 'https://selfservicerepair.com',
            'Referer': 'https://selfservicerepair.com/fr-CA/order',
        })
        self._lock = threading.RLock()
        self._token = None
        self._device_models = None
        self._device_models_ts = 0.0
        self._prewarm_started = False

    # ---- low level ----
    def _get_token(self, force=False):
        with self._lock:
            if self._token and not force:
                return self._token
            r = self.session.get(API_BASE + '/Orders/GetSessionToken', timeout=self.timeout)
            r.raise_for_status()
            self._token = r.json()['token']
            return self._token

    def _read_disk_cache(self):
        try:
            if not os.path.exists(DEVICE_MODELS_FILE):
                return None
            with open(DEVICE_MODELS_FILE, 'r', encoding='utf-8') as fh:
                payload = json.load(fh)
            if time.time() - payload.get('ts', 0) < DEVICE_TYPES_TTL:
                return payload.get('models')
        except Exception:
            return None
        return None

    def _write_disk_cache(self, models):
        try:
            tmp = DEVICE_MODELS_FILE + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as fh:
                json.dump({'ts': time.time(), 'models': models}, fh)
            os.replace(tmp, DEVICE_MODELS_FILE)
        except Exception:
            pass

    def _fetch_device_models(self):
        token = self._get_token()
        r = self.session.get(API_BASE + '/DeviceTypes',
                             headers={'WEBSTORE_SESSION': token}, timeout=self.timeout)
        r.raise_for_status()
        mapping = {}
        for group in r.json():
            for dm in group.get('devicemodels', []):
                code = (dm.get('modelcode') or '').upper()
                if code:
                    mapping[code] = dm
        return mapping

    def _load_device_models(self):
        with self._lock:
            if self._device_models is not None and (time.time() - self._device_models_ts) < DEVICE_TYPES_TTL:
                return self._device_models
            cached = self._read_disk_cache()
            if cached:
                self._device_models = cached
                self._device_models_ts = time.time()
                return cached
            mapping = self._fetch_device_models()
            self._device_models = mapping
            self._device_models_ts = time.time()
            self._write_disk_cache(mapping)
            return mapping

    def _find_device_model(self, model_code):
        if not model_code:
            return None
        return self._load_device_models().get(model_code.upper())

    def _search_once(self, token, device_model_id, serial):
        params = {
            'deviceModelId': device_model_id,
            'repairTypeId': LOGIC_BOARD_TYPE,
            'sn': serial,
        }
        r = self.session.get(API_BASE + '/Spares/SearchByDevice',
                             headers={'WEBSTORE_SESSION': token},
                             params=params, timeout=self.timeout)
        if r.status_code == 200:
            return r.json()
        return None

    def _search_by_device(self, device_model_id, serial, hedges=2):
        """Fire hedged requests and return the first successful result.

        Apple's search endpoint occasionally spikes to several seconds; issuing
        two parallel identical requests and taking the first response keeps the
        tail latency low.
        """
        for attempt in range(2):
            token = self._get_token(force=(attempt > 0))
            executor = ThreadPoolExecutor(max_workers=hedges)
            futures = [executor.submit(self._search_once, token, device_model_id, serial)
                       for _ in range(hedges)]
            try:
                for fut in as_completed(futures):
                    try:
                        items = fut.result()
                    except Exception:
                        items = None
                    if items is not None:
                        return items
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
        return []

    @staticmethod
    def _extract_config(items):
        for item in items or []:
            name = None
            for attr in item.get('language_specific_attributes', []):
                if attr.get('id_languages') == 'fr':
                    name = attr.get('description1') or attr.get('name')
                    break
            if not name:
                name = item.get('name')
            if not name or 'Carte logique' not in name:
                continue
            m = _CONFIG_RE.search(name)
            if m:
                return m.group(1).strip()
        return None

    def _resolve_model_code(self, serial):
        lookup = self.macfax.lookup_serial(serial)
        data = (lookup or {}).get('data') or {}
        return data.get('model_code') or ''

    def _model_code_hedged(self, serial, hedges=2):
        """Resolve model_code, taking the first of hedged Macfax lookups.

        Macfax bills one credit per distinct serial per 24h, so repeated
        lookups of the same serial are free and hedging is cost-neutral.
        """
        executor = ThreadPoolExecutor(max_workers=hedges)
        futures = [executor.submit(self._resolve_model_code, serial) for _ in range(hedges)]
        try:
            for fut in as_completed(futures):
                try:
                    code = fut.result()
                except Exception:
                    code = ''
                if code:
                    return code
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        return ''

    # ---- public ----
    def prewarm(self):
        """Warm the Apple token + DeviceTypes cache in the background (best effort)."""
        with self._lock:
            if self._prewarm_started:
                return
            self._prewarm_started = True

        def _run():
            try:
                self.macfax.get_credits()
            except Exception:
                pass
            try:
                self._load_device_models()
            except Exception:
                pass

        threading.Thread(target=_run, name='apple-api-prewarm', daemon=True).start()

    def get_config(self, serial):
        """Return {'success', 'config', 'serial'} or {'success': False, 'error'}."""
        serial = (serial or '').strip().upper()
        if not serial:
            return {'success': False, 'error': 'Serial number required'}

        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_macfax = pool.submit(self._model_code_hedged, serial)
            fut_models = pool.submit(self._load_device_models)

            try:
                model_code = fut_macfax.result()
            except Exception as e:
                return {'success': False, 'error': f'Macfax lookup failed: {e}'}

            try:
                fut_models.result()
            except Exception as e:
                return {'success': False, 'error': f'DeviceTypes lookup failed: {e}'}

        if not model_code:
            return {'success': False, 'error': 'Could not resolve model from serial'}

        dm = self._find_device_model(model_code)
        if not dm:
            return {'success': False, 'error': f'No Apple device model for code {model_code}'}

        try:
            items = self._search_by_device(dm['id'], serial)
        except Exception as e:
            return {'success': False, 'error': f'Apple search failed: {e}'}

        config = self._extract_config(items)
        if not config:
            return {'success': False, 'error': 'Configuration not found in Apple catalog'}

        return {'success': True, 'config': config, 'serial': serial}
