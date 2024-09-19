import discord
from discord import app_commands
from discord.ext import commands
import importlib
import json
import os
import sys
import asyncio
from dotdict import dotdict
from Gamba import Gamba
from RoleInventory import RoleInventory
from EmoteMaker import EmoteMaker

def load_config():
    global config
    config_file = 'config.json' if env == 'prod' else 'config.test.json'
    with open(config_file, encoding='utf8') as stream:
        config = json.load(stream)
    config = dotdict(config)

env = os.getenv('BOT_ENV')
load_config()

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='>', intents=intents)

cogs = ['RoleInventory', 'Gamba', 'EmoteMaker', 'TimedRole', 'Trivia']

async def setup_hook():
    for cog in cogs:
        module = getattr(importlib.import_module(cog), cog)
        await bot.add_cog(module(bot, config))
bot.setup_hook = setup_hook

@bot.event
async def on_ready():
    server = discord.Object(id=config.server)
    bot.tree.add_command(reload_cog, guild=server)
    bot.tree.add_command(reload_config, guild=server)

    await asyncio.sleep(1)
    await bot.tree.sync(guild=server)
    print('Bot ready to go!')

@app_commands.command(name='reload_cog', description='Reload a Cog on the bot')
async def reload_cog(interaction: discord.Interaction, cog: str):
    await interaction.response.defer(ephemeral=True)

    if cog in cogs:
        removed = await bot.remove_cog(cog)
        if not removed:
            await interaction.followup.send(f'Error unloading Cog `{cog}`')
            return

        module = sys.modules[cog]
        importlib.reload(module)
        myclass = getattr(sys.modules[cog], cog)
        await bot.add_cog(myclass(bot, config))

        await asyncio.sleep(1)
        await bot.tree.sync(guild=discord.Object(id=config.server))

        await interaction.followup.send(f'Reloaded `{cog}`')
    else:
        await interaction.followup.send(f'Unknown Cog: {cog}')

@reload_cog.autocomplete('cog')
async def autocomplete_cog(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=cog, value=cog) for cog in cogs if cog.startswith(current)
    ]

@app_commands.command(name='reload_config', description='Reload the bot config')
async def reload_config(interaction):
    load_config()
    await interaction.response.send_message('Reloaded config', ephemeral=True)

bot.run(config.token)
