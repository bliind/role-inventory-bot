import discord
import datetime
import asyncio
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
import TimedRoleDatabase as db
from ConfirmView import ConfirmView

def timestamp():
    now = datetime.datetime.now()
    return int(round(now.timestamp()))

class TimedRole(commands.Cog):
    def __init__(self, bot, config):
        # assign for use in the methods
        self.bot = bot
        self.config = config
        self.server = discord.Object(id=config.server)

    @commands.Cog.listener()
    async def on_ready(self):
        # add the commands to the tree
        self.bot.tree.add_command(self.create_timed_role, guild=self.server)
        self.bot.tree.add_command(self.remove_timed_role, guild=self.server)
        self.bot.tree.add_command(self.list_timed_roles, guild=self.server)
        self.bot.tree.add_command(self.check_roles, guild=self.server)

        # start loop
        self.check_timed_role_users.start()

    async def cog_unload(self):
        """this gets called when the cog is unloaded, remove the commands from the tree"""
        self.bot.tree.remove_command('create_timed_role', guild=self.server)
        self.bot.tree.remove_command('remove_timed_role', guild=self.server)
        self.bot.tree.remove_command('list_timed_roles', guild=self.server)
        self.bot.tree.remove_command('check_roles', guild=self.server)

    @app_commands.command(name='create_timed_role', description='Add an expiration timer to an existing role')
    async def create_timed_role(self, interaction: discord.Interaction, role: discord.Role, expire_days: int):
        await interaction.response.defer(ephemeral=True)

        # check if role is already timed role
        # if yes, check for overwrite confirm
        # insert into database
        check = await db.check_timed_role(role.id)
        if check:
            confirm = ConfirmView(timeout=20)
            message = f'This role is already a timed role with an expiry time of {check["expire_days"]} days.\n\nOverwrite?'
            embed = discord.Embed(
                color=discord.Color.yellow(),
                description=message
            )

            await interaction.edit_original_response(embed=embed, view=confirm)
            await confirm.wait()
            await interaction.edit_original_response(view=confirm)

            if confirm.value:
                # yes was picked, update role in db
                if await db.update_timed_role(role.id, expire_days):
                    await interaction.edit_original_response(embed=discord.Embed(color=discord.Color.green(), description='Updated timed role!'))

        else:
            # no existing role in db
            if await db.add_timed_role(role.id, expire_days):
                await interaction.edit_original_response(embed=discord.Embed(color=discord.Color.green(), description='Added timed role!'))

    @app_commands.command(name='remove_timed_role', description='Remove the expiration timer from a role')
    async def remove_timed_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        if await db.remove_timed_role(role.id):
            await interaction.edit_original_response(embed=discord.Embed(color=discord.Color.green(), description='Removed timed role.'))
        else:
            await interaction.edit_original_response(embed=discord.Embed(color=discord.Color.red(), description='Something weird happened.'))

    @app_commands.command(name='list_timed_roles', description='List all timed roles')
    async def list_timed_roles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        roles = await db.list_timed_roles()
        message = ''
        for role in roles:
            message += f'<@&{role["role_id"]}> - {role["expire_days"]} days\n'

        await interaction.edit_original_response(embed=discord.Embed(color=discord.Color.green(), description=message))

    @app_commands.command(name='check_roles', description='Check the expiration of your timed roles')
    async def check_roles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        roles = await db.get_users_roles(interaction.user.id)
        now = timestamp()

        message = ''
        for role in roles:
            elapsed = now - role['date_acquired']
            total_time = role['expire_days'] * 86400 # convert days to seconds

            remaining = round((total_time - elapsed) / 86400, 1) # convert back to days
            message += f'<@&{role["role_id"]}> - {remaining} days\n'

        if message != '':
            await interaction.edit_original_response(embed=discord.Embed(color=discord.Color.blue(), description=message))
        else:
            await interaction.edit_original_response(embed=discord.Embed(color=discord.Color.yellow(), description='You have no temporary roles!'))

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # watch for assignment of roles
        b_roles = [r.id for r in before.roles]
        a_roles = [r.id for r in after.roles]
        added = [r for r in a_roles if r not in b_roles]

        # fetch list of timed role IDs
        # for timed_role_ids if any are in added, log to timed_role_user
        timed_roles = await db.get_timed_roles()
        for role_id in timed_roles:
            if role_id in added:
                await db.add_timed_role_user(after.id, role_id, timestamp())

    @tasks.loop(seconds=3600)
    async def check_timed_role_users(self):
        try:
            expired_users = await db.get_expired_role_users(timestamp())
            if not expired_users:
                return
            guild = self.bot.get_guild(self.config.server)

            for user in expired_users:
                member = await guild.fetch_member(user['user_id'])
                await member.remove_roles(discord.Object(id=user['role_id']))
                await db.remove_role_user(user['user_id'], user['role_id'])
                await asyncio.sleep(0.9)
        except Exception as e:
            print('Error with timed users loop:')
            print(e)
