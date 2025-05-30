from db import get_connection
import json
from datetime import datetime

def save_market_data(campaign_id, trading_post, secret_stash):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO campaign_market (campaign_id, generated_at, trading_post, secret_stash)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(campaign_id) DO UPDATE SET
            generated_at=excluded.generated_at,
            trading_post=excluded.trading_post,
            secret_stash=excluded.secret_stash
    """, (
        campaign_id,
        datetime.utcnow().isoformat(),
        json.dumps(trading_post),
        json.dumps(secret_stash)
    ))
    conn.commit()
    conn.close()

def get_market_data(campaign_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT trading_post, secret_stash, generated_at FROM campaign_market WHERE campaign_id = ?", (campaign_id,))
    row = c.fetchone()
    conn.close()
    if row:
        trading_post, secret_stash, generated_at = row
        return json.loads(trading_post), json.loads(secret_stash), generated_at
    return None, None, None

def create_trade_offer(campaign_id, from_gang_id, to_gang_id, offered_assets, offered_credits, requested_assets, requested_credits):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO trade_offers (campaign_id, from_gang_id, to_gang_id, offered_assets, offered_credits, requested_assets, requested_credits, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (campaign_id, from_gang_id, to_gang_id, offered_assets, offered_credits, requested_assets, requested_credits))
    offer_id = c.lastrowid
    conn.commit()
    conn.close()
    return offer_id


def get_trade_offer(offer_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM trade_offers WHERE id = ?", (offer_id,))
    row = c.fetchone()
    conn.close()
    if row:
        keys = [desc[0] for desc in c.description]
        return dict(zip(keys, row))
    return None


def accept_trade_offer(offer_id):
    offer = get_trade_offer(offer_id)
    if not offer:
        return False, "Trade offer not found."
    if offer['status'] != 'pending':
        return False, "Trade offer has already been resolved."

    conn = get_connection()
    c = conn.cursor()

    # Transfer assets
    for asset_name in offer['offered_assets'].split(','):
        c.execute("UPDATE gang_assets SET gang_id = ? WHERE gang_id = ? AND asset_type = ?", (offer['to_gang_id'], offer['from_gang_id'], asset_name.strip()))
    for asset_name in offer['requested_assets'].split(','):
        c.execute("UPDATE gang_assets SET gang_id = ? WHERE gang_id = ? AND asset_type = ?", (offer['from_gang_id'], offer['to_gang_id'], asset_name.strip()))

    # Transfer credits
    if offer['credits']:
        c.execute("UPDATE gangs SET credits = credits - ? WHERE id = ?", (offer['credits'], offer['from_gang_id']))
        c.execute("UPDATE gangs SET credits = credits + ? WHERE id = ?", (offer['credits'], offer['to_gang_id']))

    c.execute("UPDATE trade_offers SET status = 'accepted' WHERE id = ?", (offer_id,))
    conn.commit()
    conn.close()
    return True, f"Trade offer #{offer_id} accepted."


def get_trade_offers_by_campaign(campaign_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM trade_offers WHERE campaign_id = ?", (campaign_id,))
    rows = c.fetchall()
    keys = [desc[0] for desc in c.description]
    conn.close()
    return [dict(zip(keys, row)) for row in rows]
