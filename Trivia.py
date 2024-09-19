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
from TriviaView import TriviaView

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

def timestamp():
    now = datetime.datetime.now()
    return int(round(now.timestamp()))

scores = {}
scores_chunk = 25
round_timer = 10

class Trivia(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.server = discord.Object(id=config.server)
        self.bot.tree.add_command(self.start_trivia, guild=self.server)
        self.bot.tree.add_command(self.stop_trivia, guild=self.server)

        self.trivia_started = False
        self.trivia_channel = None
        self.trivia_data = {}
        self.trivia_questions = []
        self.current_question = None

    def cog_unload(self):
        self.trivia_loop.cancel()
        self.bot.tree.remove_command('start_trivia', guild=self.server)
        self.bot.tree.remove_command('stop_trivia', guild=self.server)

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

        # make the embed bigger with 512x4 mostly transparent bar
        embed.set_image(url='https://i.imgur.com/OLsuQKm.png')

        if 'icon' in self.trivia_data:
            # if the quiz has an icon, use it
            embed.set_thumbnail(url=self.trivia_data['icon'])

        return embed

    async def change_current_question(self, question):
        self.current_question = question

    @app_commands.command(name='start_trivia', description='Start a round of Trivia')
    @app_commands.describe(quiz_name='The name of the quiz to start')
    async def start_trivia(self, interaction: discord.Interaction, quiz_name: str):
        if self.trivia_started:
            # if already started do nothing
            await interaction.response.send_message('Trivia already started', ephemeral=True)
            return

        # defer response
        await interaction.response.defer(thinking=True, ephemeral=False)

        # load the trivia json
        trivia_data = await load_trivia(quiz_name)
        if trivia_data:
            # set some necessary values
            self.trivia_started = True
            self.trivia_channel = interaction.channel.id
            self.trivia_data = trivia_data
            self.trivia_questions = self.trivia_data['questions'][:]
            random.shuffle(self.trivia_questions)

        # print info about chosen quiz
        string = f'# {self.trivia_data["name"]}\n'
        string += f'## by {self.trivia_data["author"]}\n\n'
        string += f'### {len(self.trivia_questions)} questions total\n\n'
        string += f'### __Starts in {round_timer} seconds__'
        embed = self.make_embed('blurple', description=string, title='Starting Quiz')
        await interaction.edit_original_response(embed=embed)

        # start loop
        self.last_question_ts = timestamp()
        # manually loop every second because @loop was NOT reliable
        while self.trivia_started:
            await self.trivia_loop()
            await asyncio.sleep(1)

    @start_trivia.autocomplete('quiz_name')
    async def autocomplete_quiz_name(self, interaction: discord.Interaction, current: str):
        quiz_names = [f[:-5] for f in os.listdir('./trivia') if f.endswith('.json')]

        return [
            app_commands.Choice(name=quiz_name, value=quiz_name) for quiz_name in quiz_names if quiz_name.startswith(current)
        ]

    @app_commands.command(name='stop_trivia', description='Stop the currently running Trivia')
    async def stop_trivia(self, interaction: discord.Interaction):
        # reset all variables no matter what so stop can be a clean slate
        self.trivia_data = {}
        self.trivia_started = False
        self.trivia_channel = None
        self.current_question = None
        global scores
        scores = {}

        if not self.trivia_started:
            # if not started, do nothing
            embed = discord.Embed(color=discord.Color.yellow(), description='Trivia is not started')
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        string = f'Stopping {self.trivia_data["name"]}'
        embed = discord.Embed(color=discord.Color.yellow(), description=string)
        await interaction.response.send_message(embed=embed)

    async def send_scores(self, final=False):
        if len(list(scores.items())) == 0:
            return

        # sort by most points
        sorted_scores = sorted(scores.items(), key=lambda x:x[1], reverse=True)

        msg = f'## Current Scores\n\n'
        # show only top 25 normally
        display_scores = sorted_scores
        count = len(sorted_scores)
        if count > scores_chunk:
            display_scores = sorted_scores[0:scores_chunk]
            msg = f'## Current Scores (Top {scores_chunk})\n\n'

        if final:
            msg = '## Final Scores\n\n'

        # loop through the scores
        for i, score in enumerate(display_scores):
            msg += f'{i+1}) <@{score[0]}> - {score[1]}\n'

        score_embed = self.make_embed('teal', description=msg)
        channel = self.bot.get_channel(self.trivia_channel)
        await channel.send(embed=score_embed)

        # send the rest of the scores for final
        if not final:
            return
        for chunk in range(scores_chunk, count, scores_chunk):
            description = '## Final Scores Continued'
            for i, score in enumerate(sorted_scores[chunk:chunk+scores_chunk]):
                description += f'{i+chunk+1}) <@{score[0]}> - {score[1]}\n'
            score_embed = self.make_embed('teal', description=description)
            channel = self.bot.get_channel(self.trivia_channel)
            await channel.send(embed=score_embed)

    async def trivia_loop(self):
        # check 10 seconds passed from last question
        if timestamp() - self.last_question_ts < round_timer:
            return

        # get channel for sending messages
        channel = self.bot.get_channel(self.trivia_channel)

        if self.current_question:
            # show results for last question
            last_q = '## Time\'s up!\n\n'
            last_q += f'## The correct answer was: **{self.current_question["answer"]}**\n\n'
            last_q += f'### Next question in {round_timer} seconds..'
            embed = self.make_embed('green', description=last_q)
            await channel.send(embed=embed)
            self.last_question_ts = timestamp()

            # no more questions, end quiz
            final = len(self.trivia_questions) == 0
            if final:
                # end quiz
                embed = self.make_embed('blurple', description='# Quiz over!\n\n## Thanks for playing!')
                await channel.send(embed=embed)

            # show scores
            await self.send_scores(final=final)

            # reset all variables if final
            if final:
                self.trivia_data = {}
                self.trivia_started = False
                self.trivia_channel = None
                self.current_question = None
                global scores
                scores = {}

            # do the next question on the next loop
            self.current_question = None
            return

        # next question
        self.current_question = self.trivia_questions.pop(0)
        answers = [self.current_question['answer'], *self.current_question['wrong_answers']]
        random.shuffle(answers)

        # create the question/answer string
        this_q = f'## {self.current_question["question"]}\n\n'
        this_q += f'### :regional_indicator_a:) **{answers[0]}**\n'
        this_q += f'### :regional_indicator_b:) **{answers[1]}**\n'
        this_q += f'### :regional_indicator_c:) **{answers[2]}**\n'
        this_q += f'### :regional_indicator_d:) **{answers[3]}**'

        # create the embed
        embed = self.make_embed('yellow', description=this_q)

        # get question count for.. footer?
        total_questions = len(self.trivia_data['questions'])
        questions_left = len(self.trivia_questions)
        question_number = total_questions - questions_left
        embed.set_footer(text=f'Question {question_number} out of {total_questions}')

        # create the view
        letters = ['A','B','C','D']
        correct = letters[answers.index(self.current_question['answer'])]
        view = TriviaView(timeout=round_timer, scores=scores, correct=correct, ts=timestamp())
        question_msg = await channel.send(embed=embed, view=view)
        self.last_question_ts = timestamp()

        # update buttons to disabled when finished
        await view.wait()
        for child in view.children:
            child.disabled = True
        await question_msg.edit(embed=embed, view=view)

