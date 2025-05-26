from db import get_connection

def log_transaction(gang_id: int, change: int, reason: str, user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO gang_transactions (gang_id, change, reason, user_id) VALUES (?, ?, ?, ?)", (gang_id, change, reason, user_id))
    conn.commit()
    conn.close()

def get_current_credits(gang_id: int) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(change) FROM gang_transactions WHERE gang_id = ?", (gang_id,))
    total = c.fetchone()[0]
    conn.close()
    return total if total is not None else 0

def get_transaction_history(gang_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT change, reason, timestamp FROM gang_transactions WHERE gang_id = ? ORDER BY timestamp DESC", (gang_id,))
    history = c.fetchall()
    conn.close()
    return history