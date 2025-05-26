import discord
from discord.ext import commands
from discord import app_commands
import random
import re

class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='roll')
    async def roll_text(self, ctx, *, formula: str):
        result = self.roll_formula(formula)
        await ctx.send(result)

# Define as slash command separately
@app_commands.command(name="roll", description="Roll dice using standard notation (e.g., 2d6+3)")
async def roll_slash(interaction: discord.Interaction, formula: str):
    result = Dice.roll_formula_static(formula)
    await interaction.response.send_message(result)

# Slash command group (optional if more dice commands are added later)
dice_group = app_commands.Group(name="dice", description="Dice rolling commands")
dice_group.add_command(roll_slash)

# Static method for shared formula logic
@staticmethod
def roll_formula_static(formula: str) -> str:
    pattern = re.compile(r"(\d*)d(\d+)([+-]?\d*)")
    match = pattern.fullmatch(formula.replace(" ", ""))
    if not match:
        return "Invalid dice formula. Use format NdM+K, e.g., 2d6+3"

    num_dice = int(match.group(1)) if match.group(1) else 1
    die_sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    rolls = [random.randint(1, die_sides) for _ in range(num_dice)]
    total = sum(rolls) + modifier
    breakdown = f"Rolls: {rolls}, Modifier: {modifier}, Total: {total}"
    return breakdown

# Bind the static method to class for text command use
Dice.roll_formula = staticmethod(roll_formula_static)

def setup(bot):
    bot.add_cog(Dice(bot))
    bot.tree.add_command(dice_group)