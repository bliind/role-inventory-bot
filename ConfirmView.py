import discord

class ConfirmView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.value = None

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            color=discord.Color.green(),
            description='Proceeding..'
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.value = True
        await self.on_timeout()
        self.stop()

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            color=discord.Color.red(),
            description='Aborting'
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.value = False
        await self.on_timeout()
        self.stop()
