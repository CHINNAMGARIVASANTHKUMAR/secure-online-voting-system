import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'evoting.db'

DEFAULT_PARTIES = [
    {"party": "BJP", "candidate": "Ravi Kumar", "symbol": "🪷", "photo": "RK", "display_order": 1},
    {"party": "INC", "candidate": "Anita Reddy", "symbol": "✋", "photo": "AR", "display_order": 2},
    {"party": "TDP", "candidate": "Suresh Naidu", "symbol": "🚲", "photo": "SN", "display_order": 3},
    {"party": "YSRCP", "candidate": "Meena Das", "symbol": "🌀", "photo": "MD", "display_order": 4},
    {"party": "NOTA", "candidate": "None of the Above", "symbol": "❌", "photo": "NA", "display_order": 5},
]


def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = get_db()
    cur = con.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            unique_id TEXT PRIMARY KEY,
            aadhaar_hash TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            dob TEXT NOT NULL,
            mobile TEXT NOT NULL,
            father_name TEXT NOT NULL,
            state TEXT NOT NULL,
            district TEXT NOT NULL,
            mandal TEXT NOT NULL,
            pincode TEXT NOT NULL,
            assembly_code TEXT NOT NULL,
            village_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS otp_store (
            mobile TEXT PRIMARY KEY,
            otp TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_id TEXT NOT NULL,
            aadhaar_hash TEXT NOT NULL,
            state TEXT NOT NULL,
            district TEXT NOT NULL,
            mandal TEXT NOT NULL,
            village_name TEXT NOT NULL,
            assembly_code TEXT NOT NULL,
            party TEXT NOT NULL,
            candidate_name TEXT NOT NULL,
            voted_at TEXT NOT NULL,
            block_hash TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            block_index INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            data_json TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            current_hash TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS party_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            party TEXT NOT NULL UNIQUE,
            candidate TEXT NOT NULL,
            symbol TEXT NOT NULL,
            photo TEXT NOT NULL DEFAULT '',
            photo_path TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            display_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_id TEXT NOT NULL,
            full_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'New',
            created_at TEXT NOT NULL
        )
    ''')

    cur.execute(
        'INSERT OR IGNORE INTO app_settings (setting_key, setting_value) VALUES (?, ?)',
        ('voting_enabled', '1')
    )

    count = cur.execute('SELECT COUNT(*) AS c FROM party_config').fetchone()['c']
    if count == 0:
        for item in DEFAULT_PARTIES:
            cur.execute(
                '''INSERT INTO party_config (party, candidate, symbol, photo, is_active, display_order)
                   VALUES (?, ?, ?, ?, 1, ?)''',
                (item['party'], item['candidate'], item['symbol'], item['photo'], item['display_order'])
            )

    con.commit()
    con.close()


def get_setting(key: str, default: str | None = None) -> str | None:
    con = get_db()
    row = con.execute('SELECT setting_value FROM app_settings WHERE setting_key=?', (key,)).fetchone()
    con.close()
    if row:
        return row['setting_value']
    return default


def set_setting(key: str, value: str):
    con = get_db()
    con.execute(
        'INSERT INTO app_settings (setting_key, setting_value) VALUES (?, ?) ON CONFLICT(setting_key) DO UPDATE SET setting_value=excluded.setting_value',
        (key, value)
    )
    con.commit()
    con.close()


def is_voting_enabled() -> bool:
    return get_setting('voting_enabled', '1') == '1'


def fetch_parties(active_only: bool = False):
    con = get_db()
    if active_only:
        rows = con.execute(
            'SELECT * FROM party_config WHERE is_active=1 ORDER BY display_order ASC, party ASC'
        ).fetchall()
    else:
        rows = con.execute(
            'SELECT * FROM party_config ORDER BY display_order ASC, party ASC'
        ).fetchall()
    con.close()
    return rows


def save_party(party: str, candidate: str, symbol: str, photo: str, photo_path: str | None, is_active: int):
    con = get_db()
    row = con.execute('SELECT id, display_order FROM party_config WHERE party=?', (party,)).fetchone()
    if row:
        con.execute(
            '''UPDATE party_config
               SET candidate=?, symbol=?, photo=?, photo_path=COALESCE(?, photo_path), is_active=?
               WHERE party=?''',
            (candidate, symbol, photo, photo_path, int(is_active), party)
        )
    else:
        next_order = con.execute('SELECT COALESCE(MAX(display_order), 0) + 1 AS n FROM party_config').fetchone()['n']
        con.execute(
            '''INSERT INTO party_config (party, candidate, symbol, photo, photo_path, is_active, display_order)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (party, candidate, symbol, photo, photo_path, int(is_active), next_order)
        )
    con.commit()
    con.close()


def toggle_party_status(party_id: int):
    con = get_db()
    row = con.execute('SELECT is_active FROM party_config WHERE id=?', (party_id,)).fetchone()
    if row:
        new_value = 0 if int(row['is_active']) == 1 else 1
        con.execute('UPDATE party_config SET is_active=? WHERE id=?', (new_value, party_id))
        con.commit()
    con.close()


def save_complaint(unique_id: str, full_name: str, mobile: str, subject: str, message: str, created_at: str):
    con = get_db()
    con.execute(
        '''INSERT INTO complaints (unique_id, full_name, mobile, subject, message, created_at)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (unique_id, full_name, mobile, subject, message, created_at)
    )
    con.commit()
    con.close()


def fetch_complaints():
    con = get_db()
    rows = con.execute('SELECT * FROM complaints ORDER BY id DESC').fetchall()
    con.close()
    return rows


def update_complaint_status(complaint_id: int, status: str):
    con = get_db()
    con.execute('UPDATE complaints SET status=? WHERE id=?', (status, complaint_id))
    con.commit()
    con.close()
