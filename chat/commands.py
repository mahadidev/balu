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
        
        embed.set_footer(text="Use !globalchat <command> for more details")
        
        await ctx.send(embed=embed)
    
    # Simple command equivalents
    @commands.command(name='createRoom')
    async def create_room_simple(self, ctx, *, room_name: str):
        """Create a new chat room and auto-subscribe current channel"""
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ You need 'Manage Channels' permission to create rooms.")
            return
        
        success = self.chat_manager.db.create_chat_room(room_name, str(ctx.author.id))
        
        if success:
            # Auto-subscribe the current channel to the new room
            result = await self.chat_manager.register_channel(
                ctx.guild, 
                ctx.channel,
                room_name.strip(),
                ctx.author
            )
            
            await ctx.send(f"✅ Created chat room: **{room_name}**\n{result}")
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
        
        success = self.chat_manager.db.create_chat_room(room_name, str(interaction.user.id))
        
        if success:
            # Auto-subscribe the current channel to the new room
            result = await self.chat_manager.register_channel(
                interaction.guild, 
                interaction.channel,
                room_name.strip(),
                interaction.user
            )
            
            await interaction.response.send_message(f"✅ Created chat room: **{room_name}**\n{result}")
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
        
        success = self.chat_manager.db.create_chat_room(room_name, str(ctx.author.id))
        
        if success:
            # Auto-subscribe the current channel to the new room
            result = await self.chat_manager.register_channel(
                ctx.guild, 
                ctx.channel,
                room_name.strip(),
                ctx.author
            )
            
            await ctx.send(f"✅ Created chat room: **{room_name}**\n{result}")
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
    
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages in global chat channels"""
        await self.chat_manager.handle_message(message)
    
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