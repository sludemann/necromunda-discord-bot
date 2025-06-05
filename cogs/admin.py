import discord
from discord.ext import commands
from discord import app_commands
from cogs.banking import get_credit_history
from db.banking import log_transaction, get_current_credits
from db.gangs import get_gang_by_id
from db.gang_assets import insert_gang_asset, delete_gang_asset
from cogs.autocomplete import gang_autocomplete,asset_type_autocomplete, asset_autocomplete, resolve_user_preferences, MissingPreferenceError
import os

admin_group = app_commands.Group(name="admin", description="Admin tools")

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@admin_group.command(name="export_db", description="Export the database file")
async def export_db_slash(interaction: discord.Interaction):
    if interaction.user.id != interaction.client.owner_id:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    if os.path.exists("necromunda.db"):
        await interaction.response.send_message("Here is the database:", ephemeral=True)
        await interaction.followup.send(file=discord.File("necromunda.db"))
    else:
        await interaction.response.send_message("Database file not found.", ephemeral=True)

@admin_group.command(
    name="adjust_credits",
    description="(Admin) Adjust any gang's credits in *this* campaign"
)
@app_commands.describe(
    gang_id="Target gang",
    amount="Credits (positive to add, negative to subtract)",
    reason="Optional reason"
)
@app_commands.autocomplete(gang_id=gang_autocomplete)
async def admin_adjust(
    interaction: discord.Interaction,
    gang_id: int,
    amount: int,
    reason: str = "admin adjustment"
):
    if interaction.user.id != interaction.client.owner_id:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    current = get_current_credits(gang_id)
    if amount < 0 and current < -amount:
        gang = get_gang_by_id(gang_id)
        await interaction.response.send_message(
            f"❌ Cannot subtract {abs(amount)} credits; **{gang[3]}** only has {current}.",
            ephemeral=True
        )
        return

    log_transaction(gang_id, amount, reason, interaction.user.id)
    total = get_current_credits(gang_id)
    gang = get_gang_by_id(gang_id)
    verb = "Added" if amount >= 0 else "Subtracted"
    await interaction.response.send_message(
        f"✅ {verb} {abs(amount)} credits "
        f"{'to' if amount>=0 else 'from'} **{gang[3]}**. "
        f"New balance: **{total}** credits."
    )

@admin_group.command(name="set_credits", description="Set a gang's credits to an exact value")
@app_commands.describe(
    gang_id="Select a gang", 
    amount="New credit value", 
    reason="Optional reason")
@app_commands.autocomplete(gang_id=gang_autocomplete)
async def set_credits(interaction: discord.Interaction, 
    gang_id: int, 
    amount: int,
    reason: str = "admin adjustment"
):
    if interaction.user.id != interaction.client.owner_id:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return
        
    try:
        campaign_id, _ = resolve_user_preferences(interaction, require_campaign=True, require_gang=False)
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)
        return

    current = get_current_credits(gang_id)
    gang = get_gang_by_id(gang_id)
    delta = amount - current
    log_transaction(gang_id, delta, reason, interaction.user.id)
    await interaction.response.send_message(
        f"✅ New Balance: **{abs(amount)}** credits "
        f"Old balance: **{current}** credits."
    )

@admin_group.command(
    name="credit_history",
    description="Show a gang's credit transaction history (paged)"
)
@app_commands.describe(
    page="Which page to view (starting at 1)",
    limit="How many entries per page"
)
@app_commands.autocomplete(gang_id=gang_autocomplete)
async def credit_history(
    interaction: discord.Interaction,
    gang_id: int,
    page: int = 1,
    limit: int = 10
):
    if interaction.user.id != interaction.client.owner_id:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return
    
    try:
        _, gang_id = resolve_user_preferences(interaction, require_campaign=True, require_gang=True)
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)
        return

    await interaction.response.send_message(embed=get_credit_history(gang_id, page, limit))

@admin_group.command(name="add_asset", description="Add an asset to a gang")
@app_commands.describe(gang_id="ID of the gang", asset_type="Type of asset", value="Credit value", roll_formula="Dice formula", note="Additional note", should_sell="Mark as to be sold on next payday", is_consumed="Mark as consumed")
@app_commands.autocomplete(gang_id=gang_autocomplete, asset_type=asset_type_autocomplete)
async def add_asset_command(interaction: discord.Interaction, gang_id: int, asset_type: str, name: str, value: int = None, roll_formula: str = None, note: str = None, should_sell: bool = False, is_consumed: bool = False):
    if interaction.user.id != interaction.client.owner_id:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return
        
    try:
        campaign_id, _ = resolve_user_preferences(interaction, require_campaign=True, require_gang=False)
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)
        return
    insert_gang_asset(gang_id, name, asset_type, value, roll_formula, is_consumed, should_sell, note)
    await interaction.response.send_message(f"Asset '{asset_type}' added to gang {gang_id}.")

@admin_group.command(name="remove_asset", description="Remove an asset from a gang")
@app_commands.describe(gang_id="ID of the gang", asset_id="ID of the asset")
@app_commands.autocomplete(gang_id=gang_autocomplete, asset_id=asset_autocomplete)
async def remove_asset_command(interaction: discord.Interaction, gang_id: int, asset_id: int):
    if interaction.user.id != interaction.client.owner_id:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return
        
    try:
        campaign_id, _ = resolve_user_preferences(interaction, require_campaign=True, require_gang=False)
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)
        return
    delete_gang_asset(asset_id)
    await interaction.response.send_message(f"Asset ID '{asset_id}' removed from gang {gang_id}.")

def setup(bot):
    bot.add_cog(Admin(bot))
    bot.tree.add_command(admin_group)