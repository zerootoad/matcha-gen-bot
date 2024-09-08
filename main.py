import discord
import json
import os

current_dir = os.path.dirname(__file__)
with open(os.path.join(current_dir, 'settings', 'config.json'), 'r', encoding='utf-8') as f:
    settings = json.load(f)
    
TOKEN = settings['token']
guild_id = settings['guild']

bot = discord.Bot(intents=discord.Intents.all(), debug_guilds=[guild_id], auto_sync_commands=True)

@bot.event
async def on_connect():
    await bot.sync_commands()
    print(f"We have connected as {bot.user} and found {len(bot.all_commands.items())} commands")

if __name__ == '__main__':
    current_dir = os.path.dirname(__file__)
    for filename in os.listdir(os.path.join(current_dir, 'cogs')): 
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"Loaded Cog: {filename[:-3]}")
    
    bot.run(TOKEN)
