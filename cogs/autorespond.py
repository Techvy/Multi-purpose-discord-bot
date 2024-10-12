import discord
from discord.ext import commands
from discord import app_commands
import json
import os

class AutoRespond(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = os.path.join("database", "automessage.json")
        self.load_config()
        self.enabled = True

    def load_config(self):
        if not os.path.exists(self.config_path):
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump({}, f)
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)

    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    autorespond_group = app_commands.Group(name="autorespond", description="Manage auto-respond messages")

    @autorespond_group.command(name="set", description="Set an auto-respond message")
    @app_commands.describe(trigger="The message to respond to", response="The message to reply with")
    async def autorespond_set(self, interaction: discord.Interaction, trigger: str, response: str):
        trigger_lower = trigger.lower()
        self.config[trigger_lower] = response
        self.save_config()

        embed = discord.Embed(title="Auto-Respond Set", color=discord.Color.green())
        embed.add_field(name="Trigger", value=f'`{trigger}`', inline=False)
        embed.add_field(name="Response", value=response, inline=False)

        await interaction.response.send_message(embed=embed)

    @autorespond_group.command(name="show", description="Show all auto-respond messages")
    async def autorespond_show(self, interaction: discord.Interaction):
        if not self.config:
            embed = discord.Embed(title="Auto-Respond Messages", description="No auto-respond messages set.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(title="Auto-Respond Messages", color=discord.Color.blue())
        for trigger, response in self.config.items():
            embed.add_field(name=trigger, value=response, inline=False)
        await interaction.response.send_message(embed=embed)

    @autorespond_group.command(name="remove", description="Remove an auto-respond message")
    @app_commands.describe(trigger="The message to remove")
    async def autorespond_remove(self, interaction: discord.Interaction, trigger: str):
        trigger_lower = trigger.lower()
        if trigger_lower not in self.config:
            embed = discord.Embed(title="Error", description="That auto-respond message does not exist.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return
        del self.config[trigger_lower]
        self.save_config()
        embed = discord.Embed(title="Auto-Respond Removed", description=f"Auto-respond message '{trigger}' removed.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @autorespond_group.command(name="disable", description="Disable auto-respond messages")
    async def autorespond_disable(self, interaction: discord.Interaction):
        if not self.enabled:
            embed = discord.Embed(title="Error", description="Auto-respond messages are already disabled.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        self.enabled = False
        embed = discord.Embed(title="Auto-Respond Disabled", description="Auto-respond messages disabled.", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)

    @autorespond_group.command(name="enable", description="Enable auto-respond messages")
    async def autorespond_enable(self, interaction: discord.Interaction):
        if self.enabled:
            embed = discord.Embed(title="Info", description="Auto-respond messages are already enabled. To disable, use /autorespond disable.", color=discord.Color.orange())
            await interaction.response.send_message(embed=embed)
            return

        self.enabled = True
        embed = discord.Embed(title="Auto-Respond Enabled", description="Auto-respond messages enabled.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if not self.enabled:
            return

        response = self.config.get(message.content.lower())
        if response:
            embed = discord.Embed(
                description=response,
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(AutoRespond(bot))