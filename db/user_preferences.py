from db import get_connection

def set_user_preferences(user_id, campaign_id=None, gang_id=None):
    conn = get_connection()
    with conn:
        if campaign_id is not None and gang_id is not None:
            conn.execute('''
                INSERT INTO user_preferences (user_id, current_campaign_id, current_gang_id)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    current_campaign_id=excluded.current_campaign_id,
                    current_gang_id=excluded.current_gang_id
            ''', (user_id, campaign_id, gang_id))
        elif campaign_id is not None:
            conn.execute('''
                INSERT INTO user_preferences (user_id, current_campaign_id)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    current_campaign_id=excluded.current_campaign_id
            ''', (user_id, campaign_id))
        elif gang_id is not None:
            conn.execute('''
                INSERT INTO user_preferences (user_id, current_gang_id)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    current_gang_id=excluded.current_gang_id
            ''', (user_id, gang_id))

def get_user_preferences(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT current_campaign_id, current_gang_id
        FROM user_preferences WHERE user_id = ?
    ''', (user_id,))
    return cur.fetchone()