import os
import random
import json
import datetime
import discord
from discord import app_commands
from discord.ext import commands
import db
from dotdict import dotdict

# load the loot table according to the environment
env = os.getenv('BOT_ENV')
file = 'loot_table.json' if env == 'prod' else 'loot_table.test.json'
with open(file, encoding='utf8') as stream:
    loot_table = json.load(stream)
loot_table = dotdict(loot_table)

# cooldown in seconds
gamba_cooldown = 300

# make a losing roll
def lose_roll():
    emotes = ['🍒', '🌈', '🍎', '🍋', '🍍', '🔔', '💎', '💰', '🍀']
    result_str = '🍒 | 🍒 | 🍒'
    while result_str[0] == result_str[4] and result_str[4] == result_str[8]:
        result_str = ' | '.join(random.choice(emotes) for i in range(3))

    return result_str

fail_messages = [
    "Better luck next time!",
    "Have you tried spinning better?",
    "Skill issue.",
    "Is this your first time mining?"
]

cooldowns = {}

hot_hour = {
    "hour": 0,
    "active": False
}

# quick and dirty epoch timestamp
def timestamp():
    now = datetime.datetime.now()
    return int(round(now.timestamp()))

class Gamba(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.server = discord.Object(id=config.server)
        self.bot.tree.add_command(self.mine, guild=self.server)

    @app_commands.command(name='mine', description='Open for a chance at a rare role!')
    async def mine(self, interaction):
        if interaction.user.id not in cooldowns:
            cooldowns[interaction.user.id] = timestamp()-700

        cooldown = 300
        for role in interaction.user.roles:
            if role.name == '[Booster]':
                cooldown = 180
                break

        now = datetime.datetime.now()
        if hot_hour['active']:
            if hot_hour['hour'] != now.hour:
                # if hot hour is active but we're not in that hour anymore, turn it off
                hot_hour['active'] = False
        else:
            # if we're not in a checked hour and close to the start of the hour
            if hot_hour['hour'] != now.hour and now.minute >= 0 and now.minute <= 10:
                # and we hit a 10% chance
                if random.randrange(1,6) == 1:
                    # activate hot hour and send a message to the channel
                    hot_hour['active'] = True
                    await interaction.channel.send('# Whoa it\'s getting really **ROCKY** in here')

            hot_hour['hour'] = now.hour


        # if hot hour, 1 minute cooldown for everyone
        if hot_hour['active']:
            cooldown = 60

        # debug
        if interaction.guild.id == 479676054546546730:
            cooldown = 0

        # check last spin for the user
        # cooldown, now - then < cooldown
        seconds_left = timestamp() - cooldowns[interaction.user.id]
        if (seconds_left < cooldown):
            # count down how much time left till it's up
            s_l = (cooldowns[interaction.user.id] + cooldown) - timestamp()
            minutes = int(s_l / 60)
            seconds = int(s_l - (minutes*60))
            time_string = ''
            if minutes:
                time_string += f'{minutes} minute{"s" if minutes > 1 else ""}'
            if minutes and seconds:
                time_string += ', '
            if seconds:
                time_string += f'{seconds} second{"s" if seconds > 1 else ""}'

            await interaction.response.send_message(f'Still cooling down from your last spin!\n\nTry again in {time_string}', ephemeral=True)
            return

        # roll a random number,
        # loop through the loot table and find the rarest reward hit
        award = None
        smol_first = sorted(loot_table.items(), key=lambda x:x[1]['chance'], reverse=True)
        for loot in smol_first:
            roll = random.randrange(1, loot[1]['chance']+1)
            if roll == 1:
                award = loot[0]
                break

        # save the timestamp for the cooldown
        cooldowns[interaction.user.id] = timestamp()

        # Create a pretty embed
        embed = discord.Embed(
            color=discord.Color.blue(),
            title='Rock Slots!'
        )
        # embed.set_footer(text=roll) # for debug to show the roll
        # fancy thumbnail to look nice
        embed.set_thumbnail(url='https://media.discordapp.net/attachments/772018609610031104/1193726070474678343/image.png')

        if not award:
            # no win, show only to user who spun
            embed.description = f'{lose_roll()}\n\n{random.choice(fail_messages)}'
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            # won, show publicly
            embed.description = f'{loot_table[award]["spin"]}\n\nYou won the {award} role!'
            if award == 'GOLDEN JEFF':
                # rarest spin gets a different message
                embed.description += f' I didn\'t even know that was possible!!'
            if award == 'Rock':
                embed.description = f'{loot_table[award]["spin"]}\n\nOh cool, you won a rock.'
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed)

            # oh yeah give the user the role
            await interaction.user.add_roles(discord.Object(id=loot_table[award]['role']))

    async def cog_unload(self):
        """this gets called if the cog gets unloaded, remove commands from tree"""
        self.bot.tree.remove_command('mine', guild=self.server)
