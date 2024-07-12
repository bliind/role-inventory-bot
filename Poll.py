import os
import random
import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
from dotdict import dotdict
from PollView import PollView

def timestamp():
    now = datetime.datetime.now()
    return int(round(now.timestamp()))

scores = {}

class Poll(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.server = discord.Object(id=config.server)
        self.bot.tree.add_command(self.create_poll, guild=self.server)

    def cog_unload(self):
        self.bot.tree.remove_command('create_poll', guild=self.server)

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

        # make the embed bigger?
        embed.set_image(url='https://cdn.discordapp.com/attachments/1139650618907185262/1195909270282186762/transparent_bar.png')

        return embed

    @app_commands.command(name='create_poll', description='Create a community poll')
    async def create_poll(self, interaction: discord.Interaction):
        # defer response
        await interaction.response.send_message('Creating poll', ephemeral=True)
        await interaction.delete_original_response()

        description = '# Overall, how satisfied are you with MARVEL SNAP?\n\n'
        description += '😍  Very Satisfied\n\n'
        description += '🙂  Somewhat Satisfied\n\n'
        description += '😐  Neither Satisfied Nor Dissatisfied\n\n'
        description += '🙁  Somewhat Dissatisfied\n\n'
        description += '😣  Very Dissatisfied\n\n'
        embed = self.make_embed('blue', description=description)

        view = PollView(timeout=None)
        poll_msg = await interaction.channel.send(embed=embed, view=view)

        # update buttons to disabled when finished
        await view.wait()
        for child in view.children:
            child.disabled = True
        await poll_msg.edit(embed=embed, view=view)
