import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db.__init__ import init_db
from cogs.admin import Admin, admin_group
from cogs.dice import Dice, dice_group
from cogs.campaigns import Campaigns, campaign_group
from cogs.gangs import Gangs, gang_group
from cogs.banking import Banking, banking_group
from cogs.assets import Assets, asset_group
from cogs.marketplace import Marketplace, marketplace_group
from cogs.user_preferences import UserPreferences, profile_group

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    try:
        await bot.add_cog(UserPreferences(bot))
        bot.tree.add_command(profile_group)
        await bot.add_cog(Campaigns(bot))
        bot.tree.add_command(campaign_group)
        await bot.add_cog(Gangs(bot))
        bot.tree.add_command(gang_group)
        await bot.add_cog(Dice(bot))
        bot.tree.add_command(dice_group)
        await bot.add_cog(Admin(bot))
        bot.tree.add_command(admin_group)
        await bot.add_cog(Banking(bot))
        bot.tree.add_command(banking_group)
        await bot.add_cog(Assets(bot))
        bot.tree.add_command(asset_group)
        await bot.add_cog(Marketplace(bot))
        bot.tree.add_command(marketplace_group)
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands.')
    except Exception as e:
        print(f'Error syncing commands: {e}')

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

if __name__ == '__main__':
    load_dotenv()
    init_db()
    bot.owner_id = int(os.getenv("BOT_OWNER_ID"))
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))