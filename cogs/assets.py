from discord import app_commands, Interaction
from discord.ext import commands
from db.gang_items import add_asset, get_assets_by_campaign, get_assets_by_gang, remove_asset, update_asset
from cogs.autocomplete import campaign_autocomplete, gang_autocomplete, asset_autocomplete

asset_group = app_commands.Group(name="asset", description="Gang Asset related commands")

class Assets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@asset_group.command(name="add", description="Add an asset to a gang")
@app_commands.describe(campaign_id="ID of the campaign", gang_id="ID of the gang", type="Type of asset", value="Credit value", roll_formula="Dice formula", note="Additional note", should_sell="Mark as to be sold on next payday")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def add_asset_command(interaction: Interaction, campaign_id: int, gang_id: int, type: str, value: int = None, roll_formula: str = None, note: str = None, should_sell: bool = False, is_consumed: bool = False):
    add_asset(gang_id, type, value, roll_formula, note, should_sell, is_consumed)
    await interaction.response.send_message(f"Asset '{type}' added to gang {gang_id}.")

@asset_group.command(name="remove", description="Remove an asset from a gang")
@app_commands.describe(campaign_id="ID of the campaign", gang_id="ID of the gang", asset_type="Type of the asset to remove")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def remove_asset_command(interaction: Interaction, campaign_id: int, gang_id: int, asset_type: str):
    remove_asset(gang_id, asset_type)
    await interaction.response.send_message(f"Asset '{asset_type}' removed from gang {gang_id}.")

@asset_group.command(name="sell", description="Mark an asset as to be sold in the next Pay Day")
@app_commands.describe(campaign_id="ID of the campaign", gang_id="ID of the gang", asset_id="ID of the gang")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete, asset_id=asset_autocomplete)
async def remove_asset_command(interaction: Interaction, campaign_id: int, gang_id: int, asset_id: int):
    update_asset(asset_id, true)
    await interaction.response.send_message(f"Asset '{asset_id}' updated to be for sale in the next pay day.")

@asset_group.command(name="list_by_campaign", description="List all assets by campaign")
@app_commands.autocomplete(campaign_id=campaign_autocomplete)
async def list_assets_by_campaign(interaction: Interaction, campaign_id: int):
    rows = get_assets_by_campaign(campaign_id)
    if rows:
        response = "**Assets by Campaign:**\n" + "\n".join([
            f"{row[0]} - {row[5]}: {row[1]} credits, {row[2]} roll, sell: {bool(row[4])}, note: {row[3]}" for row in rows
        ])
    else:
        response = "No assets found for this campaign."
    await interaction.response.send_message(response)

@asset_group.command(name="list_by_gang", description="List all assets by gang")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def list_assets_by_gang(interaction: Interaction, campaign_id: int, gang_id: int):
    rows = get_assets_by_gang(gang_id)
    if rows:
        response = "**Assets for Gang:**\n" + "\n".join([
            f"{row[0]}: {row[1]} credits, {row[2]} roll, sell: {bool(row[4])}, note: {row[3]}" for row in rows
        ])
    else:
        response = "No assets found for this gang."
    await interaction.response.send_message(response)

def setup(bot):
    bot.add_cog(Assets(bot))
    bot.tree.add_command(asset_group)