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
async def load_loot_table():
    global loot_table
    file = 'loot_table.json' if env == 'prod' else 'loot_table.test.json'
    with open(file, encoding='utf8') as stream:
        loot_table = json.load(stream)
    loot_table = dotdict(loot_table)

async def load_fail_messages():
    global fail_messages
    with open('fail_messages.json', encoding='utf8') as stream:
        fail_messages = json.load(stream)

env = os.getenv('BOT_ENV')
load_loot_table()
load_fail_messages()

# cooldown in seconds
gamba_cooldown = 300

# make a losing roll
def lose_roll():
    emotes = ['🍒', '🌈', '🍎', '🍋', '🍍', '🔔', '💎', '💰', '🍀']
    results = []
    while len(set(results)) < 2:
        results = [random.choice(emotes) for i in range(3)]

    return ' | '.join(results)

cooldowns = {}

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
        self.bot.tree.add_command(self.reload_loot_table, guild=self.server)
        self.bot.tree.add_command(self.reload_fail_messages, guild=self.server)
        self.hot_hour = {
            "hour": 0,
            "active": False,
            "odds": 6
        }

    async def get_hot_hour(self):
        return self.hot_hour

    async def change_hot_hour(self, hot_hour):
        for k,v in hot_hour.items():
            self.hot_hour[k] = v

    @app_commands.command(name='reload_loot_table', description='Re-read the loot table')
    async def reload_loot_table(self, interaction):
        await load_loot_table()
        await interaction.response.send_message('Reloaded', ephemeral=True)

    @app_commands.command(name='reload_fail_messages', description='Re-read the fail message table')
    async def reload_fail_messages(self, interaction):
        await load_fail_messages()
        await interaction.response.send_message('Reloaded', ephemeral=True)

    @app_commands.command(name='mine', description='Open for a chance at a rare role!')
    async def mine(self, interaction):
        if interaction.user.id not in cooldowns:
            cooldowns[interaction.user.id] = timestamp()-700

        cooldown = 300
        for role in interaction.user.roles:
            if role.name == '[Booster]':
                cooldown = 180
                break

        hot_hour = await self.get_hot_hour()
        now = datetime.datetime.now()
        if hot_hour['active']:
            if hot_hour['hour'] != now.hour:
                # if hot hour is active but we're not in that hour anymore, turn it off
                await self.change_hot_hour({"active": False})
        else:
            # if we're not in a checked hour and close to the start of the hour
            if hot_hour['hour'] != now.hour and now.minute >= 0 and now.minute <= 10:
                # and we hit the current chance
                if random.randrange(1,hot_hour['odds']) == 1:
                    # activate hot hour and send a message to the channel
                    await self.change_hot_hour({"active": True, "odds": 6})
                    await interaction.channel.send('# Whoa it\'s getting really **ROCKY** in here')
                else:
                    await self.change_hot_hour({"odds": self.hot_hour['odds'] - 1})

            await self.change_hot_hour({"hour": now.hour})

        # if hot hour, 1 minute cooldown for everyone
        if self.hot_hour['active']:
            cooldown = 60

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
            fail_msgs = fail_messages[:]
            if interaction.user.id != 821114303377309696:
                fail_msgs.append("LemonSlayR is a better miner than you")
            embed.description = f'{lose_roll()}\n\n{random.choice(fail_msgs)}'
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
        self.bot.tree.remove_command('reload_loot_table', guild=self.server)
        self.bot.tree.remove_command('reload_fail_messages', guild=self.server)
