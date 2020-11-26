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

    @commands.group()
    async def level(self, ctx):
        pass

    @level.command()
    @commands.has_permissions(manage_guild=True)
    async def add(self, ctx, target_level: int, role: discord.Role):
        sql = """
        INSERT INTO reward(hash_id, guild_id, target_level, reward_role_id)
        VALUES ($1, $2, $3, $4)
        """

        hashids = Hashids(salt=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ids = hashids.encode(ctx.guild.id + role.id + target_level)

        async with self.pool.acquire() as con:
            status = await con.execute(sql, ids, ctx.guild.id, target_level, role.id)

        if status == "INSERT 0 1":
            await ctx.send("追加しました。")
        else:
            await ctx.send("追加に失敗しました。")

    @level.command()
    @commands.has_permissions(manage_guild=True)
    async def remove(self, ctx, hash_id: str):
        sql = """
        DELETE FROM reward
        WHERE guild_id = $1 AND hash_id = $2
        """

        async with self.pool.acquire() as con:
            status = await con.execute(sql, ctx.guild.id, hash_id)

        if status == "DELETE 1":
            await ctx.send("削除しました。")
        else:
            await ctx.send("削除に失敗しました。")

    @level.command(name="list")
    async def _list(self, ctx):
        sql = """
        SELECT * FROM reward
        WHERE guild_id = $1
        """

        async with self.pool.acquire() as con:
            rowdata = await con.fetch(sql, ctx.guild.id)

        embed = discord.Embed(title="Rewards")
        for data in rowdata:
            embed.add_field(name=data[1], value=f"Level: {data[3]}, Role: {data[4]}")

        await ctx.send(embed=embed)

    @commands.command()
    async def rank(self, ctx, member: Optional[discord.Member] = None):
        if member is None:
            member = ctx.author

        data = await self._fetch_user_data(member.guild.id, member.id, rank=True)

        if data is None:
            await ctx.send(f"{member.display_name}の情報は存在しません。")
            return

        embed = discord.Embed()
        embed.title = f"{member.display_name}'s Rank"
        embed.add_field(name="Rank", value=data.rank)
        embed.add_field(name="Level", value=data.level)
        embed.add_field(name="Current Exp", value=data.own_exp)
        embed.add_field(name="Next Exp", value=data.next_exp)
        embed.add_field(name="Total Exp", value=data.total_exp)

        await ctx.send(embed=embed)

    @level.group()
    @commands.is_owner()
    async def debug(self, ctx):
        pass

    @debug.command()
    @commands.is_owner()
    async def add_level(self, ctx):
        user_data = await self._fetch_user_data(ctx.guild.id, ctx.author.id)
        await self.level_up(ctx.message, user_data.level + 1)

    @debug.command()
    @commands.is_owner()
    async def reset(self, ctx):
        await self._update_user_data(
            ctx.guild.id,
            ctx.author.id,
            level=0,
            own_exp=0,
            next_exp=100,
            total_exp=0,
            last_message_timestamp=None
        )

    async def level_up(self, message, level, **kwargs):
        await self._update_user_data(message.guild.id, message.author.id, level=level ,**kwargs)
        await self.on_level_up(message, level)

    async def _fetch_user_data(self, guild_id, user_id, *, rank=False) -> Optional[UserData]:
        if rank:
            sql = """
            SELECT *
            FROM (
                SELECT guild_id, user_id, level, own_exp, next_exp, total_exp, last_message_timestamp,
                rank() OVER (PARTITION BY guild_id ORDER BY total_exp DESC)
                FROM user_data
                WHERE guild_id = $1
            ) AS GUD
            WHERE GUD.user_id = $2
            """
        else:
            sql = """
            SELECT guild_id, user_id, level, own_exp, next_exp, total_exp, last_message_timestamp
            FROM user_data
            WHERE guild_id = $1 AND user_id = $2
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

    async def cog_command_error(self, ctx, error):
        await ctx.send(error)


def setup(bot):
    bot.add_cog(MemberLeveling(bot))
