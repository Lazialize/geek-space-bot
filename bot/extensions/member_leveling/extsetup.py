from .member_leveling_cog import MemberLeveling

def setup(bot):
    bot.add_cog(MemberLeveling(bot))