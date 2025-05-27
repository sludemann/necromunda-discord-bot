from discord import app_commands, Interaction
from discord.ext import commands
from db.gang_items import add_territory, get_territories_by_campaign, get_territories_by_gang, remove_territory, steal_territory
from cogs.autocomplete import campaign_autocomplete, gang_autocomplete

territory_group = app_commands.Group(name="territory", description="Gang Territory related commands")

class Territories(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@territory_group.command(name="add", description="Add a territory to a gang")
@app_commands.describe(campaign_id="ID of the campaign", gang_id="ID of the gang", name="Territory name", type="Type of territory", static_value="Flat value", roll_formula="Dice formula")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def add_territory_command(interaction: Interaction, campaign_id: int, gang_id: int, name: str, type: str, static_value: int = None, roll_formula: str = None):
    add_territory(gang_id, name, type, static_value, roll_formula)
    await interaction.response.send_message(f"Territory '{name}' added to gang {gang_id}.")

@territory_group.command(name="remove", description="Remove a territory from a gang")
@app_commands.describe(gang_id="ID of the gang", name="Name of the territory to remove")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def remove_territory_command(interaction: Interaction, campaign_id: int, gang_id: int, name: str):
    remove_territory(gang_id, name)
    await interaction.response.send_message(f"Territory '{name}' removed from gang {gang_id}.")

@territory_group.command(name="steal", description="Transfer a territory from one gang to another")
@app_commands.describe(campaign_id="ID of the campaign", from_gang_id="ID of the gang to steal from", to_gang_id="ID of the gang to give to", name="Name of the territory")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, from_gang_id=gang_autocomplete, to_gang_id=gang_autocomplete)
async def steal_territory_command(interaction: Interaction, campaign_id: int, from_gang_id: int, to_gang_id: int, name: str):
    success = steal_territory(from_gang_id, to_gang_id, name)
    if not success:
        await interaction.response.send_message(f"Territory '{name}' not found for gang {from_gang_id}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Territory '{name}' moved from gang {from_gang_id} to gang {to_gang_id}.")

@territory_group.command(name="list_by_campaign", description="List all territories by campaign")
@app_commands.autocomplete(campaign_id=campaign_autocomplete)
async def territories_by_campaign(interaction: Interaction, campaign_id: int):
    rows = get_territories_by_campaign(campaign_id)
    if rows:
        response = "**Territories by Campaign:**\n" + "\n".join([
            f"{row[0]} ({row[1]}) - {row[4]}: {row[2]} static, {row[3]} roll" for row in rows
        ])
    else:
        response = "No territories found for this campaign."
    await interaction.response.send_message(response)

@territory_group.command(name="list_by_gang", description="List all territories by gang")
@app_commands.autocomplete(campaign_id=campaign_autocomplete, gang_id=gang_autocomplete)
async def territories_by_gang(interaction: Interaction, campaign_id: int, gang_id: int):
    rows = get_territories_by_gang(gang_id)
    if rows:
        response = "**Territories for Gang:**\n" + "\n".join([
            f"{row[0]} ({row[1]}): {row[2]} static, {row[3]} roll" for row in rows
        ])
    else:
        response = "No territories found for this gang."
    await interaction.response.send_message(response)

def setup(bot):
    bot.add_cog(Territories(bot))
    bot.tree.add_command(territory_group)
