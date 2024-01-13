import os
import random
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
import triviadb
from dotdict import dotdict

async def load_trivia(name):
    name = name.lower()
    if '/' in name or '..' in name:
        return False
    try:
        with open(f'./trivia/{name}.json') as s:
            data = json.load(s)
        return data
    except:
        return False

class Trivia(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.server = discord.Object(id=config.server)
        self.bot.tree.add_command(self.start, guild=self.server)
        self.bot.tree.add_command(self.stop, guild=self.server)

        self.trivia_started = False
        self.trivia_channel = None
        self.trivia_data = {}
        self.trivia_questions = []
    
    def cog_unload(self):
        self.trivia_loop.stop()
        self.bot.tree.remove_command('start', guild=self.server)
        self.bot.tree.remove_command('stop', guild=self.server)

    @app_commands.command(name='start', description='Start a round of Trivia')
    async def start(self, interaction: discord.Interaction, trivia_name: str):
        if self.trivia_started:
            # if already started do nothing
            await interaction.response.send_message('Trivia already started', ephemeral=True)
            return

        # defer response
        await interaction.response.defer(thinking=True, ephemeral=False)

        # load the trivia json
        trivia_data = await load_trivia(trivia_name)
        if trivia_data:
            # set some necessary values
            self.trivia_started = True
            self.trivia_channel = interaction.channel.id
            self.trivia_data = trivia_data
            self.trivia_questions = self.trivia_data['questions']
            random.shuffle(self.trivia_questions)

        # print info about chosen quiz
        string = f'## {self.trivia_data["name"]}\n\n'
        string += f'by {self.trivia_data["author"]}\n\n'
        string += f'{len(self.trivia_questions)} questions\n\n'
        string += 'Starting...'
        await interaction.edit_original_response(content=string)
        # start loop
        self.trivia_loop.start()

    @app_commands.command(name='stop', description='Stop the currently running Trivia')
    async def stop(self, interaction: discord.Interaction):
        if not self.trivia_started:
            # if not started, do nothing
            await interaction.response.send_message('Trivia is not started', ephemeral=True)
            return

        # defer response
        await interaction.response.defer(thinking=True, ephemeral=False)

        self.trivia_loop.stop()
        self.trivia_data = {}
        self.trivia_started = False
        self.trivia_channel = None

        await interaction.edit_original_response(content='Stopped it, boss')

    @tasks.loop(seconds=10)
    async def trivia_loop(self):
        self.current_question = self.trivia_questions.pop(0)
        q = self.current_question
        channel = self.bot.get_channel(self.trivia_channel)
        answers = [q['answer'], *q['wrong_answers']]
        random.shuffle(answers)

        string = f'{q["question"]}\n\n'
        string += f'a) {answers[0]}\n'
        string += f'b) {answers[1]}\n'
        string += f'c) {answers[2]}\n'
        string += f'd) {answers[3]}'

        await channel.send(string)
