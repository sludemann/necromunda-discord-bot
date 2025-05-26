import discord
from discord.ext import commands
from discord import app_commands
import os

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@app_commands.command(name="export_db", description="Export the database file")
async def export_db_slash(interaction: discord.Interaction):
    if interaction.user.id != interaction.client.owner_id:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    if os.path.exists("necromunda.db"):
        await interaction.response.send_message("Here is the database:", ephemeral=True)
        await interaction.followup.send(file=discord.File("necromunda.db"))
    else:
        await interaction.response.send_message("Database file not found.", ephemeral=True)

admin_group = app_commands.Group(name="admin", description="Admin tools")
admin_group.add_command(export_db_slash)

def setup(bot):
    bot.add_cog(Admin(bot))
    bot.tree.add_command(admin_group)