import sqlite3

DB_FILE = 'necromunda.db'
SCHEMA_VERSION = 1

def get_connection():
    return sqlite3.connect(DB_FILE)

def get_schema_version(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    cursor = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'")
    row = cursor.fetchone()
    return int(row[0]) if row else 0

def set_schema_version(conn, version):
    conn.execute("REPLACE INTO meta (key, value) VALUES ('schema_version', ?)", (str(version),))

def init_db():
    conn = get_connection()
    version = get_schema_version(conn)

    if version < 1:
        conn.execute('''CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_by TEXT NOT NULL,
            server_id TEXT NOT NULL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS gangs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            campaign_id INTEGER NOT NULL,
            yaktribe_url TEXT NOT NULL,
            gang_name TEXT,
            gang_type TEXT,
            credits INTEGER,
            meat INTEGER,
            gang_rating INTEGER,
            reputation INTEGER,
            wealth INTEGER,
            gangers TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
        )''')
        set_schema_version(conn, 1)

    conn.commit()
    conn.close()
