import discord

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

class RoleView(discord.ui.View):
    def __init__(self, roles, action, timeout):
        super().__init__(timeout=timeout)
        self.value = None
        self.select = RoleSelect(roles, action)

        self.add_item(self.select)
        # self.add_item(EditButton())
        # self.add_item(CancelButton())
