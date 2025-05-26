import discord
from discord.ext import commands
from discord import app_commands
from db.campaigns import add_campaign, get_all_campaigns, delete_campaign

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
async def delete_campaign_slash(interaction: discord.Interaction, campaign_id: int):
    response = delete_campaign(campaign_id, str(interaction.user.id), str(interaction.guild.id))
    await interaction.response.send_message(response)

# Grouping
campaign_group = app_commands.Group(name="campaign", description="Campaign related commands")
campaign_group.add_command(create_campaign_slash)
campaign_group.add_command(list_campaigns)
campaign_group.add_command(delete_campaign_slash)

def setup(bot):
    bot.add_cog(Campaigns(bot))
    bot.tree.add_command(campaign_group)
