import random
from collections import namedtuple
from typing import Optional

import asyncio
import discord
from discord.ext import commands

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

        data = await self.fetch_user_data(message.guild.id, message.author.id)

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
            sql = """
            UPDATE user_data SET own_exp = $1, total_exp = $2, last_message_timestamp = $3
            WHERE guild_id = $4 AND user_id = $5
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

        data = await self.fetch_user_data(guild_id, user_id, rank=True)

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

    async def fetch_user_data(self, guild_id, user_id, *, rank=False) -> UserData:
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


def setup(bot):
    bot.add_cog(MemberLeveling(bot))
