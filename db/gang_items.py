from db import get_connection

def add_territory(gang_id, name, type, static_value=None, roll_formula=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO gang_territories (gang_id, name, type, static_value, roll_formula)
                 VALUES (?, ?, ?, ?, ?)''',
              (gang_id, name, type, static_value, roll_formula))
    conn.commit()
    conn.close()

def remove_territory(gang_id, name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM gang_territories WHERE gang_id = ? AND name = ?", (gang_id, name))
    conn.commit()
    conn.close()

def steal_territory(from_gang_id, to_gang_id, name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name, type, static_value, roll_formula FROM gang_territories WHERE gang_id = ? AND name = ?", (from_gang_id, name))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    c.execute("DELETE FROM gang_territories WHERE gang_id = ? AND name = ?", (from_gang_id, name))
    c.execute("INSERT INTO gang_territories (gang_id, name, type, static_value, roll_formula) VALUES (?, ?, ?, ?, ?)", (to_gang_id, *row))
    conn.commit()
    conn.close()
    return True

def get_territories_by_campaign(campaign_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT gt.id, gt.name, gt.type, gt.static_value, gt.roll_formula, g.gang_name
        FROM gang_territories gt
        JOIN gangs g ON g.id = gt.gang_id
        WHERE g.campaign_id = ?
    """, (campaign_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_territories_by_gang(gang_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, type, static_value, roll_formula FROM gang_territories WHERE gang_id = ?", (gang_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_asset(gang_id, type, value=None, roll_formula=None, note=None, should_sell=False, is_consumed=False):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO gang_assets (gang_id, type, value, roll_formula, note, should_sell, is_consumed)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (gang_id, type, value, roll_formula, note, int(should_sell), int(is_consumed)))
    conn.commit()
    conn.close()

def remove_asset(gang_id, asset_type):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM gang_assets WHERE gang_id = ? AND type = ?", (gang_id, asset_type))
    conn.commit()
    conn.close()

def update_asset(asset_id, should_sell):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE gang_assets SET should_sell = ? WHERE id = ? AND type = ?", (asset_id, int(should_sell)))
    conn.commit()
    conn.close()

def get_assets_by_campaign(campaign_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT ga.id, ga.type, ga.value, ga.roll_formula, ga.note, ga.should_sell, g.gang_name
        FROM gang_assets ga
        JOIN gangs g ON g.id = ga.gang_id
        WHERE g.campaign_id = ?
    """, (campaign_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_assets_by_gang(gang_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, type, value, roll_formula, note, should_sell FROM gang_assets WHERE gang_id = ?", (gang_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_hanger_on(gang_id, name, type, static_value=None, roll_formula=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO gang_hangers_on (gang_id, name, type, static_value, roll_formula)
                 VALUES (?, ?, ?, ?, ?)''',
              (gang_id, name, type, static_value, roll_formula))
    conn.commit()
    conn.close()

def remove_hanger_on(gang_id, name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM gang_hangers_on WHERE gang_id = ? AND name = ?", (gang_id, name))
    conn.commit()
    conn.close()

def get_hangers_on_by_campaign(campaign_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT h.id, h.name, h.type, h.static_value, h.roll_formula, g.gang_name
        FROM gang_hangers_on h
        JOIN gangs g ON g.id = h.gang_id
        WHERE g.campaign_id = ?
    """, (campaign_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_hangers_on_by_gang(gang_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, type, static_value, roll_formula FROM gang_hangers_on WHERE gang_id = ?", (gang_id,))
    rows = c.fetchall()
    conn.close()
    return rows