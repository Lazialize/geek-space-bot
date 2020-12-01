from typing import Any
import discord
from discord.ext import commands

from asyncpg.pool import Pool
from discord.ext.commands import Bot

EXTENSIONS = (
    "extensions.member_leveling",
)


class GeekSpaceBot(Bot): # type: ignore
    def __init__(self, *args: Any, **kwargs: Any):
        intents = discord.Intents.default()
        intents.members = True

        self.pool: Pool = kwargs.pop("connection")

        super().__init__(intents=intents, *args, **kwargs)

        # Load extensions
        for extension in EXTENSIONS:
            self.load_extension(extension)