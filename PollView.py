import discord
import datetime

def timestamp():
    now = datetime.datetime.now()
    return int(round(now.timestamp()))

class PollView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.used = []
        self.answers = {
            "very_satisfied": 0,
            "somewhat_satisfied": 0,
            "neither": 0,
            "somewhat_dissatisfied": 0,
            "very_dissatisfied": 0
        }

    @discord.ui.button(label='😍', style=discord.ButtonStyle.primary)
    async def button_v_s(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        # if already answered, skip
        if user_id in self.used: return
        self.used.append(user_id)
        self.answers['very_satisfied'] += 1

    @discord.ui.button(label='🙂', style=discord.ButtonStyle.primary)
    async def button_s_s(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        # if already answered, skip
        if user_id in self.used: return
        self.used.append(user_id)
        self.answers['somewhat_satisfied'] += 1

    @discord.ui.button(label='😐', style=discord.ButtonStyle.primary)
    async def button_n(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        # if already answered, skip
        if user_id in self.used: return
        self.used.append(user_id)
        self.answers['neither'] += 1

    @discord.ui.button(label='🙁', style=discord.ButtonStyle.primary)
    async def button_s_d(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        # if already answered, skip
        if user_id in self.used: return
        self.used.append(user_id)
        self.answers['somewhat_dissatisfied'] += 1


    @discord.ui.button(label='😣', style=discord.ButtonStyle.primary)
    async def button_v_d(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        # if already answered, skip
        if user_id in self.used: return
        self.used.append(user_id)
        self.answers['very_dissatisfied'] += 1
