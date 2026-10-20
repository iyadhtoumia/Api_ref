"""
Service Sync — Option C implementation.

What it does (3x per day):
  1. Probe every active service with a known dummy IMEI.
     - Error S01 (Service ID is Wrong)  → service no longer exists → deactivate
     - Error A01 (API key wrong)        → config issue, skip (don't touch DB)
     - Error E02 (IMEI wrong) or any result → service is alive → keep active
  2. Re-activate services that were previously deactivated if they respond again.
  3. Record last_checked timestamp and last_status on every service row.

Admin import (manual update):
  Call import_services(rows) with a list of dicts:
    [{'id': 105, 'name': '...', 'category': '...', 'price': 1.30}, ...]
  This upserts into the DB without touching active/last_checked.
"""

import sqlite3
import os
import datetime
import requests
import threading
from config import Config

DATABASE = os.getenv('DATABASE', 'users.db')

# A real-ish IMEI that won't trigger a paid check — sickw returns E02 for bad
# IMEIs which means the service exists. We never get charged for E02.
PROBE_IMEI = '000000000000000'

# Errors that mean the SERVICE ID itself is invalid (deactivate)
DEAD_SERVICE_ERRORS = {'S01', 'Error S01'}

# Error that means our API key is wrong — don't touch services
API_KEY_ERRORS = {'A01', 'Error A01'}

_sync_lock = threading.Lock()


def _get_db():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    return conn


def _probe(service_id: int) -> str:
    """
    Probe a single service. Returns status string:
      'active'       — service responded (even with IMEI error)
      'dead'         — service ID no longer valid on sickw
      'api_error'    — our API key issue, cannot determine
      'timeout'      — request timed out
      'error:<msg>'  — unexpected error
    """
    api_key = Config.SICKW_API_KEY
    if not api_key or api_key == 'YOUR-API-KEY':
        return 'api_error'

    try:
        resp = requests.get(
            Config.SICKW_BASE_URL,
            params={
                'format': 'json',
                'key': api_key,
                'imei': PROBE_IMEI,
                'service': service_id,
            },
            timeout=30,
        )
        resp.raise_for_status()

        # Try JSON first
        try:
            data = resp.json()
            error_code = str(data.get('error', '') or data.get('Error', ''))
        except ValueError:
            error_code = resp.text.strip()

        # Check for dead service
        for dead in DEAD_SERVICE_ERRORS:
            if dead in error_code:
                return 'dead'

        # Check for API key error
        for api_err in API_KEY_ERRORS:
            if api_err in error_code:
                return 'api_error'

        # Anything else (E02 = bad IMEI, actual result, etc.) = service alive
        return 'active'

    except requests.exceptions.Timeout:
        return 'timeout'
    except Exception as e:
        return f'error:{str(e)[:80]}'


def sync_all(verbose: bool = False) -> dict:
    """
    Probe all services in DB and update their status.
    Returns summary dict.
    """
    if not _sync_lock.acquire(blocking=False):
        return {'skipped': True, 'reason': 'sync already running'}

    summary = {'checked': 0, 'deactivated': 0, 'reactivated': 0,
                'api_error': 0, 'timeout': 0, 'started_at': datetime.datetime.utcnow().isoformat()}
    try:
        conn = _get_db()
        rows = conn.execute('SELECT id, name, active FROM services').fetchall()
        conn.close()

        for row in rows:
            service_id = row['id']
            was_active = bool(row['active'])
            status = _probe(service_id)
            now = datetime.datetime.utcnow().isoformat()

            if verbose:
                print(f'[Sync] Service {service_id} ({row["name"][:30]}) → {status}')

            conn = _get_db()
            if status == 'active':
                new_active = 1
                if not was_active:
                    summary['reactivated'] += 1
                    print(f'[Sync] Reactivated service {service_id}')
            elif status == 'dead':
                new_active = 0
                if was_active:
                    summary['deactivated'] += 1
                    print(f'[Sync] Deactivated service {service_id} — no longer on sickw')
            elif status == 'api_error':
                summary['api_error'] += 1
                conn.close()
                continue  # Don't touch active status when our key is the issue
            elif status == 'timeout':
                summary['timeout'] += 1
                # Keep current active state, just record the check
                new_active = 1 if was_active else 0
            else:
                new_active = 1 if was_active else 0

            conn.execute(
                'UPDATE services SET active = ?, last_checked = ?, last_status = ? WHERE id = ?',
                (new_active, now, status, service_id)
            )
            conn.commit()
            conn.close()
            summary['checked'] += 1

    except Exception as e:
        summary['error'] = str(e)
        print(f'[Sync] Fatal error: {e}')
    finally:
        _sync_lock.release()

    summary['finished_at'] = datetime.datetime.utcnow().isoformat()
    print(f'[Sync] Done — {summary}')
    return summary


def import_services(rows: list) -> dict:
    """
    Bulk upsert services from a list of dicts.
    Each dict: {id, name, category, price}
    Preserves active/last_checked/last_status.
    """
    if not rows:
        return {'imported': 0}

    conn = _get_db()
    count = 0
    for svc in rows:
        try:
            conn.execute('''
                INSERT INTO services (id, name, category, price, active)
                VALUES (:id, :name, :category, :price, 1)
                ON CONFLICT(id) DO UPDATE SET
                    name     = excluded.name,
                    category = excluded.category,
                    price    = excluded.price,
                    active   = 1
            ''', svc)
            count += 1
        except Exception as e:
            print(f'[Import] Skipped service {svc.get("id")}: {e}')
    conn.commit()
    conn.close()
    return {'imported': count}


if __name__ == '__main__':
    # Manual run: python sync_services.py
    result = sync_all(verbose=True)
    print(result)
