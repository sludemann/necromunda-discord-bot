from collections import defaultdict
from datetime import datetime
import discord
import pandas as pd
from discord import app_commands, Interaction
from discord.ext import commands
from db.campaigns import get_campaign
from db.gangs import get_gang_by_id
from db.marketplace import save_market_data, get_market_data, create_trade_offer, accept_trade_offer, get_trade_offers_by_campaign
from cogs.autocomplete import gang_autocomplete, resolve_user_preferences, MissingPreferenceError

marketplace_group = app_commands.Group(name="marketplace", description="Marketplace management commands")

TRADING_POST_CSV = "./Trading Post.csv"
df = pd.read_csv(TRADING_POST_CSV, encoding='utf-8-sig')

def parse_rarity_rating(value):
    if isinstance(value, str):
        value = value.strip().upper()
        if value == "C":
            return 0
        if value[0] in ("R", "I"):
            try:
                return int(value[1:])
            except ValueError:
                return None
    return None

df_clean = df.dropna(subset=["Name", "Category", "Rarity", "Rarity Rating", "Cost"]).copy()
df_clean["Parsed Rarity"] = df_clean["Rarity Rating"].apply(parse_rarity_rating)
df_clean = df_clean.dropna(subset=["Parsed Rarity"])

def generate_market_data():
    categories = df_clean["Category"].unique()
    trading_post = []

    # Ensure at least one item per category
    for category in categories:
        items = df_clean[df_clean["Category"] == category]
        item = weighted_choice(items)
        if item is not None:
            trading_post.append(item)

    # Fill the rest to make 20 unique entries
    selected_names = {item['Name'] for item in trading_post}
    attempts = 0
    while len(trading_post) < 20 and attempts < 1000:
        item = weighted_choice(df_clean)
        attempts += 1
        if item and item['Name'] not in selected_names:
            trading_post.append(item)
            selected_names.add(item['Name'])

    if len(trading_post) < 20:
        print(f"Only generated {len(trading_post)} items after {attempts} attempts")

    # Secret Stash: 5 unique items with Rarity/Illegal >= 10
    stash_pool = df_clean[df_clean["Parsed Rarity"] >= 10]
    stash_items = []
    stash_selected = set()
    stash_attempts = 0
    while len(stash_items) < 5 and stash_attempts < 500:
        if stash_pool.empty:
            break
        item = stash_pool.sample(1).iloc[0]
        stash_attempts += 1
        if item["Name"] not in stash_selected:
            stash_items.append(item_to_dict(item))
            stash_selected.add(item["Name"])

    return trading_post, stash_items

def weighted_choice(df):
    try:
        weights = df["Parsed Rarity"].apply(lambda r: 1 / (r + 1)).tolist()
        if sum(weights) == 0:
            return None
        item = df.sample(weights=weights).iloc[0]
        return item_to_dict(item)
    except Exception as e:
        print(f"weighted_choice error: {e}")
        return None

def item_to_dict(row):
    return {
        "Name": row["Name"],
        "Category": row["Category"],
        "Rarity": row["Rarity"],
        "Rarity Rating": row["Rarity Rating"],
        "Cost": row["Cost"]
    }

MAX_FIELD_VALUE_LENGTH = 1024
# A bit of buffer to account for newlines and " (Cont.)" in title, etc.
PRACTICAL_MAX_FIELD_VALUE_LENGTH = 1000 


def format_items_for_single_category(items_in_category: list[dict[str, any]]) -> list[str]:
    """Formats items within a single category into a list of strings."""
    item_lines = []
    for item in items_in_category:
        name = item.get('Name', 'Unknown Item')
        rarity = item.get('Rarity Rating', 'N/A')
        cost = item.get('Cost', 'N/A')
        item_lines.append(f"- **{name}** (Rarity {rarity}) - Cost: {cost}")
    return item_lines

def add_section_to_embed(
    embed: discord.Embed,
    items: list[dict[str, any]] | None,
    base_field_name: str,
    empty_section_message_suffix: str = "this section"
):
    """
    Adds a section's items (grouped by category) to the embed, splitting into
    multiple fields if necessary to respect character limits.
    """
    if not items:
        embed.add_field(
            name=base_field_name,
            value=f"No items currently in {empty_section_message_suffix.lower()}.",
            inline=False
        )
        return

    categorized_items = defaultdict(list)
    for item in items:
        category = item.get('Category', 'Uncategorized')
        categorized_items[category].append(item)

    if not categorized_items: # Should be caught by 'if not items' but good to have
        embed.add_field(
            name=base_field_name,
            value=f"No items currently in {empty_section_message_suffix.lower()}.",
            inline=False
        )
        return

    current_field_lines: list[str] = []
    current_field_char_count = 0
    field_continuation_count = 0

    sorted_categories = sorted(categorized_items.keys())

    for i, category_name in enumerate(sorted_categories):
        category_header = f"\n**--- {category_name} ---**" # Added newline for spacing
        category_item_lines = format_items_for_single_category(categorized_items[category_name])

        # Calculate length of this category's content
        # Add 1 for newline joining category_header and first item if item_lines not empty
        category_content_block = [category_header] + category_item_lines
        category_block_text = "\n".join(category_content_block).lstrip('\n') # lstrip for the very first header
        category_block_len = len(category_block_text) + 1 # +1 for potential newline separator

        # Check if adding this category block would exceed the limit
        if current_field_lines and (current_field_char_count + category_block_len > PRACTICAL_MAX_FIELD_VALUE_LENGTH):
            # Finalize and add the current field
            field_name_to_add = base_field_name
            if field_continuation_count > 0:
                field_name_to_add += f" (Cont. {field_continuation_count})"
            
            embed.add_field(
                name=field_name_to_add,
                value="\n".join(current_field_lines).lstrip('\n'), # lstrip for first line
                inline=False
            )
            field_continuation_count += 1
            current_field_lines = [] # Reset for the new field
            current_field_char_count = 0
        
        # Add the current category's content to the (potentially new) current field
        current_field_lines.extend(category_content_block)
        current_field_char_count += category_block_len # Approximating here, precise recalculation later

        # Recalculate actual char count for safety (though approximation should be close)
        current_field_char_count = len("\n".join(current_field_lines).lstrip('\n'))


    # Add any remaining content in the last field
    if current_field_lines:
        field_name_to_add = base_field_name
        if field_continuation_count > 0:
            field_name_to_add += f" (Cont. {field_continuation_count})"
        
        field_value_str = "\n".join(current_field_lines).lstrip('\n')
        if len(field_value_str) > MAX_FIELD_VALUE_LENGTH: # Final truncation if still too long
            safe_truncate_pos = field_value_str.rfind('\n', 0, MAX_FIELD_VALUE_LENGTH - 20) # -20 for "... (truncated)"
            if safe_truncate_pos == -1: safe_truncate_pos = MAX_FIELD_VALUE_LENGTH - 20
            field_value_str = field_value_str[:safe_truncate_pos] + "\n... (section truncated)"

        embed.add_field(name=field_name_to_add, value=field_value_str, inline=False)

class Marketplace(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@marketplace_group.command(name="generate", description="Generate the trading post and secret stash")
async def generate_market(interaction: Interaction):
    try:
        campaign_id, _ = resolve_user_preferences(interaction, require_campaign=True, require_gang=False)
        trading_post, secret_stash = generate_market_data()
        save_market_data(campaign_id, trading_post, secret_stash)
        await interaction.response.send_message(f"Marketplace generated for campaign {campaign_id} with {len(trading_post)} trading items and {len(secret_stash)} secret stash items.")
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)

@marketplace_group.command(name="view", description="View the current trading post and secret stash")
async def view_market(interaction: Interaction):
    try:
        campaign_id, _ = resolve_user_preferences(interaction, require_campaign=True, require_gang=False)
        trading_post_items, secret_stash_items, generated_at = get_market_data(campaign_id)

        if trading_post_items is None and secret_stash_items is None:
            await interaction.response.send_message(
                f"No marketplace data found for Campaign {campaign_id}.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Marketplace - Campaign {campaign_id}",
            color=discord.Color.dark_magenta() 
        )

        if generated_at:
            if isinstance(generated_at, datetime):
                embed.description = f"Last Updated: {discord.utils.format_dt(generated_at, style='R')} ({discord.utils.format_dt(generated_at, style='F')})"
            else:
                embed.set_footer(text=f"Generated: {str(generated_at)}")
        else:
            embed.set_footer(text="Update time not available")

        # Add Trading Post items to embed
        add_section_to_embed(
            embed,
            trading_post_items,
            "🛒 Trading Post",
            empty_section_message_suffix="the Trading Post"
        )

        # Add Secret Stash items to embed
        add_section_to_embed(
            embed,
            secret_stash_items,
            "🤫 Secret Stash",
            empty_section_message_suffix="the Secret Stash"
        )
        
        if len(embed.fields) > 25:
            print(f"Warning: Embed for campaign {campaign_id} has {len(embed.fields)} fields, max is 25.")

        await interaction.response.send_message(embed=embed) # Or ephemeral=True

    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)
    except Exception as e:
        import traceback
        print(f"Error in view_market: {e}\n{traceback.format_exc()}")
        await interaction.response.send_message(
            "An unexpected error occurred while fetching market data.",
            ephemeral=True
        )

@marketplace_group.command(name="trade", description="Create a trade offer")
@app_commands.describe(to_gang_id="Target Gang ID", offered_assets="Assets offered (comma-separated)", offered_credits="Credits offered", requested_assets="Assets requested (comma-separated)", requested_credits="Credits requested")
@app_commands.autocomplete(to_gang_id=gang_autocomplete)
async def make_offer(interaction: Interaction, to_gang_id: int, offered_assets: str = None, offered_credits: int = 0, requested_assets: str = None, requested_credits: int = 0):
    try:
        campaign_id, from_gang_id = resolve_user_preferences(interaction)
        offer_id = create_trade_offer(campaign_id, from_gang_id, to_gang_id, offered_assets or "", offered_credits, requested_assets or "", requested_credits)
        await interaction.response.send_message(f"Trade offer #{offer_id} created from gang {from_gang_id} to gang {to_gang_id}.")
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)

@marketplace_group.command(name="list_trades", description="List all trade offers in the current campaign")
async def list_offers(interaction: Interaction):
    try:
        campaign_id, _ = resolve_user_preferences(interaction, require_campaign=True, require_gang=False)
        offers = get_trade_offers_by_campaign(campaign_id)
        if not offers:
            await interaction.response.send_message("No trade offers available.")
            return
        message = "**Trade Offers:**\n"
        for offer in offers:
            message += f"ID {offer['id']}: Gang {offer['from_gang_id']} offers [{offer['offered_assets']}] + {offer['offered_credits']} credits to Gang {offer['to_gang_id']} for [{offer['requested_assets']}] + {offer['requested_credits']} credits — {offer['status']}\n"
        await interaction.response.send_message(message)
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)

@marketplace_group.command(name="accept_trade", description="Accept a trade offer")
@app_commands.describe(offer_id="ID of the offer to accept")
async def accept_offer_cmd(interaction: Interaction, offer_id: int):
    try:
        _, to_gang_id = resolve_user_preferences(interaction, require_campaign=False)
        user_id = str(interaction.user.id)
        owner_id = get_gang_by_id(to_gang_id)[2]
        if user_id != owner_id:
            await interaction.response.send_message("You do not own the target gang and cannot accept this trade.", ephemeral=True)
            return
        result = accept_trade_offer(offer_id)
        await interaction.response.send_message(result)
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)

def setup(bot):
    bot.add_cog(Marketplace(bot))
