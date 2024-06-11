import discord
import math

class RoleSelect(discord.ui.Select):
    def __init__(self, roles, action):
        self.selected = None
        options = []
        for role in roles:
            options.append(discord.SelectOption(
                label=role.name,
                value=role.id
            ))

        super().__init__(placeholder=f'Select role to {action}', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = [f for f in self.options if str(f.value) in self.values][0]
        self.selected = {"name": selected.label, "id": selected.value}
        await interaction.response.defer()
        self.view.value = True
        self.view.stop()

class EditButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label='Edit Post',
            style=discord.ButtonStyle.green
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.value = True
        await interaction.response.defer()
        self.view.stop()

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label='Cancel',
            style=discord.ButtonStyle.red
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.value = False
        await interaction.response.defer()
        self.view.stop()

class LeftButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label='◀',
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.view.page_down()

class RightButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label='▶',
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.view.page_up()

class RoleView(discord.ui.View):
    def __init__(self, interaction, roles, action, timeout):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.action = action
        self.value = None
        self.page = 0
        self.total_pages = 1
        self.roles = roles

        if len(roles) > 25:
            self.page = 1
            self.total_pages = math.ceil(len(roles) / 25)
            roles = self.roles[0:25]
            action = f'{action} (Page 1)'

        self.select = RoleSelect(roles, action)

        self.add_item(self.select)
        if self.page > 0:
            self.add_item(LeftButton())
            self.add_item(RightButton())

            # disable left button, we're first page at the start
            self.children[1].disabled = True

    async def page_down(self):
        if self.page <= 1:
            return
        self.page -= 1
        await self.change_page()

    async def page_up(self):
        if self.page >= self.total_pages:
            return
        self.page += 1
        await self.change_page()

    async def change_page(self):
        start = (self.page - 1) * 25
        end = start + 25
        roles = self.roles[start:end]

        # remove old select, add new select
        self.remove_item(self.select)

        action = f'{self.action} (Page {self.page})'
        self.select = RoleSelect(roles, action)
        self.add_item(self.select)

        # disable buttons if needed
        self.children[0].disabled = self.page == 1
        self.children[1].disabled = self.page == self.total_pages

        await self.interaction.edit_original_response(view=self)
