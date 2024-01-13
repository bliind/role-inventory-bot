import os
import random
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
import triviadb
from dotdict import dotdict

async def load_trivia(name):
    if '/' in name or '..' in name:
        return False
    with open('./trivia/{name}.json') as s:
        data = json.load(s)
    return data

class Trivia(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.server = discord.Object(id=config.server)
        self.trivia_started = False
        self.trivia_data = []
        self.bot.tree.add_command(self.start, guild=self.server)

    @app_commands.command(name='start', description='Start a round of Trivia')
    async def start(self, interaction: discord.Interaction, trivia_name: str):
        if self.trivia_started:
            await interaction.response.send_message('Trivia already started', ephemeral=True)
            return

        trivia_data = await load_trivia(trivia_name)
        if trivia_data:
            self.trivia_data = trivia_data
            self.trivia_started = True
