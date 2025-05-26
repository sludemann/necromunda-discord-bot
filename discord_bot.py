# necromunda_discord_bot.py

import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
import re
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

def init_db():
    conn = sqlite3.connect('necromunda.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_by TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS gangs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            campaign_id INTEGER NOT NULL,
            yaktribe_url TEXT NOT NULL,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
        )
    ''')
    conn.commit()
    conn.close()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands.')
    except Exception as e:
        print(f'Error syncing commands: {e}')

@bot.tree.command(name='ping', description="Test the bot")
async def ping(ctx):
    await ctx.send('Pong!')

@bot.tree.command(name='create_campaign', description="Create a campaign")
async def create_campaign(ctx, *, name: str):
    conn = sqlite3.connect('necromunda.db')
    c = conn.cursor()
    c.execute('INSERT INTO campaigns (name, created_by) VALUES (?, ?)', (name, str(ctx.author.id)))
    conn.commit()
    conn.close()
    await ctx.send(f"Campaign '{name}' created by {ctx.author.name}!")

@bot.tree.command(name="list_campaigns", description="List all campaigns")
async def list_campaigns(interaction: discord.Interaction):
    conn = sqlite3.connect('necromunda.db')
    c = conn.cursor()
    c.execute('SELECT id, name FROM campaigns')
    campaigns = c.fetchall()
    conn.close()

    if campaigns:
        response = "**Campaigns:**\n" + "\n".join([f"ID {cid}: {name}" for cid, name in campaigns])
    else:
        response = "No campaigns found."

    await interaction.response.send_message(response)

@bot.tree.command(name="register_gang", description="Register your gang to a campaign with a Yaktribe link")
async def register_gang_slash(interaction: discord.Interaction, campaign_id: int, yaktribe_url: str):
    match = re.match(r'https://yaktribe\.games/underhive/print/cards/(\d+)', yaktribe_url)
    if not match:
        await interaction.response.send_message("Invalid Yaktribe URL. Please use the correct format.", ephemeral=True)
        return

    conn = sqlite3.connect('necromunda.db')
    c = conn.cursor()
    c.execute('SELECT name FROM campaigns WHERE id = ?', (campaign_id,))
    campaign = c.fetchone()

    if not campaign:
        await interaction.response.send_message("Campaign ID not found.", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    c.execute('INSERT INTO gangs (user_id, campaign_id, yaktribe_url) VALUES (?, ?, ?)',
              (user_id, campaign_id, yaktribe_url))
    conn.commit()
    conn.close()

    await interaction.response.send_message(f"Gang registered to campaign '{campaign[0]}' for {interaction.user.name}.")

@bot.tree.command(name="list_gangs", description="List all gangs in a campaign")
async def list_gangs(interaction: discord.Interaction, campaign_id: int):
    conn = sqlite3.connect('necromunda.db')
    c = conn.cursor()
    c.execute('SELECT yaktribe_url, user_id FROM gangs WHERE campaign_id = ?', (campaign_id,))
    gangs = c.fetchall()
    conn.close()

    if gangs:
        response = f"**Gangs in Campaign {campaign_id}:**\n" + "\n".join([
            f"User ID {user_id}: {url}" for url, user_id in gangs
        ])
    else:
        response = f"No gangs found for Campaign ID {campaign_id}."

    await interaction.response.send_message(response)

if __name__ == '__main__':
    init_db()
    bot.run(TOKEN)