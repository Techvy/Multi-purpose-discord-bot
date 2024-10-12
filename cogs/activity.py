from discord.ext import commands
from discord import Activity, ActivityType

class PresenceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='setpresence', description='Change the bot\'s presence status')
    async def set_presence(self, ctx: commands.Context, act_type: str, *, status: str):
        act_type = act_type.lower()
        if act_type == 'playing':
            act = Activity(type=ActivityType.playing, name=status)
        elif act_type == 'streaming':
            act = Activity(type=ActivityType.streaming, name=status)
        elif act_type == 'listening':
            act = Activity(type=ActivityType.listening, name=status)
        elif act_type == 'watching':
            act = Activity(type=ActivityType.watching, name=status)
        else:
            await ctx.send("Invalid activity type. Choose from 'playing', 'streaming', 'listening', 'watching'.")
            return

        await self.bot.change_presence(activity=act)
        await ctx.send(f'Presence updated to {act_type} {status}')

async def setup(bot):
    await bot.add_cog(PresenceCog(bot))
