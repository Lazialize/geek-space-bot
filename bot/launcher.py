import os
import sys

from gsbot import GeekSpaceBot

debug_flag = os.getenv("DEBUG_MODE")

def main(debug=False):
    bot = GeekSpaceBot(command_prefix="g!")

    token = os.getenv("DISCORD_BOT_DEBUG_TOKEN") if debug else os.getenv("DISCORD_BOT_RELEASE_TOKEN")

    bot.run(token)

main(debug_flag) 