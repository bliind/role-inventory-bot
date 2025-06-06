import os
import random
import json
import datetime
import discord
import math
from discord import app_commands
from discord.ext import commands, tasks
import slotsdb
from dotdict import dotdict
from FrenzyRoleView import FrenzyRoleView
from UpgradeView import UpgradeView

# load the loot table according to the environment
def load_loot_table():
    global loot_table
    file = 'loot_table.json' if env == 'prod' else 'loot_table.test.json'
    with open(file, encoding='utf8') as stream:
        loot_table = json.load(stream)
    loot_table = dotdict(loot_table)

def load_upgrade_table():
    global upgrade_table
    file = 'upgrade_table.json' if env == 'prod' else 'upgrade_table.json'
    with open(file, encoding='utf8') as stream:
        upgrade_table = json.load(stream)
    upgrade_table = dotdict(upgrade_table)

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
load_upgrade_table()
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
        title='Rock Slots!'
    )
    embed.set_thumbnail(url='https://i.imgur.com/WkeREMF.png')
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
        self.bot.tree.add_command(self.reload_upgrade_table, guild=self.server)
        self.bot.tree.add_command(self.reload_fail_messages, guild=self.server)
        self.bot.tree.add_command(self.reload_slots_cfg, guild=self.server)
        self.bot.tree.add_command(self.goose_say, guild=self.server)
        self.bot.tree.add_command(self.check_spins, guild=self.server)
        self.bot.tree.add_command(self.get_stats, guild=self.server)
        self.bot.tree.add_command(self.hot_hour, guild=self.server)
        self.bot.tree.add_command(self.frenzy_role_message, guild=self.server)
        self.bot.tree.add_command(self.rock_wallet, guild=self.server)
        self.bot.tree.add_command(self.rock_upgrade, guild=self.server)
        # self.check_hot_hour.start()

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            view = FrenzyRoleView(frenzy_role_id=gamba_cfg.frenzy_alert_role, timeout=None)
            self.bot.add_view(view)
        except Exception as e:
            print('Initializing view failed:', e)

    async def check_cooldown(self, user):
        # get user last roll from db
        last_roll = await slotsdb.get_last_slot_pull(user.id)
        # if user has no last, give them one 700 seconds ago
        if not last_roll:
            last_roll = {"datestamp": timestamp()-700}

        # lower cooldown for boosters
        cooldown = gamba_cfg.cooldown
        for role in user.roles:
            if role.id == gamba_cfg.booster_role_id:
                cooldown = gamba_cfg.booster_cooldown
                break

        # check for hot hour
        hot_hour = await slotsdb.get_hot_hour()
        if hot_hour['active']:
            cooldown = gamba_cfg.hot_hour_cooldown

        # check for pickaxe roles (reduced cooldown)
        for role in user.roles:
            role_name = role.name.lower()
            if 'pickaxe' in role_name:
                if 'bronze' in role_name:
                    cooldown -= cooldown * .1
                if 'iron' in role_name:
                    cooldown -= cooldown * .2
                if 'diamond' in role_name:
                    cooldown -= cooldown * .3

        cooldown = math.ceil(cooldown)

        # check last spin for the user
        # cooldown, now - then < cooldown
        seconds_left = timestamp() - last_roll['datestamp']
        seconds_to_add = 2
        if (seconds_left < cooldown):
            # add a small amount of seconds to the cooldown to combat command spamming
            await slotsdb.update_slot_pull(last_roll['id'], last_roll['datestamp'] + seconds_to_add)
            return (last_roll['datestamp'] + seconds_to_add + cooldown) - timestamp()

        return 0

    @app_commands.command(name='hot_hour', description='Start or stop the hot hour loop')
    async def hot_hour(self, interaction: discord.Interaction, action: str):
        await interaction.response.defer(ephemeral=True)
        if action == 'start':
            self.check_hot_hour.start()
            message = 'Started Hot Hour Loop'
        elif action == 'stop':
            self.check_hot_hour.stop()
            message = 'Stopped Hot Hour Loop'
        else:
            message = f'Action "{action}" unknown'

        embed = discord.Embed(description=message)
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name='get_stats', description='Get your ROCK SLOTS stats')
    async def get_stats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        total = await slotsdb.get_total_pulls(interaction.user.id)
        stats = await slotsdb.get_stats(interaction.user.id)

        content = f'You spun the ROCK SLOTS {total} times!\n'
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

    @app_commands.command(name='check_spins', description='See how many times you spun the ROCK SLOTS!')
    async def check_spins(self, interaction):
        await interaction.response.defer(ephemeral=True)
        total = await slotsdb.get_total_pulls(interaction.user.id)
        await interaction.edit_original_response(content=f'You spun the ROCK SLOTS {total} times!')

    @app_commands.command(name='reload_loot_table', description='Re-read the loot table')
    async def reload_loot_table(self, interaction):
        load_loot_table()
        await interaction.response.send_message('Reloaded', ephemeral=True)

    @app_commands.command(name='reload_upgrade_table', description='Re-read the upgrade table')
    async def reload_upgrade_table(self, interaction):
        load_upgrade_table()
        await interaction.response.send_message('Reloaded', ephemeral=True)

    @app_commands.command(name='reload_fail_messages', description='Re-read the fail message table')
    async def reload_fail_messages(self, interaction):
        load_fail_messages()
        await interaction.response.send_message('Reloaded', ephemeral=True)

    @app_commands.command(name='reload_slots_cfg', description='Reload the ROCK SLOTS config')
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
            fail_msg = random.choice(fail_msgs)
            embed = make_embed('red', f'{lose_roll()}')
            if fail_msg.startswith('image:'):
                embed.set_image(url=fail_msg.replace('image:', ''))
            else:
                embed.description += f'\n\n{fail_msg}'

            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            # won

            # add to rock wallet
            await slotsdb.add_to_wallet(interaction.user.id, award)

            win_spin = f'{loot_table[award]["spin"]}'
            embed = make_embed('green', f'{win_spin}\n\nYou won the {award} role!')
            if award == 'GOLDEN JEFF':
                    # rarest reward gets a special message
                    embed.description += ' I didn\'t even know that was possible!!'
            if award == 'Rock':
                # don't show rock public, too common
                # chance for bundle of rocks
                if random.randrange(1, 4) == 3:
                    rocks = random.randrange(2, 5)
                    await slotsdb.add_to_wallet(interaction.user.id, award, rocks - 1)
                    embed.description = f'{win_spin}\n\nWhoa, you found {rocks} Rocks!'
                else:
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

    @app_commands.command(name='rock_wallet', description='View your mining gains!')
    async def rock_wallet(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        wallet = await slotsdb.get_wallet(interaction.user.id)
        embed = make_embed('blue', '## Your ROCK WALLET:\n\n')
        for award, count in wallet.items():
            embed.description += f'**{award}**: {count}\n'

        if len(wallet.keys()) > 0:
            embed.description += '\nCollect enough and use the /rock_upgrade command to get better ones!'
        else:
            # empty wallet gif
            embed.set_image(url='https://i.imgur.com/q2qTDRe.gif')

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name='rock_upgrade', description='Spend rocks to get better rocks!')
    async def rock_upgrade(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        wallet = await slotsdb.get_wallet(interaction.user.id)
        upgrades = []
        for award, count in wallet.items():
            try:
                upgrade = upgrade_table[award]
                if count >= upgrade['amount']:
                    times = math.floor(count / upgrade['amount'])
                    label = f'{upgrade["amount"] * times} {award}s for {times} {upgrade["upgrade"]}'
                    if times > 1: label += 's'
                    upgrades.append((award, label, times))
            except:
                pass

        if len(upgrades) == 0:
            embed = make_embed('red', '### No Available Upgrades.\nGet more rocks!')
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = make_embed('green', '### Select an upgrade!')
        view = UpgradeView(interaction, upgrades)
        message = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        await view.wait()
        if view.value:
            # they picked something, gather info
            user_id = interaction.user.id
            selected = view.select.selected

            upgrade_award = selected['award']
            times = selected['times']
            award = upgrade_table[upgrade_award]
            new_role = loot_table[award['upgrade']]['role']

            to_remove = int(award['amount']) * int(times)
            if await slotsdb.remove_from_wallet(user_id, upgrade_award, to_remove):
                # update the wallet
                await slotsdb.add_to_wallet(user_id, award['upgrade'], amount=int(times))

                # give them the new role
                await interaction.user.add_roles(discord.Object(id=new_role))

                # send a message to the chat
                await message.delete()
                trade = selected['label'].replace(' for ', ' into ')
                description = f'### 💥 You have mysteriously transformed {trade}! 💥'
                embed = make_embed('blue', description)
                await interaction.channel.send(interaction.user.mention, embed=embed)
            else:
                embed = make_embed('red', '### You do not have the funds for this upgrade')
                await message.edit(view=None, embed=embed)
        else:
            embed = make_embed('dark_grey', 'Cancelled.')
            await message.edit(view=None, embed=embed)


    @app_commands.command(name='frenzy_role_message', description='Send the frenzy role message')
    async def frenzy_role_message(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.delete_original_response()

        view = FrenzyRoleView(frenzy_role_id=gamba_cfg.frenzy_alert_role, timeout=None)
        embed = discord.Embed(
            color=discord.Color.teal(),
            title='Frenzy Alert Role',
            description='''# Get pinged every time there's a frenzy (reduced cooldowns for mining)

            ### _Hit the button again to remove the role and stop getting pinged_
            '''.replace(' '*12, '').strip()
        )
        message = await interaction.channel.send(embed=embed, view=view)
        await view.wait()

    async def change_avatar(self, avatar):
        image_file = None
        if avatar == 'normal':
            image_file = gamba_cfg.normal_avatar
        if avatar == 'frenzy':
            image_file = gamba_cfg.frenzy_avatar
        if image_file:
            with open(image_file, 'rb') as image:
                await self.bot.user.edit(avatar=image.read())

    async def cog_unload(self):
        """this gets called if the cog gets unloaded, remove commands from tree"""
        self.check_hot_hour.stop()
        self.bot.tree.remove_command('mine', guild=self.server)
        self.bot.tree.remove_command('scava', guild=self.server)
        self.bot.tree.remove_command('reload_loot_table', guild=self.server)
        self.bot.tree.remove_command('reload_upgrade_table', guild=self.server)
        self.bot.tree.remove_command('reload_fail_messages', guild=self.server)
        self.bot.tree.remove_command('reload_slots_cfg', guild=self.server)
        self.bot.tree.remove_command('goose_say', guild=self.server)
        self.bot.tree.remove_command('check_spins', guild=self.server)
        self.bot.tree.remove_command('get_stats', guild=self.server)
        self.bot.tree.remove_command('hot_hour', guild=self.server)
        self.bot.tree.remove_command('frenzy_role_message', guild=self.server)
        self.bot.tree.remove_command('rock_wallet', guild=self.server)
        self.bot.tree.remove_command('rock_upgrade', guild=self.server)

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

                    # change avatar to non-frenzy avatar
                    await self.change_avatar('normal')

            if hot_hour['active'] == 0:
                # if we're not in a checked hour and close to the start of the hour
                if hot_hour['hour'] != now.hour:# and now.minute >= 0 and now.minute <= 10:
                    # and we hit the current chance
                    if random.randrange(1, hot_hour['odds']) == 1:
                        # activate hot hour and send a message to the channel
                        await slotsdb.change_hot_hour(active=1, odds=6)
                        channel = self.bot.get_channel(gamba_cfg.slots_channel)
                        await channel.send(f'# Whoa it\'s getting really **ROCKY** in here\n\n<@&{gamba_cfg.frenzy_alert_role}>')
                        # change avatar to Frenzy Avatar
                        await self.change_avatar('frenzy')
                    else:
                        await slotsdb.change_hot_hour(odds=hot_hour['odds'] - 1)

                await slotsdb.change_hot_hour(hour=now.hour)
        except Exception as e:
            print('Error checking hot hour')
            print(e)
