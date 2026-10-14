"""
Shared SQLite cache for Apple configuration lookups.

Cross-worker: backed by the users.db file (WAL mode) so multiple gunicorn
workers/threads share cache hits instead of each re-scraping.

Single-flight: `ConfigCache.lock_for(serial)` returns a process-wide lock
per serial, so concurrent lookups of the same serial trigger one scrape.
"""

import os
import sqlite3
import threading
import time

DEFAULT_DB = 'users.db'
DEFAULT_TTL = 3600  # 1 hour


class ConfigCache:
    def __init__(self, db_path=None, ttl=DEFAULT_TTL):
        self.db_path = db_path or os.getenv('DATABASE', DEFAULT_DB)
        self.ttl = ttl
        self._ready = False
        self._init_lock = threading.Lock()
        self._locks = {}
        self._locks_guard = threading.Lock()

    # ---- plumbing ----
    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        return conn

    def _ensure_table(self):
        if self._ready:
            return
        with self._init_lock:
            if self._ready:
                return
            conn = self._conn()
            try:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS config_cache (
                        serial TEXT PRIMARY KEY,
                        config TEXT NOT NULL,
                        ts REAL NOT NULL
                    )
                ''')
                conn.commit()
            finally:
                conn.close()
            self._ready = True

    # ---- cache API ----
    def get(self, serial, ttl=None):
        """Return cached config for serial, or None if missing/expired."""
        self._ensure_table()
        ttl = self.ttl if ttl is None else ttl
        conn = self._conn()
        try:
            row = conn.execute(
                'SELECT config, ts FROM config_cache WHERE serial = ?', (serial,)
            ).fetchone()
        finally:
            conn.close()
        if not row:
            return None
        if time.time() - row['ts'] > ttl:
            self.delete(serial)
            return None
        return row['config']

    def set(self, serial, config):
        """Store config for serial (upsert)."""
        self._ensure_table()
        conn = self._conn()
        try:
            conn.execute(
                'INSERT OR REPLACE INTO config_cache (serial, config, ts) VALUES (?, ?, ?)',
                (serial, config, time.time())
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, serial):
        self._ensure_table()
        conn = self._conn()
        try:
            conn.execute('DELETE FROM config_cache WHERE serial = ?', (serial,))
            conn.commit()
        finally:
            conn.close()

    def lock_for(self, serial):
        """Return a process-wide lock for a serial (single-flight)."""
        with self._locks_guard:
            lock = self._locks.get(serial)
            if lock is None:
                lock = threading.Lock()
                self._locks[serial] = lock
            return lock


# Shared instance used across the app
cache = ConfigCache()
