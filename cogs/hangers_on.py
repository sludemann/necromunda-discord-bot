from discord import app_commands, Interaction
from discord.ext import commands
from db.gang_items import add_hanger_on, remove_hanger_on, get_hangers_on_by_campaign, get_hangers_on_by_gang
from cogs.autocomplete import campaign_autocomplete, gang_autocomplete

hanger_group = app_commands.Group(name="hanger", description="Gang Hangers-On related commands")

class HangersOn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@hanger_group.command(name="add", description="Add a hanger-on to a gang")
@app_commands.describe(gang_id="ID of the gang", name="Name of the hanger-on", type="Type of hanger-on", static_value="Flat value", roll_formula="Dice formula")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def add_hanger(interaction: Interaction, campaign_id: int, gang_id: int, name: str, type: str, static_value: int = None, roll_formula: str = None):
    add_hanger_on(gang_id, name, type, static_value, roll_formula)
    await interaction.response.send_message(f"Hanger-On '{name}' added to gang {gang_id}.")

@hanger_group.command(name="remove", description="Remove a hanger-on from a gang")
@app_commands.describe(gang_id="ID of the gang", name="Name of the hanger-on to remove")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def remove_hanger(interaction: Interaction, campaign_id: int, gang_id: int, name: str):
    remove_hanger_on(gang_id, name)
    await interaction.response.send_message(f"Hanger-On '{name}' removed from gang {gang_id}.")

@hanger_group.command(name="list_by_campaign", description="List all hangers-on by campaign")
@app_commands.autocomplete(campaign_id=campaign_autocomplete)
async def list_by_campaign(interaction: Interaction, campaign_id: int):
    rows = get_hangers_on_by_campaign(campaign_id)
    if rows:
        response = "**Hangers-On by Campaign:**\n" + "\n".join([
            f"{row[0]} ({row[1]}) - {row[4]}: {row[2]} static, {row[3]} roll" for row in rows
        ])
    else:
        response = "No hangers-on found for this campaign."
    await interaction.response.send_message(response)

@hanger_group.command(name="list_by_gang", description="List all hangers-on by gang")
@app_commands.autocomplete(gang_id=gang_autocomplete)
async def list_by_gang(interaction: Interaction, campaign_id: int, gang_id: int):
    rows = get_hangers_on_by_gang(gang_id)
    if rows:
        response = "**Hangers-On for Gang:**\n" + "\n".join([
            f"{row[0]} ({row[1]}): {row[2]} static, {row[3]} roll" for row in rows
        ])
    else:
        response = "No hangers-on found for this gang."
    await interaction.response.send_message(response)

def setup(bot):
    bot.add_cog(HangersOn(bot))
    bot.tree.add_command(hanger_group)
