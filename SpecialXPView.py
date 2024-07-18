import discord
import roledb as db

def make_embed(color, description=None):
    color = getattr(discord.Color, color)
    embed = discord.Embed(color=color())
    if description: embed.description = description
    return embed

class SpecialXPView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)

    @discord.ui.button(label='Remove SR Role', style=discord.ButtonStyle.primary, custom_id='special_xp_remove_sr')
    async def button_remove_sr(self, interaction: discord.Interaction, button: discord.ui.Button):
        sr_roles = [r['role_id'] for r in await db.list_sr_roles()]
        found = False
        for role in interaction.user.roles:
            if role.id in sr_roles:
                found = True
                await interaction.user.remove_roles(role)
                await interaction.response.send_message(embed=make_embed('green', f'Your <@&{role.id}> has been removed!'), ephemeral=True)
        if not found:
            await interaction.response.send_message(embed=make_embed('yellow', 'You don\'t have any SR roles!'), ephemeral=True)

    @discord.ui.button(label='No XP Role', style=discord.ButtonStyle.primary, custom_id='special_xp_no_xp')
    async def button_no_xp(self, interaction: discord.Interaction, button: discord.ui.Button):
        no_xp_id = await db.get_no_xp_role()
        found = False
        for role in interaction.user.roles:
            if role.id == no_xp_id:
                found = True
                await interaction.user.remove_roles(role)
                await interaction.response.send_message(embed=make_embed('green', 'Your No XP role has been removed!'), ephemeral=True)

        if not found:
            await interaction.user.add_roles(discord.Object(id=no_xp_id))
            await interaction.response.send_message(embed=make_embed('green', 'You have been given the No XP role!'), ephemeral=True)
