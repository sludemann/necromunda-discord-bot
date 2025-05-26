from db import get_connection

def add_campaign(name: str, user_id: str, server_id: str) -> str:
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO campaigns (name, created_by, server_id) VALUES (?, ?, ?)', (name, user_id, server_id))
    conn.commit()
    conn.close()
    return f"Campaign '{name}' created successfully."

def delete_campaign(campaign_id: int, user_id: str, server_id: str) -> str:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT created_by FROM campaigns WHERE id = ? AND server_id = ?', (campaign_id, server_id))
    row = c.fetchone()
    if not row:
        conn.close()
        return "Campaign not found."
    if row[0] != user_id:
        conn.close()
        return "You are not authorized to delete this campaign."
    c.execute('DELETE FROM campaigns WHERE id = ?', (campaign_id,))
    conn.commit()
    conn.close()
    return f"Campaign {campaign_id} deleted successfully."

def get_all_campaigns(server_id: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, name FROM campaigns WHERE server_id = ?', (server_id,))
    campaigns = c.fetchall()
    conn.close()
    return campaigns