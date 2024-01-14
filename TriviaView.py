import discord
import datetime

def timestamp():
    now = datetime.datetime.now()
    return int(round(now.timestamp()))

def calculate_score(time1, time2):
    max_score = 1000
    decrement = 64
    diff = time2 - time1

    return int(max_score - (decrement * diff))

class TriviaView(discord.ui.View):
    def __init__(self, timeout, scores, correct, ts):
        super().__init__(timeout=timeout)
        self.scores = scores
        self.correct = correct
        self.used = []
        self.timestamp = ts

    @discord.ui.button(label='A', style=discord.ButtonStyle.green)
    async def button_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user_id = interaction.user.id
        # if already answered, skip
        if user_id in self.used: return

        # store user in scores if not there
        if user_id not in self.scores:
            self.scores[user_id] = 0

        # if correct answer, increment score
        if self.correct == 'A':
            self.scores[user_id] += calculate_score(self.timestamp, timestamp())
        self.used.append(user_id)

    @discord.ui.button(label='B', style=discord.ButtonStyle.green)
    async def button_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user_id = interaction.user.id
        # if already answered, skip
        if user_id in self.used: return

        # store user in scores if not there
        if user_id not in self.scores:
            self.scores[user_id] = 0

        # if correct answer, increment score
        if self.correct == 'B':
            self.scores[user_id] += calculate_score(self.timestamp, timestamp())
        self.used.append(user_id)

    @discord.ui.button(label='C', style=discord.ButtonStyle.green)
    async def button_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user_id = interaction.user.id
        # if already answered, skip
        if user_id in self.used: return

        # store user in scores if not there
        if user_id not in self.scores:
            self.scores[user_id] = 0

        # if correct answer, increment score
        if self.correct == 'C':
            self.scores[user_id] += calculate_score(self.timestamp, timestamp())
        self.used.append(user_id)

    @discord.ui.button(label='D', style=discord.ButtonStyle.green)
    async def button_d(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user_id = interaction.user.id
        # if already answered, skip
        if user_id in self.used: return

        # store user in scores if not there
        if user_id not in self.scores:
            self.scores[user_id] = 0

        # if correct answer, increment score
        if self.correct == 'D':
            self.scores[user_id] += calculate_score(self.timestamp, timestamp())
        self.used.append(user_id)
