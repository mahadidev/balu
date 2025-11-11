import discord
from discord.ext import commands
from discord import app_commands
from chat.chat_manager import GlobalChatManager

class GlobalChatCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_manager = GlobalChatManager(bot)
    
    @commands.group(name='globalchat', aliases=['gc'], invoke_without_command=True)
    async def globalchat(self, ctx):
        """Global chat management commands"""
        embed = discord.Embed(
            title="🌐 Cross Server Chat Room Commands",
            color=0x00ff00,
            description="Cross-server chat room system"
        )
        
        embed.add_field(
            name="📝 Room Management",
            value="`!createRoom <name>` or `/createroom` - Create new chat room\n"
                  "`!rooms` or `/rooms` - List available rooms",
            inline=False
        )
        
        embed.add_field(
            name="📝 Subscription",
            value="`!subscribe <room>` or `/subscribe` - Subscribe to room\n"
                  "`!unsubscribe` or `/unsubscribe` - Unsubscribe from room",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Room Settings (Owner Only)",
            value="`!roomsettings <room_id>` - View room settings using room ID\n"
                  "`!roomset <room_id> <setting> <value>` - Update room setting using room ID",
            inline=False
        )
        
        embed.set_footer(text="Use !globalchat <command> for more details")
        
        await ctx.send(embed=embed)
    
    # Simple command equivalents
    @commands.command(name='createRoom')
    async def create_room_simple(self, ctx, *, room_name: str):
        """Create a new chat room and auto-subscribe current channel"""
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ You need 'Manage Channels' permission to create rooms.")
            return
        
        room_id = self.chat_manager.db.create_chat_room(room_name, str(ctx.author.id))
        
        if room_id:
            # Auto-subscribe the current channel to the new room
            result = await self.chat_manager.register_channel(
                ctx.guild, 
                ctx.channel,
                room_name.strip(),
                ctx.author
            )
            
            await ctx.send(f"✅ Created chat room: **{room_name}**\n{result}")
            
            # Show interactive permission setup
            await self.chat_manager.show_interactive_permissions(
                ctx, 
                room_name.strip(), 
                str(ctx.author.id),
                room_id
            )
        else:
            await ctx.send(f"❌ Room '{room_name}' already exists.")
    
    @commands.command(name='rooms')
    async def list_rooms_simple(self, ctx):
        """List all available chat rooms"""
        rooms = self.chat_manager.db.get_chat_rooms()
        
        if not rooms:
            embed = discord.Embed(
                title="🏠 Cross Server Chat Rooms",
                description="No chat rooms available. Create one with `!createRoom <name>`",
                color=0xff9900
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="🏠 Available Cross Server Chat Rooms",
            color=0x00ff00,
            description=f"Total: {len(rooms)} rooms"
        )
        
        room_list = []
        for room in rooms:
            room_list.append(f"**{room['room_name']}** ({room['subscriber_count']} servers)")
        
        embed.add_field(
            name="Rooms",
            value="\n".join(room_list),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='subscribe')
    async def subscribe_simple(self, ctx, *, room_name: str):
        """Subscribe channel to a chat room"""
        target_channel = ctx.channel
        
        result = await self.chat_manager.register_channel(
            ctx.guild, 
            target_channel,
            room_name.strip(),
            ctx.author
        )
        
        await ctx.send(result)
    
    @commands.command(name='unsubscribe')
    async def unsubscribe_simple(self, ctx, channel: discord.TextChannel = None):
        """Unsubscribe channel from global chat"""
        target_channel = channel or ctx.channel
        
        result = await self.chat_manager.unregister_channel(
            ctx.guild, 
            target_channel, 
            ctx.author
        )
        
        await ctx.send(result)
    
    # Slash commands
    @app_commands.command(name="createroom", description="Create a new chat room and auto-subscribe current channel")
    @app_commands.describe(room_name="Name of the room to create")
    async def createroom_slash(self, interaction: discord.Interaction, room_name: str):
        """Create a new chat room and auto-subscribe current channel"""
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ You need 'Manage Channels' permission to create rooms.", ephemeral=True)
            return
        
        room_id = self.chat_manager.db.create_chat_room(room_name, str(interaction.user.id))
        
        if room_id:
            # Auto-subscribe the current channel to the new room
            result = await self.chat_manager.register_channel(
                interaction.guild, 
                interaction.channel,
                room_name.strip(),
                interaction.user
            )
            
            await interaction.response.send_message(f"✅ Created chat room: **{room_name}**\n{result}")
            
            # Show interactive permission setup for slash commands
            class FakeCtx:
                def __init__(self, interaction):
                    self.author = interaction.user
                    self.channel = interaction.channel
                    self.guild = interaction.guild
                    self.send = interaction.followup.send
            
            fake_ctx = FakeCtx(interaction)
            await self.chat_manager.show_interactive_permissions(
                fake_ctx, 
                room_name.strip(), 
                str(interaction.user.id),
                room_id
            )
        else:
            await interaction.response.send_message(f"❌ Room '{room_name}' already exists.")
    
    @app_commands.command(name="rooms", description="List all available chat rooms")
    async def rooms_slash(self, interaction: discord.Interaction):
        """List all available chat rooms"""
        rooms = self.chat_manager.db.get_chat_rooms()
        
        if not rooms:
            embed = discord.Embed(
                title="🏠 Cross Server Chat Rooms",
                description="No chat rooms available. Create one with `/createroom`",
                color=0xff9900
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="🏠 Available Cross Server Chat Rooms",
            color=0x00ff00,
            description=f"Total: {len(rooms)} rooms"
        )
        
        room_list = []
        for room in rooms:
            room_list.append(f"**{room['room_name']}** ({room['subscriber_count']} servers)")
        
        embed.add_field(
            name="Rooms",
            value="\n".join(room_list),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="subscribe", description="Subscribe channel to a chat room")
    @app_commands.describe(
        room_name="Name of the room to subscribe to",
        channel="Channel to subscribe (defaults to current channel)"
    )
    async def subscribe_slash(self, interaction: discord.Interaction, room_name: str, channel: discord.TextChannel = None):
        """Subscribe channel to a chat room"""
        target_channel = channel or interaction.channel
        
        result = await self.chat_manager.register_channel(
            interaction.guild, 
            target_channel,
            room_name,
            interaction.user
        )
        
        await interaction.response.send_message(result)
    
    @app_commands.command(name="unsubscribe", description="Unsubscribe channel from global chat")
    @app_commands.describe(channel="Channel to unsubscribe (defaults to current channel)")
    async def unsubscribe_slash(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Unsubscribe channel from global chat"""
        target_channel = channel or interaction.channel
        
        result = await self.chat_manager.unregister_channel(
            interaction.guild, 
            target_channel, 
            interaction.user
        )
        
        await interaction.response.send_message(result)
    
    @globalchat.command(name='createroom')
    async def create_room(self, ctx, *, room_name: str):
        """Create a new chat room and auto-subscribe current channel"""
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ You need 'Manage Channels' permission to create rooms.")
            return
        
        room_id = self.chat_manager.db.create_chat_room(room_name, str(ctx.author.id))
        
        if room_id:
            # Auto-subscribe the current channel to the new room
            result = await self.chat_manager.register_channel(
                ctx.guild, 
                ctx.channel,
                room_name.strip(),
                ctx.author
            )
            
            await ctx.send(f"✅ Created chat room: **{room_name}**\n{result}")
            
            # Show interactive permission setup
            await self.chat_manager.show_interactive_permissions(
                ctx, 
                room_name.strip(), 
                str(ctx.author.id),
                room_id
            )
        else:
            await ctx.send(f"❌ Room '{room_name}' already exists.")
    
    @globalchat.command(name='rooms')
    async def list_rooms(self, ctx):
        """List all available chat rooms"""
        rooms = self.chat_manager.db.get_chat_rooms()
        
        if not rooms:
            embed = discord.Embed(
                title="🏠 Chat Rooms",
                description="No chat rooms available. Create one with `!globalchat createroom <name>`",
                color=0xff9900
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="🏠 Available Chat Rooms",
            color=0x00ff00,
            description=f"Total: {len(rooms)} rooms"
        )
        
        room_list = []
        for room in rooms:
            room_list.append(f"**{room['room_name']}** ({room['subscriber_count']} servers)")
        
        embed.add_field(
            name="Rooms",
            value="\n".join(room_list),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @globalchat.command(name='register')
    async def register_channel(self, ctx, *, room_name: str):
        """Register a channel to a chat room"""
        target_channel = ctx.channel
        
        result = await self.chat_manager.register_channel(
            ctx.guild, 
            target_channel,
            room_name.strip(),
            ctx.author
        )
        
        await ctx.send(result)
    
    @globalchat.command(name='unregister')
    async def unregister_channel(self, ctx, channel: discord.TextChannel = None):
        """Unregister a channel from global chat"""
        target_channel = channel or ctx.channel
        
        result = await self.chat_manager.unregister_channel(
            ctx.guild, 
            target_channel, 
            ctx.author
        )
        
        await ctx.send(result)
    
    @commands.command(name='roomsettings')
    async def room_settings(self, ctx, room_id: int):
        """View room settings using room ID (owner only)"""
        # Check if room exists by ID
        room = self.chat_manager.db.get_room_by_id(room_id)
        
        if not room:
            await ctx.send(f"❌ Room with ID {room_id} not found.")
            return
        
        # Check if user is room owner
        if not self.chat_manager.db.is_room_owner_by_id(room_id, str(ctx.author.id)):
            await ctx.send(f"❌ Only the room owner can view settings for **{room['room_name']}** (ID: {room_id}).")
            return
        
        # Get room permissions
        perms = self.chat_manager.db.get_room_permissions_by_id(room_id)
        
        embed = discord.Embed(
            title=f"⚙️ Room Settings: {room['room_name']}",
            color=0x00ff00,
            description=f"**Room ID:** {room_id}\n**Owner:** <@{room['created_by']}>"
        )
        
        embed.add_field(
            name="📝 Content Settings",
            value=f"🔗 Allow URLs: {'✅ Yes' if perms['allow_urls'] else '❌ No'}\n"
                  f"📎 Allow Files: {'✅ Yes' if perms['allow_files'] else '❌ No'}\n"
                  f"🚫 Bad Word Filter: {'✅ On' if perms['enable_bad_word_filter'] else '❌ Off'}\n"
                  f"💬 Allow Mentions: {'✅ Yes' if perms['allow_mentions'] else '❌ No'}\n"
                  f"😀 Allow Emojis: {'✅ Yes' if perms['allow_emojis'] else '❌ No'}",
            inline=False
        )
        
        embed.add_field(
            name="⏱️ Rate Limits",
            value=f"📏 Max Message Length: {perms['max_message_length']} chars\n"
                  f"⏰ Rate Limit: {perms['rate_limit_seconds']} seconds",
            inline=False
        )
        
        embed.add_field(
            name="📖 Usage",
            value="`!roomset <room_id> allow_urls true/false`\n"
                  "`!roomset <room_id> allow_files true/false`\n"
                  "`!roomset <room_id> bad_word_filter true/false`\n"
                  "`!roomset <room_id> allow_mentions true/false`\n"
                  "`!roomset <room_id> allow_emojis true/false`\n"
                  "`!roomset <room_id> max_length <number>`\n"
                  "`!roomset <room_id> rate_limit <seconds>`",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='roomset')
    async def room_set(self, ctx, room_id: int, setting: str, *, value: str):
        """Update room setting using room ID (owner only)"""
        # Check if room exists by ID
        room = self.chat_manager.db.get_room_by_id(room_id)
        
        if not room:
            await ctx.send(f"❌ Room with ID {room_id} not found.")
            return
        
        # Check if user is room owner
        if not self.chat_manager.db.is_room_owner_by_id(room_id, str(ctx.author.id)):
            await ctx.send(f"❌ Only the room owner can change settings for **{room['room_name']}** (ID: {room_id}).")
            return
        
        # Validate and process setting
        setting = setting.lower()
        value = value.lower().strip()
        
        valid_settings = {
            'allow_urls': ('allow_urls', ['true', 'false', 'yes', 'no', 'on', 'off']),
            'allow_files': ('allow_files', ['true', 'false', 'yes', 'no', 'on', 'off']),
            'bad_word_filter': ('enable_bad_word_filter', ['true', 'false', 'yes', 'no', 'on', 'off']),
            'allow_mentions': ('allow_mentions', ['true', 'false', 'yes', 'no', 'on', 'off']),
            'allow_emojis': ('allow_emojis', ['true', 'false', 'yes', 'no', 'on', 'off']),
            'max_length': ('max_message_length', None),
            'rate_limit': ('rate_limit_seconds', None)
        }
        
        if setting not in valid_settings:
            await ctx.send(f"❌ Invalid setting. Valid options: {', '.join(valid_settings.keys())}")
            return
        
        db_field, valid_values = valid_settings[setting]
        
        # Process boolean values
        if valid_values:
            if value in ['true', 'yes', 'on']:
                processed_value = 1
                display_value = 'enabled'
            elif value in ['false', 'no', 'off']:
                processed_value = 0
                display_value = 'disabled'
            else:
                await ctx.send(f"❌ Invalid value for {setting}. Use: true/false, yes/no, or on/off")
                return
        else:
            # Process numeric values
            try:
                processed_value = int(value)
                if setting == 'max_length' and (processed_value < 10 or processed_value > 4000):
                    await ctx.send("❌ Max length must be between 10 and 4000 characters.")
                    return
                elif setting == 'rate_limit' and (processed_value < 0 or processed_value > 300):
                    await ctx.send("❌ Rate limit must be between 0 and 300 seconds.")
                    return
                display_value = str(processed_value)
            except ValueError:
                await ctx.send(f"❌ {setting} must be a number.")
                return
        
        # Update the setting using room ID
        success = self.chat_manager.db.update_room_permission_by_id(
            room_id, 
            db_field, 
            processed_value, 
            str(ctx.author.id)
        )
        
        if success:
            await ctx.send(f"✅ Updated **{setting}** to **{display_value}** for room **{room['room_name']}** (ID: {room_id}).")
        else:
            await ctx.send(f"❌ Failed to update setting for room **{room['room_name']}** (ID: {room_id}).")
    
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages in global chat channels"""
        await self.chat_manager.handle_message(message)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle reaction-based permission toggles"""
        if payload.user_id == self.bot.user.id:  # Ignore bot's own reactions
            return
        await self.chat_manager.handle_permission_reaction(payload)
    
    @globalchat.error
    async def globalchat_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided.")
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")

async def setup(bot):
    cog = GlobalChatCommands(bot)
    await bot.add_cog(cog)