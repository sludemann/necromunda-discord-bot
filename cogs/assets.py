import discord
from discord import app_commands, Interaction
from discord.ext import commands

from db.gang_assets import (
    insert_gang_asset,
    get_gang_assets_by_campaign,
    get_gang_assets,
    delete_gang_asset,
    update_gang_asset
)
from cogs.autocomplete import (
    resolve_user_preferences,
    MissingPreferenceError,
    asset_autocomplete,
    asset_type_autocomplete
)

asset_group = app_commands.Group(name="asset", description="Gang Asset commands")

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

@asset_group.command(
    name="add",
    description="Add an asset to your current gang"
)
@app_commands.describe(
    asset_type="Type of asset",
    name="Name of the asset",
    value="Credit value",
    roll_formula="Dice formula",
    note="Additional note",
    should_sell="Mark to sell next payday",
    is_consumed="Mark as consumed"
)
@app_commands.autocomplete(asset_type=asset_type_autocomplete)
async def add_asset_command(
    interaction: Interaction,
    asset_type: str,
    name: str,
    value: int = None,
    roll_formula: str = None,
    note: str = None,
    should_sell: bool = False,
    is_consumed: bool = False
):
    try:
        _, gang_id = resolve_user_preferences(interaction, require_campaign=True, require_gang=True)
    except MissingPreferenceError as e:
        return await interaction.response.send_message(str(e), ephemeral=True)

    insert_gang_asset(
        gang_id, name, asset_type,
        value, roll_formula,
        is_consumed, should_sell,
        note
    )
    await interaction.response.send_message(
        f"✅ Added **{asset_type} {name}** to your gang."
    )

@asset_group.command(
    name="remove",
    description="Remove an asset from your current gang"
)
@app_commands.describe(asset_id="ID of the asset")
@app_commands.autocomplete(asset_id=asset_autocomplete)
async def remove_asset_command(interaction: Interaction, asset_id: int):
    try:
        _, gang_id = resolve_user_preferences(interaction, require_campaign=True, require_gang=True)
    except MissingPreferenceError as e:
        return await interaction.response.send_message(str(e), ephemeral=True)

    delete_gang_asset(asset_id)
    await interaction.response.send_message(f"🗑️ Removed asset **{asset_id}** from your gang.")

@asset_group.command(
    name="sell",
    description="Mark an asset for sale on next payday"
)
@app_commands.describe(asset_id="ID of the asset")
@app_commands.autocomplete(asset_id=asset_autocomplete)
async def sell_asset_command(interaction: Interaction, asset_id: int):
    try:
        _, gang_id = resolve_user_preferences(interaction, require_campaign=True, require_gang=True)
    except MissingPreferenceError as e:
        return await interaction.response.send_message(str(e), ephemeral=True)

    update_gang_asset(asset_id, should_sell=True)
    await interaction.response.send_message(
        f"💰 Asset **{asset_id}** marked for sale on the next payday."
    )

@asset_group.command(
    name="list_by_campaign",
    description="List all assets in your current campaign"
)
async def list_assets_by_campaign(interaction: Interaction):
    try:
        campaign_id, _ = resolve_user_preferences(interaction, require_campaign=True, require_gang=False)
    except MissingPreferenceError as e:
        return await interaction.response.send_message(str(e), ephemeral=True)

    rows = get_gang_assets_by_campaign(campaign_id)
    embed = discord.Embed(title="Campaign Assets", color=0x00ff00)

    if rows:
        for row in rows:
            asset_id, gang_id, asset_type, value, formula, name, *_ = row
            icon = ASSET_ICONS.get(asset_type, "🔹")
            color = ASSET_COLORS.get(asset_type, 0x00ff00)
            embed.color = color
            embed.add_field(
                name=f"{icon} {name} (ID {asset_id})",
                value=(
                    f"• Gang ID: {gang_id}\n"
                    f"• Type: {asset_type}\n"
                    f"• Value: {value}\n"
                    f"• Roll: {formula or '—'}"
                ),
                inline=False
            )
    else:
        embed.description = "No assets found for this campaign."

    await interaction.response.send_message(embed=embed)

@asset_group.command(
    name="list_by_gang",
    description="List all assets for your current gang"
)
async def list_assets_by_gang(interaction: Interaction):
    try:
        _, gang_id = resolve_user_preferences(interaction, require_campaign=True, require_gang=True)
    except MissingPreferenceError as e:
        return await interaction.response.send_message(str(e), ephemeral=True)

    rows = get_gang_assets(gang_id)
    embed = discord.Embed(title="Your Gang’s Assets", color=0x00ff00)

    if rows:
        for row in rows:
            asset_id, _, name, asset_type, value, formula, _, should_sell, note, *_ = row
            icon = ASSET_ICONS.get(asset_type, "🔹")
            color = ASSET_COLORS.get(asset_type, 0x00ff00)
            embed.color = color
            embed.add_field(
                name=f"{icon} {name} (ID {asset_id})",
                value=(
                    f"• Type: {asset_type}\n"
                    f"• Value: {value}\n"
                    f"• Roll: {formula or '—'}\n"
                    f"• Sell: {should_sell}\n"
                    f"• Note: {note or 'None'}"
                ),
                inline=False
            )
    else:
        embed.description = "No assets found for your gang."

    await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(Assets(bot))
    bot.tree.add_command(asset_group)
