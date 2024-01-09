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
BROKEN_PICKAXE_COOLDOWN = 3600

# pickaxe break chance (1/x)
pickaxe_break_chance = 1000

# make a losing roll
def lose_roll():
    emotes = ['🍒', '🌈', '🍎', '🍋', '🍍', '🔔', '💎', '💰', '🍀']
    result_str = '🍒 | 🍒 | 🍒'
    while result_str[0] == result_str[4] and result_str[4] == result_str[8]:
        result_str = ' | '.join(random.choice(emotes) for i in range(3))

    return result_str

fail_messages = [
    "Better luck next time!",
    "That's rough, buddy.",
    "Not this time!",
    "Well, you have to try again.",
    "Have you tried spinning better?",
    "Skill issue.",
    "Is this your first time mining?",
    "LemonSlayR is a better miner than you",
    "Unions decrease odds of winning big",
    "Imagine not winning",
    "You obviously never played DRG",
    "Rocks are for winners",
    "Your pay is getting docked for how bad that one was.",
    "L",
    "Maybe you should have cooled down a bit longer"
]

cooldowns = {}

hot_hour = {
    "hour": 0,
    "active": False,
    "odds": 6
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
        
        now = datetime.datetime.now()
        if hot_hour['active']:
            if hot_hour['hour'] != now.hour:
                # if hot hour is active but we're not in that hour anymore, turn it off
                hot_hour['active'] = False
        else:
            # if we're not in a checked hour and close to the start of the hour
            if hot_hour['hour'] != now.hour and now.minute >= 0 and now.minute <= 10:
                # and we hit the current chance
                if random.randrange(1,hot_hour['odds']) == 1:
                    # activate hot hour and send a message to the channel
                    hot_hour['active'] = True
                    hot_hour['odds'] = 6
                    await interaction.channel.send('# Whoa it\'s getting really **ROCKY** in here')
                else:
                    hot_hour['odds'] -= 1

            hot_hour['hour'] = now.hour


        if interaction.user.id not in cooldowns:
            cooldowns[interaction.user.id]["last_roll"] = timestamp()-700


        if hot_hour['active']: # if hot hour, 1 minute cooldown for everyone
            cooldown = 60
        elif cooldowns[interaction.user.id]["pickaxe_state"] == True: # if the user's pickaxe is broken, 3600 second (1 hour) cooldown
            cooldown = BROKEN_PICKAXE_COOLDOWN
        else: # else, standard cooldown timer
            cooldown = 300
            for role in interaction.user.roles:
                if role.name == '[Booster]':
                    cooldown = 180
                    break

        # check last spin for the user
        # cooldown, now - then < cooldown
        seconds_left = timestamp() - cooldowns[interaction.user.id]["last_roll"]
        if (seconds_left < cooldown):
            # count down how much time left till it's up
            s_l = (cooldowns[interaction.user.id]["last_roll"] + cooldown) - timestamp()
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

        # save the timestamp for the cooldown and pickaxe state
        is_pickaxe_broken = (random.randrange(1, pickaxe_break_chance) == 1)
        cooldowns[interaction.user.id] = {"last_roll": timestamp(), "pickaxe_state": is_pickaxe_broken}

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
            if is_pickaxe_broken:
                embed.description += (f'\nYour pickaxe broke 🤦 You have to wait %d seconds for a new one to be delivered.') % BROKEN_PICKAXE_COOLDOWN
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
