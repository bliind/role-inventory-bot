import discord

def make_embed(color, description=None):
    color = getattr(discord.Color, color)
    embed = discord.Embed(color=color())
    if description: embed.description = description
    return embed

class FrenzyRoleView(discord.ui.View):
    def __init__(self, frenzy_role_id, timeout):
        super().__init__(timeout=timeout)
        self.frenzy_role_id = frenzy_role_id

    @discord.ui.button(label='Toggle Frenzy Role', style=discord.ButtonStyle.primary, custom_id='frenzy_role_toggle')
    async def frenzy_role_toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        role_ids = [role.id for role in interaction.user.roles]
        if self.frenzy_role_id in role_ids:
            try:
                await interaction.user.remove_roles(discord.Object(id=self.frenzy_role_id))
                await interaction.response.send_message(embed=make_embed('red', 'You have removed your Frenzy Alert role'), ephemeral=True)
            except Exception as e:
                print('error with removing frenzy role')
                print(e)
        else:
            try:
                await interaction.user.add_roles(discord.Object(id=self.frenzy_role_id))
                await interaction.response.send_message(embed=make_embed('green', 'You have added the Frenzy Alert role!'), ephemeral=True)
            except Exception as e:
                print('error with assigning frenzy role')
                print(e)


