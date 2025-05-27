from discord import app_commands, Interaction
from db.campaigns import get_all_campaigns
from db.gangs import get_gangs_by_campaign
from db.gang_items import get_assets_by_gang, get_territories_by_campaign

async def campaign_autocomplete(interaction: Interaction, current: str):
    campaigns = get_all_campaigns(str(interaction.guild.id))
    return [app_commands.Choice(name=f"{name} ({cid})", value=cid) for cid, name in campaigns if current.lower() in name.lower()][:25]

async def gang_autocomplete(interaction: Interaction, current: str):
    campaign_id = interaction.namespace.campaign_id
    gangs = get_gangs_by_campaign(campaign_id)
    return [app_commands.Choice(name=f"{g[3]} ({g[0]})", value=g[0]) for g in gangs if current.lower() in g[3].lower()][:25]

async def territory_autocomplete(interaction: Interaction, current: str):
    campaign_id = interaction.namespace.campaign_id
    territories = get_territories_by_campaign(campaign_id)
    return [app_commands.Choice(name=f"{g[1]} ({g[3]}) - {g[5]}", value=g[0]) for g in territories if current.lower() in g[1].lower()][:25]

async def asset_autocomplete(interaction: Interaction, current: str):
    gang_id = interaction.namespace.gang_id
    assets = get_assets_by_gang(gang_id)
    return [app_commands.Choice(name=f"{g[1]} ({g[0]}) - {g[4]}", value=g[0]) for g in assets if current.lower() in g[1].lower()][:25]