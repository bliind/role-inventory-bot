import discord
from discord import app_commands
from discord.ext import commands
from dotdict import dotdict
from views import RoleView
import roledb
from SpecialXPView import SpecialXPView

class RoleInventory(commands.Cog):
    def __init__(self, bot, config):
        # assign for use in the methods
        self.bot = bot
        self.config = config
        self.server = discord.Object(id=config.server)

        # add the commands to the tree
        self.bot.tree.add_command(self.add_role, guild=self.server)
        self.bot.tree.add_command(self.store_role, guild=self.server)
        self.bot.tree.add_command(self.save_roles, guild=self.server)
        self.bot.tree.add_command(self.special_xp_message, guild=self.server)
        self.bot.tree.add_command(self.add_sr_role, guild=self.server)
        self.bot.tree.add_command(self.remove_sr_role, guild=self.server)
        self.bot.tree.add_command(self.set_no_xp_role, guild=self.server)
        self.bot.tree.add_command(self.champion, guild=self.server)
        self.bot.tree.add_command(self.add_champion_role, guild=self.server)
        self.bot.tree.add_command(self.remove_champion_role, guild=self.server)
        self.bot.tree.add_command(self.add_allowed_rank, guild=self.server)
        self.bot.tree.add_command(self.remove_allowed_rank, guild=self.server)

    def make_embed(self, color, description=None):
        color = getattr(discord.Color, color)
        embed = discord.Embed(
            color=color(),
            title='Role Inventory'
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        if description:
            embed.description = description

        return embed

    async def cog_unload(self):
        """this gets called when the cog is unloaded, remove the commands from the tree"""
        self.bot.tree.remove_command('add_role', guild=self.server)
        self.bot.tree.remove_command('store_role', guild=self.server)
        self.bot.tree.remove_command('save_roles', guild=self.server)
        self.bot.tree.remove_command('special_xp_message', guild=self.server)
        self.bot.tree.remove_command('add_sr_role', guild=self.server)
        self.bot.tree.remove_command('remove_sr_role', guild=self.server)
        self.bot.tree.remove_command('set_no_xp_role', guild=self.server)
        self.bot.tree.remove_command('champion', guild=self.server)
        self.bot.tree.remove_command('add_champion_role', guild=self.server)
        self.bot.tree.remove_command('remove_champion_role', guild=self.server)
        self.bot.tree.remove_command('add_allowed_rank', guild=self.server)
        self.bot.tree.remove_command('remove_allowed_rank', guild=self.server)

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            view = SpecialXPView(timeout=None)
            self.bot.add_view(view)
        except Exception as e:
            print('Initializing view failed:', e)

    @app_commands.command(name='save_roles', description='Take a snapshot of your current roles')
    async def save_roles(self, interaction):
        """allows a user to save their roles without removing any"""

        # defer response for lag reasons
        await interaction.response.defer(thinking=True, ephemeral=True)

        # create a list of roles to save, including any that have been saved before
        user_id = interaction.user.id
        current_roles = [r.id for r in interaction.user.roles]
        saved_roles = await roledb.get_roles(user_id)
        new_roles = saved_roles + [c for c in current_roles if str(c) not in saved_roles]

        # save all their roles to the database, check if it needs updating if it exists
        role_string = ','.join([str(v) for v in new_roles])
        if await roledb.check_user(user_id):
            if role_string != '':
                await roledb.update_user(user_id, role_string)
        else:
            await roledb.add_user(user_id, role_string)

        embed = self.make_embed('green', 'Roles saved!')
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name='store_role', description='Store a role in my inventory')
    async def store_role(self, interaction):
        """allows a user to remove a role and saves it"""

        # defer response for lag reasons
        await interaction.response.defer(thinking=True, ephemeral=True)

        # create a list of roles the user has and can remove
        user_roles = []
        for role in interaction.user.roles:
            if role.name == '@everyone':
                continue
            if role.id not in self.config.exclude:
                user_roles.append(dotdict({"id": role.id, "name": role.name}))

        # if they have no roles that can be removed just stop here
        if not user_roles:
            embed = self.make_embed('yellow', 'You have no roles that can be stored.')
            await interaction.edit_original_response(embed=embed)
            return

        # create the fancy dropdown View to send
        view = RoleView(interaction, user_roles, 'remove', 30)
        embed = self.make_embed('blurple', 'Select a role to remove and store in my inventory!\n\nYou\'ll be able to retrieve it again with the /add_role command')
        await interaction.edit_original_response(embed=embed, view=view)

        # wait for interaction with the dropdown (or timeout)
        await view.wait()
        if view.value:
            # they picked something, gather info
            user_id = interaction.user.id
            selected = view.select.selected
            current_roles = [r.id for r in interaction.user.roles]
            saved_roles = await roledb.get_roles(user_id)
            new_roles = saved_roles + [c for c in current_roles if str(c) not in saved_roles]

            # save all their roles to the database, check if it needs updating if it exists
            role_string = ','.join([str(v) for v in new_roles])
            if await roledb.check_user(user_id):
                if role_string != '':
                    await roledb.update_user(user_id, role_string)
            else:
                await roledb.add_user(user_id, role_string)

            # remove the user's role, tell them about it
            await interaction.user.remove_roles(discord.Object(id=selected['id']))
            description = f'''
                Your role "{selected['name']}" has been removed and stored.

                You can re-add roles with the /add_role command
            '''.replace(' '*12, '').strip()
        else:
            # nothing selected/timed out
            description = 'Canceled'

        # edit the response to disable elements
        await interaction.edit_original_response(
            view=None,
            embed=self.make_embed('blue', description)
        )

    @app_commands.command(name='add_role', description='Add a role from your storage')
    async def add_role(self, interaction: discord.Interaction):
        # defer response so discord doesn't kill the link while we pull from db
        await interaction.response.defer(thinking=True, ephemeral=True)

        # ensure the user has roles saved
        user_id = interaction.user.id
        if not await roledb.check_user(user_id):
            embed = self.make_embed('red', 'You have not stored any roles yet!')
            await interaction.edit_original_response(embed=embed)
            return

        # create a list of roles eligible for re-apply
        server = [g for g in self.bot.guilds if g.id == self.config.server][0]
        current_roles = [r.id for r in interaction.user.roles]
        saved_roles = await roledb.get_roles(user_id)
        eligible_roles = [s for s in saved_roles if int(s) not in current_roles]
        user_roles = []
        for role in server.roles:
            if str(role.id) in eligible_roles and role.id not in self.config.exclude:
                user_roles.append(dotdict({"id": role.id, "name": role.name}))

        # if no eligible roles, kick back
        if not user_roles:
            embed = self.make_embed('yellow', 'You have no saved roles you don\'t currently have.')
            await interaction.edit_original_response(embed=embed)
            return

        # create and send the fancy dropdown selection View
        view = RoleView(interaction, user_roles, 'add', 30)
        embed = self.make_embed('blurple', 'Retreive a role you saved in my inventory!')
        await interaction.edit_original_response(embed=embed, view=view)

        # wait for View interaction/timeout
        await view.wait()
        if view.value:
            # user selected a role, slap it on them
            selected = view.select.selected
            await interaction.user.add_roles(discord.Object(id=selected['id']))
            description = f'''
                Re-added your role "{selected["name"]}"!

                You can store roles with the /store_role command.
            '''.replace(' '*12, '').strip()
        else:
            # timed out probably
            description = 'Canceled'

        # update original response to disable elements
        await interaction.edit_original_response(
            view=None,
            embed=self.make_embed('green', description)
        )

    @app_commands.command(name='special_xp_message', description='Send the special XP message')
    async def special_xp_message(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.delete_original_response()

        view = SpecialXPView(timeout=None)
        embed = discord.Embed(
            color=discord.Color.yellow(),
            description='''
                Here you can choose to remove your SR roles. The roles cannot be added back on manually. You will continue to gain XP and will acquire the next SR role automatically.

                You can also choose to completely disable XP gain with the No XP role. Hitting the button again will remove the No XP role.
            '''
        )
        message = await interaction.channel.send(embed=embed, view=view)
        await view.wait()

    @app_commands.command(name='add_sr_role', description='Add a role to the SR role remover')
    async def add_sr_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await roledb.add_sr_role(role.name, role.id)
        await interaction.edit_original_response(embed=self.make_embed('green', f'<@&{role.id}> added!'))

    @app_commands.command(name='remove_sr_role', description='Remove a role from the SR role remover')
    async def remove_sr_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await roledb.add_sr_role(role.name, role.id)
        await interaction.edit_original_response(embed=self.make_embed('red', f'<@&{role.id}> removed!'))

    @app_commands.command(name='set_no_xp_role', description='Set the No XP role')
    async def set_no_xp_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await roledb.set_no_xp_role(role.id)
        embed = self.make_embed('red', f'No XP role set as: <@&{role.id}>!')
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name='champion', description='Become a Server Champion (if you can)')
    async def champion(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        all_of = await roledb.list_champion_roles()
        any_of = await roledb.list_allowed_ranks()

        role_ids = [r.id for r in interaction.user.roles]
        missing = []
        for all_role in all_of:
            if all_role['role_id'] not in role_ids:
                missing.append(all_role)

        if len(missing) > 0:
            description = 'Alas, you are missing some roles to become a Server Champion:\n\n'
            for missing_id in missing:
                description += f'- <@&{missing_id["role_id"]}>\n'
            embed = self.make_embed('red', description)
            await interaction.edit_original_response(embed=embed)
            return

        ranked = False
        for any_role in any_of:
            if any_role['role_id'] in role_ids:
                ranked = True
                break

        if not ranked:
            description = 'Alas, you are not ranked high enough to become a Server Champion. Allowed ranks:\n\n'
            for needed_rank in any_of:
                description += f'- <@&{needed_rank["role_id"]}>\n'
            embed = self.make_embed('red', description)
            await interaction.edit_original_response(embed=embed)
            return

        if ranked == True and len(missing) == 0:
            await interaction.user.add_roles(discord.Object(id=self.config.server_champion))
            embed = self.make_embed('green', 'Congratulations! You are a Server Champion!')
            await interaction.edit_original_response(embed=embed)

    @app_commands.command(name='add_champion_role', description='Add a role to the Server Champion required roles')
    async def add_champion_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await roledb.add_champion_role(role.name, role.id)
        await interaction.edit_original_response(embed=self.make_embed('green', f'<@&{role.id}> added!'))

    @app_commands.command(name='remove_champion_role', description='Remove a role from the Server Champion required roles')
    async def remove_champion_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await roledb.add_champion_role(role.name, role.id)
        await interaction.edit_original_response(embed=self.make_embed('red', f'<@&{role.id}> removed!'))

    @app_commands.command(name='add_allowed_rank', description='Add a role to the Server Champion allowed SRs')
    async def add_allowed_rank(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await roledb.add_allowed_rank(role.name, role.id)
        await interaction.edit_original_response(embed=self.make_embed('green', f'<@&{role.id}> added!'))

    @app_commands.command(name='remove_allowed_rank', description='Remove a role from the Server Champion allowed SRs')
    async def remove_allowed_rank(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await roledb.add_allowed_rank(role.name, role.id)
        await interaction.edit_original_response(embed=self.make_embed('red', f'<@&{role.id}> removed!'))
