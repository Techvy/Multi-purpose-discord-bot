import discord
from discord.ext import commands
import json
import os

class AFKCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file_path = os.path.join('database', 'afk.json')
        self.load_config()

    def load_config(self):
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    'afk_users': {},
                    'ping_records': {}
                }
        except json.JSONDecodeError as e:
            print(f"Error loading JSON configuration: {e}")
            self.config = {
                'afk_users': {},
                'ping_records': {}
            }
        except Exception as e:
            print(f"An unexpected error occurred while loading the configuration: {e}")
            self.config = {
                'afk_users': {},
                'ping_records': {}
            }

    def save_config(self):
        if not os.path.exists('database'):
            os.makedirs('database')
        with open(self.config_file_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    @commands.hybrid_command(name="afk", description="Set yourself as AFK")
    async def afk(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        self.config['afk_users'][user_id] = {
            'username': str(ctx.author),
            'afk_since': discord.utils.utcnow().isoformat()
        }
        self.save_config()

        embed = discord.Embed(
            title="AFK Status",
            description="You are now set as AFK. I'll notify you when you receive a message or are pinged.",
            color=discord.Color.orange()
        )
        embed.set_footer(text="AFK System")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Check if the author is AFK
        if str(message.author.id) in self.config['afk_users']:
            # Notify the author
            embed = discord.Embed(
                title="AFK Status Removed",
                description="I've removed your AFK status since you sent a message.",
                color=discord.Color.green()
            )
            embed.set_footer(text="AFK System")
            await message.author.send(embed=embed)
            # Remove the user from the AFK list
            del self.config['afk_users'][str(message.author.id)]
            self.save_config()

        # Check if any user is pinged and is AFK
        for user in message.mentions:
            if str(user.id) in self.config['afk_users']:
                # Delete the message
                await message.delete()
                # Notify the sender
                embed = discord.Embed(
                    title="User AFK",
                    description=f"{user.mention} is currently AFK. Please try again later.",
                    color=discord.Color.red()
                )
                embed.set_footer(text="AFK System")
                await message.channel.send(embed=embed)

                # Record the ping
                ping_record = self.config['ping_records'].get(str(user.id), [])
                ping_record.append({
                    'user': str(message.author),
                    'message': message.content,
                    'time': discord.utils.utcnow().isoformat()
                })
                self.config['ping_records'][str(user.id)] = ping_record
                self.save_config()

                # Send DM to the AFK user
                dm_embed = discord.Embed(
                    title="You Were PINGED!",
                    description=f"You were pinged by {message.author.mention} while you were AFK.",
                    color=discord.Color.orange()
                )
                dm_embed.add_field(name="Message", value=message.content, inline=False)
                dm_embed.set_footer(text="AFK System")
                await user.send(embed=dm_embed)

async def setup(bot) -> None:
    await bot.add_cog(AFKCog(bot))
