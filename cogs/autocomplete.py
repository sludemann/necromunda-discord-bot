from discord import app_commands, Interaction
from db.campaigns import get_all_campaigns
from db.gangs import get_gangs_by_campaign
from db.gang_assets import get_gang_assets
from db.user_preferences import get_user_preferences

class MissingPreferenceError(Exception):
    pass

def resolve_user_preferences(interaction: Interaction, require_campaign=True, require_gang=True):
    user_id = str(interaction.user.id)
    prefs = get_user_preferences(user_id)
    campaign_id = None
    gang_id = None
    if (prefs):
      campaign_id = prefs[0]
      gang_id = prefs[1]

    if require_campaign and not campaign_id:
        raise MissingPreferenceError("You must set a current campaign using `/profile set_campaign`.")
    if require_gang and not gang_id:
        raise MissingPreferenceError("You must set a current gang using `/profile set_gang`.")

    return campaign_id, gang_id

async def campaign_autocomplete(interaction: Interaction, current: str):
    campaigns = get_all_campaigns(str(interaction.guild.id))
    return [app_commands.Choice(name=f"{name} ({cid})", value=cid) for cid, name in campaigns if current.lower() in name.lower()][:25]

async def gang_autocomplete(interaction: Interaction, current: str):
    prefs = get_user_preferences(str(interaction.user.id))
    campaign_id = None
    if (prefs):
      campaign_id = prefs[0]
    else:
      campaign_id = interaction.namespace.campaign_id
    print(f"Gang Autocomplete - {campaign_id}")
    gangs = get_gangs_by_campaign(campaign_id)
    return [app_commands.Choice(name=f"{g[3]} ({g[0]})", value=g[0]) for g in gangs if current.lower() in g[3].lower()][:25]

def get_autocomplete_asset_types():
    return ['Territory', 'Hanger-On', 'Skill', 'Equipment', 'Captive', 'Other']

async def asset_type_autocomplete(interaction: Interaction, current: str):
    types = get_autocomplete_asset_types()
    return [app_commands.Choice(name=t, value=t) for t in types if current.lower() in t.lower()][:25]

async def asset_autocomplete(interaction: Interaction, current: str):
    gang_id = interaction.namespace.gang_id
    asset_type = getattr(interaction.namespace, 'asset_type', None)
    all_assets = get_gang_assets(gang_id)
    filtered = [a for a in all_assets if current.lower() in a[1].lower() and (asset_type is None or a[3] == asset_type)]
    return [app_commands.Choice(name=f"{a[2]} (ID: {a[0]})", value=str(a[0])) for a in filtered[:25]]