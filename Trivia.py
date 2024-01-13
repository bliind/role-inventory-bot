import os
import random
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
import asyncio
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
        self.current_question = None

    def cog_unload(self):
        self.trivia_loop.stop()
        self.bot.tree.remove_command('start', guild=self.server)
        self.bot.tree.remove_command('stop', guild=self.server)

    def make_embed(self, color, description=None, title=None):
        # get the color function
        color = getattr(discord.Color, color)

        if title == None and 'name' in self.trivia_data:
            # set title to quiz name if available
            title = self.trivia_data['name']

        # make the embed
        embed = discord.Embed(
            color=color(),
            timestamp=datetime.datetime.now(),
            title=title,
            description=description
        )

        if 'icon' in self.trivia_data:
            # if the quiz has an icon, use it
            embed.set_thumbnail(url=self.trivia_data['icon'])

        return embed

    async def change_current_question(self, question):
        self.current_question = question

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
        embed = self.make_embed('blurple', description=string, title='Starting Quiz')
        await interaction.edit_original_response(embed=embed)

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

        string = f'Stopping {self.trivia_data["name"]}'
        self.trivia_loop.cancel()
        self.trivia_data = {}
        self.trivia_started = False
        self.trivia_channel = None
        self.current_question = None

        await interaction.edit_original_response(content=f'Stopping: {string}')

    @tasks.loop(seconds=30)
    async def trivia_loop(self):
        # first loop skip to give some time
        if self.trivia_loop.current_loop == 0:
            return

        # get channel for sending messages
        channel = self.bot.get_channel(self.trivia_channel)

        if self.current_question:
            # show results for last question
            last_q = '## Time\'s up!\n\n'
            last_q += f'The correct answer was: {self.current_question["answer"]}\n\n'
            last_q += 'Next question in 30 seconds..'
            embed = self.make_embed('green', description=last_q)
            await channel.send(embed=embed)

            # do the next question on the next loop
            self.current_question = None
            return

        # todo: show current scores

        if len(self.trivia_questions) == 0:
            # end quiz
            embed = self.make_embed('blurple', description='Quiz over!\n\nThanks for playing')
            await channel.send(embed=embed)
            # todo: final scores
            self.trivia_loop.cancel()
            return

        # next question
        self.current_question = self.trivia_questions.pop(0)
        answers = [self.current_question['answer'], *self.current_question['wrong_answers']]
        random.shuffle(answers)

        # create the question/answer string
        this_q = f'{self.current_question["question"]}\n\n'
        this_q += f'a) {answers[0]}\n'
        this_q += f'b) {answers[1]}\n'
        this_q += f'c) {answers[2]}\n'
        this_q += f'd) {answers[3]}'

        # create the embed
        embed = self.make_embed('yellow', description=this_q)

        await channel.send(embed=embed)
