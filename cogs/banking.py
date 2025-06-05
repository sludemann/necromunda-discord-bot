import math
import discord
from discord import app_commands, Interaction
from discord.ext import commands

from db.banking import log_transaction, get_current_credits, get_transaction_history
from db.gangs import get_gang_by_id
from cogs.autocomplete import resolve_user_preferences, MissingPreferenceError, gang_autocomplete

banking_group = app_commands.Group(name="bank", description="Gang credit management")

def format_credit_history_embed(
    gang_name: str,
    current_credits: int,
    page: int,
    total_pages: int,
    total_transactions_count: int,
    transactions: list[tuple[any, int, str, int]] # (ts, change, reason, running_total_after)
) -> discord.Embed:
    embed = discord.Embed(
        title=f"{gang_name} Transaction History",
        description=(
            f"**Current Gang Credits:** {current_credits} credits\n"
            f"Showing page {page} of {total_pages} ({total_transactions_count} total transactions)"
        ),
        color=discord.Color.green() # Or your preferred color
    )

    if not transactions:
        embed.add_field(
            name="No transactions",
            value="This gang has no recorded transactions on this page.",
            inline=False
        )
    else:
        for timestamp, change, reason, running_total_after_this_tx in transactions:
            # Calculate the 'before' balance using the 'after' balance and the change
            balance_before_tx = running_total_after_this_tx - change

            embed.add_field(
                name=f"{timestamp:%Y-%m-%d %H:%M %Z}", # %Z for timezone name (e.g., UTC)
                value=(
                    f"**Change:** {'+' if change >= 0 else ''}{change}\n"
                    f"**Before:** {balance_before_tx} → **After:** {running_total_after_this_tx}\n"
                    f"**Reason:** {reason}"
                ),
                inline=False
            )
    return embed

def get_credit_history(
        gang_id: int, 
        page: int, 
        limit: int
    ) -> discord.Embed:
    page = max(page, 1)
    limit = max(min(limit, 50), 1)
    offset = (page - 1) * limit

    current_total_credits = get_current_credits(gang_id)
    transactions_page_data, total_transaction_count = get_transaction_history(gang_id,current_total_credits, limit=limit, offset=offset)
    gang = get_gang_by_id(gang_id) # gang[3] is the gang name

    # Calculate total pages and adjust if current page is out of bounds
    total_pages = max(math.ceil(total_transaction_count / limit), 1)
    if page > total_pages:
        page = total_pages
        offset = (page - 1) * limit
        transactions_page_data, _ = get_transaction_history(gang_id, current_total_credits, limit=limit, offset=offset)

    return format_credit_history_embed(
        gang_name=gang[3],
        current_credits=current_total_credits,
        page=page,
        total_pages=total_pages,
        total_transactions_count=total_transaction_count,
        transactions=transactions_page_data
    )

@banking_group.command(
    name="adjust",
    description="Add or subtract credits from *your* gang (positive to add, negative to subtract)"
)
@app_commands.describe(
    amount="Credits (e.g. 10 or -5)",
    reason="Optional reason for this adjustment"
)
async def adjust_credits(interaction: Interaction, amount: int, reason: str = "manual adjustment"):
    try:
        # pulls your saved campaign & gang; errors if you haven’t set them
        _, gang_id = resolve_user_preferences(interaction, require_campaign=True, require_gang=True)
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)
        return

    current = get_current_credits(gang_id)
    if amount < 0 and current < -amount:
        gang = get_gang_by_id(gang_id)
        await interaction.response.send_message(
            f"❌ Cannot subtract {abs(amount)} credits; **{gang[3]}** only has {current}.",
            ephemeral=True
        )
        return

    log_transaction(gang_id, amount, reason, interaction.user.id)
    total = get_current_credits(gang_id)
    gang = get_gang_by_id(gang_id)
    verb = "Added" if amount >= 0 else "Subtracted"
    await interaction.response.send_message(
        f"✅ {verb} {abs(amount)} credits "
        f"{'to' if amount>=0 else 'from'} **{gang[3]}**. "
        f"New balance: **{total}** credits."
    )

@banking_group.command(
    name="view",
    description="View your gang's current credit balance"
)
async def view_credits(interaction: Interaction):
    try:
        _, gang_id = resolve_user_preferences(interaction, require_campaign=True, require_gang=True)
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)
        return

    total = get_current_credits(gang_id)
    gang = get_gang_by_id(gang_id)
    embed = discord.Embed(
        title=f"{gang[3]} Credits",
        description=f"**{total}** credits",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

@banking_group.command(
    name="history",
    description="Show your gang's credit transaction history (paged)"
)
@app_commands.describe(
    page="Which page to view (starting at 1)",
    limit="How many entries per page"
)
async def credit_history(
    interaction: Interaction,
    page: int = 1,
    limit: int = 10
):
    try:
        _, gang_id = resolve_user_preferences(interaction, require_campaign=True, require_gang=True)
    except MissingPreferenceError as e:
        await interaction.response.send_message(str(e), ephemeral=True)
        return

    await interaction.response.send_message(embed=get_credit_history(gang_id, page, limit))

class Banking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Banking(bot))
    bot.tree.add_command(banking_group)
