import discord
from discord.ext import commands

EXTENSIONS = (
)

class GeekSpaceBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.default()
        intents.members = True

        self.pool = kwargs.pop("connection")

        super().__init__(intents=intents, *args, **kwargs)

        # Load extensions
        for extension in EXTENSIONS:
            self.load_extension(extension)