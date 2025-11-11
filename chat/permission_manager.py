"""
Permission management and notification system for global chat.
Handles permission checks and user notifications.
"""

import discord
from typing import Dict, Any


class PermissionManager:
    """Handles permission checks and notifications for global chat system."""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def notify_permission_issue(self, channel_info: Dict[str, Any], permission_type: str, room_name: str):
        """
        Send DM notification to user who registered the channel about permission issues.
        
        Args:
            channel_info: Channel information dict containing registered_by
            permission_type: Type of permission issue (e.g., "send messages")
            room_name: Name of the chat room
        """
        try:
            # Get the user who registered this channel
            registered_by_id = channel_info.get('registered_by')
            if not registered_by_id:
                print(f"   ⚠️ No registered_by info for channel {channel_info['guild_name']} - {channel_info['channel_name']}")
                return
            
            # Get the user object
            user = self.bot.get_user(int(registered_by_id))
            if not user:
                try:
                    user = await self.bot.fetch_user(int(registered_by_id))
                except:
                    print(f"   ⚠️ Could not find user {registered_by_id} for permission notification")
                    return
            
            # Create notification embed
            embed = discord.Embed(
                title="🚫 Global Chat Permission Issue",
                description=f"**Bot has no permission to {permission_type}**\n\n"
                           f"**Room:** {room_name}\n"
                           f"**Server:** {channel_info['guild_name']}\n"
                           f"**Channel:** #{channel_info['channel_name']}\n\n"
                           f"**Action Required:**\n"
                           f"Please give the bot permission to **{permission_type}** in {channel_info['channel_name']} to receive global chat messages.\n\n"
                           f"**How to fix:**\n"
                           f"1. Go to your server settings\n"
                           f"2. Navigate to Roles → @{self.bot.user.name} role\n"
                           f"3. Enable 'Send Messages' permission\n"
                           f"4. Or give the bot permission in the specific channel",
                color=0xff6b6b
            )
            embed.set_footer(text="This notification was sent because you registered this channel for global chat")
            
            # Send DM to the user
            await user.send(embed=embed)
            print(f"   ✅ Permission notification sent to user {user.name} ({registered_by_id})")
            
        except discord.Forbidden:
            print(f"   ❌ Could not send DM to user {registered_by_id} - DMs are disabled")
        except Exception as e:
            print(f"   ❌ Error sending permission notification to user {registered_by_id}: {e}")
    
    def check_message_permissions(self, channel: discord.TextChannel, guild: discord.Guild) -> bool:
        """
        Check if bot has permission to send messages in the channel.
        
        Args:
            channel: Discord channel to check
            guild: Discord guild containing the channel
            
        Returns:
            bool: True if bot can send messages
        """
        return channel.permissions_for(guild.me).send_messages
    
    def check_channel_management_permission(self, member: discord.Member) -> bool:
        """
        Check if member has permission to manage channels.
        
        Args:
            member: Discord member to check
            
        Returns:
            bool: True if member can manage channels
        """
        return member.guild_permissions.manage_channels
    
    async def get_missing_permissions(self, channel: discord.TextChannel, guild: discord.Guild) -> list[str]:
        """
        Get list of missing permissions for the bot in a channel.
        
        Args:
            channel: Discord channel to check
            guild: Discord guild containing the channel
            
        Returns:
            list[str]: List of missing permission names
        """
        missing_permissions = []
        permissions = channel.permissions_for(guild.me)
        
        # Check essential permissions
        essential_perms = {
            'send_messages': 'Send Messages',
            'read_messages': 'Read Messages',
            'embed_links': 'Embed Links',
            'read_message_history': 'Read Message History'
        }
        
        for perm_name, display_name in essential_perms.items():
            if not getattr(permissions, perm_name, False):
                missing_permissions.append(display_name)
        
        return missing_permissions