import discord
from discord.ext import commands
from discord import app_commands
import random
import re
import ast
import operator
from typing import TypedDict, List, Union, Optional

class RollResultSuccess(TypedDict):
    original: str
    parsed: str
    rolls: List[str]
    total: float

class RollResultError(TypedDict):
    original: str
    parsed: str
    rolls: List[str]
    total: float
    error: str

RollResult = Union[RollResultSuccess, RollResultError]

class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='roll')
    async def roll_text(self, ctx, *, formula: str):
        result = self.roll_formula(formula)
        await ctx.send(embed=self.format_rolls_embed([result]))

# Define as slash command separately
@app_commands.command(name="roll", description="Roll dice using standard notation (e.g., 2d6+3)")
async def roll_slash(interaction: discord.Interaction, formula: str):
    result = Dice.roll_formula(formula)
    await interaction.response.send_message(embed=Dice.format_rolls_embed([result]))

# Slash command group (optional if more dice commands are added later)
dice_group = app_commands.Group(name="dice", description="Dice rolling commands")
dice_group.add_command(roll_slash)

# Static method for shared formula logic
@staticmethod
def roll_formula_static(formula: str) -> RollResult:
    rolls_log = []

    def roll_dice(match):
        num = int(match.group(1)) if match.group(1) else 1
        sides = int(match.group(2))
        rolls = [random.randint(1, sides) for _ in range(num)]
        rolls_log.append(f"{num}d{sides}: {rolls}")
        return f"({'+'.join(map(str, rolls))})"

    formula = formula.lower().replace(" ", "").replace("x", "*")
    parsed_formula = re.sub(r"(\d*)d(\d+)", roll_dice, formula)

    try:
        node = ast.parse(parsed_formula, mode='eval')

        def eval_expr(expr):
            if isinstance(expr, ast.Expression):
                return eval_expr(expr.body)
            elif isinstance(expr, ast.BinOp):
                left = eval_expr(expr.left)
                right = eval_expr(expr.right)
                ops = {
                    ast.Add: operator.add,
                    ast.Sub: operator.sub,
                    ast.Mult: operator.mul,
                    ast.Div: operator.truediv,
                }
                return ops[type(expr.op)](left, right)
            elif isinstance(expr, ast.Num):
                return expr.n
            elif isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
                return -eval_expr(expr.operand)
            else:
                raise ValueError("Unsupported operation")

        total = eval_expr(node)
        return {
            "original": formula,
            "parsed": parsed_formula,
            "rolls": rolls_log,
            "total": total
        }

    except Exception as e:
        return {
            "original": formula,
            "parsed": "",
            "rolls": [],
            "total": 0,
            "error": str(e)
        }

@staticmethod
def format_rolls_embed(results: List[RollResult]) -> discord.Embed:
    embed = discord.Embed(
        title="Dice Roll Results",
        color=discord.Color.purple()
    )

    for i, result in enumerate(results):
        if "error" in result:
            embed.add_field(
                name=f"Roll {i+1}: {result['original']}",
                value=f"❌ Error: {result['error']}",
                inline=False
            )
        else:
            rolls = "\n".join(result["rolls"])
            embed.add_field(
                name=f"Roll {i+1}: {result['original']}",
                value=(
                    f"**Parsed Expression:** `{result['parsed']}`\n"
                    f"**Rolls:**\n{rolls}\n"
                    f"**Total:** {result['total']:.2f}"
                ),
                inline=False
            )

    return embed

# Bind the static method to class for text command use
Dice.roll_formula = staticmethod(roll_formula_static)
Dice.format_rolls_embed = staticmethod(format_rolls_embed)

def setup(bot):
    bot.add_cog(Dice(bot))
    bot.tree.add_command(dice_group)