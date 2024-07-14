import os
import random
import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
from dotdict import dotdict
from SurveyView import SurveyView
import SurveyDatabase as db

def timestamp():
    now = datetime.datetime.now()
    return int(round(now.timestamp()))

def humantime(timestamp):
    date = datetime.datetime.fromtimestamp(timestamp)
    return date.strftime('%Y-%m-%d %H:%M:%S')

class Survey(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.server = discord.Object(id=config.server)
        self.bot.tree.add_command(self.create_survey, guild=self.server)
        self.bot.tree.add_command(self.last_survey_results, guild=self.server)

    def cog_unload(self):
        self.bot.tree.remove_command('create_survey', guild=self.server)
        self.bot.tree.remove_command('last_survey_results', guild=self.server)

    def make_embed(self, color, description=None, title=None):
        # get the color function
        color = getattr(discord.Color, color)

        # make the embed
        embed = discord.Embed(
            color=color(),
            timestamp=datetime.datetime.now(),
            title=title,
            description=description
        )

        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        latest = await db.get_latest_survey()
        if latest:
            view = SurveyView(timeout=None, channel_id=latest['channel_id'])
            view.message_id = latest['message_id']
            self.bot.add_view(view, message_id=latest['message_id'])

    @app_commands.command(name='create_survey', description='Create a satisfaction survey')
    async def create_survey(self, interaction: discord.Interaction):
        # defer response
        await interaction.response.defer(ephemeral=True)
        await interaction.delete_original_response()

        description = '# Overall, how satisfied are you with MARVEL SNAP?\n\n'
        description += '😍  Very Satisfied\n\n'
        description += '🙂  Somewhat Satisfied\n\n'
        description += '😐  Neither Satisfied Nor Dissatisfied\n\n'
        description += '🙁  Somewhat Dissatisfied\n\n'
        description += '😣  Very Dissatisfied\n\n'
        embed = self.make_embed('blue', description=description)

        view = SurveyView(timeout=None, channel_id=interaction.channel.id)
        survey_msg = await interaction.channel.send(embed=embed, view=view)
        view.message_id = survey_msg.id

        await db.create_survey(timestamp(), interaction.channel.id, survey_msg.id, 0)

        # update buttons to disabled when finished
        await view.wait()
        for child in view.children:
            child.disabled = True
        await survey_msg.edit(embed=embed, view=view)

    @app_commands.command(name='last_survey_results', description='Get the results for the most recent survey')
    async def last_survey_results(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        latest = await db.get_latest_survey()
        if not latest: return

        message = f'Latest survey posted <t:{latest["datestamp"]}>:\n\n'

        results = await db.get_results(latest['channel_id'], latest['message_id'])

        responses = {
            'Very Satisfied': 0,
            'Somewhat Satisfied': 0,
            'Neither': 0,
            'Somewhat Dissatisfied': 0,
            'Very Dissatisfied': 0,
        }
        for result in results:
            responses[result['response']] = result['count']

        message += '```\n'
        for response, count in responses.items():
            message += f'{(response + ':').ljust(22)} {count}\n'
        message += '```'

        embed = self.make_embed('blurple', message, 'Survey Results')

        await interaction.edit_original_response(embed=embed)
