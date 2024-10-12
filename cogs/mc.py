import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import Context



#atrangi vichitra prani
networkemoji = "<:network:1270364022268760066>"


class Minecraft(commands.Cog, name="minecraft"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.default_icon_url = "https://images-ext-1.discordapp.net/external/QQYQnSuVr1s60UMShOup4RIiQ-F58ruQh713FpJ--Zk/https/www.tripwire.com/sites/default/files/2023-06/minecraft.jpg?format=webp&width=771&height=441"
        self.server_data_cache = {}
        self.mcstats_task.start()

    async def fetch_server_data(self, serverip: str) -> dict:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"https://api.mcsrvstat.us/2/{serverip}") as response:
                    if response.status == 200:
                        return await response.json()
                    return {"error": f"HTTP error {response.status}"}
            except Exception as e:
                return {"error": str(e)}

    async def fetch_icon_url(self, serverip: str) -> str:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"https://eu.mc-api.net/v3/server/favicon/{serverip}") as response:
                    if response.status == 200:
                        return f"https://eu.mc-api.net/v3/server/favicon/{serverip}"
                    return None
            except Exception:
                return None

    @commands.hybrid_command(
        name="livestatus",
        description="Get live status and receive periodic updates."
    )
    async def livestatus(self, context: Context, serverip: str) -> None:
        await context.defer()

        data = await self.fetch_server_data(serverip)
        if "error" in data:
            await context.send(f"Oops! Something went wrong: {data['error']}")
            return

        if not data.get("online"):
            await context.send(f"Seems like the server {serverip} is offline right now.")
            return

        icon_url = await self.fetch_icon_url(serverip) or self.default_icon_url

        embed = discord.Embed(
            title=f" ",
            color=discord.Color.dark_embed()
        )
        emoji = "<:general:1263092233079361607>"
        emoji2 = "<:network:1270364022268760066>"
        embed.add_field(name="Server IP", value=f"__**{serverip}**__", inline=False)
        embed.add_field(name=f"{emoji2} Online Players", value=data["players"]["online"], inline=True)
        embed.add_field(name="Max Players", value=data["players"]["max"], inline=True)
        embed.add_field(name="Version", value=data["version"], inline=True)

        if "list" in data["players"]:
            player_names = ", ".join(data["players"]["list"])
            embed.add_field(name="Players", value=player_names, inline=False)

        if "motd" in data:
            motd = "\n".join(data["motd"]["clean"])
            embed.add_field(name="Description", value=motd, inline=False)

        embed.set_thumbnail(url=icon_url)
        embed.set_footer(text="Updates every 10 minutes")

        if serverip in self.server_data_cache:
            try:
                await self.server_data_cache[serverip].delete()
            except discord.NotFound:
                pass

        message = await context.send(embed=embed)
        self.server_data_cache[serverip] = message

    @commands.hybrid_command(
        name="mcstatus",
        description="Get a snapshot of the Minecraft server status."
    )
    async def mcstatus(self, context: Context, serverip: str) -> None:
        await context.defer()

        data = await self.fetch_server_data(serverip)
        if "error" in data:
            await context.send(f"Oops! Something went wrong: {data['error']}")
            return

        if not data.get("online"):
            await context.send(f"The server {serverip} appears to be offline.")
            return

        icon_url = await self.fetch_icon_url(serverip) or self.default_icon_url

        embed = discord.Embed(
            title=f" ",
            color=discord.Color.dark_embed() 
        )
  
        embed.add_field(name="Server IP", value=f"__**{serverip}**__", inline=False)
        embed.add_field(name=f"{networkemoji} Online Players", value=data["players"]["online"], inline=True)
        embed.add_field(name="Max Players", value=data["players"]["max"], inline=True)
        embed.add_field(name="Version", value=data["version"], inline=True)

        if "list" in data["players"]:
            player_names = ", ".join(data["players"]["list"])
            embed.add_field(name="Players", value=player_names, inline=False)

        if "motd" in data:
            motd = "\n".join(data["motd"]["clean"])
            embed.add_field(name="Description", value=motd, inline=False)

        embed.set_thumbnail(url=icon_url)
        embed.set_footer(text="Status report")

        await context.send(embed=embed)

    @tasks.loop(seconds=600)
    async def mcstats_task(self):
        for serverip, message in self.server_data_cache.items():
            data = await self.fetch_server_data(serverip)
            if "error" in data:
                await message.delete()
                self.server_data_cache.pop(serverip, None)
                continue

            if not data.get("online"):
                await message.delete()
                await message.channel.send(f"The server {serverip} is currently offline.")
                self.server_data_cache.pop(serverip, None)
                continue

            icon_url = await self.fetch_icon_url(serverip) or self.default_icon_url

            embed = discord.Embed(
                title=f"Server Status: {serverip}",
                color=discord.Color.dark_embed()
            )
            emoji = "<:general:1263092233079361607>"
            emoji2 = "<:network:1270364022268760066>"
            embed.add_field(name="Server IP", value=f"__**{serverip}**__", inline=False)
            embed.add_field(name=f"{emoji2} Online Players", value=data["players"]["online"], inline=True)
            embed.add_field(name="Max Players", value=data["players"]["max"], inline=True)
            embed.add_field(name="Version", value=data["version"], inline=True)

            if "list" in data["players"]:
                player_names = ", ".join(data["players"]["list"])
                embed.add_field(name="Players", value=player_names, inline=False)

            if "motd" in data:
                motd = "\n".join(data["motd"]["clean"])
                embed.add_field(name="Description", value=motd, inline=False)

            embed.set_thumbnail(url=icon_url)
            embed.set_footer(text="Updates every 10 minutes")

            try:
                await message.edit(embed=embed)
            except discord.NotFound:
                self.server_data_cache.pop(serverip, None)

async def setup(bot) -> None:
    await bot.add_cog(Minecraft(bot))