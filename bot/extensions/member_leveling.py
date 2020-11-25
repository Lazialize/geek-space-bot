import random
from collections import namedtuple
from datetime import datetime
from typing import Optional

import asyncio
import discord
from discord.ext import commands
from hashids import Hashids

UserData = namedtuple("UserData", ("guild_id", "user_id", "level", "own_exp", "next_exp", "total_exp", "last_message_timestamp", "rank"))

class MemberLeveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pool = bot.pool

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        if ctx.command is not None:
            return

        exp = 10

        data = await self._fetch_user_data(message.guild.id, message.author.id)

        if data is None:
            sql = """
            INSERT INTO user_data(guild_id, user_id, level, own_exp, next_exp, total_exp, last_message_timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, $7);
            """

            async with self.pool.acquire() as con:
                await con.execute(sql, message.guild.id, message.author.id, 0, exp, 100, exp, message.created_at)

            return

        if (message.created_at - data.last_message_timestamp).seconds < 60:
            return

        if data.next_exp - (data.own_exp + exp) > 0:
            await self._update_user_data(
                message.guild.id,
                message.author.id,
                own_exp=data.own_exp+exp,
                total_exp=data.total_exp+exp,
                last_message_timestamp=message.created_at
            )

        else:
            await self.level_up(
                message,
                data.level + 1,
                own_exp=(data.own_exp + exp) - data.next_exp,
                next_exp=int(data.next_exp * 1.2),
                total_exp=data.total_exp + exp,
                last_message_timestamp=message.create_at
            )

    async def on_level_up(self, message: discord.Message, level: int):
        await message.channel.send(f"レベルアップ！ {message.author.display_name}のレベルが{level}になりました。")

            sql = """
        SELECT * FROM reward
        WHERE guild_id = $1 AND target_level = $2
        """

        async with self.pool.acquire() as con:
            rowdata = await con.fetch(sql, message.guild.id, level)

        if len(rowdata) <= 0:
            return

        rewards = map(lambda x: message.guild.get_role(x[4]), rowdata)

        await message.author.add_roles(*rewards)

            """

            async with self.pool.acquire() as con:
                await con.execute(sql, data.own_exp + exp, data.total_exp + exp, message.created_at, message.guild.id, message.author.id)

        else:
            sql = """
            UPDATE user_data SET level = $1, own_exp = $2, next_exp = $3, total_exp = $4, last_message_timestamp = $5
            WHERE guild_id = $6 AND user_id = $7
            """

            async with self.pool.acquire() as con:
                await con.execute(sql, data.level + 1, (data.own_exp + exp) - data.next_exp, int(data.next_exp * 1.2), data.total_exp + exp, message.created_at, message.guild.id, message.author.id)

            await message.channel.send(f"Level up! {message.author.display_name}'s level is {data.level + 1}.")

    @commands.command()
    async def rank(self, ctx, member: Optional[discord.Member] = None):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        if member is not None:
            guild_id = member.guild.id
            user_id = member.id

        data = await self._fetch_user_data(guild_id, user_id, rank=True)

        if data is None:
            await ctx.send(f"{ctx.author.display_name}'s information is not exists")
            return

        embed = discord.Embed()
        embed.title = f"{ctx.author.display_name}'s Rank"
        embed.add_field(name="Rank", value=data.rank)
        embed.add_field(name="Level", value=data.level)
        embed.add_field(name="Current Exp", value=data.own_exp)
        embed.add_field(name="Next Exp", value=data.next_exp)
        embed.add_field(name="Total Exp", value=data.total_exp)

        await ctx.send(embed=embed)

    async def level_up(self, message, level, **kwargs):
        await self._update_user_data(message.guild.id, message.author.id, level=level ,**kwargs)
        await self.on_level_up(message, level)

    async def _fetch_user_data(self, guild_id, user_id, *, rank=False) -> Optional[UserData]:
        select_data = ["guild_id", "user_id", "level", "own_exp", "next_exp", "total_exp", "last_message_timestamp"]
        if rank:
            select_data.append("rank() OVER (ORDER BY total_exp DESC)")

        sql = f"""
        SELECT {', '.join(select_data)}
        FROM user_data
        WHERE guild_id = $1 AND user_id = $2;
        """

        async with self.pool.acquire() as con:
            record = await con.fetchrow(sql, guild_id, user_id)

        if record is None:
            return record

        return UserData(record[0], record[1], record[2], record[3], record[4], record[5], record[6], record[7] if rank else None)

    async def _update_user_data(self, guild_id, user_id, **kwargs):
        columns = []
        count = 1
        for k in kwargs.keys():
            columns.append(f"{k} = ${count}")
            count += 1

        sql = f"""
        UPDATE user_data SET {', '.join(columns)}
        WHERE guild_id = ${count} AND user_id = ${count+1}
        """

        async with self.pool.acquire() as con:
            await con.execute(sql, *kwargs.values(), guild_id, user_id)


def setup(bot):
    bot.add_cog(MemberLeveling(bot))
