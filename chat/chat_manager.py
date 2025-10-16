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
        self.rate_limit_seconds = int(self.db.get_global_chat_setting('rate_limit_seconds') or 3)
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
        
        # Check if this is a registered global chat channel
        if not self.db.is_global_chat_channel(str(message.guild.id), str(message.channel.id)):
            return
        
        # Rate limiting
        user_key = f"{message.guild.id}_{message.author.id}"
        current_time = time.time()
        
        if user_key in self.last_message_time:
            time_diff = current_time - self.last_message_time[user_key]
            if time_diff < self.rate_limit_seconds:
                await message.add_reaction("⏱️")
                return
        
        self.last_message_time[user_key] = current_time
        
        # Message length check
        if len(message.content) > self.max_message_length:
            await message.add_reaction("📏")
            return
        
        # Content filtering
        if self.enable_filtering and self._contains_blocked_content(message.content):
            await message.add_reaction("🚫")
            return
        
        # Log the message
        self.db.log_global_chat_message(
            str(message.id),
            str(message.guild.id),
            str(message.channel.id),
            str(message.author.id),
            message.author.display_name,
            message.guild.name,
            message.content
        )
        
        # Broadcast to all other registered channels
        await self.broadcast_message(message)
    
    def _contains_blocked_content(self, content: str) -> bool:
        """Check if message contains blocked content"""
        content_lower = content.lower()
        for word in self.blocked_words:
            if word in content_lower:
                return True
        return False
    
    async def broadcast_message(self, original_message: discord.Message):
        """Broadcast message to all registered global chat channels"""
        # Get all registered channels
        channels = self.db.get_global_chat_channels()
        
        # Create plain text message
        message_content = f"**{original_message.content}**\n\n-# {original_message.guild} • {original_message.author.mention}"
        
        # Handle attachments
        if original_message.attachments:
            attachment = original_message.attachments[0]
            if attachment.content_type and attachment.content_type.startswith('image/'):
                message_content += f"\n🖼️ Image: {attachment.url}"
            else:
                message_content += f"\n📎 Attachment: [{attachment.filename}]({attachment.url})"
        
        # Send to all other channels
        for channel_info in channels:
            # Skip the original channel
            if (channel_info['guild_id'] == str(original_message.guild.id) and 
                channel_info['channel_id'] == str(original_message.channel.id)):
                continue
            
            try:
                guild = self.bot.get_guild(int(channel_info['guild_id']))
                if not guild:
                    continue
                
                channel = guild.get_channel(int(channel_info['channel_id']))
                if not channel:
                    continue
                
                # Check if bot has permission to send messages
                if not channel.permissions_for(guild.me).send_messages:
                    continue
                
                await channel.send(message_content)
                
            except discord.Forbidden:
                print(f"No permission to send message in {channel_info['guild_name']} - {channel_info['channel_name']}")
            except discord.NotFound:
                print(f"Channel not found: {channel_info['guild_name']} - {channel_info['channel_name']}")
            except Exception as e:
                print(f"Error sending message to {channel_info['guild_name']}: {e}")
    
    async def register_channel(self, guild: discord.Guild, channel: discord.TextChannel, registered_by: discord.Member) -> str:
        """Register a channel for global chat"""
        # Check if user has manage channels permission
        if not registered_by.guild_permissions.manage_channels:
            return "You need 'Manage Channels' permission to register for global chat."
        
        result = self.db.register_global_chat_channel(
            str(guild.id),
            str(channel.id),
            guild.name,
            channel.name,
            str(registered_by.id)
        )
        
        if result == True:
            return f"✅ Successfully registered {channel.mention} for global chat!"
        elif result == "updated":
            return f"✅ Updated registration for {channel.mention} in global chat!"
        else:
            return f"❌ Failed to register {channel.mention} for global chat."
    
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
    
    async def send_status_message(self, channel: discord.TextChannel):
        """Send status message about global chat"""
        channels = self.get_registered_channels()
        
        embed = discord.Embed(
            title="🌐 Global Chat Status",
            color=0x00ff00,
            description=f"Connected to {len(channels)} servers"
        )
        
        if channels:
            server_list = []
            for i, ch in enumerate(channels[:10], 1):  # Show max 10 servers
                server_list.append(f"{i}. **{ch['guild_name']}** - #{ch['channel_name']}")
            
            if len(channels) > 10:
                server_list.append(f"... and {len(channels) - 10} more servers")
            
            embed.add_field(
                name="Connected Servers",
                value="\n".join(server_list),
                inline=False
            )
        
        embed.add_field(
            name="Settings",
            value=f"Rate Limit: {self.rate_limit_seconds}s\nMax Length: {self.max_message_length} chars",
            inline=True
        )
        
        embed.set_footer(text="Messages are relayed across all connected servers")
        
        await channel.send(embed=embed)