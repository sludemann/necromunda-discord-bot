from bs4 import BeautifulSoup
import re
import requests
import json
from db import get_connection

def parse_gang_page(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Gang name
    name_tag = soup.select_one("tr.subheader td[colspan='2']")
    name = name_tag.get_text(strip=True) if name_tag else "Unknown"

    # Gang info table
    gang_info = {}
    for row in soup.select("table")[1].select("tr")[1:]:
        if row.th and row.td:
            label = row.th.get_text(strip=True).rstrip(":")
            value = row.td.get_text(strip=True)
            gang_info[label] = value

    gang_type = gang_info.get("Gang Type", "Unknown")
    credits = int(gang_info.get("Credits", "0"))
    meat = int(gang_info.get("Meat", "0"))
    rating = int(gang_info.get("Gang Rating", "0"))
    rep = int(gang_info.get("Reputation", "0"))
    wealth = int(gang_info.get("Wealth", "0"))

    # Gangers
    gangers = []
    for fighter_row in soup.select("table")[5].select("tr")[1:]:
        name_cell = fighter_row.select_one("td:nth-of-type(2)")
        if name_cell:
            name_parts = name_cell.decode_contents().split("<br>")
            fighter_name = name_parts[0].strip()
            gangers.append(fighter_name)

    return {
        "name": name,
        "type": gang_type,
        "credits": credits,
        "meat": meat,
        "rating": rating,
        "rep": rep,
        "wealth": wealth,
        "gangers": gangers
    }

def add_gang(user_id: str, campaign_id: int, yaktribe_url: str) -> str:
    match = re.match(r'https://yaktribe\.games/underhive/print/gang/(\d+)\?.*', yaktribe_url)
    if not match:
        return "Invalid Yaktribe URL. Please use the correct format."

    try:
        html = requests.get(yaktribe_url).text
        data = parse_gang_page(html)
    except Exception as e:
        return f"Failed to fetch or parse Yaktribe data: {e}"

    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT name FROM campaigns WHERE id = ?', (campaign_id,))
    campaign = c.fetchone()

    if not campaign:
        return "Campaign ID not found."

    c.execute('''
        INSERT INTO gangs (user_id, campaign_id, yaktribe_url, gang_name, gang_type, credits, meat, gang_rating, reputation, wealth, gangers)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, campaign_id, yaktribe_url,
        data['name'], data['type'], data['credits'],
        data['meat'], data['rating'], data['rep'],
        data['wealth'], json.dumps(data['gangers'])
    ))
    conn.commit()
    conn.close()

    return f"Gang '{data['name']}' registered to campaign '{campaign[0]}' successfully."

def delete_gang(gang_id: int, user_id: str) -> str:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT user_id FROM gangs WHERE id = ?', (gang_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return "Gang not found."
    if row[0] != user_id:
        conn.close()
        return "You are not authorized to delete this gang."
    c.execute('DELETE FROM gangs WHERE id = ?', (gang_id,))
    conn.commit()
    conn.close()
    return f"Gang {gang_id} deleted successfully."

def get_gang_by_id(gang_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, yaktribe_url, user_id, gang_name, gang_type FROM gangs WHERE id = ?', (gang_id,))
    gangs = c.fetchall()
    conn.close()
    return gangs

def get_gangs_by_campaign(campaign_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, yaktribe_url, user_id, gang_name, gang_type FROM gangs WHERE campaign_id = ?', (campaign_id,))
    gangs = c.fetchall()
    conn.close()
    return gangs
  
def get_gangs_by_user(user_id: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT g.id, g.campaign_id, c.name, g.gang_name, g.gang_type, g.credits, g.meat, g.gang_rating
        FROM gangs g
        JOIN campaigns c ON g.campaign_id = c.id
        WHERE g.user_id = ?
    ''', (user_id,))
    gangs = c.fetchall()
    conn.close()
    return gangs

