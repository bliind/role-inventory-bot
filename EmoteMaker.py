import discord
import requests
import uuid
import subprocess
import os
import glob
import time
from discord import app_commands
from discord.ext import commands

def get_member_image(member):
    try:
        if member.guild_avatar:
            return member.guild_avatar.url
    except: pass
    try:
        if member.display_avatar:
            return member.display_avatar.url
    except: pass
    try:
        return member.avatar.url
    except:
        return None

class EmoteMaker(commands.Cog):
    def __init__(self, bot, config):
        # assign for use in the methods
        self.bot = bot
        self.config = config
        self.server = discord.Object(id=config.server)

        # add the commands to the tree
        self.bot.tree.add_command(self.make_emote, guild=self.server)

    async def cog_unload(self):
        """this gets called when the cog is unloaded, remove the commands from the tree"""
        self.bot.tree.remove_command('make_emote', guild=self.server)

    @app_commands.command(name='make_emote', description='Make an emote of someone\'s avatar')
    async def make_emote(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)

        # get avatar url
        image_url = get_member_image(member)

        # create a random filename
        the_uuid = uuid.uuid4()
        filename = f'{the_uuid}.png'

        # download the image
        img_data = requests.get(image_url).content
        with open(filename, 'wb') as handler:
            handler.write(img_data)

        # resize image
        subprocess.run(['/usr/bin/mogrify', '-resize', '128x128!', filename])

        # if it was a gif it resized into a whole bunch of frames
        # we want frame 0, the rest can be deleted
        bad_filename = filename.replace('.png', '-0.png')
        if os.path.isfile(bad_filename):
            os.rename(bad_filename, filename)
            for extra in glob.glob(f'{the_uuid}-*.png'):
                os.remove(extra)

        # apply circle thingie
        newfilename = f'circle_{filename}'
        subprocess.run([
            '/usr/bin/convert',
            filename,
            '(',
            '+clone',
            '-alpha',
            'transparent',
            '-draw',
            'circle 64,64 20,20',
            ')',
            '-compose',
            'copyopacity',
            '-composite',
            newfilename
        ])

        # send new file to user
        await interaction.followup.send(file=discord.File(newfilename))

        os.remove(filename)
        os.remove(newfilename)
