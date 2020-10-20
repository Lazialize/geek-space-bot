from discord.ext import commands

class MemberLeveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_messsage(self, message):
        pass

    @commands.command()
    async def rank(self, ctx):
        await ctx.send("Test")


def setup(bot):
    bot.add_cog(MemberLeveling(bot))
