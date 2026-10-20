"""
Creates and seeds the `services` table in users.db.
Uses real sickw service IDs so they map directly to their API.
Run once: python seed_services.py
"""

import sqlite3
import os

DATABASE = os.getenv('DATABASE', 'users.db')

# (sickw_service_id, name, category, price_eur)
SERVICES = [
    # ── Apple Check Services ──────────────────────────────────────────────
    (105, 'APPLE SOLD BY & COUNTRY INFO',              'Apple Check Services',    1.30),
    (63,  'APPLE GSX PREMIUM DETAILS',                 'Apple Check Services',    1.40),
    (146, 'APPLE GSX PREMIUM - PROMO',                 'Apple Check Services',    0.70),
    (29,  'APPLE REPLACEMENTS HISTORY',                'Apple Check Services',    0.60),
    (77,  'APPLE GSX REPAIR ELIGIBILITY',              'Apple Check Services',    0.12),
    (68,  'APPLE GSX CASES & REPAIRS',                 'Apple Check Services',    0.90),
    (60,  'APPLE iCLOUD ID HINT',                      'Apple Check Services',    0.35),
    (219, 'APPLE PART NUMBER - MPN',                   'Apple Check Services',    0.10),
    (103, 'iPHONE CARRIER',                            'Apple Check Services',    0.05),
    (78,  'iPHONE CARRIER & FMI',                      'Apple Check Services',    0.07),
    (151, 'iPHONE CARRIER & CHIMAERA DETECT',          'Apple Check Services',    0.09),
    (61,  'iPHONE CARRIER & FMI & BLACKLIST',          'Apple Check Services',    0.09),
    (147, 'iPHONE CARRIER & FMI & BLACKLIST - S2',     'Apple Check Services',    0.18),
    (72,  'APPLE CARRIER + MDM & iCLOUD & GSX STATUS', 'Apple Check Services',    0.30),
    (92,  'iPHONE MODEL COLOR & CAPACITY',             'Apple Check Services',    0.018),
    (12,  'IMEI ⇄ SN CONVERT',                        'Apple Check Services',    0.022),
    (26,  'APPLE SERIAL INFO',                         'Apple Check Services',    0.01),
    (3,   'iCLOUD ON/OFF',                             'Apple Check Services',    0.015),
    (101, 'APPLE ACTIVATION STATUS',                   'Apple Check Services',    0.03),
    (88,  'APPLE ACTIVATION STATUS - PRO',             'Apple Check Services',    0.03),
    (152, 'APPLE WARRANTY STATUS - BY SERIAL',         'Apple Check Services',    0.015),
    (85,  'APPLE DEMO DEVICES INFO',                   'Apple Check Services',    0.15),
    (81,  'APPLE MDM STATUS',                          'Apple Check Services',    0.22),
    (40,  'APPLE MDM & iCLOUD STATUS',                 'Apple Check Services',    0.20),
    (110, 'MACBOOK & iMAC iCLOUD ON/OFF STATUS',       'Apple Check Services',    0.16),
    (66,  'iPHONE & MAC iCLOUD CLEAN/LOST STATUS',     'Apple Check Services',    0.18),
    # ── Premium Tools & Services ──────────────────────────────────────────
    (94,  'MDM LOCK BYPASS (MAX IOS 26) - iPHONE/iPAD','Premium Tools & Services',14.0),
    (160, 'MDM LOCK BYPASS (IOS 27) - iPHONE/iPAD',   'Premium Tools & Services',18.5),
    (245, 'XIAOMI MI ACCOUNT REMOVE - EUROPE',         'Premium Tools & Services',14.0),
    # ── Status Check Services ─────────────────────────────────────────────
    (65,  'AT&T USA STATUS & UNLOCK',                  'Status Check Services',   0.30),
    (16,  'T-MOBILE USA STATUS - PRO',                 'Status Check Services',   0.04),
    (21,  'CRICKET USA STATUS - PRO',                  'Status Check Services',   0.12),
    (232, 'VERIZON USA STATUS - PRO',                  'Status Check Services',   0.05),
    (230, 'XFINITY USA STATUS - PRO',                  'Status Check Services',   0.06),
    (231, 'CSPIRE USA STATUS - PRO',                   'Status Check Services',   0.06),
    (220, 'TRACFONE USA STATUS - PRO',                 'Status Check Services',   0.04),
    (6,   'WW BLACKLIST STATUS - PRO',                 'Status Check Services',   0.10),
    (54,  'WW BLACKLIST STATUS',                       'Status Check Services',   0.03),
    (24,  'BRAZIL BLACKLIST STATUS',                   'Status Check Services',   0.07),
    (20,  'KOREA BLACKLIST STATUS',                    'Status Check Services',   0.015),
    (32,  'JAPAN BLACKLIST STATUS',                    'Status Check Services',   0.05),
    (31,  'AUSTRALIA BLACKLIST STATUS',                'Status Check Services',   0.01),
    # ── Generic Services ──────────────────────────────────────────────────
    (34,  'ASUS INFO',                                 'Generic Services',        0.05),
    (23,  'ACER INFO',                                 'Generic Services',        0.05),
    (73,  'HONOR INFO',                                'Generic Services',        0.06),
    (86,  'SPARX INFO',                                'Generic Services',        0.01),
    (56,  'DOOGEE INFO',                               'Generic Services',        0.04),
    (15,  'HUAWEI INFO',                               'Generic Services',        0.08),
    (22,  'LENOVO INFO',                               'Generic Services',        0.05),
    (43,  'KYOCERA INFO',                              'Generic Services',        0.04),
    (80,  'SAMSUNG INFO',                              'Generic Services',        0.05),
    (17,  'ALCATEL INFO',                              'Generic Services',        0.05),
    (13,  'MOTOROLA INFO',                             'Generic Services',        0.05),
    (75,  'VIVO | IQOO INFO',                          'Generic Services',        0.01),
    (42,  'GOOGLE PIXEL INFO',                         'Generic Services',        0.10),
    (233, 'NOTHING PHONE INFO',                        'Generic Services',        0.02),
    (1,   'SAMSUNG INFO - PRO',                        'Generic Services',        0.09),
    (203, 'BRAND & MODEL INFO',                        'Generic Services',        0.003),
    (87,  'UNITY CELLECOR INFO',                       'Generic Services',        0.01),
    (37,  'SIM ICCID | IMSI INFO',                     'Generic Services',        0.00),
    (82,  'SAMSUNG KNOX GUARD INFO',                   'Generic Services',        0.20),
    (55,  'ZTE | NUBIA | REDMAGIC INFO',               'Generic Services',        0.04),
    (45,  'ITEL | INFINIX | TECNO | SONIM INFO',       'Generic Services',        0.02),
    (153, 'XIAOMI | REDMI | POCO WARRANTY INFO',       'Generic Services',        0.07),
    (39,  'OPPO | ONEPLUS | REALME - EUROPE INFO',     'Generic Services',        0.18),
    (206, 'XIAOMI | REDMI | POCO MI LOCK ON/OFF INFO', 'Generic Services',        0.08),
    # ── iPhone Unlock Services ────────────────────────────────────────────
    (98,  'UK O2 TESCO - CLEAN',                       'iPhone Unlock Services',  2.00),
    (127, 'UK VODAFONE - CLEAN',                       'iPhone Unlock Services',  7.00),
    (111, 'USA C SPIRE - CLEAN',                       'iPhone Unlock Services',  1.50),
    (95,  'CANADA TELUS - CLEAN',                      'iPhone Unlock Services',  1.50),
    (126, 'JAPAN AU KDDI - CLEAN',                     'iPhone Unlock Services',  3.00),
    (97,  'UK EE/ORANGE - PREMIUM',                    'iPhone Unlock Services',  1.40),
    (52,  'JAPAN SOFTBANK - CLEAN',                    'iPhone Unlock Services',  2.00),
    (113, 'EMEA SERVICE - PREMIUM',                    'iPhone Unlock Services',  0.80),
    (116, 'JAPAN NTT DOCOMO - CLEAN',                  'iPhone Unlock Services',  2.00),
    (69,  'ROMANIA ORANGE - PREMIUM',                  'iPhone Unlock Services', 12.0),
    (50,  'PHILIPPINES GLOBE - CLEAN',                 'iPhone Unlock Services',  5.00),
    (71,  'ROMANIA VODAFONE - PREMIUM',                'iPhone Unlock Services', 16.0),
    (51,  'USA AT&T - CLEAN/ACTIVE LINE',              'iPhone Unlock Services',  7.00),
    (96,  'CANADA FIDO/ROGERS - PREMIUM',              'iPhone Unlock Services', 18.5),
    (137, 'AUSTRIA A1 MOBILKOM - PREMIUM',             'iPhone Unlock Services',160.0),
    (234, 'USA AT&T - SOLD DATE: 60 DAYS',             'iPhone Unlock Services', 24.0),
    (53,  'USA CRICKET - CLEAN & 6 MONTHS OLD',        'iPhone Unlock Services',  5.50),
    (138, 'AUSTRIA A1 MOBILKOM - OUT OF CONTRACT',     'iPhone Unlock Services',110.0),
    (159, 'IRELAND HUTCHISON THREE / O2 - PREMIUM',    'iPhone Unlock Services',  3.00),
    (132, 'CLARO ALL COUNTRIES - PREMIUM (iPHONE 14)', 'iPhone Unlock Services', 57.0),
    (142, 'CLARO ALL COUNTRIES - PREMIUM (iPHONE 15)', 'iPhone Unlock Services', 87.0),
    (135, 'CLARO ALL COUNTRIES - PREMIUM (UP TO iPHONE 13)', 'iPhone Unlock Services', 45.0),
    # ── Generic Unlock Services ───────────────────────────────────────────
    (57,  'UK O2 - CLEAN',                             'Generic Unlock Services',  7.20),
    (107, 'FRANCE BOUYGUES',                           'Generic Unlock Services',  1.00),
    (104, 'CANADA VIDEOTRON',                          'Generic Unlock Services',  0.75),
    (115, 'HTC INTERNATIONAL',                         'Generic Unlock Services',  1.80),
    (125, 'SAMSUNG EUROPE - PREMIUM',                  'Generic Unlock Services', 17.0),
    (134, 'SAMSUNG UK & IRELAND - PREMIUM',            'Generic Unlock Services', 17.0),
    (130, 'SAMSUNG EUROPE - LIMITED COUNTRIES',        'Generic Unlock Services', 13.5),
]


def seed():
    conn = sqlite3.connect(DATABASE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id       INTEGER PRIMARY KEY,
            name     TEXT    NOT NULL,
            category TEXT    NOT NULL,
            price    REAL    NOT NULL,
            active   INTEGER NOT NULL DEFAULT 1,
            last_checked TIMESTAMP,
            last_status  TEXT DEFAULT 'unknown'
        )
    ''')
    # Add new columns to existing table if needed
    for col, definition in [
        ('last_checked', 'TIMESTAMP'),
        ('last_status',  "TEXT DEFAULT 'unknown'"),
    ]:
        try:
            conn.execute(f'ALTER TABLE services ADD COLUMN {col} {definition}')
        except Exception:
            pass

    conn.executemany(
        '''INSERT OR REPLACE INTO services (id, name, category, price, active)
           VALUES (?, ?, ?, ?, 1)''',
        SERVICES
    )
    conn.commit()
    count = conn.execute('SELECT COUNT(*) FROM services').fetchone()[0]
    conn.close()
    print(f'Done — {count} services seeded with real sickw IDs.')


if __name__ == '__main__':
    seed()
