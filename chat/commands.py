import discord
from discord.ext import commands
from discord import app_commands
import sys
sys.path.insert(0, '/app')
from shared.database.manager import db_manager
from shared.cache.cache_manager import cache_manager


class GlobalChatCommands(commands.Cog):
    """Discord commands for the Global Chat System with new database backend."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(name='globalchat', aliases=['gc'], invoke_without_command=True)
    async def globalchat(self, ctx):
        """Global chat management commands"""
        embed = discord.Embed(
            title="🌐 Global Chat System",
            color=0x00ff00,
            description="Cross-server chat system with PostgreSQL backend"
        )
        
        embed.add_field(
            name="📝 Basic Commands",
            value="`!register <room_name>` - Register this channel to a room\n"
                  "`!unregister` - Remove this channel from global chat\n"
                  "`!rooms` - List available rooms",
            inline=False
        )
        
        embed.add_field(
            name="🏠 Room Management",
            value="`!createroom <name>` - Create new room (requires Manage Channels)\n"
                  "`!roominfo <room_name>` - Get room information",
            inline=False
        )
        
        embed.add_field(
            name="💬 Usage",
            value="Just send messages in registered channels!\n"
                  "Your messages will appear in all other channels registered to the same room.",
            inline=False
        )
        
        embed.set_footer(text="Use !globalchat <command> for more details")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='rooms')
    async def list_rooms(self, ctx):
        """List all available chat rooms"""
        try:
            rooms = await db_manager.get_all_rooms()
            
            if not rooms:
                embed = discord.Embed(
                    title="🏠 Global Chat Rooms",
                    description="No chat rooms available. Create one with `!createroom <name>`",
                    color=0xff9900
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="🏠 Available Global Chat Rooms",
                color=0x00ff00,
                description=f"Total: {len(rooms)} rooms"
            )
            
            room_list = []
            for room in rooms:
                status = "🟢 Active" if room['is_active'] else "🔴 Inactive"
                room_list.append(f"**{room['name']}** - {status} ({room['channel_count']} channels)")
            
            embed.add_field(
                name="Rooms",
                value="\n".join(room_list) if room_list else "No rooms available",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error fetching rooms: {str(e)}")
    
    @commands.command(name='createroom')
    async def create_room(self, ctx, *, room_name: str):
        """Create a new chat room"""
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ You need 'Manage Channels' permission to create rooms.")
            return
        
        try:
            # Check if room already exists
            existing_room = await db_manager.get_room_by_name(room_name.strip())
            if existing_room:
                await ctx.send(f"❌ Room '{room_name}' already exists.")
                return
            
            # Create the room
            room_id = await db_manager.create_room(
                name=room_name.strip(),
                created_by=str(ctx.author.id),
                max_servers=50
            )
            
            if room_id:
                await ctx.send(f"✅ Created chat room: **{room_name}**\n"
                             f"Room ID: {room_id}\n"
                             f"Use `!register {room_name}` to connect this channel to the room.")
            else:
                await ctx.send(f"❌ Failed to create room '{room_name}'.")
                
        except Exception as e:
            await ctx.send(f"❌ Error creating room: {str(e)}")
    
    @commands.command(name='register')
    async def register_channel(self, ctx, *, room_name: str):
        """Register this channel to a chat room"""
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ You need 'Manage Channels' permission to register channels.")
            return
        
        try:
            # Check if room exists
            room_data = await db_manager.get_room_by_name(room_name.strip())
            if not room_data:
                await ctx.send(f"❌ Room '{room_name}' not found. Use `!rooms` to see available rooms.")
                return
            
            # Check if channel is already registered
            existing_room_id = await db_manager.is_channel_registered(
                str(ctx.guild.id), 
                str(ctx.channel.id)
            )
            if existing_room_id:
                await ctx.send(f"❌ This channel is already registered to a room.")
                return
            
            # Register the channel
            success = await db_manager.register_channel(
                guild_id=str(ctx.guild.id),
                channel_id=str(ctx.channel.id),
                room_id=room_data['id'],
                guild_name=ctx.guild.name,
                channel_name=ctx.channel.name,
                registered_by=str(ctx.author.id)
            )
            
            if success:
                # Invalidate related caches
                await cache_manager.invalidate_channel_registration(str(ctx.guild.id), str(ctx.channel.id))
                await cache_manager.invalidate_room_channels(room_data['id'])
                
                await ctx.send(f"✅ Successfully registered this channel to room **{room_name}**!\n"
                             f"Messages sent here will now appear in all other channels connected to this room.")
            else:
                await ctx.send(f"❌ Failed to register channel to room '{room_name}'.")
                
        except Exception as e:
            await ctx.send(f"❌ Error registering channel: {str(e)}")
    
    @commands.command(name='unregister')
    async def unregister_channel(self, ctx):
        """Remove this channel from global chat"""
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send("❌ You need 'Manage Channels' permission to unregister channels.")
            return
        
        try:
            # Check if channel is registered
            room_id = await db_manager.is_channel_registered(
                str(ctx.guild.id), 
                str(ctx.channel.id)
            )
            
            if not room_id:
                await ctx.send("❌ This channel is not registered to any global chat room.")
                return
            
            # TODO: Implement channel unregistration in database manager
            # For now, just inform the user
            await ctx.send("⚠️ Channel unregistration is not yet implemented in the new system.\n"
                         "Please use the admin panel to manage channel registrations.")
                         
        except Exception as e:
            await ctx.send(f"❌ Error checking channel registration: {str(e)}")
    
    @commands.command(name='roominfo')
    async def room_info(self, ctx, *, room_name: str):
        """Get information about a specific room"""
        try:
            # Get room data
            room_data = await db_manager.get_room_by_name(room_name.strip())
            if not room_data:
                await ctx.send(f"❌ Room '{room_name}' not found.")
                return
            
            # Get room channels
            channels = await db_manager.get_room_channels(room_data['id'])
            
            # Get room permissions
            permissions = await db_manager.get_room_permissions(room_data['id'])
            
            embed = discord.Embed(
                title=f"🏠 Room Information: {room_data['name']}",
                color=0x00ff00
            )
            
            embed.add_field(
                name="📊 Basic Info",
                value=f"**Created by:** <@{room_data['created_by']}>\n"
                      f"**Created at:** {room_data['created_at']}\n"
                      f"**Max servers:** {room_data['max_servers']}\n"
                      f"**Status:** {'🟢 Active' if room_data['is_active'] else '🔴 Inactive'}",
                inline=False
            )
            
            embed.add_field(
                name="📺 Connected Channels",
                value=f"**Total:** {len(channels)} channels\n" + 
                      ("\n".join([f"• {ch['guild_name']} #{ch['channel_name']}" for ch in channels[:5]]) if channels else "No channels registered") +
                      (f"\n... and {len(channels) - 5} more" if len(channels) > 5 else ""),
                inline=False
            )
            
            embed.add_field(
                name="⚙️ Permissions",
                value=f"🔗 URLs: {'✅' if permissions.get('allow_urls') else '❌'}\n"
                      f"📎 Files: {'✅' if permissions.get('allow_files') else '❌'}\n"
                      f"💬 Mentions: {'✅' if permissions.get('allow_mentions') else '❌'}\n"
                      f"😀 Emojis: {'✅' if permissions.get('allow_emojis') else '❌'}\n"
                      f"🚫 Bad word filter: {'✅' if permissions.get('enable_bad_word_filter') else '❌'}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error fetching room info: {str(e)}")
    
    # Slash command versions
    @app_commands.command(name="rooms", description="List all available chat rooms")
    async def rooms_slash(self, interaction: discord.Interaction):
        """List all available chat rooms"""
        try:
            rooms = await db_manager.get_all_rooms()
            
            if not rooms:
                embed = discord.Embed(
                    title="🏠 Global Chat Rooms",
                    description="No chat rooms available.",
                    color=0xff9900
                )
                await interaction.response.send_message(embed=embed)
                return
            
            embed = discord.Embed(
                title="🏠 Available Global Chat Rooms",
                color=0x00ff00,
                description=f"Total: {len(rooms)} rooms"
            )
            
            room_list = []
            for room in rooms:
                status = "🟢 Active" if room['is_active'] else "🔴 Inactive"
                room_list.append(f"**{room['name']}** - {status}")
            
            embed.add_field(
                name="Rooms",
                value="\n".join(room_list),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="register", description="Register this channel to a chat room")
    @app_commands.describe(room_name="Name of the room to register to")
    async def register_slash(self, interaction: discord.Interaction, room_name: str):
        """Register this channel to a chat room"""
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ You need 'Manage Channels' permission to register channels.", ephemeral=True)
            return
        
        try:
            # Check if room exists
            room_data = await db_manager.get_room_by_name(room_name.strip())
            if not room_data:
                await interaction.response.send_message(f"❌ Room '{room_name}' not found. Use `/rooms` to see available rooms.", ephemeral=True)
                return
            
            # Check if channel is already registered
            existing_room_id = await db_manager.is_channel_registered(
                str(interaction.guild.id), 
                str(interaction.channel.id)
            )
            if existing_room_id:
                await interaction.response.send_message("❌ This channel is already registered to a room.", ephemeral=True)
                return
            
            # Register the channel
            success = await db_manager.register_channel(
                guild_id=str(interaction.guild.id),
                channel_id=str(interaction.channel.id),
                room_id=room_data['id'],
                guild_name=interaction.guild.name,
                channel_name=interaction.channel.name,
                registered_by=str(interaction.user.id)
            )
            
            if success:
                await interaction.response.send_message(f"✅ Successfully registered this channel to room **{room_name}**!")
            else:
                await interaction.response.send_message(f"❌ Failed to register channel to room '{room_name}'.", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages in global chat channels"""
        # Skip bot messages
        if message.author.bot:
            return
        
        # Skip command messages
        if message.content.startswith('!') or message.content.startswith('/'):
            return
        
        try:
            # Check if this channel is registered to a room
            room_id = await db_manager.is_channel_registered(
                str(message.guild.id), 
                str(message.channel.id)
            )
            
            if not room_id:
                return  # Channel not registered, ignore message
            
            # Get room permissions
            permissions = await db_manager.get_room_permissions(room_id)
            
            # Basic content filtering (simplified)
            if not permissions.get('allow_urls', False) and ('http://' in message.content or 'https://' in message.content):
                try:
                    await message.delete()
                    await message.author.send("❌ URLs are not allowed in this global chat room.")
                except:
                    pass
                return
            
            # Log the message
            message_data = {
                'message_id': str(message.id),
                'room_id': room_id,
                'guild_id': str(message.guild.id),
                'channel_id': str(message.channel.id),
                'user_id': str(message.author.id),
                'username': message.author.display_name,
                'guild_name': message.guild.name,
                'content': message.content[:2000],  # Truncate if too long
            }
            
            # Handle replies
            if message.reference and message.reference.message_id:
                reply_data = await db_manager.get_message_for_reply(
                    str(message.reference.message_id), 
                    room_id
                )
                if reply_data:
                    message_data.update({
                        'reply_to_message_id': str(message.reference.message_id),
                        'reply_to_username': reply_data.get('username'),
                        'reply_to_content': reply_data.get('content', '')[:200]  # Truncate reply content
                    })
            
            # Log message to database
            await db_manager.log_message_fast(message_data)
            
            # Get all channels in this room
            room_channels = await db_manager.get_room_channels(room_id)
            
            # Format and send message to all other channels
            for channel_data in room_channels:
                # Skip sending to the same channel
                if channel_data['guild_id'] == str(message.guild.id) and channel_data['channel_id'] == str(message.channel.id):
                    continue
                
                try:
                    # Get the Discord channel
                    guild = self.bot.get_guild(int(channel_data['guild_id']))
                    if not guild:
                        continue
                    
                    channel = guild.get_channel(int(channel_data['channel_id']))
                    if not channel:
                        continue
                    
                    # Format the message
                    formatted_content = f"**{message.author.display_name}** • {message.guild.name}: {message.content}"
                    
                    # Handle replies
                    if message_data.get('reply_to_username'):
                        reply_line = f"┌─ Replying to @{message_data['reply_to_username']}: {message_data.get('reply_to_content', '')[:100]}"
                        formatted_content = f"{reply_line}\n└─ {formatted_content}"
                    
                    # Send the message
                    await channel.send(formatted_content[:2000])  # Discord message limit
                    
                except Exception as e:
                    print(f"❌ Error sending message to {channel_data['guild_name']}: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Error handling message: {e}")


async def setup(bot):
    """Setup function for loading the cog"""
    cog = GlobalChatCommands(bot)
    await bot.add_cog(cog)