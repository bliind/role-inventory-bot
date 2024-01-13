import discord
from discord import app_commands
from discord.ext import commands
from dotdict import dotdict
from views import RoleView
import roledb

class RoleInventory(commands.Cog):
    def __init__(self, bot, config):
        # assign for use in the methods
        self.bot = bot
        self.config = config
        self.server = discord.Object(id=config.server)

        # add the commands to the tree
        self.bot.tree.add_command(self.add_role, guild=self.server)
        self.bot.tree.add_command(self.remove_role, guild=self.server)
        self.bot.tree.add_command(self.save_roles, guild=self.server)

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
        self.bot.tree.remove_command('remove_role', guild=self.server)
        self.bot.tree.remove_command('save_roles', guild=self.server)

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

    @app_commands.command(name='remove_role', description='Remove a role and store it')
    async def remove_role(self, interaction):
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
            embed = self.make_embed('yellow', 'You have no roles that can be removed.')
            await interaction.edit_original_response(embed=embed)
            return

        # create the fancy dropdown View to send
        view = RoleView(user_roles, 'remove', 30)
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
            embed = self.make_embed('red', 'You have not removed any roles yet!')
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
        view = RoleView(user_roles, 'add', 30)
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

                You can remove roles with the /remove_role command.
            '''.replace(' '*12, '').strip()
        else:
            # timed out probably
            description = 'Canceled'

        # update original response to disable elements
        await interaction.edit_original_response(
            view=None,
            embed=self.make_embed('green', description)
        )
