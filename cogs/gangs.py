import discord
from discord.ext import commands
from discord import app_commands
from db.gangs import add_gang, get_gangs_by_campaign, get_gangs_by_user, delete_gang
from cogs.autocomplete import campaign_autocomplete, gang_autocomplete

gang_group = app_commands.Group(name="gang", description="Gang related commands")

class Gangs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='register_gang')
    async def register_gang_text(self, ctx, campaign_id: int, yaktribe_url: str):
        response = add_gang(str(ctx.author.id), campaign_id, yaktribe_url)
        await ctx.send(response)

@gang_group.command(name="register", description="Register your gang to a campaign")
@app_commands.autocomplete(campaign_id=campaign_autocomplete)
async def register_gang_slash(interaction: discord.Interaction, campaign_id: int, yaktribe_url: str):
    response = add_gang(str(interaction.user.id), campaign_id, yaktribe_url)
    await interaction.response.send_message(response)

@gang_group.command(name="list", description="List all gangs in a campaign")
@app_commands.autocomplete(campaign_id=campaign_autocomplete)
async def list_gangs(interaction: discord.Interaction, campaign_id: int):
    gangs = get_gangs_by_campaign(campaign_id)
    if gangs:
        response = f"**Gangs in Campaign {campaign_id}:**\n" + "\n".join([
            f"ID {gid}, User ID {user_id}: {url}" for gid, url, user_id in gangs
        ])
    else:
        response = f"No gangs found for Campaign ID {campaign_id}."
    await interaction.response.send_message(response)

@gang_group.command(name="delete", description="Delete one of your gangs")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def delete_gang_slash(interaction: discord.Interaction, campaign_id: int, gang_id: int):
    response = delete_gang(gang_id, str(interaction.user.id))
    await interaction.response.send_message(response)

@gang_group.command(name="mine", description="List all gangs you've registered across campaigns")
async def list_user_gangs(interaction: discord.Interaction):
    gangs = get_gangs_by_user(str(interaction.user.id))
    if gangs:
        response = "**Your Gangs:**\n" + "\n".join([
            f"Gang ID {gid}: '{gname}' ({gtype}) — Campaign '{cname}' (ID {cid})\nCredits: {credits}, Meat: {meat}, Rating: {rating}"
            for gid, cid, cname, gname, gtype, credits, meat, rating in gangs
        ])
    else:
        response = "You haven't registered any gangs."
    await interaction.response.send_message(response)

def setup(bot):
    bot.add_cog(Gangs(bot))
    bot.tree.add_command(gang_group)
