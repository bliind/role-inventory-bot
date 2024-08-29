import os
import random
import json
import datetime
import discord
from discord import app_commands
from discord.ext import commands, tasks
import slotsdb
from dotdict import dotdict

# load the loot table according to the environment
def load_loot_table():
    global loot_table
    file = 'loot_table.json' if env == 'prod' else 'loot_table.test.json'
    with open(file, encoding='utf8') as stream:
        loot_table = json.load(stream)
    loot_table = dotdict(loot_table)

def load_fail_messages():
    global fail_messages
    with open('fail_messages.json', encoding='utf8') as stream:
        fail_messages = json.load(stream)

def load_gamba_cfg():
    global gamba_cfg
    file = 'gamba_cfg.json' if env == 'prod' else 'gamba_cfg.test.json'
    with open(file, encoding='utf8') as stream:
        gamba_cfg = json.load(stream)
    gamba_cfg = dotdict(gamba_cfg)

env = os.getenv('BOT_ENV')
load_loot_table()
load_fail_messages()
load_gamba_cfg()

def lose_roll():
    """creates a losing roll"""
    emotes = gamba_cfg.emotes[:]
    if random.randrange(1,501) == 1:
        emotes.append('✨')
    # pick 2 emotes (might be the same)
    results = [random.choice(emotes) for i in range(2)]
    # remove one of the picked emotes from the list
    emotes.pop(emotes.index(random.choice(results)))
    # add an emote that definitely won't be a third like emote
    results.append(random.choice(emotes))
    return ' | '.join(results)

def timestamp():
    """quick and dirty epoch timestamp"""
    now = datetime.datetime.now()
    return int(round(now.timestamp()))

def seconds_to_time_string(seconds_left):
    """convert an amount of seconds into a minutes and seconds string"""
    minutes = int(seconds_left / 60)
    seconds = int(seconds_left - (minutes*60))
    time_string = ''
    if minutes:
        time_string += f'{minutes} minute{"s" if minutes > 1 else ""}'
    if minutes and seconds:
        time_string += ', '
    if seconds:
        time_string += f'{seconds} second{"s" if seconds > 1 else ""}'

    return time_string

def make_embed(color, description=None):
    """Create a discord embed with standard styling"""
    color = getattr(discord.Color, color)
    embed = discord.Embed(
        color=color(),
        title='Pixel Slots!'
    )
    # embed.set_thumbnail(url='https://media.discordapp.net/attachments/772018609610031104/1193726070474678343/image.png')
    embed.set_thumbnail(url='https://i.imgur.com/AxPqhnq.jpeg')
    if description:
        embed.description = description

    return embed

class Gamba(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.server = discord.Object(id=config.server)
        self.bot.tree.add_command(self.mine, guild=self.server)
        self.bot.tree.add_command(self.scava, guild=self.server)
        self.bot.tree.add_command(self.reload_loot_table, guild=self.server)
        self.bot.tree.add_command(self.reload_fail_messages, guild=self.server)
        self.bot.tree.add_command(self.reload_slots_cfg, guild=self.server)
        self.bot.tree.add_command(self.goose_say, guild=self.server)
        self.bot.tree.add_command(self.check_spins, guild=self.server)
        self.bot.tree.add_command(self.get_stats, guild=self.server)
        # self.check_hot_hour.start()

    async def check_cooldown(self, user):
        # get user last roll from db
        last_roll = await slotsdb.get_last_slot_pull(user.id)
        # if user has no last, give them one 700 seconds ago
        if not last_roll:
            last_roll = {"datestamp": timestamp()-700}

        # lower cooldown for boosters
        cooldown = gamba_cfg.cooldown
        for role in user.roles:
            if role.name == '[Booster]':
                cooldown = gamba_cfg.booster_cooldown
                break

        # # check for hot hour
        hot_hour = await slotsdb.get_hot_hour()
        if hot_hour['active']:
            cooldown = gamba_cfg.hot_hour_cooldown

        # check last spin for the user
        # cooldown, now - then < cooldown
        seconds_left = timestamp() - last_roll['datestamp']
        if (seconds_left < cooldown):
            return (last_roll['datestamp'] + cooldown) - timestamp()

        return 0

    @app_commands.command(name='get_stats', description='Get your PIXEL SLOTS stats')
    async def get_stats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        total = await slotsdb.get_total_pulls(interaction.user.id)
        stats = await slotsdb.get_stats(interaction.user.id)

        content = f'You spun the PIXEL SLOTS {total} times!\n'
        for stat in stats:
            if stat['award'] != 'None':
                plural = 's' if int(stat["count"]) > 1 else ''
                content += f'\nYou won {stat["count"]} {stat["award"]}{plural}!'
        await interaction.edit_original_response(content=content)

    @app_commands.command(name='goose_say', description='Make Goose say something')
    async def goose_say(self, interaction: discord.Interaction, msg: str):
        if interaction.user.id not in [145971157902950401, 126491358239129600]:
            await interaction.response.send_message('Uh, no', ephemeral=True)
        else:
            await interaction.response.defer()
            await interaction.channel.send(msg)
            await interaction.delete_original_response()

    @app_commands.command(name='check_spins', description='See how many times you spun the PIXEL SLOTS!')
    async def check_spins(self, interaction):
        await interaction.response.defer(ephemeral=True)
        total = await slotsdb.get_total_pulls(interaction.user.id)
        await interaction.edit_original_response(content=f'You spun the PIXEL SLOTS {total} times!')

    @app_commands.command(name='reload_loot_table', description='Re-read the loot table')
    async def reload_loot_table(self, interaction):
        load_loot_table()
        await interaction.response.send_message('Reloaded', ephemeral=True)

    @app_commands.command(name='reload_fail_messages', description='Re-read the fail message table')
    async def reload_fail_messages(self, interaction):
        load_fail_messages()
        await interaction.response.send_message('Reloaded', ephemeral=True)

    @app_commands.command(name='reload_slots_cfg', description='Reload the PIXEL SLOTS config')
    async def reload_slots_cfg(self, interaction):
        load_gamba_cfg()
        await interaction.response.send_message('Reloaded', ephemeral=True)

    @app_commands.command(name='mine', description='Open for a chance at a rare role!')
    async def mine(self, interaction):
        return await self.mine_stuff(interaction)

    @app_commands.command(name='scava', description='Apri per un\'opportunità ad un ruolo raro')
    async def scava(self, interaction):
        return await self.mine_stuff(interaction)

    async def mine_stuff(self, interaction):
        # defer response so we don't lag out
        await interaction.response.defer(ephemeral=True)

        # check time left for user
        time_left = await self.check_cooldown(interaction.user)
        if time_left > 0:
            time_string = seconds_to_time_string(time_left)
            await interaction.edit_original_response(content=f'Still cooling down from your last spin!\n\nTry again in {time_string}')
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

        if not award:
            # no win, show only to user who spun
            fail_msgs = fail_messages[:]
            # if interaction.user.id != 78488223046701056:
            #     fail_msgs.append("Sigphale is a better miner than you")

            embed = make_embed('red', f'{lose_roll()}\n\n{random.choice(fail_msgs)}')
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            # won
            win_spin = f'{loot_table[award]["spin"]}'
            embed = make_embed('green', f'{win_spin}\n\nYou won the {award} role!')
            if award == 'GOLDEN JEFF':
                    # rarest reward gets a special message
                    embed.description += ' I didn\'t even know that was possible!!'
            if award == 'Rock':
                # don't show rock public, too common
                embed.description = f'{win_spin}\n\nOh cool, you won a rock.'
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                # everything else show public
                # send to the channel, ping the user
                await interaction.channel.send(interaction.user.mention, embed=embed)
                # delete the deferred response
                await interaction.delete_original_response()

            # oh yeah give the user the role
            await interaction.user.add_roles(discord.Object(id=loot_table[award]['role']))

        # save the timestamp for the cooldown
        await slotsdb.save_slot_pull(interaction.user.id, timestamp(), award)

    async def change_avatar(self, avatar):
        image_file = None
        if avatar == 'base':
            image_file = 'BaseGoose.png'
        if avatar == 'luca':
            image_file = 'LucaGoose.png'
        if image_file:
            with open(image_file, 'rb') as image:
                await self.bot.user.edit(avatar=image.read())

    async def cog_unload(self):
        """this gets called if the cog gets unloaded, remove commands from tree"""
        self.check_hot_hour.stop()
        self.bot.tree.remove_command('mine', guild=self.server)
        self.bot.tree.remove_command('scava', guild=self.server)
        self.bot.tree.remove_command('reload_loot_table', guild=self.server)
        self.bot.tree.remove_command('reload_fail_messages', guild=self.server)
        self.bot.tree.remove_command('reload_slots_cfg', guild=self.server)
        self.bot.tree.remove_command('goose_say', guild=self.server)
        self.bot.tree.remove_command('check_spins', guild=self.server)
        self.bot.tree.remove_command('get_stats', guild=self.server)

    @tasks.loop(minutes=1)
    async def check_hot_hour(self):
        try:
            # hot hour can activate at the beginning of an hour
            # it should remain active until that hour is over
            # has an increasing chance to trigger every hour it doesn't trigger
            hot_hour = dict(await slotsdb.get_hot_hour())
            now = datetime.datetime.now()
            if hot_hour['active'] == 1:
                if hot_hour['hour'] != now.hour:
                    # if hot hour is active but we're not in that hour anymore, turn it off
                    await slotsdb.change_hot_hour(active=0)
                    hot_hour['active'] = 0

                    # change avatar to BaseGoose
                    # await self.change_avatar('base')

            if hot_hour['active'] == 0:
                # if we're not in a checked hour and close to the start of the hour
                if hot_hour['hour'] != now.hour:# and now.minute >= 0 and now.minute <= 10:
                    # and we hit the current chance
                    if random.randrange(1, hot_hour['odds']) == 1:
                        # activate hot hour and send a message to the channel
                        await slotsdb.change_hot_hour(active=1, odds=6)
                        channel = self.bot.get_channel(gamba_cfg.slots_channel)
                        await channel.send(f'# Whoa it\'s getting really **PIXELY** in here\n\n<@&{gamba_cfg.frenzy_alert_role}>')
                        # change avatar to LucaGoose
                        # await self.change_avatar('luca')
                    else:
                        await slotsdb.change_hot_hour(odds=hot_hour['odds'] - 1)

                await slotsdb.change_hot_hour(hour=now.hour)
        except Exception as e:
            print('Error checking hot hour')
            print(e)
