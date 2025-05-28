import discord
from discord import app_commands, Interaction
from discord.ext import commands
from db.gang_assets import insert_gang_asset, get_gang_assets_by_campaign, get_gang_assets, delete_gang_asset, update_gang_asset
from cogs.autocomplete import campaign_autocomplete, gang_autocomplete, asset_autocomplete, asset_type_autocomplete

asset_group = app_commands.Group(name="asset", description="Gang Asset related commands")

ASSET_COLORS = {
    "Territory": 0x3b9dff,
    "Hanger-On": 0x6a0dad,
    "Skill": 0x32cd32,
    "Equipment": 0xffa500,
    "Captive": 0xdc143c,
    "Other": 0x808080
}

ASSET_ICONS = {
    "Territory": "🏞️",
    "Hanger-On": "🧑‍🤝‍🧑",
    "Skill": "📘",
    "Equipment": "🔧",
    "Captive": "🪤",
    "Other": "🎲"
}

class Assets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@asset_group.command(name="add", description="Add an asset to a gang")
@app_commands.describe(campaign_id="ID of the campaign", gang_id="ID of the gang", asset_type="Type of asset", value="Credit value", roll_formula="Dice formula", note="Additional note", should_sell="Mark as to be sold on next payday", is_consumed="Mark as consumed")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete, asset_type=asset_type_autocomplete)
async def add_asset_command(interaction: Interaction, campaign_id: int, gang_id: int, asset_type: str, name: str, value: int = None, roll_formula: str = None, note: str = None, should_sell: bool = False, is_consumed: bool = False):
    insert_gang_asset(gang_id, name, asset_type, value, roll_formula, is_consumed, should_sell, note)
    await interaction.response.send_message(f"Asset '{asset_type}' added to gang {gang_id}.")

@asset_group.command(name="remove", description="Remove an asset from a gang")
@app_commands.describe(campaign_id="ID of the campaign", gang_id="ID of the gang", asset_id="ID of the asset")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete, asset_id=asset_autocomplete)
async def remove_asset_command(interaction: Interaction, campaign_id: int, gang_id: int, asset_id: int):
    delete_gang_asset(asset_id)
    await interaction.response.send_message(f"Asset ID '{asset_id}' removed from gang {gang_id}.")

@asset_group.command(name="sell", description="Mark an asset as to be sold in the next Pay Day")
@app_commands.describe(campaign_id="ID of the campaign", gang_id="ID of the gang", asset_id="ID of the asset")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete, asset_id=asset_autocomplete)
async def sell_asset_command(interaction: Interaction, campaign_id: int, gang_id: int, asset_id: int):
    update_gang_asset(asset_id, should_sell=True)
    await interaction.response.send_message(f"Asset ID '{asset_id}' marked for sale in the next Pay Day.")

@asset_group.command(name="list_by_campaign", description="List all assets by campaign")
@app_commands.autocomplete(campaign_id=campaign_autocomplete)
async def list_assets_by_campaign(interaction: Interaction, campaign_id: int):
    rows = get_gang_assets_by_campaign(campaign_id)
    embed = discord.Embed(title="Assets by Campaign", color=0x00ff00)
    if rows:
        for row in rows:
            icon = ASSET_ICONS.get(row[2], "🔹")
            color = ASSET_COLORS.get(row[2], 0x00ff00)
            embed.color = color
            embed.add_field(
                name=f"{icon} {row[5]} - {row[1]} (ID {row[0]})",
                value=f"Type: {row[2]}\nValue: {row[3]}\nRoll: {row[4]}",
                inline=False
            )
    else:
        embed.description = "No assets found for this campaign."
    await interaction.response.send_message(embed=embed)

@asset_group.command(name="list_by_gang", description="List all assets by gang")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def list_assets_by_gang(interaction: Interaction, campaign_id: int, gang_id: int):
    rows = get_gang_assets(gang_id)
    embed = discord.Embed(title="Assets for Gang", color=0x00ff00)
    if rows:
        for row in rows:
            icon = ASSET_ICONS.get(row[3], "🔹")
            color = ASSET_COLORS.get(row[3], 0x00ff00)
            embed.color = color
            embed.add_field(
                name=f"{icon} {row[2]} (ID {row[0]})",
                value=f"Type: {row[3]}\nValue: {row[4]}\nRoll: {row[5]}\nSell: {bool(row[7])}\nNote: {row[8] or 'None'}",
                inline=False
            )
    else:
        embed.description = "No assets found for this gang."
    await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(Assets(bot))
    bot.tree.add_command(asset_group)