from discord.ext import commands
from dotdict import dotdict
from views import RoleView
from db import *
import discord
import json
import os

def load_config():
    global config
    config_file = 'config.json' if env == 'prod' else 'config.test.json'
    with open(config_file, encoding='utf8') as stream:
        config = dotdict(json.load(stream))

env = os.getenv('BOT_ENV')
load_config()

class MyClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix='>', intents=intents)
        self.synced = False

    async def on_ready(self):
        synced = await self.tree.sync(guild=discord.Object(id=config.server))
        print(f'Synced {len(synced)} command(s)')
        print(f"{config.env.upper()} Role Inventory Bot is ready for duty")

bot = MyClient()

@bot.tree.command(name='reload_exclusions', description='Reload the Role Inventory excluded roles', guild=discord.Object(id=config.server))
async def reload_config_command(interaction):
    load_config()
    await interaction.response.send_message('Reloaded', ephemeral=True)

@bot.tree.command(name='remove_role', description='Remove a role and store it', guild=discord.Object(id=config.server))
async def remove_role(interaction: discord.Interaction):
    user_roles = []
    for role in interaction.user.roles:
        if role.name == '@everyone':
            continue
        if role.id not in config.exclude:
            user_roles.append(dotdict({"id": role.id, "name": role.name}))

    if not user_roles:
        await interaction.response.send_message(embed=discord.Embed(
            color=discord.Color.yellow(),
            description='You have no roles that can be removed.'
        ), ephemeral=True)
        return

    view = RoleView(user_roles, 'remove', 30)
    embed = discord.Embed(
        color=discord.Color.blurple(),
        description='Select a role to remove and store in my inventory!\
            \n\nYou\'ll be able to retrieve it again with the /add_role command'
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await view.wait()
    if view.value:
        user_id = interaction.user.id
        selected = view.select.selected
        current_roles = [r.id for r in interaction.user.roles]
        saved_roles = get_roles(user_id)
        new_roles = saved_roles + [c for c in current_roles if str(c) not in saved_roles]

        role_string = ','.join([str(v) for v in new_roles])
        if check_user(user_id):
            if role_string != '':
                update_user(user_id, role_string)
        else:
            add_user(user_id, role_string)

        await interaction.user.remove_roles(discord.Object(id=selected['id']))

        description = f'''
            Your role "{selected['name']}" has been removed and stored.

            You can re-add roles with the /add_role command
        '''.replace(' '*12, '').strip()
    else:
        description = 'Canceled'

    await interaction.edit_original_response(
        view=None,
        embed=discord.Embed(color=discord.Color.blue(), description=description)
    )

@bot.tree.command(name='add_role', description='Add a role from your storage', guild=discord.Object(id=config.server))
async def add_role(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)

    user_id = interaction.user.id
    if not check_user(user_id):
        await interaction.edit_original_response(embed=discord.Embed(
            color=discord.Color.red(),
            description='You have not removed any roles yet!'
        ))
        return

    server = [g for g in bot.guilds if g.id == config.server][0]
    current_roles = [r.id for r in interaction.user.roles]
    saved_roles = get_roles(user_id)
    eligible_roles = [s for s in saved_roles if int(s) not in current_roles]
    user_roles = []
    for role in server.roles:
        if str(role.id) in eligible_roles and role.id not in config.exclude:
            user_roles.append(dotdict({"id": role.id, "name": role.name}))

    if not user_roles:
        await interaction.edit_original_response(embed=discord.Embed(
            color=discord.Color.yellow(),
            description='You have no saved roles you don\'t currently have.'
        ))
        return


    view = RoleView(user_roles, 'add', 30)
    embed = discord.Embed(
        color=discord.Color.blurple(),
        description='Retreive a role you saved in my inventory!'
    )
    await interaction.edit_original_response(embed=embed, view=view)
    await view.wait()
    if view.value:
        selected = view.select.selected
        await interaction.user.add_roles(discord.Object(id=selected['id']))
        description = f'''
            Re-added your role "{selected["name"]}"!

            You can remove roles with the /remove_role command.
        '''.replace(' '*12, '').strip()
    else:
        description = 'Canceled'

    await interaction.edit_original_response(
        view=None,
        embed=discord.Embed(color=discord.Color.green(), description=description)
    )

bot.run(config.token)
