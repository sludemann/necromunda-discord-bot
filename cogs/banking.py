import discord
from discord.ext import commands
from discord import app_commands
from db.banking import log_transaction, get_current_credits, get_transaction_history
from db.gangs import get_gangs_by_campaign, get_gang_by_id
from db.campaigns import get_all_campaigns
from cogs.autocomplete import campaign_autocomplete, gang_autocomplete

class Banking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@app_commands.command(name="add_credits", description="Add credits to a gang")
@app_commands.describe(campaign_id="ID of the campaign", gang_id="Select a gang", amount="Credits to add")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def add_credits(interaction: discord.Interaction, campaign_id: int, gang_id: int, amount: int):
    gang = get_gang_by_id(gang_id)
    log_transaction(gang_id, amount, "manual addition", interaction.user.id)
    total = get_current_credits(gang_id)
    await interaction.response.send_message(f"Added {amount} credits to {gang[0][3]}. Current: {total}")

@app_commands.command(name="subtract_credits", description="Subtract credits from a gang")
@app_commands.describe(campaign_id="ID of the campaign", gang_id="Select a gang", amount="Credits to subtract")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def subtract_credits(interaction: discord.Interaction, campaign_id: int, gang_id: int, amount: int):
    current = get_current_credits(gang_id)
    gang = get_gang_by_id(gang_id)
    if current < amount:
        await interaction.response.send_message(f"Cannot subtract {amount} credits. {gang[0][3]} only has {current} credits.", ephemeral=True)
        return
    log_transaction(gang_id, -amount, "manual subtraction", interaction.user.id)
    total = current - amount
    await interaction.response.send_message(f"Subtracted {amount} credits from {gang[0][3]}. Current: {total}")

@app_commands.command(name="set_credits", description="Set a gang's credits to an exact value")
@app_commands.describe(campaign_id="ID of the campaign", gang_id="Select a gang", amount="New credit value")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def set_credits(interaction: discord.Interaction, campaign_id: int, gang_id: int, amount: int):
    current = get_current_credits(gang_id)
    gang = get_gang_by_id(gang_id)
    delta = amount - current
    log_transaction(gang_id, delta, "manual set", interaction.user.id)
    await interaction.response.send_message(f"Set credits for {gang[0][3]} to {amount}.")

@app_commands.command(name="view_credits", description="View the current credits for a gang")
@app_commands.describe(campaign_id="ID of the campaign", gang_id="Select a gang")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def view_credits(interaction: discord.Interaction, campaign_id: int, gang_id: int):
    total = get_current_credits(gang_id)
    gang = get_gang_by_id(gang_id)
    await interaction.response.send_message(embed=discord.Embed(
        title=f"{gang[0][3]} Total Credits",
        description=f"**{total}**",
        color=discord.Color.blue()
    ))

@app_commands.command(name="credit_history", description="View the credit transaction history for a gang")
@app_commands.describe(campaign_id="ID of the campaign", gang_id="Select a gang")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def credit_history(interaction: discord.Interaction, campaign_id: int, gang_id: int):
    transactions = get_transaction_history(gang_id)
    current_total = get_current_credits(gang_id)
    gang = get_gang_by_id(gang_id)
    embed = discord.Embed(
        title=f"{gang[0][3]} Transaction History",
        description=f"**Current Credits:** {current_total}",
        color=discord.Color.green()
    )

    if not transactions:
        embed.description += "\n\nNo transactions recorded."
        return embed

    running_total = current_total

    for change, reason, timestamp in transactions:
        entry = (
            f"**Change:** {'+' if change >= 0 else ''}{change}\n"
            f"**Total After:** {running_total}\n"
            f"**Reason:** {reason}\n"
            f"**When:** {timestamp}"
        )
        embed.add_field(name="Transaction", value=entry, inline=False)
        running_total -= change  # Calculate total before this transaction
    
    
    await interaction.response.send_message(embed=embed)

banking_group = app_commands.Group(name="bank", description="Gang credit management")
banking_group.add_command(add_credits)
banking_group.add_command(subtract_credits)
banking_group.add_command(set_credits)
banking_group.add_command(view_credits)
banking_group.add_command(credit_history)

def setup(bot):
    bot.add_cog(Banking(bot))
    bot.tree.add_command(banking_group)
