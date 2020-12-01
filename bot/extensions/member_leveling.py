from datetime import datetime
from typing import Any, NamedTuple, Optional

import discord
from discord import User, Message, TextChannel, Embed
from discord.ext.commands import Cog, Context, command, group, has_permissions, is_owner, guild_only
from discord.member import Member
from hashids import Hashids
from ..gsbot import GeekSpaceBot

class UserData(NamedTuple):
    guild_id: int
    user_id: int
    level: int
    own_exp: int
    next_exp: int
    total_exp: int
    last_message_timestamp: datetime
    rank: Optional[int]

class MemberLeveling(Cog):
    def __init__(self, bot: GeekSpaceBot):
        self.bot = bot
        self.pool = bot.pool

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not isinstance(message.channel, TextChannel):
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
                last_message_timestamp=message.created_at
            )

    async def on_level_up(self, message: Message, level: int):
        # Actually, on_level_up is triggered only when Member speak on the guild
        if isinstance(message.author, User):
            return

        await message.channel.send(f"レベルアップ！ {message.author.display_name}のレベルが{level}になりました。")

        sql = """
        SELECT * FROM reward
        WHERE guild_id = $1 AND target_level = $2
        """

        async with self.pool.acquire() as con:
            rowdata = await con.fetch(sql, message.guild.id, level)

        if len(rowdata) <= 0:
            return

        rewards = []
        for data in rowdata:
            role = message.guild.get_role(data[4])

            if role is None:
                continue

            rewards.append(role)

        await message.author.add_roles(*rewards)

    @group()
    async def level(self, ctx: Context):
        if ctx.invoked_subcommand is not None:
            return

        sql = """
        SELECT user_id, level, total_exp, last_message_timestamp,
        rank() OVER (PARTITION BY guild_id ORDER BY total_exp DESC, last_message_timestamp ASC)
        FROM user_data
        WHERE guild_id = $1
        ORDER BY total_exp DESC, last_message_timestamp ASC
        LIMIT 10
        """

        async with self.pool.acquire() as con:
            data = await con.fetch(sql, ctx.guild.id)

        embed = Embed(title="Ranking")
        ranking_member = []

        for d in data:
            member = ctx.guild.get_member(d[0])
            embed.add_field(name=f"第{d[4]}位", value=f"**{member.display_name}**: Level {d[1]}, Total Exp{d[2]}", inline=False)
            ranking_member.append(member)

        if ctx.author not in ranking_member:
            user_data = await self._fetch_user_data(ctx.guild.id, ctx.author.id, rank=True)
            embed.add_field(name=f"第{user_data.rank}位", value=f"**{ctx.author.display_name}**: Level {user_data.level}, Total Exp{user_data.total_exp}", inline=False)

        await ctx.send(embed=embed)

    @level.command()
    @has_permissions(manage_guild=True)
    async def add(self, ctx: Context, target_level: int, role: discord.Role):
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
    @has_permissions(manage_guild=True)
    async def remove(self, ctx: Context, hash_id: str):
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
    @guild_only()
    async def _list(self, ctx: Context):
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

    @command()
    @guild_only()
    async def rank(self, ctx: Context, member: Optional[discord.Member] = None):
        if member is None:
            # ctx.author is always Member because the command is executable in the guild only.
            member = ctx.author #type: ignore

        data = await self._fetch_user_data(member.guild.id, member.id, rank=True)

        if data is None:
            await ctx.send(f"{member.display_name}の情報は存在しません。")
            return

        embed = discord.Embed()
        embed.title = f"{member.display_name}'s Rank"
        embed.add_field(name="Rank", value=str(data.rank))
        embed.add_field(name="Level", value=str(data.level))
        embed.add_field(name="Current Exp", value=str(data.own_exp))
        embed.add_field(name="Next Exp", value=str(data.next_exp))
        embed.add_field(name="Total Exp", value=str(data.total_exp))

        await ctx.send(embed=embed)

    @level.group()
    @is_owner()
    async def debug(self, ctx: Context):
        pass

    @debug.command()
    @is_owner()
    async def add_level(self, ctx: Context):
        user_data = await self._fetch_user_data(ctx.guild.id, ctx.author.id)
        await self.level_up(ctx.message, user_data.level + 1)

    @debug.command()
    @is_owner()
    async def reset(self, ctx: Context):
        await self._update_user_data(
            ctx.guild.id,
            ctx.author.id,
            level=0,
            own_exp=0,
            next_exp=100,
            total_exp=0,
            last_message_timestamp=None
        )

    async def level_up(self, message: Message, level: int, **kwargs: Any):
        await self._update_user_data(message.guild.id, message.author.id, level=level ,**kwargs)
        await self.on_level_up(message, level)

    async def _fetch_user_data(self, guild_id: int, user_id: int, *, rank=False) -> Optional[UserData]:
        if rank:
            sql = """
            SELECT *
            FROM (
                SELECT guild_id, user_id, level, own_exp, next_exp, total_exp, last_message_timestamp,
                rank() OVER (PARTITION BY guild_id ORDER BY total_exp DESC, last_message_timestamp ASC)
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

    async def _update_user_data(self, guild_id: int, user_id: int, **kwargs: Any) -> bool:
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
            status: str = await con.execute(sql, *kwargs.values(), guild_id, user_id)

        # The execute method returns status following format:
        # OPERATOR_NAME OID OPERATED_RECORD_COUNT
        # e.g. UPDATE 1
        return status.split()[1] == "1"

    async def cog_command_error(self, ctx: Context, error):
        await ctx.send(error)


def setup(bot: GeekSpaceBot):
    bot.add_cog(MemberLeveling(bot))
