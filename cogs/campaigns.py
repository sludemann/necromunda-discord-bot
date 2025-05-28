import discord
from discord.ext import commands
from discord import app_commands
from db.campaigns import add_campaign, get_all_campaigns, delete_campaign
from cogs.autocomplete import campaign_autocomplete, gang_autocomplete
from cogs.dice import Dice
from db.gangs import get_gangs_by_campaign
from db.gang_assets import get_gang_assets
from db.banking import log_transaction


async def calculate_payday(gang_id: int, user_id: int):
    assets = get_gang_assets(gang_id)
    total = 0

    for asset in assets:
        asset_id, gang_id, name, asset_type, value, formula, is_consumed, should_sell, note, *_ = asset

        if asset_type in ('Territory', 'Hanger-On', 'Skill', 'Other') or should_sell:
            if value:
                total += value
            if formula:
                result = Dice.roll_formula(formula)
                total += result["total"]

        # if should_sell:
          # remove the asset after sold

    log_transaction(gang_id, total, "Pay Day", user_id)
    return total

class Campaigns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='create_campaign')
    async def create_campaign_text(self, ctx, *, name: str):
        response = add_campaign(name, str(ctx.author.id), str(ctx.guild.id))
        await ctx.send(response)

# Slash commands
@app_commands.command(name="create", description="Create a new campaign")
async def create_campaign_slash(interaction: discord.Interaction, name: str):
    response = add_campaign(name, str(interaction.user.id), str(interaction.guild.id))
    await interaction.response.send_message(response)

@app_commands.command(name="list", description="List all campaigns")
async def list_campaigns(interaction: discord.Interaction):
    campaigns = get_all_campaigns(str(interaction.guild.id))
    if campaigns:
        response = "**Campaigns:**\n" + "\n".join([f"ID {cid}: {name}" for cid, name in campaigns])
    else:
        response = "No campaigns found."
    await interaction.response.send_message(response)

@app_commands.command(name="delete", description="Delete a campaign you created")
@app_commands.describe(campaign_id="ID of the campaign to delete")
@app_commands.autocomplete(campaign_id=campaign_autocomplete)
async def delete_campaign_slash(interaction: discord.Interaction, campaign_id: int):
    response = delete_campaign(campaign_id, str(interaction.user.id), str(interaction.guild.id))
    await interaction.response.send_message(response)

@app_commands.command(name="payday_all", description="Apply payday to all gangs in a campaign")
@app_commands.autocomplete(campaign_id=campaign_autocomplete)
async def payday_all(interaction: discord.Interaction, campaign_id: int):
    gangs = get_gangs_by_campaign(campaign_id)
    if not gangs:
        await interaction.response.send_message("No gangs found for this campaign.", ephemeral=True)
        return

    summary = []
    for gang_id, yak_url, user_id, gang_name, gang_type in gangs:
        total = await calculate_payday(gang_id, interaction.user.id)
        summary.append(f"{gang_name}: {total} credits")

    message = "**Payday Summary:**\n" + "\n".join(summary)
    await interaction.response.send_message(message)

@app_commands.command(name="payday_one", description="Apply payday to a single gang")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def payday_one(interaction: discord.Interaction, campaign_id: int, gang_id: int):
    total = await calculate_payday(gang_id, interaction.user.id)
    await interaction.response.send_message(f"Gang ID {gang_id} received {total} credits.")

# Grouping
campaign_group = app_commands.Group(name="campaign", description="Campaign related commands")
campaign_group.add_command(create_campaign_slash)
campaign_group.add_command(list_campaigns)
campaign_group.add_command(delete_campaign_slash)
campaign_group.add_command(payday_all)
campaign_group.add_command(payday_one)

def setup(bot):
    bot.add_cog(Campaigns(bot))
    bot.tree.add_command(campaign_group)
