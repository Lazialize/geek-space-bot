import os
import sys

import asyncio
import asyncpg
from gsbot import GeekSpaceBot

debug_flag = os.getenv("DEBUG_MODE")

async def create_connection_pool():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")

    count = 0
    while True:
        count += 1

        if count > 5:
            raise asyncio.InvalidStateError()
        try:
            # TODO: Change host and port to environment variables.
            connection_pool = await asyncpg.create_pool(host="db", port=5432, user=user, password=password, database=db)
        except:
            await asyncio.sleep(3)
            continue

        break
    return connection_pool


async def main(debug=False):
    con = await create_connection_pool()
    bot = GeekSpaceBot(command_prefix="g!", connection=con)

    token = os.getenv("DISCORD_BOT_DEBUG_TOKEN") if debug else os.getenv("DISCORD_BOT_RELEASE_TOKEN")

    await bot.start(token)

loop = asyncio.get_event_loop()
loop.run_until_complete(main(debug_flag))
loop.close()