import os

import asyncio
import asyncpg
from asyncpg.pool import Pool
from .gsbot import GeekSpaceBot

debug_flag: bool = bool(os.getenv("DEBUG_MODE"))


async def create_connection_pool() -> Pool:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")

    if not (user and password and db):
        # TODO: Replace to a concrete exception.
        raise Exception()

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

    if connection_pool is None:
        # TODO: Replace to a concrete exception.
        raise Exception()

    return connection_pool


async def main(debug: bool=False) -> None:
    con = await create_connection_pool()
    bot = GeekSpaceBot(command_prefix="g!", connection=con) # type: ignore

    token = os.getenv("DISCORD_BOT_DEBUG_TOKEN") if debug else os.getenv("DISCORD_BOT_RELEASE_TOKEN")

    if token is None:
        # TODO: Replace to a concrete exception
        raise Exception()

    await bot.start(token)

loop = asyncio.get_event_loop()
loop.run_until_complete(main(debug_flag))
loop.close()
