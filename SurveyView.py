import discord
import datetime
import SurveyDatabase as db

def timestamp():
    now = datetime.datetime.now()
    return int(round(now.timestamp()))

def make_embed(good, message):
    return discord.Embed(
        color=discord.Color.green() if good else discord.Color.red(),
        description=message,
        timestamp=datetime.datetime.now()
    )

class SurveyView(discord.ui.View):
    def __init__(self, timeout, channel_id: int):
        super().__init__(timeout=timeout)
        self.channel_id = channel_id
        self.message_id = None

    # all button presses call this
    async def press_button(self, interaction, response):
        user_id = interaction.user.id

        # if already answered, skip
        check = await db.check_user_answered(self.channel_id, self.message_id, user_id)
        if check:
            embed = make_embed(False, f'You already responded with "{check["response"]}"')
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if await db.add_survey_response(timestamp(), self.channel_id, self.message_id, user_id, response):
            embed = make_embed(True, f'Your response of "{response}" has been recorded, thank you!')
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = make_embed(False, 'Something went wrong, please try again')
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label='😍', style=discord.ButtonStyle.primary, custom_id='survey_very_satisfied')
    async def button_v_s(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.press_button(interaction, 'Very Satisfied')

    @discord.ui.button(label='🙂', style=discord.ButtonStyle.primary, custom_id='survey_somewhat_satisfied')
    async def button_s_s(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.press_button(interaction, 'Somewhat Satisfied')

    @discord.ui.button(label='😐', style=discord.ButtonStyle.primary, custom_id='survey_neither')
    async def button_n(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.press_button(interaction, 'Neither')

    @discord.ui.button(label='🙁', style=discord.ButtonStyle.primary, custom_id='survey_somewhat_dissatisfied')
    async def button_s_d(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.press_button(interaction, 'Somewhat Dissatisfied')


    @discord.ui.button(label='😣', style=discord.ButtonStyle.primary, custom_id='survey_very_dissatisfied')
    async def button_v_d(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.press_button(interaction, 'Very Dissatisfied')
