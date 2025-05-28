from db import get_connection

def insert_gang_asset(gang_id, name, asset_type, static_value=None, roll_formula=None, is_consumed=False, should_sell=False, note=None):
    conn = get_connection()
    sql = '''INSERT INTO gang_assets (gang_id, name, asset_type, static_value, roll_formula, is_consumed, should_sell, note)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
    cur = conn.cursor()
    cur.execute(sql, (gang_id, name, asset_type, static_value, roll_formula, is_consumed, should_sell, note))
    conn.commit()
    return cur.lastrowid

def get_gang_assets(gang_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, gang_id, name, asset_type, static_value, 
        roll_formula, is_consumed, should_sell, note 
    FROM gang_assets WHERE gang_id = ?""", (gang_id,))
    return cur.fetchall()

def update_gang_asset(asset_id, **kwargs):
    conn = get_connection()
    fields = ', '.join(f"{key} = ?" for key in kwargs)
    values = list(kwargs.values())
    values.append(asset_id)
    sql = f'UPDATE gang_assets SET {fields} WHERE id = ?'
    conn.execute(sql, values)
    conn.commit()

def delete_gang_asset(asset_id):
    conn = get_connection()
    conn.execute('DELETE FROM gang_assets WHERE id = ?', (asset_id,))
    conn.commit()

def get_gang_assets_by_campaign(campaign_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT ga.id, ga.name, ga.asset_type, ga.static_value, ga.roll_formula, g.gang_name
        FROM gang_assets ga
        JOIN gangs g ON g.id = ga.gang_id
        WHERE g.campaign_id = ?
    """, (campaign_id,))
    rows = c.fetchall()
    conn.close()
    return rows