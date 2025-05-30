import pandas as pd
from discord import app_commands, Interaction
from discord.ext import commands
from db.gangs import get_gang_by_id
from db.marketplace import save_market_data, get_market_data, create_trade_offer, get_trade_offer, accept_trade_offer, get_trade_offers_by_campaign
from cogs.autocomplete import campaign_autocomplete, gang_autocomplete, resolve_user_preferences, MissingPreferenceError

marketplace_group = app_commands.Group(name="marketplace", description="Marketplace management commands")

TRADING_POST_CSV = "./Trading Post.csv"
df = pd.read_csv(TRADING_POST_CSV, encoding='utf-8-sig')

def parse_rarity_rating(value):
    if isinstance(value, str):
        value = value.strip().upper()
        if value == "C":
            return 0
        if value[0] in ("R", "I"):
            try:
                return int(value[1:])
            except ValueError:
                return None
    return None

df_clean = df.dropna(subset=["Name", "Category", "Rarity", "Rarity Rating", "Cost"]).copy()
df_clean["Parsed Rarity"] = df_clean["Rarity Rating"].apply(parse_rarity_rating)
df_clean = df_clean.dropna(subset=["Parsed Rarity"])

def generate_market_data():
    categories = df_clean["Category"].unique()
    trading_post = []

    # Ensure at least one item per category
    for category in categories:
        items = df_clean[df_clean["Category"] == category]
        item = weighted_choice(items)
        if item is not None:
            trading_post.append(item)

    # Fill the rest to make 20 unique entries
    selected_names = {item['Name'] for item in trading_post}
    attempts = 0
    while len(trading_post) < 20 and attempts < 1000:
        item = weighted_choice(df_clean)
        attempts += 1
        if item and item['Name'] not in selected_names:
            trading_post.append(item)
            selected_names.add(item['Name'])

    if len(trading_post) < 20:
        print(f"Only generated {len(trading_post)} items after {attempts} attempts")

    # Secret Stash: 5 unique items with Rarity/Illegal >= 10
    stash_pool = df_clean[df_clean["Parsed Rarity"] >= 10]
    stash_items = []
    stash_selected = set()
    stash_attempts = 0
    while len(stash_items) < 5 and stash_attempts < 500:
        if stash_pool.empty:
            break
        item = stash_pool.sample(1).iloc[0]
        stash_attempts += 1
        if item["Name"] not in stash_selected:
            stash_items.append(item_to_dict(item))
            stash_selected.add(item["Name"])

    return trading_post, stash_items

def weighted_choice(df):
    try:
        weights = df["Parsed Rarity"].apply(lambda r: 1 / (r + 1)).tolist()
        if sum(weights) == 0:
            return None
        item = df.sample(weights=weights).iloc[0]
        return item_to_dict(item)
    except Exception as e:
        print(f"weighted_choice error: {e}")
        return None

def item_to_dict(row):
    return {
        "Name": row["Name"],
        "Category": row["Category"],
        "Rarity": row["Rarity"],
        "Rarity Rating": row["Rarity Rating"],
        "Cost": row["Cost"]
    }

class Marketplace(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@marketplace_group.command(name="generate", description="Generate the trading post and secret stash")
async def generate_market(interaction: Interaction):
    from . import generate_market_data
    try:
        campaign_id, _ = resolve_user_preferences(interaction, require_campaign=True, require_gang=False)
        trading_post, secret_stash = generate_market_data()
        save_market_data(campaign_id, trading_post, secret_stash)
        await interaction.response.send_message(f"Marketplace generated for campaign {campaign_id} with {len(trading_post)} trading items and {len(secret_stash)} secret stash items.")
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)

@marketplace_group.command(name="view", description="View the current trading post and secret stash")
async def view_market(interaction: Interaction):
    try:
        campaign_id, _ = resolve_user_preferences(interaction, require_campaign=True, require_gang=False)
        trading_post, secret_stash, generated_at = get_market_data(campaign_id)
        if trading_post is None:
            await interaction.response.send_message("No marketplace data found for this campaign.")
            return

        response = f"**Marketplace for Campaign {campaign_id}**\nGenerated at: {generated_at}\n\n**Trading Post:**\n"
        for item in trading_post:
            response += f"- {item['Name']} ({item['Category']}, Rarity {item['Rarity Rating']}) - Cost {item['Cost']}\n"

        response += "\n**Secret Stash:**\n"
        for item in secret_stash:
            response += f"- {item['Name']} ({item['Category']}, Rarity {item['Rarity Rating']}) - Cost {item['Cost']}\n"

        await interaction.response.send_message(response)
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)

@marketplace_group.command(name="trade", description="Create a trade offer")
@app_commands.describe(to_gang_id="Target Gang ID", offered_assets="Assets offered (comma-separated)", offered_credits="Credits offered", requested_assets="Assets requested (comma-separated)", requested_credits="Credits requested")
@app_commands.autocomplete(to_gang_id=gang_autocomplete)
async def make_offer(interaction: Interaction, to_gang_id: int, offered_assets: str = None, offered_credits: int = 0, requested_assets: str = None, requested_credits: int = 0):
    try:
        campaign_id, from_gang_id = resolve_user_preferences(interaction)
        offer_id = create_trade_offer(campaign_id, from_gang_id, to_gang_id, offered_assets or "", offered_credits, requested_assets or "", requested_credits)
        await interaction.response.send_message(f"Trade offer #{offer_id} created from gang {from_gang_id} to gang {to_gang_id}.")
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)

@marketplace_group.command(name="list_trades", description="List all trade offers in the current campaign")
async def list_offers(interaction: Interaction):
    try:
        campaign_id, _ = resolve_user_preferences(interaction, require_campaign=True, require_gang=False)
        offers = get_trade_offers_by_campaign(campaign_id)
        if not offers:
            await interaction.response.send_message("No trade offers available.")
            return
        message = "**Trade Offers:**\n"
        for offer in offers:
            message += f"ID {offer['id']}: Gang {offer['from_gang_id']} offers [{offer['offered_assets']}] + {offer['offered_credits']} credits to Gang {offer['to_gang_id']} for [{offer['requested_assets']}] + {offer['requested_credits']} credits — {offer['status']}\n"
        await interaction.response.send_message(message)
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)

@marketplace_group.command(name="accept_trade", description="Accept a trade offer")
@app_commands.describe(offer_id="ID of the offer to accept")
async def accept_offer_cmd(interaction: Interaction, offer_id: int):
    try:
        _, to_gang_id = resolve_user_preferences(interaction, require_campaign=False)
        user_id = str(interaction.user.id)
        owner_id = get_gang_by_id(to_gang_id)[2]
        if user_id != owner_id:
            await interaction.response.send_message("You do not own the target gang and cannot accept this trade.", ephemeral=True)
            return
        result = accept_trade_offer(offer_id)
        await interaction.response.send_message(result)
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)

def setup(bot):
    bot.add_cog(Marketplace(bot))
