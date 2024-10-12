import discord
from discord.ext import commands
from discord.ui import Select, View, Button, Modal, TextInput
import json
import os
import asyncio

class EmbedSetupModal(Modal):
    def __init__(self, field_type, parent_cog, preview_message):
        super().__init__(title=f'Set {field_type}')
        self.field_type = field_type
        self.parent_cog = parent_cog
        self.preview_message = preview_message
        
        if field_type == "Color":
            self.add_item(TextInput(label='Enter color code (e.g., #FF0000)', style=discord.TextStyle.short))
        elif field_type in ["Author Text", "Author Icon URL", "Footer Icon URL", "Image", "Thumbnail URL"]:
            self.add_item(TextInput(label=f'Enter {field_type}', style=discord.TextStyle.short))
        elif field_type in ["Add Field", "Add Inline Field"]:
            self.add_item(TextInput(label='Field Name', style=discord.TextStyle.short))
            self.add_item(TextInput(label='Field Value', style=discord.TextStyle.paragraph))
        else:
            self.add_item(TextInput(label=f'Enter {field_type}', style=discord.TextStyle.short))

    async def on_submit(self, interaction: discord.Interaction):
        field_value = self.children[0].value
        if self.field_type in ["Add Field", "Add Inline Field"]:
            field_name = self.children[0].value
            field_value = self.children[1].value
        
        config_path = os.path.join('database', 'embed.json')

        if not os.path.exists('database'):
            os.makedirs('database')

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    embed_data = json.load(f)
            else:
                embed_data = {}
        except json.JSONDecodeError:
            embed_data = {}

        if self.field_type in ["Add Field", "Add Inline Field"]:
            fields = embed_data.get('Fields', [])
            field = {"name": field_name, "value": field_value, "inline": (self.field_type == "Add Inline Field")}
            fields.append(field)
            embed_data['Fields'] = fields
        elif self.field_type == "Color":
            # Ensure the color value is a valid hexadecimal string
            if not field_value.startswith("#"):
                field_value = "#" + field_value
            embed_data['Color'] = int(field_value.lstrip('#'), 16)
        else:
            embed_data[self.field_type] = field_value

        with open(config_path, 'w') as f:
            json.dump(embed_data, f, indent=4)

        await self.update_preview()
        await interaction.response.send_message(f"{self.field_type} saved!", ephemeral=True)

    async def update_preview(self):
        config_path = os.path.join('database', 'embed.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    embed_data = json.load(f)
            else:
                embed_data = {}
        except json.JSONDecodeError:
            embed_data = {}

        embed = discord.Embed(
            title=embed_data.get('Title', 'Title'),
            description=embed_data.get('Description', 'Description'),
            color=embed_data.get('Color', discord.Color.blue().value)  # Default to blue if no color is set
        )

        thumbnail_url = embed_data.get('Thumbnail URL')
        if thumbnail_url:
            print(f"Setting thumbnail: {thumbnail_url}")  # Debug line
            embed.set_thumbnail(url=thumbnail_url)

        author_text = embed_data.get('Author Text')
        author_icon_url = embed_data.get('Author Icon URL')
        if author_text:
            embed.set_author(name=author_text, icon_url=author_icon_url)

        footer_icon_url = embed_data.get('Footer Icon URL')
        if footer_icon_url:
            embed.set_footer(icon_url=footer_icon_url)

        fields = embed_data.get('Fields', [])
        for field in fields:
            embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

        image_url = embed_data.get('Image')
        if image_url:
            embed.set_image(url=image_url)

        await self.preview_message.edit(embed=embed)

class EmbedActionDropdown(Select):
    def __init__(self, field_name, parent_cog, preview_message):
        self.field_name = field_name
        self.parent_cog = parent_cog
        self.preview_message = preview_message
        options = [
            discord.SelectOption(label='Edit', description=f'Edit {field_name}'), 
            discord.SelectOption(label='Reset', description=f'Reset {field_name}')
        ]
        super().__init__(placeholder=f'Actions for {field_name}', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == 'Edit':
            modal = EmbedSetupModal(self.field_name, self.parent_cog, self.preview_message)
            await interaction.response.send_modal(modal)
        elif self.values[0] == 'Cancel':
            # Remove the dropdown and send a cancellation message
            await interaction.response.send_message(f'Editing of {self.field_name} has been canceled.', ephemeral=True)
            
            # Create a new view without the dropdown
            view = View()
            
            # Recreate and add other components (if needed)
            # e.g., view.add_item(EmbedDropdown(self.parent_cog, self.preview_message))
            view.add_item(EmbedSendButton(self.parent_cog, self.preview_message))
             
            await self.preview_message.edit(view=view)
        elif self.values[0] == 'Delete':
            config_path = os.path.join('database', 'embed.json')
            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        embed_data = json.load(f)
                else:
                    embed_data = {}
            except json.JSONDecodeError:
                embed_data = {}

            if 'Fields' in embed_data:
                fields = embed_data['Fields']
                fields = [field for field in fields if field['name'] != self.field_name]
                embed_data['Fields'] = fields
                with open(config_path, 'w') as f:
                    json.dump(embed_data, f, indent=4)
                await self.update_preview()
                await interaction.response.send_message(f'{self.field_name} has been deleted from the embed.', ephemeral=True)
            else:
                await interaction.response.send_message(f'{self.field_name} not found in the embed.', ephemeral=True)

    async def update_preview(self):
        config_path = os.path.join('database', 'embed.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    embed_data = json.load(f)
            else:
                embed_data = {}
        except json.JSONDecodeError:
            embed_data = {}

        embed = discord.Embed(
            title=embed_data.get('Title', 'Title'),
            description=embed_data.get('Description', 'Description'),
            color=int(embed_data.get('Color', '0x0000FF'), 16) 
        )

        thumbnail_url = embed_data.get('Thumbnail URL')
        if thumbnail_url:
            print(f"Setting thumbnail: {thumbnail_url}")  # Debug line
            embed.set_thumbnail(url=thumbnail_url)

        author_text = embed_data.get('Author Text')
        author_icon_url = embed_data.get('Author Icon URL')
        if author_text:
            embed.set_author(name=author_text, icon_url=author_icon_url)

        footer_icon_url = embed_data.get('Footer Icon URL')
        if footer_icon_url:
            embed.set_footer(icon_url=footer_icon_url)

        fields = embed_data.get('Fields', [])
        for field in fields:
            embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

        image_url = embed_data.get('Image')
        if image_url:
            embed.set_image(url=image_url)

        await self.preview_message.edit(embed=embed)

class EmbedDropdown(Select):
    def __init__(self, parent_cog, preview_message):
        self.parent_cog = parent_cog
        self.preview_message = preview_message
        options = [
            discord.SelectOption(label='Title', description='Set the title of the embed'),
            discord.SelectOption(label='Description', description='Set the description of the embed'),
            discord.SelectOption(label='Thumbnail URL', description='Set the thumbnail URL of the embed'),
            discord.SelectOption(label='Author Text', description='Set the author text of the embed'),
            discord.SelectOption(label='Author Icon URL', description='Set the author icon URL of the embed'),
            discord.SelectOption(label='Footer Icon URL', description='Set the footer icon URL of the embed'),
            discord.SelectOption(label='Add Field', description='Add a field to the embed'),
            discord.SelectOption(label='Add Inline Field', description='Add an inline field to the embed'),
            discord.SelectOption(label='Color', description='Set the color of the embed'),
            discord.SelectOption(label='Image', description='Set the image URL of the embed'),
            discord.SelectOption(label='Reset', description='Reset the embed settings')
        ]
        super().__init__(placeholder='Edit embed', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == 'Reset':
            self.parent_cog.reset_embed_config()
            await self.update_preview()
            await interaction.response.send_message("Embed settings have been reset.", ephemeral=True)
        else:
            field_name = self.values[0]
            action_dropdown = EmbedActionDropdown(field_name, self.parent_cog, self.preview_message)
            view = View()
            view.add_item(action_dropdown)
            await interaction.response.send_message(f"What action should be done to {field_name}?", view=view, ephemeral=True)

    async def update_preview(self):
        config_path = os.path.join('database', 'embed.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    embed_data = json.load(f)
            else:
                embed_data = {}
        except json.JSONDecodeError:
            embed_data = {}

        embed = discord.Embed(
            title=embed_data.get('Title', 'Title'),
            description=embed_data.get('Description', 'Description'),
            color=int(embed_data.get('Color', '0x0000FF'), 16) 
        )

        thumbnail_url = embed_data.get('Thumbnail URL')
        if thumbnail_url:
            print(f"Setting thumbnail: {thumbnail_url}")  # Debug line
            embed.set_thumbnail(url=thumbnail_url)

        author_text = embed_data.get('Author Text')
        author_icon_url = embed_data.get('Author Icon URL')
        if author_text:
            embed.set_author(name=author_text, icon_url=author_icon_url)

        footer_icon_url = embed_data.get('Footer Icon URL')
        if footer_icon_url:
            embed.set_footer(icon_url=footer_icon_url)

        fields = embed_data.get('Fields', [])
        for field in fields:
            embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

        image_url = embed_data.get('Image')
        if image_url:
            embed.set_image(url=image_url)

        await self.preview_message.edit(embed=embed)

class EmbedSendButton(Button):
    def __init__(self, parent_cog, preview_message):
        super().__init__(label="Finish", style=discord.ButtonStyle.success)
        self.parent_cog = parent_cog
        self.preview_message = preview_message

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Please mention the channel you want to send the embed to.", ephemeral=True)

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel and msg.channel_mentions

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=30)
            channel = msg.channel_mentions[0]
            config_path = os.path.join('database', 'embed.json')

            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        embed_data = json.load(f)
                else:
                    embed_data = {}
            except json.JSONDecodeError:
                embed_data = {}

            embed = discord.Embed(
                title=embed_data.get('Title', ''),
                description=embed_data.get('Description', ''),
            )

            thumbnail_url = embed_data.get('Thumbnail URL', '')
            if thumbnail_url:
                print(f"Setting thumbnail: {thumbnail_url}")  # Debug line
                embed.set_thumbnail(url=thumbnail_url)

            author_text = embed_data.get('Author Text')
            author_icon_url = embed_data.get('Author Icon URL')
            if author_text:
                embed.set_author(name=author_text, icon_url=author_icon_url)

            footer_icon_url = embed_data.get('Footer Icon URL')
            if footer_icon_url:
                embed.set_footer(icon_url=footer_icon_url)

            fields = embed_data.get('Fields', [])
            for field in fields:
                embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

            image_url = embed_data.get('Image', '')
            if image_url:
                embed.set_image(url=image_url)

            await channel.send(embed=embed)
            await interaction.followup.send(f"Embed sent to {channel.mention}", ephemeral=True)
            self.parent_cog.reset_embed_config()  # Reset the config file after sending the embed
        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out waiting for a channel mention.", ephemeral=True)

class AdvancedCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="embed", description="Previews and edits the embed message.")
    async def embed(self, ctx: commands.Context):
        embed = discord.Embed(
            title='Title',
            description='Description',
            color=discord.Color.green()
        )

        preview_message = await ctx.send(content="Use the dropdown to start editing!", embed=embed)
        view = View()
        view.add_item(EmbedDropdown(self, preview_message))
        view.add_item(EmbedSendButton(self, preview_message))
        await preview_message.edit(embed=embed, view=view)

    def reset_embed_config(self):
        config_path = os.path.join('database', 'embed.json')
        if os.path.exists(config_path):
            os.remove(config_path)

async def setup(bot):
    await bot.add_cog(AdvancedCommands(bot))