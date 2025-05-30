import discord
from discord.ext import commands
from discord import app_commands
from db.user_preferences import set_user_preferences, get_user_preferences
from cogs.autocomplete import campaign_autocomplete, gang_autocomplete

profile_group = app_commands.Group(name="profile", description="Set and view your preferences")

class UserPreferences(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@profile_group.command(name="set_campaign", description="Set your current campaign")
@app_commands.autocomplete(campaign_id=campaign_autocomplete)
async def set_campaign(interaction: discord.Interaction, campaign_id: int):
    set_user_preferences(str(interaction.user.id), campaign_id=campaign_id)
    await interaction.response.send_message(f"Current campaign set to {campaign_id}")

@profile_group.command(name="set_gang", description="Set your current gang")
@app_commands.autocomplete(gang_id=gang_autocomplete)
async def set_gang(interaction: discord.Interaction, gang_id: int):
    set_user_preferences(str(interaction.user.id), gang_id=gang_id)
    await interaction.response.send_message(f"Current gang set to {gang_id}")

@profile_group.command(name="my_preferences", description="View your current campaign and gang")
async def my_preferences(interaction: discord.Interaction):
    prefs = get_user_preferences(str(interaction.user.id))
    if prefs:
        campaign_id, gang_id = prefs
        await interaction.response.send_message(
            f"Current Campaign: {campaign_id or 'None'}\nCurrent Gang: {gang_id or 'None'}"
        )
    else:
        await interaction.response.send_message("No preferences set.")

def setup(bot):
    bot.add_cog(UserPreferences(bot))
    bot.tree.add_command(profile_group)
