import discord

class UpgradeSelect(discord.ui.Select):
    def __init__(self, upgrades):
        self.selected = None
        self.upgrades = upgrades
        options = []
        for upgrade in upgrades:
            options.append(discord.SelectOption(
                label=upgrade[1],
                value=f'{upgrade[0]}:{upgrade[2]}'
            ))

        super().__init__(placeholder=f'Select ROCK UPGRADE', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = [f for f in self.options if str(f.value) in self.values][0]
        award, times = selected.value.split(':')
        self.selected = {
            "label": selected.label,
            "award": award,
            "times": times
        }
        await interaction.response.defer()
        self.view.value = True
        self.view.stop()

class UpgradeView(discord.ui.View):
    def __init__(self, interaction, upgrades, timeout=30):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.value = None
        self.roles = upgrades
        self.select = UpgradeSelect(upgrades)
        self.add_item(self.select)
