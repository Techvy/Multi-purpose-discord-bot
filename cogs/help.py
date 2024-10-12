import discord
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Get help with the bot")
    async def help(self, ctx: commands.Context, command: str = None):
        if command is None:
            # Show general help menu
            embed = discord.Embed(title="__Help Menu__:", description="**Categories**\n- <:general:1263092233079361607> General\n- <:moderation:1263092343461117974> Moderation\n- <:fun:1263166738762174588> Fun", color=0x6064f4)
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_footer(text="Select a category from the dropdown menu")
            select = discord.ui.Select(placeholder="Choose a category to view its commands")

            select.add_option(label="General", emoji="<:general:1263092233079361607>", description="General commands")
            select.add_option(label="Fun", emoji="<:fun:1263166738762174588>", description="Fun commands")
            if ctx.author.guild_permissions.administrator:
                select.add_option(label="Moderation", emoji="<:moderation:1263092343461117974>", description="Moderation commands")

            async def select_callback(interaction):
                if select.values[0] == "General":
                    embed.title = "**<:general:1263092233079361607> __General Category__**"
                    embed.description = ""
                    embed.clear_fields()
                    embed.add_field(name="\❓ Commands:", value=""" 
- autorespond **show**: Shows all auto-respond messages.
- autorespond **enable**: Enable auto-respond messages.
- autorespond **set**: Set an auto-respond message.
- autorespond **remove**: Remove an auto-respond message.
- autorespond **disable**: Disable auto-respond messages.      
- botinfo: Get some useful (or not) information about the bot.
- serverinfo: Get some useful (or not) information about the server.
- ping: Check if the bot is alive.
- 8ball: Ask any question to the bot.
- mcstatus: Get information about a Minecraft server.
- avatar: Get a user's avatar.
- timer: Starts a timer.
- membercount: Displays the member count of the server.
- userinfo: Displays information about a user.
- afk: Sets an user to afk.
""", inline=False)
                    embed.add_field(name="**DO /HELP <COMMAND> FOR MORE INFO**", value="")
                elif select.values[0] == "Moderation":
                    if ctx.author.guild_permissions.administrator:
                        embed.title = "<:moderation:1263092343461117974> **__Moderation Category__**"
                        embed.description = ""
                        embed.clear_fields()
                        embed.add_field(name="\❓ Commands:", value="""
- slowmode: Set a slowmode delay for the current channel.
- noslowmode: Removes the slowmode delay for the current channel.
- kick: Kicks a user out of the server.
- nick: Changes the nickname of a user on the server.
- unnick: Resets the nickname of a user on the server.
- ban: Ban a user from the server.
- purge: Delete a specified number of messages.
- lock: Locks a channel.
- unlock: Unlocks a channel.
- mute: Mutes a member.
- unmute: Unmutes a member.
- rename: Renames a channel.
- nuke: Deletes the channel and clones it to remove pings.
    """, inline=False)
                        await interaction.response.edit_message(embed=embed)
                    else:
                        await interaction.response.send_message("You do not have admin perms to view mod commands.", ephemeral=True)                        
                        embed.add_field(name="**DO /HELP <COMMAND> FOR MORE INFO**", value="")
                elif select.values[0] == "Fun":
                    embed.title = "**<:fun:1263166738762174588> __Fun Category__**"
                    embed.description = ""
                    embed.clear_fields()
                    embed.add_field(name="\❓ Commands:", value="""
- TicTacToe: Advanced multiplayer online TicTacToe.
""", inline=False)
                    embed.add_field(name="**DO /HELP <COMMAND> FOR MORE INFO**", value="")
                await interaction.response.edit_message(embed=embed)

            select.callback = select_callback

            view = discord.ui.View()
            view.add_item(select)

            await ctx.send(embed=embed, view=view)
        else:
            # Show help for specific command
            command_obj = self.bot.get_command(command)
            if command_obj:
                embed = discord.Embed(title=f"Help for `{command}`", description="", color=discord.Color.dark_embed())
                if command == "botinfo":
                    embed.description = "Get some useful (or not) information about the bot."
                    embed.add_field(name="Usage", value="`/botinfo`", inline=False)
                elif command == "serverinfo":
                    embed.description = "Get some useful (or not) information about the server."
                    embed.add_field(name="Usage", value="`/serverinfo`", inline=False)
                elif command == "ping":
                    embed.description = "Check if the bot is alive."
                    embed.add_field(name="Usage", value="`/ping`", inline=False)
                elif command == "8ball":
                    embed.description = "Ask any question to the bot."
                    embed.add_field(name="Usage", value="`/8ball <question>`", inline=False)
                elif command == "mcstatus":
                    embed.description = "Get information about a Minecraft server."
                    embed.add_field(name="Usage", value="`/mcstatus <server IP>`", inline=False)
                elif command == "avatar":
                    embed.description = "Get a user's avatar."
                    embed.add_field(name="Usage", value="`/avatar [user]`", inline=False)
                elif command == "timer":
                    embed.description = "Starts a timer."
                    embed.add_field(name="Usage", value="`/timer <duration>`", inline=False)
                elif command == "membercount":
                    embed.description = "Displays the member count of the server."
                    embed.add_field(name="Usage", value="`/membercount`", inline=False)
                elif command == "userinfo":
                    embed.description = "Displays information about a user."
                    embed.add_field(name="Usage", value="`/userinfo [user]`", inline=False)
                elif command == "afk":
                    embed.description = "Sets an user to afk."
                    embed.add_field(name="Usage", value="`/afk <reason>`", inline=False)
                elif command == "slowmode":
                    embed.description = "Set a slowmode delay for the current channel."
                    embed.add_field(name="Usage", value="`/slowmode <seconds>`", inline=False)
                elif command == "noslowmode":
                    embed.description = "Removes the slowmode delay for the current channel."
                    embed.add_field(name="Usage", value="`/noslowmode`", inline=False)
                elif command == "kick":
                    embed.description = "Kicks a user out of the server."
                    embed.add_field(name="Usage", value="`/kick <user>`", inline=False)
                elif command == "nick":
                    embed.description = "Changes the nickname of a user on the server."
                    embed.add_field(name="Usage", value="`/nick <user> <nickname>`", inline=False)
                elif command == "unnick":
                    embed.description = "Resets the nickname of a user on the server."
                    embed.add_field(name="Usage", value="`/unnick <user>`", inline=False)
                elif command == "ban":
                    embed.description = "Ban a user from the server."
                    embed.add_field(name="Usage", value="`/ban <user>`", inline=False)
                elif command == "purge":
                    embed.description = "Delete a specified number of messages."
                    embed.add_field(name="Usage", value="`/purge <number>`", inline=False)
                elif command == "lock":
                    embed.description = "Locks a channel."
                    embed.add_field(name="Usage", value="`/lock`", inline=False)
                elif command == "unlock":
                    embed.description = "Unlocks a channel."
                    embed.add_field(name="Usage", value="`/unlock`", inline=False)
                elif command == "mute":
                    embed.description = "Mutes a member."
                    embed.add_field(name="Usage", value="`/mute <user>`", inline=False)
                elif command == "unmute":
                    embed.description = "Unmutes a member."
                    embed.add_field(name="Usage", value="`/unmute <user>`", inline=False)
                elif command == "rename":
                    embed.description = "Renames a channel."
                    embed.add_field(name="Usage", value="`/rename <new name>`", inline=False)
                elif command == "nuke":
                    embed.description = "Deletes the channel and clones it to remove pings."
                    embed.add_field(name="Usage", value="`/nuke`", inline=False)
                else:
                    embed.description = "No description available."
                    embed.add_field(name="Usage", value=f"`/{command}`", inline=False)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No command named `{command}` found.")

async def setup(bot) -> None:
    await bot.add_cog(HelpCog(bot))
