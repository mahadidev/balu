import discord
import asyncio
import time
from typing import Dict, List, Optional
from database.db_manager import DatabaseManager

class GlobalChatManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.last_message_time: Dict[str, float] = {}
        self.last_message_content: Dict[str, str] = {}
        self.rate_limit_seconds = int(self.db.get_global_chat_setting('rate_limit_seconds') or 10)
        self.max_message_length = int(self.db.get_global_chat_setting('max_message_length') or 2000)
        self.enable_filtering = self.db.get_global_chat_setting('enable_filtering') == 'true'
        
        # Simple profanity filter (you can expand this)
        self.blocked_words = [
            'spam', 'hack', 'cheat', 'exploit'  # Add more as needed
        ]
    
    async def handle_message(self, message: discord.Message):
        """Handle incoming message from a global chat channel"""
        if message.author.bot:
            return
        
        # Check if this is a registered global chat channel and get room name
        room_name = self.db.is_global_chat_channel(str(message.guild.id), str(message.channel.id))
        if not room_name:
            return
        
        # Rate limiting and duplicate prevention
        user_key = f"{message.guild.id}_{message.author.id}"
        current_time = time.time()
        
        # Check rate limit (10 seconds)
        if user_key in self.last_message_time:
            time_diff = current_time - self.last_message_time[user_key]
            if time_diff < self.rate_limit_seconds:
                await message.add_reaction("⏱️")
                return
        
        # Check for duplicate messages
        if user_key in self.last_message_content:
            if self.last_message_content[user_key] == message.content.strip():
                await message.add_reaction("🔄")
                return
        
        # Message length check
        if len(message.content) > self.max_message_length:
            await message.add_reaction("📏")
            return
        
        # Content filtering
        if self.enable_filtering and self._contains_blocked_content(message.content):
            await message.add_reaction("🚫")
            return
        
        # Update tracking only after all checks pass
        self.last_message_time[user_key] = current_time
        self.last_message_content[user_key] = message.content.strip()
        
        # Log the message
        self.db.log_global_chat_message(
            str(message.id),
            room_name,
            str(message.guild.id),
            str(message.channel.id),
            str(message.author.id),
            message.author.display_name,
            message.guild.name,
            message.content
        )
        
        # Broadcast to all other registered channels in the same room
        await self.broadcast_message(message, room_name)
    
    def _contains_blocked_content(self, content: str) -> bool:
        """Check if message contains blocked content"""
        content_lower = content.lower()
        for word in self.blocked_words:
            if word in content_lower:
                return True
        return False
    
    async def broadcast_message(self, original_message: discord.Message, room_name: str):
        """Broadcast message to all registered global chat channels in the same room"""
        # Get all registered channels in the same room
        channels = self.db.get_global_chat_channels(room_name)
        
        print(f"🔄 Broadcasting message from {original_message.guild.name} to room '{room_name}' - Found {len(channels)} registered channels")
        for ch in channels:
            print(f"   - {ch['guild_name']} #{ch['channel_name']} (ID: {ch['channel_id']})")

        original_message_url = f"https://discord.com/channels/{original_message.guild.id}/{original_message.channel.id}/{original_message.id}"
        
        # Create plain text message with room name
        message_content = f"{original_message_url} • {original_message.author.mention}**: ** {original_message.content} \n\n"
        
        print(f"📝 Message content: {message_content[:100]}..." if len(message_content) > 100 else f"📝 Message content: {message_content}")
        
        # Handle attachments
        if original_message.attachments:
            attachment = original_message.attachments[0]
            if attachment.content_type and attachment.content_type.startswith('image/'):
                message_content += f"\n🖼️ Image: {attachment.url}"
            else:
                message_content += f"\n📎 Attachment: [{attachment.filename}]({attachment.url})"
        
        # Send to all other channels
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
                if not channel.permissions_for(guild.me).send_messages:
                    print(f"   ❌ No permission to send messages")
                    continue
                
                print(f"   ✅ Permissions OK, sending message...")
                await channel.send(message_content)
                print(f"   ✅ Message sent successfully!")
                
            except discord.Forbidden:
                print(f"   ❌ Forbidden: No permission to send message in {channel_info['guild_name']} - {channel_info['channel_name']}")
            except discord.NotFound:
                print(f"   ❌ Not Found: Channel not found: {channel_info['guild_name']} - {channel_info['channel_name']}")
            except Exception as e:
                print(f"   ❌ Error sending message to {channel_info['guild_name']}: {e}")
    
    async def register_channel(self, guild: discord.Guild, channel: discord.TextChannel, room_name: str, registered_by: discord.Member) -> str:
        """Register a channel for global chat room with fuzzy matching"""
        # Check if user has manage channels permission
        if not registered_by.guild_permissions.manage_channels:
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
        """Unregister a channel from global chat"""
        # Check if user has manage channels permission
        if not requested_by.guild_permissions.manage_channels:
            return "You need 'Manage Channels' permission to unregister from global chat."
        
        success = self.db.unregister_global_chat_channel(str(guild.id), str(channel.id))
        
        if success:
            return f"✅ Successfully unregistered {channel.mention} from global chat!"
        else:
            return f"❌ {channel.mention} was not registered for global chat."
    
    def get_registered_channels(self) -> List[Dict]:
        """Get all registered global chat channels"""
        return self.db.get_global_chat_channels()
    
    def is_registered_channel(self, guild_id: str, channel_id: str) -> bool:
        """Check if a channel is registered for global chat"""
        return self.db.is_global_chat_channel(guild_id, channel_id)
    
    def get_room_not_found_message(self, room_name: str) -> str:
        """Get formatted message when room is not found with available rooms list"""
        available_rooms = self.db.get_chat_rooms()
        if available_rooms:
            room_list = ", ".join([f"**{room['room_name']}**" for room in available_rooms[:8]])  # Show max 8 rooms
            if len(available_rooms) > 8:
                room_list += f" and {len(available_rooms) - 8} more"
            return f"❌ No room found matching '{room_name}'.\n\n**Available rooms:** {room_list}\n\nUse `!rooms` or `/rooms` to see all rooms or `!createRoom <name>` to create a new one."
        else:
            return f"❌ No rooms available. Create the first room with `!createRoom {room_name}`."
    
