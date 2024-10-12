from discord.ext import commands
import discord

class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.polls = {}
        self.user_reactions = {}

    @commands.hybrid_group(name="poll", with_app_command=True)
    async def poll(self, ctx: commands.Context):
        """Parent command for poll-related subcommands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `/poll start` to start a new poll.")

    @poll.command(name="start")
    async def start_poll(self, ctx: commands.Context, question: str, option1: str, option2: str, option3: str = None, option4: str = None, option5: str = None, option6: str = None, option7: str = None, option8: str = None, option9: str = None, option10: str = None):
        """Starts a new poll with the given question and options."""
        options = [option1, option2, option3, option4, option5, option6, option7, option8, option9, option10]
        options = [opt for opt in options if opt]

        if len(options) < 2:
            await ctx.send("A poll must have at least two options.")
            return

        embed = discord.Embed(title="Poll", description=question, color=discord.Color.blue())
        for idx, option in enumerate(options, start=1):
            embed.add_field(name=f"Option {idx}", value=option, inline=False)
        
        message = await ctx.send(embed=embed)
        self.polls[message.id] = {
            "channel_id": message.channel.id,
            "question": question,
            "options": {emoji: idx for idx, emoji in enumerate(('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟')[:len(options)], start=1)}
        }
        self.user_reactions[message.id] = {}

        for emoji in self.polls[message.id]["options"]:
            await message.add_reaction(emoji)
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        message_id = reaction.message.id
        if message_id in self.polls:
            if user.id in self.user_reactions[message_id]:
                await reaction.remove(user) 
                return
            self.user_reactions[message_id][user.id] = reaction.emoji

            channel_id = self.polls[message_id]["channel_id"]
            question = self.polls[message_id]["question"]
            await self.send_ephemeral_message(user, question, reaction.emoji)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.bot:
            return
        message_id = reaction.message.id
        if message_id in self.polls:
            if user.id in self.user_reactions[message_id]:
                del self.user_reactions[message_id][user.id]
            await reaction.message.add_reaction(reaction.emoji)

    async def send_ephemeral_message(self, user, question, emoji):
        embed = discord.Embed(
            title="Vote Counted",
            description=(
                f"{user.mention}, your vote has been counted!\n\n"
                f"**Poll Question:** {question}\n"
                f"**Option you chose:** {emoji}"
            ),
            color=discord.Color.green()
        )
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            pass

async def setup(bot):
    await bot.add_cog(Poll(bot))