"""
Main global chat manager that orchestrates message handling.
Coordinates between different components for a clean, modular architecture.
"""

import discord
import time
from typing import Dict
from database.db_manager import DatabaseManager
from .formatters import MessageFormatter
from .reply_handler import ReplyHandler
from .content_filter import ContentFilter
from .permission_manager import PermissionManager


class GlobalChatManager:
    """Main manager for global chat functionality with modular architecture."""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        
        # Initialize modular components
        self.formatter = MessageFormatter()
        self.reply_handler = ReplyHandler(bot, self.db, self.formatter)  # Pass formatter
        self.content_filter = ContentFilter()
        self.permission_manager = PermissionManager(bot)
        
        # Rate limiting and duplicate prevention
        self.last_message_time: Dict[str, float] = {}
        self.last_message_content: Dict[str, str] = {}
        
        # Room setup tracking for interactive permissions
        self.pending_setups = {}
    
    async def handle_message(self, message: discord.Message):
        """
        Handle incoming message from a global chat channel.
        
        Args:
            message: Discord message to process
        """
        if message.author.bot:
            return
        
        # Check if this is a registered global chat channel and get room name
        room_name = self.db.is_global_chat_channel(str(message.guild.id), str(message.channel.id))
        if not room_name:
            return
        
        # Get room-specific permissions
        room_permissions = self.db.get_room_permissions(room_name)
        
        # Perform all validation checks
        if not await self._validate_message(message, room_permissions, room_name):
            return
        
        # Check if this is a reply message
        reply_data = await self.reply_handler.extract_reply_data(message, room_name)
        
        # Log the message
        self.db.log_global_chat_message(
            str(message.id),
            room_name,
            str(message.guild.id),
            str(message.channel.id),
            str(message.author.id),
            message.author.display_name,
            message.guild.name,
            message.content,
            reply_data.get('reply_to_message_id'),
            reply_data.get('reply_to_username'),
            reply_data.get('reply_to_content')
        )
        
        # Broadcast to all other registered channels in the same room
        await self.broadcast_message(message, room_name)
    
    async def _validate_message(self, message: discord.Message, room_permissions: dict, room_name: str) -> bool:
        """
        Validate message against room permissions and rate limits.
        
        Args:
            message: Discord message to validate
            room_permissions: Room permission settings
            room_name: Name of the chat room
            
        Returns:
            bool: True if message passes all validations
        """
        # Rate limiting and duplicate prevention
        user_key = f"{message.guild.id}_{message.author.id}"
        current_time = time.time()
        
        # Check rate limit using room-specific setting
        if user_key in self.last_message_time:
            time_diff = current_time - self.last_message_time[user_key]
            if time_diff < room_permissions['rate_limit_seconds']:
                await message.add_reaction("⏱️")
                return False
        
        # Check for duplicate messages
        if user_key in self.last_message_content:
            if self.last_message_content[user_key] == message.content.strip():
                await message.add_reaction("🔄")
                return False
        
        # Message length check using room-specific setting
        if len(message.content) > room_permissions['max_message_length']:
            await message.add_reaction("📏")
            return False
        
        # URL filtering (if disabled in room settings)
        if not room_permissions['allow_urls'] and self.content_filter.contains_url(message.content):
            await message.add_reaction("🔗")
            await message.author.send(f"🚫 URLs are not allowed in the **{room_name}** chat room. Your message was blocked.")
            return False
        
        # File attachment filtering
        if not room_permissions['allow_files'] and message.attachments:
            await message.add_reaction("📎")
            await message.author.send(f"🚫 File attachments are not allowed in the **{room_name}** chat room. Your message was blocked.")
            return False
        
        # Mention filtering
        if not room_permissions['allow_mentions'] and ('@everyone' in message.content or '@here' in message.content or message.mentions):
            await message.add_reaction("💬")
            await message.author.send(f"🚫 Mentions are not allowed in the **{room_name}** chat room. Your message was blocked.")
            return False
        
        # Content filtering using room-specific setting
        if room_permissions['enable_bad_word_filter'] and self.content_filter.contains_blocked_content(message.content):
            await message.add_reaction("🚫")
            await message.author.send(f"🚫 Your message contains blocked content and was not sent to the **{room_name}** chat room.")
            return False
        
        # Update tracking only after all checks pass
        self.last_message_time[user_key] = current_time
        self.last_message_content[user_key] = message.content.strip()
        
        return True
    
    async def broadcast_message(self, original_message: discord.Message, room_name: str):
        """
        Broadcast message to all registered global chat channels in the same room.
        
        Args:
            original_message: Original Discord message
            room_name: Name of the chat room
        """
        # Get all registered channels in the same room
        channels = self.db.get_global_chat_channels(room_name)
        
        print(f"🔄 Broadcasting message from {original_message.guild.name} to room '{room_name}' - Found {len(channels)} registered channels")
        for ch in channels:
            print(f"   - {ch['guild_name']} #{ch['channel_name']} (ID: {ch['channel_id']})")

        # Check if this is a reply message and format reply context
        reply_data = await self.reply_handler.extract_reply_data(original_message, room_name)
        reply_context = ""
        if reply_data.get('reply_to_message_id'):
            reply_to_username = reply_data['reply_to_username']
            reply_to_content = reply_data['reply_to_content']
            reply_to_user_id = reply_data.get('reply_to_user_id')
            
            # Use the reusable reply context formatter with user mention
            reply_context = self.formatter.format_reply_context(reply_to_username, reply_to_content, reply_to_user_id)
            print(f"📝 Adding reply context: {reply_context.strip()}")
        else:
            print(f"📝 No reply data found, sending as regular message")
        
        # Use the reusable message formatter
        message_content = self.formatter.format_global_message(original_message, reply_context)
        
        print(f"📝 Message content: {message_content[:100]}..." if len(message_content) > 100 else f"📝 Message content: {message_content}")
        
        # Send to all other channels
        await self._send_to_channels(channels, message_content, original_message, room_name)
    
    async def _send_to_channels(self, channels: list, message_content: str, original_message: discord.Message, room_name: str):
        """
        Send message to all channels with permission handling.
        
        Args:
            channels: List of channel information
            message_content: Formatted message content
            original_message: Original Discord message
            room_name: Name of the chat room
        """
        for channel_info in channels:
            print(f"🎯 Processing channel: {channel_info['guild_name']} #{channel_info['channel_name']}")
            
            # Skip the original channel
            if (channel_info['guild_id'] == str(original_message.guild.id) and 
                channel_info['channel_id'] == str(original_message.channel.id)):
                print(f"   ⏭️ Skipping original channel")
                continue
            
            try:
                guild = self.bot.get_guild(int(channel_info['guild_id']))
                if not guild:
                    print(f"   ❌ Guild not found: {channel_info['guild_id']}")
                    continue
                
                print(f"   ✅ Guild found: {guild.name}")
                
                channel = guild.get_channel(int(channel_info['channel_id']))
                if not channel:
                    print(f"   ❌ Channel not found: {channel_info['channel_id']}")
                    continue
                
                print(f"   ✅ Channel found: #{channel.name}")
                
                # Check if bot has permission to send messages
                if not self.permission_manager.check_message_permissions(channel, guild):
                    print(f"   ❌ No permission to send messages")
                    await self.permission_manager.notify_permission_issue(channel_info, "send messages", room_name)
                    continue
                
                print(f"   ✅ Permissions OK, sending message...")
                await channel.send(message_content)
                print(f"   ✅ Message sent successfully!")
                
            except discord.Forbidden:
                print(f"   ❌ Forbidden: No permission to send message in {channel_info['guild_name']} - {channel_info['channel_name']}")
                await self.permission_manager.notify_permission_issue(channel_info, "send messages (Forbidden)", room_name)
            except discord.NotFound:
                print(f"   ❌ Not Found: Channel not found: {channel_info['guild_name']} - {channel_info['channel_name']}")
            except Exception as e:
                print(f"   ❌ Error sending message to {channel_info['guild_name']}: {e}")
    
    # Channel registration methods (delegating to existing functionality)
    async def register_channel(self, guild: discord.Guild, channel: discord.TextChannel, room_name: str, registered_by: discord.Member) -> str:
        """Register a channel for global chat room with fuzzy matching."""
        # Check if user has manage channels permission
        if not self.permission_manager.check_channel_management_permission(registered_by):
            return "You need 'Manage Channels' permission to register for global chat."
        
        # Try to find the closest matching room name
        closest_room = self.db.find_closest_room(room_name)
        
        if not closest_room:
            return self.get_room_not_found_message(room_name)
        
        # Use the closest matching room name
        actual_room_name = closest_room
        
        result = self.db.register_global_chat_channel(
            str(guild.id),
            str(channel.id),
            actual_room_name,
            guild.name,
            channel.name,
            str(registered_by.id)
        )
        
        # Prepare response message
        suggestion_msg = ""
        if actual_room_name.lower() != room_name.lower():
            suggestion_msg = f" (auto-matched from '{room_name}')"
        
        if result == True:
            return f"✅ Successfully registered {channel.mention} to room **{actual_room_name}**{suggestion_msg}!"
        elif result == "updated":
            return f"✅ Updated registration for {channel.mention} to room **{actual_room_name}**{suggestion_msg}!"
        elif result == "room_not_found":
            return f"❌ Room '{actual_room_name}' does not exist. This shouldn't happen - please try again."
        else:
            return f"❌ Failed to register {channel.mention} to room '{actual_room_name}'."
    
    async def unregister_channel(self, guild: discord.Guild, channel: discord.TextChannel, requested_by: discord.Member) -> str:
        """Unregister a channel from global chat."""
        # Check if user has manage channels permission
        if not self.permission_manager.check_channel_management_permission(requested_by):
            return "You need 'Manage Channels' permission to unregister from global chat."
        
        success = self.db.unregister_global_chat_channel(str(guild.id), str(channel.id))
        
        if success:
            return f"✅ Successfully unregistered {channel.mention} from global chat!"
        else:
            return f"❌ {channel.mention} was not registered for global chat."
    
    def get_registered_channels(self) -> list:
        """Get all registered global chat channels."""
        return self.db.get_global_chat_channels()
    
    def is_registered_channel(self, guild_id: str, channel_id: str) -> bool:
        """Check if a channel is registered for global chat."""
        return self.db.is_global_chat_channel(guild_id, channel_id)
    
    def get_room_not_found_message(self, room_name: str) -> str:
        """Get formatted message when room is not found with available rooms list."""
        available_rooms = self.db.get_chat_rooms()
        if available_rooms:
            room_list = ", ".join([f"**{room['room_name']}**" for room in available_rooms[:8]])  # Show max 8 rooms
            if len(available_rooms) > 8:
                room_list += f" and {len(available_rooms) - 8} more"
            return f"❌ No room found matching '{room_name}'.\n\n**Available rooms:** {room_list}\n\nUse `!rooms` or `/rooms` to see all rooms or `!createRoom <name>` to create a new one."
        else:
            return f"❌ No rooms available. Create the first room with `!createRoom {room_name}`."
    
    # Interactive permission setup methods would go here
    # (These can be added later or kept in a separate setup manager)