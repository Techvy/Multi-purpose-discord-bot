import discord
from discord.ext import commands
from discord.ui import Select, View, Modal, TextInput
import json
import os
import asyncio
import io

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file_path = os.path.join('database', 'config.json')
        self.load_config()
        self.ticket_creators = {}
        self.persistent_views_added = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.persistent_views_added:
            self.bot.add_view(self.TicketSelect(self))
            self.persistent_views_added = True

    def load_config(self):
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    'ticket_title': "Create a Ticket",
                    'ticket_description': "Please select the relevant option to open a ticket.\n\n",
                    'ticket_thumbnail': None,
                    'ticket_author_text': None,
                    'ticket_author_icon_url': None,
                    'ticket_footer_icon_url': None,
                    'ticket_image': None,
                    'ticket_fields': []
                }
        except json.JSONDecodeError as e:
            print(f"Error loading JSON configuration: {e}")
            self.config = {
                'ticket_log_channel_id': None,
                'ticket_category_id': None,
                'ticket_title': "Create a Ticket",
                'ticket_description': "Please select the relevant option to open a ticket.\n\n",
                'ticket_thumbnail': None
            }
        except Exception as e:
            print(f"An unexpected error occurred while loading the configuration: {e}")
            self.config = {
                'ticket_log_channel_id': None,
                'ticket_category_id': None,
                'ticket_title': "Create a Ticket",
                'ticket_description': "Please select the relevant option to open a ticket.\n\n",
                'ticket_thumbnail': None
            }

    def save_config(self):
        if not os.path.exists('database'):
            os.makedirs('database')
        with open(self.config_file_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_log_channel(self):
        if self.config.get('ticket_log_channel_id'):
            return self.bot.get_channel(self.config['ticket_log_channel_id'])
        return None

    def get_ticket_category(self):
        if self.config.get('ticket_category_id'):
            return self.bot.get_channel(self.config['ticket_category_id'])
        return None

    @commands.hybrid_command(name="ticketsetup", description="Setup the ticket system")
    async def ticketsetup(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Ticket System Configuration",
            description="Configure your ticket system using the dropdown menus below.",
            color=discord.Color.blue()
        )

        class SetupSelect(Select):
            def __init__(self, parent_cog):
                self.parent_cog = parent_cog
                options = [
                    discord.SelectOption(label="Ticket Log Channel", description="Set the channel for ticket logs"),
                    discord.SelectOption(label="Ticket Category", description="Set the category for tickets"),
                    discord.SelectOption(label="Reset", description="Reset the configuration settings")
                ]
                super().__init__(placeholder="Select an option", min_values=1, max_values=1, options=options)

            async def callback(self, interaction: discord.Interaction):
                if self.values[0] == "Ticket Log Channel":
                    await interaction.response.send_modal(TicketLogChannelModal(self.parent_cog))
                elif self.values[0] == "Ticket Category":
                    await interaction.response.send_modal(TicketCategoryModal(self.parent_cog))
                elif self.values[0] == "Reset":
                    self.parent_cog.config = {
                        'ticket_log_channel_id': None,
                        'ticket_category_id': None,
                        'ticket_title': "Create a Ticket",
                        'ticket_description': "Please select the relevant option to open a ticket.\n\n",
                        'ticket_thumbnail': None
                    }
                    self.parent_cog.save_config()
                    await interaction.response.send_message("Configuration has been reset.", ephemeral=True)
                else:
                    await interaction.response.send_message("Invalid option selected.", ephemeral=True)

        class TicketLogChannelModal(Modal):
            def __init__(self, parent_cog):
                super().__init__(title="Set Ticket Log Channel")
                self.parent_cog = parent_cog
                self.channel_id = TextInput(label="Channel ID", style=discord.TextStyle.short)
                self.add_item(self.channel_id)

            async def on_submit(self, interaction: discord.Interaction):
                try:
                    channel_id = int(self.channel_id.value)
                    self.parent_cog.config['ticket_log_channel_id'] = channel_id
                    self.parent_cog.save_config()
                    channel = self.parent_cog.bot.get_channel(channel_id)
                    if channel:
                        await interaction.response.send_message(f"Ticket log channel has been set to {channel.mention}", ephemeral=True)
                    else:
                        await interaction.response.send_message("Invalid channel ID. Please try again.", ephemeral=True)
                except ValueError:
                    await interaction.response.send_message("Invalid channel ID. Please enter a valid ID.", ephemeral=True)

        class TicketCategoryModal(Modal):
            def __init__(self, parent_cog):
                super().__init__(title="Set Ticket Category")
                self.parent_cog = parent_cog
                self.category_id = TextInput(label="Category ID", style=discord.TextStyle.short)
                self.add_item(self.category_id)

            async def on_submit(self, interaction: discord.Interaction):
                try:
                    category_id = int(self.category_id.value)
                    self.parent_cog.config['ticket_category_id'] = category_id
                    self.parent_cog.save_config()
                    category = self.parent_cog.bot.get_channel(category_id)
                    if category:
                        await interaction.response.send_message(f"Ticket category has been set to {category.name}", ephemeral=True)
                    else:
                        await interaction.response.send_message("Invalid category ID. Please try again.", ephemeral=True)
                except ValueError:
                    await interaction.response.send_message("Invalid category ID. Please enter a valid ID.", ephemeral=True)

        view = View()
        view.add_item(SetupSelect(self))

        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="ticket", description="Create a ticket")
    async def ticket(self, ctx: commands.Context):
        category = self.get_ticket_category()
        if category is None:
            await ctx.send("Ticket category is not set. Please use /ticketsetup to configure the ticket system.", ephemeral=True)
            return

        embed = discord.Embed(
            title=self.config.get('ticket_title', "Create a Ticket"),
            description=self.config.get('ticket_description', "Click the button below to create a support ticket."),
            color=discord.Color.orange()
        )

        thumbnail_url = self.config.get('ticket_thumbnail')
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        author_text = self.config.get('ticket_author_text')
        author_icon_url = self.config.get('ticket_author_icon_url')
        if author_text and author_icon_url:
            embed.set_author(name=author_text, icon_url=author_icon_url)

        footer_icon_url = self.config.get('ticket_footer_icon_url')
        if footer_icon_url:
            embed.set_footer(text="Powered by Vanilla Development", icon_url=footer_icon_url)

        image_url = self.config.get('ticket_image')
        if image_url:
            embed.set_image(url=image_url)

        for field in self.config.get('ticket_fields', []):
            embed.add_field(name=field['name'], value=field['value'], inline=field.get('inline', False))

        class GeneralSupportButton(discord.ui.Button):
            def __init__(self, parent_cog):
                super().__init__(label="General Support", style=discord.ButtonStyle.primary)
                self.parent_cog = parent_cog

            async def callback(self, interaction: discord.Interaction):
                await interaction.response.defer()
                existing_channel = discord.utils.get(ctx.guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")
                if existing_channel:
                    await interaction.followup.send(f"You already have an open ticket: {existing_channel.mention}", ephemeral=True)
                    return

                category = self.parent_cog.get_ticket_category()
                if category is None:
                    await interaction.followup.send("Ticket category is not set. Please use /ticketsetup to configure the ticket system.", ephemeral=True)
                    return

                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    ctx.guild.get_role(1283000154919800926): discord.PermissionOverwrite(read_messages=True, send_messages=True)  # Add role
                }

                channel = await ctx.guild.create_text_channel(
                    name=f"ticket-{interaction.user.name.lower()}",
                    category=category,
                    overwrites=overwrites
                )


                self.parent_cog.ticket_creators[channel.id] = interaction.user.id

                ticket_embed = discord.Embed(title="__Vanilla Support__", description=f"Hello **{interaction.user.name.lower()}**,\n\n> Welcome to our support team!\n> Please Describe your issue for assistance.", color=discord.Color.default())
                ticket_embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)   
                ticket_embed.set_footer(text="\nWe do not work 24/7. Please wait for a response.")    
                async def set_permissions():
                    await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
                    await channel.set_permissions(ctx.guild.default_role, read_messages=False)

                async def log_ticket_creation():
                    log_channel = self.parent_cog.get_log_channel()
                    if log_channel:
                        embed = discord.Embed(
                            title="Ticket Created",
                            description=f"A new ticket has been created.",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="Created By", value=interaction.user.mention, inline=True)
                        embed.add_field(name="Channel", value=channel.mention, inline=True)
                        embed.set_footer(text=f"Ticket ID: {channel.id}")
                        await log_channel.send(embed=embed)

                async def get_channel_transcript(channel):
                    transcript = ""
                    async for message in channel.history(limit=None, oldest_first=True):
                        transcript += f"{message.created_at} - {message.author}: {message.content}\n"
                    return transcript

                async def close_ticket(interaction: discord.Interaction):
                    if channel.id in self.parent_cog.ticket_creators and self.parent_cog.ticket_creators[channel.id] == interaction.user.id:
                        await interaction.response.send_message("Ticket will be deleted in few seconds.", ephemeral=True)

                        transcript = await get_channel_transcript(channel)
                        log_channel = self.parent_cog.get_log_channel()
                        if log_channel:
                            embed = discord.Embed(
                                title="Ticket Closed",
                                description=f"Ticket {channel.name} has been closed by {interaction.user.mention}.",
                                color=discord.Color.red()
                            )
                            embed.set_footer(text=f"Ticket ID: {channel.id}")
                            await log_channel.send(embed=embed)

                            transcript_file = discord.File(io.StringIO(transcript), filename=f"transcript-{channel.name}.txt")
                            await log_channel.send(file=transcript_file)

                        del self.parent_cog.ticket_creators[channel.id]
                        await channel.delete()
                    else:
                        await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)

                class TicketCloseButton(discord.ui.Button):
                    def __init__(self, parent_cog):
                        self.parent_cog = parent_cog
                        super().__init__(label="🔒 Close Ticket", style=discord.ButtonStyle.success)

                    async def callback(self, interaction: discord.Interaction):
                        await close_ticket(interaction)

                ticket_view = View(timeout=None)
                ticket_view.add_item(TicketCloseButton(self.parent_cog))

                await channel.send(content=f"{interaction.user.mention}", embed=ticket_embed, view=ticket_view)
                await interaction.followup.send(f"Your ticket has been created: {channel.mention}", ephemeral=True)

                await set_permissions()
                await log_ticket_creation()

        view = View(timeout=None)
        view.add_item(GeneralSupportButton(self))

        await ctx.send(embed=embed, view=view)


    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if channel.id in self.ticket_creators:
            del self.ticket_creators[channel.id]

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.component:
            if interaction.data["component_type"] == 2:  # 2 represents buttons
                if interaction.custom_id == "close_ticket":
                    await self.close_ticket(interaction)

    async def close_ticket(self, interaction):
        channel = interaction.channel
        if channel.id in self.ticket_creators and self.ticket_creators[channel.id] == interaction.user.id:
            await interaction.response.send_message("Closing ticket...", ephemeral=True)
            log_channel = self.get_log_channel()
            if log_channel:
                embed = discord.Embed(
                    title="Ticket Closed",
                    description=f"Ticket {channel.name} has been closed by {interaction.user.mention}.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Ticket ID: {channel.id}")
                await log_channel.send(embed=embed)

            del self.ticket_creators[channel.id]
            await channel.delete()
        else:
            await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)


    @commands.hybrid_command(name="ticketembed", description="Previews the ticket message to edit it.")
    async def ticketembed(self, ctx: commands.Context):
        embed = discord.Embed(
            title=self.config.get('ticket_title', "Create a Ticket"),
            description=self.config.get('ticket_description', "Please select the relevant option to open a ticket.\n\n"),
            color=discord.Color.orange()
        )

        thumbnail_url = self.config.get('ticket_thumbnail')
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        author_text = self.config.get('ticket_author_text')
        author_icon_url = self.config.get('ticket_author_icon_url')
        if author_text and author_icon_url:
            embed.set_author(name=author_text, icon_url=author_icon_url)

        footer_icon_url = self.config.get('ticket_footer_icon_url')
        if footer_icon_url:
            embed.set_footer(text="Powered by Blocktune Development", icon_url=footer_icon_url)

        image_url = self.config.get('ticket_image')
        if image_url:
            embed.set_image(url=image_url)

        for field in self.config.get('ticket_fields', []):
            embed.add_field(name=field['name'], value=field['value'], inline=field.get('inline', False))

        class EmbedSetupSelect(Select):
            def __init__(self, parent_cog, preview_message):
                self.parent_cog = parent_cog
                self.preview_message = preview_message
                options = [
                    discord.SelectOption(label="Description", description="Set the description of the ticket embed"),
                    discord.SelectOption(label="Thumbnail URL", description="Set the thumbnail URL of the ticket embed"),
                    discord.SelectOption(label="Author Text", description="Set the author text of the ticket embed"),
                    discord.SelectOption(label="Author Icon URL", description="Set the author icon URL of the ticket embed"),
                    discord.SelectOption(label="Footer Icon URL", description="Set the footer icon URL of the ticket embed"),
                    discord.SelectOption(label="Image URL", description="Set the image URL of the ticket embed"),
                    discord.SelectOption(label="Add Field", description="Add a field to the ticket embed"),
                    discord.SelectOption(label="Reset", description="Reset the embed settings")
                ]
                super().__init__(placeholder="Select an option", min_values=1, max_values=1, options=options)

            async def callback(self, interaction: discord.Interaction):
                if self.values[0] == "Description":
                    await interaction.response.send_modal(TicketDescriptionModal(self.parent_cog, self.preview_message))
                elif self.values[0] == "Thumbnail URL":
                    await interaction.response.send_modal(TicketThumbnailModal(self.parent_cog, self.preview_message))
                elif self.values[0] == "Author Text":
                    await interaction.response.send_modal(TicketAuthorTextModal(self.parent_cog, self.preview_message))
                elif self.values[0] == "Author Icon URL":
                    await interaction.response.send_modal(TicketAuthorIconModal(self.parent_cog, self.preview_message))
                elif self.values[0] == "Footer Icon URL":
                    await interaction.response.send_modal(TicketFooterIconModal(self.parent_cog, self.preview_message))
                elif self.values[0] == "Image URL":
                    await interaction.response.send_modal(TicketImageModal(self.parent_cog, self.preview_message))
                elif self.values[0] == "Add Field":
                    await interaction.response.send_modal(TicketFieldModal(self.parent_cog, self.preview_message))
                elif self.values[0] == "Reset":
                    self.parent_cog.config['ticket_description'] = "Please select the relevant option to open a ticket.\n\n"
                    self.parent_cog.config['ticket_thumbnail'] = None
                    self.parent_cog.config['ticket_author_text'] = None
                    self.parent_cog.config['ticket_author_icon_url'] = None
                    self.parent_cog.config['ticket_footer_icon_url'] = None
                    self.parent_cog.config['ticket_image'] = None
                    self.parent_cog.config['ticket_fields'] = []
                    self.parent_cog.save_config()
                    await self.update_preview()
                    await interaction.response.send_message("Embed settings have been reset.", ephemeral=True)
                else:
                    await interaction.response.send_message("Invalid option selected.", ephemeral=True)

            async def update_preview(self):
                embed = discord.Embed(
                    title=self.parent_cog.config.get('ticket_title', "Create a Ticket"),
                    description=self.parent_cog.config.get('ticket_description', "Please select the relevant option to open a ticket.\n\n"),
                    color=discord.Color.orange()
                )

                thumbnail_url = self.parent_cog.config.get('ticket_thumbnail')
                if thumbnail_url:
                    embed.set_thumbnail(url=thumbnail_url)

                author_text = self.parent_cog.config.get('ticket_author_text')
                author_icon_url = self.parent_cog.config.get('ticket_author_icon_url')
                if author_text and author_icon_url:
                    embed.set_author(name=author_text, icon_url=author_icon_url)
                elif author_text:
                    embed.set_author(name=author_text)

                footer_icon_url = self.parent_cog.config.get('ticket_footer_icon_url')
                if footer_icon_url:
                    embed.set_footer(text="Powered by Blocktune Development", icon_url=footer_icon_url)

                image_url = self.parent_cog.config.get('ticket_image')
                if image_url:
                    embed.set_image(url=image_url)

                for field in self.parent_cog.config.get('ticket_fields', []):
                    embed.add_field(name=field['name'], value=field['value'], inline=field.get('inline', False))

                await self.preview_message.edit(embed=embed)

        class TicketDescriptionModal(Modal):
            def __init__(self, parent_cog, preview_message):
                super().__init__(title="Set Ticket Embed Description")
                self.parent_cog = parent_cog
                self.preview_message = preview_message
                self.description = TextInput(label="Description", style=discord.TextStyle.paragraph)
                self.add_item(self.description)

            async def on_submit(self, interaction: discord.Interaction):
                self.parent_cog.config['ticket_description'] = self.description.value
                self.parent_cog.save_config()
                await self.update_preview()
                await interaction.response.send_message(f"Ticket embed description has been set.", ephemeral=True)

            async def update_preview(self):
                await EmbedSetupSelect(self.parent_cog, self.preview_message).update_preview()

        class TicketThumbnailModal(Modal):
            def __init__(self, parent_cog, preview_message):
                super().__init__(title="Set Ticket Embed Thumbnail URL")
                self.parent_cog = parent_cog
                self.preview_message = preview_message
                self.thumbnail_url = TextInput(label="Thumbnail URL", style=discord.TextStyle.short)
                self.add_item(self.thumbnail_url)

            async def on_submit(self, interaction: discord.Interaction):
                self.parent_cog.config['ticket_thumbnail'] = self.thumbnail_url.value
                self.parent_cog.save_config()
                await self.update_preview()
                await interaction.response.send_message(f"Ticket embed thumbnail URL has been set.", ephemeral=True)

            async def update_preview(self):
                await EmbedSetupSelect(self.parent_cog, self.preview_message).update_preview()

        class TicketAuthorTextModal(Modal):
            def __init__(self, parent_cog, preview_message):
                super().__init__(title="Set Ticket Embed Author Text")
                self.parent_cog = parent_cog
                self.preview_message = preview_message
                self.author_text = TextInput(label="Author Text", style=discord.TextStyle.short)
                self.add_item(self.author_text)

            async def on_submit(self, interaction: discord.Interaction):
                self.parent_cog.config['ticket_author_text'] = self.author_text.value
                self.parent_cog.save_config()
                await self.update_preview()
                await interaction.response.send_message(f"Ticket embed author text has been set.", ephemeral=True)

            async def update_preview(self):
                await EmbedSetupSelect(self.parent_cog, self.preview_message).update_preview()

        class TicketAuthorIconModal(Modal):
            def __init__(self, parent_cog, preview_message):
                super().__init__(title="Set Ticket Embed Author Icon URL")
                self.parent_cog = parent_cog
                self.preview_message = preview_message
                self.author_icon_url = TextInput(label="Author Icon URL", style=discord.TextStyle.short)
                self.add_item(self.author_icon_url)
            async def on_submit(self, interaction: discord.Interaction):
                self.parent_cog.config['ticket_author_icon_url'] = self.author_icon_url.value
                self.parent_cog.save_config()
                await self.update_preview()
                await interaction.response.send_message(f"Ticket embed author icon URL has been set.", ephemeral=True)

            async def update_preview(self):
                await EmbedSetupSelect(self.parent_cog, self.preview_message).update_preview()

        class TicketFooterIconModal(Modal):
            def __init__(self, parent_cog, preview_message):
                super().__init__(title="Set Ticket Embed Footer Icon URL")
                self.parent_cog = parent_cog
                self.preview_message = preview_message
                self.footer_icon_url = TextInput(label="Footer Icon URL", style=discord.TextStyle.short)
                self.add_item(self.footer_icon_url)

            async def on_submit(self, interaction: discord.Interaction):
                self.parent_cog.config['ticket_footer_icon_url'] = self.footer_icon_url.value
                self.parent_cog.save_config()
                await self.update_preview()
                await interaction.response.send_message(f"Ticket embed footer icon URL has been set.", ephemeral=True)

            async def update_preview(self):
                await EmbedSetupSelect(self.parent_cog, self.preview_message).update_preview()

        class TicketImageModal(Modal):
            def __init__(self, parent_cog, preview_message):
                super().__init__(title="Set Ticket Embed Image URL")
                self.parent_cog = parent_cog
                self.preview_message = preview_message
                self.image_url = TextInput(label="Image URL", style=discord.TextStyle.short)
                self.add_item(self.image_url)

            async def on_submit(self, interaction: discord.Interaction):
                self.parent_cog.config['ticket_image'] = self.image_url.value
                self.parent_cog.save_config()
                await self.update_preview()
                await interaction.response.send_message(f"Ticket embed image URL has been set.", ephemeral=True)

            async def update_preview(self):
                await EmbedSetupSelect(self.parent_cog, self.preview_message).update_preview()

        class TicketFieldModal(Modal):
            def __init__(self, parent_cog, preview_message):
                super().__init__(title="Add Ticket Embed Field")
                self.parent_cog = parent_cog
                self.preview_message = preview_message
                self.name = TextInput(label="Field Name", style=discord.TextStyle.short)
                self.value = TextInput(label="Field Value", style=discord.TextStyle.paragraph)
                self.inline = TextInput(label="Inline", style=discord.TextStyle.short, placeholder="True/False")
                self.add_item(self.name)
                self.add_item(self.value)
                self.add_item(self.inline)

            async def on_submit(self, interaction: discord.Interaction):
                fields = self.parent_cog.config.get('ticket_fields', [])
                fields.append({
                    'name': self.name.value,
                    'value': self.value.value,
                    'inline': self.inline.value.lower() == 'true'
                })
                self.parent_cog.config['ticket_fields'] = fields
                self.parent_cog.save_config()
                await self.update_preview()
                await interaction.response.send_message(f"Ticket embed field has been added.", ephemeral=True)

            async def update_preview(self):
                await EmbedSetupSelect(self.parent_cog, self.preview_message).update_preview()

        preview_message = await ctx.send(content="Preview message:", embed=embed)
        view = View()
        view.add_item(EmbedSetupSelect(self, preview_message))

        await preview_message.edit(embed=embed, view=view)
async def setup(bot):
    await bot.add_cog(TicketCog(bot))
