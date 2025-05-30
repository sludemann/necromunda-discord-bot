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
        conn.execute('''CREATE TABLE IF NOT EXISTS gang_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gang_id INTEGER NOT NULL,
            change INTEGER NOT NULL,
            reason TEXT,
            user_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (gang_id) REFERENCES gangs (id)
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS gang_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gang_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            asset_type TEXT CHECK(asset_type IN ('Territory', 'Hanger-On', 'Skill', 'Equipment', 'Captive', 'Other')) NOT NULL,
            static_value INTEGER,
            roll_formula TEXT,
            is_consumed BOOLEAN DEFAULT 0,
            should_sell BOOLEAN DEFAULT 0,
            note TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (gang_id) REFERENCES gangs (id)
        )''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS campaign_market (
                campaign_id INTEGER PRIMARY KEY,
                generated_at TEXT NOT NULL,
                trading_post TEXT NOT NULL,
                secret_stash TEXT NOT NULL,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_campaign_market_generated_at ON campaign_market (generated_at)')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trade_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_gang_id INTEGER NOT NULL,
                to_gang_id INTEGER NOT NULL,
                campaign_id INTEGER NOT NULL,
                offered_assets TEXT,
                offered_credits INTEGER DEFAULT 0,
                requested_assets TEXT,
                requested_credits INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (from_gang_id) REFERENCES gangs(id),
                FOREIGN KEY (to_gang_id) REFERENCES gangs(id),
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trade_offers_campaign_id ON trade_offers (campaign_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trade_offers_to_gang_id ON trade_offers (to_gang_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trade_offers_from_gang_id ON trade_offers (from_gang_id)')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                current_campaign_id INTEGER,
                current_gang_id INTEGER,
                FOREIGN KEY (current_campaign_id) REFERENCES campaigns(id),
                FOREIGN KEY (current_gang_id) REFERENCES gangs(id)
            )
        ''')
        set_schema_version(conn, 1)

    conn.commit()
    conn.close()
