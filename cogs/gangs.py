import discord
from discord.ext import commands
from discord import app_commands
from db.gangs import add_gang, get_gangs_by_campaign, get_gangs_by_user, delete_gang
from cogs.autocomplete import campaign_autocomplete, gang_autocomplete

gang_group = app_commands.Group(name="gang", description="Gang related commands")

class Gangs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        embed = discord.Embed(
            title=f"Gangs in Campaign {campaign_id}",
            description="Here are the gangs currently participating:",
            color=discord.Color.blue()
        )
        for gid, url, user_id, name, type in gangs:
            embed.add_field(
                name=f"{name} ({type})",
                value=f"ID: `{gid}` | User ID: `{user_id}`\n[Link to Gang]({url})",
                inline=False
            )
    else:
        embed = discord.Embed(
            title="No Gangs Found",
            description=f"No gangs found for Campaign ID `{campaign_id}`.",
            color=discord.Color.red()
        )

    await interaction.response.send_message(embed=embed)

@gang_group.command(name="delete", description="Delete one of your gangs")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def delete_gang_slash(interaction: discord.Interaction, campaign_id: int, gang_id: int):
    response = delete_gang(gang_id, str(interaction.user.id))
    await interaction.response.send_message(response)

@gang_group.command(name="mine", description="List all gangs you've registered across campaigns")
async def list_user_gangs(interaction: discord.Interaction):
    gangs = get_gangs_by_user(str(interaction.user.id))

    if gangs:
        embed = discord.Embed(
            title="Your Registered Gangs",
            description="Below are the gangs you've registered across all campaigns:",
            color=discord.Color.green()
        )
        for gid, cid, cname, gname, gtype, credits, meat, rating in gangs:
            embed.add_field(
                name=f"'{gname}' ({gtype})",
                value=(
                    f"**Gang ID:** `{gid}`\n"
                    f"**Campaign:** '{cname}' (ID `{cid}`)\n"
                    f"**Credits:** {credits} | **Meat:** {meat} | **Rating:** {rating}"
                ),
                inline=False
            )
    else:
        embed = discord.Embed(
            title="No Gangs Registered",
            description="You haven't registered any gangs yet.",
            color=discord.Color.orange()
        )

    await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(Gangs(bot))
    bot.tree.add_command(gang_group)
