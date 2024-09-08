import discord
import json
import os
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

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

def load_cogs():
    current_dir = os.path.dirname(__file__)
    for filename in os.listdir(os.path.join(current_dir, 'cogs')): 
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"Loaded Cog: {filename[:-3]}")

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    load_cogs()
    bot.run(TOKEN)
