import discord
import asyncio
from typing import Optional

class ChannelManager:
    def __init__(self, bot):
        self.bot = bot
    
    async def clear_text_channel(self, channel: discord.TextChannel, user: discord.Member) -> dict:
        """
        Clear all messages from a text channel by recreating it
        Returns a dictionary with success status and message
        """
        try:
            # Store channel information
            channel_position = channel.position
            channel_category = channel.category
            channel_topic = channel.topic
            channel_slowmode = channel.slowmode_delay
            channel_nsfw = channel.nsfw
            channel_overwrites = channel.overwrites
            
            # Create new channel with same properties
            new_channel = await channel.guild.create_text_channel(
                name=channel.name,
                category=channel_category,
                topic=channel_topic,
                slowmode_delay=channel_slowmode,
                nsfw=channel_nsfw,
                overwrites=channel_overwrites,
                position=channel_position,
                reason=f"Channel cleared by {user.display_name}"
            )
            
            # Delete the old channel
            await channel.delete(reason=f"Channel cleared by {user.display_name}")
            
            # Small delay to ensure channel is ready
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "new_channel": new_channel,
                "message": f"✅ **Channel cleared successfully!**\n"
                          f"All messages have been removed from #{new_channel.name}\n"
                          f"*Cleared by {user.mention}*"
            }
            
        except discord.Forbidden:
            return {
                "success": False,
                "message": "❌ I don't have permission to manage channels."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ An error occurred while clearing the channel: {str(e)}"
            }
    
    def validate_channel_name(self, actual_name: str, input_name: str) -> bool:
        """Validate that the input channel name matches the actual channel name"""
        return actual_name.lower().strip() == input_name.lower().strip()
    
    def check_permissions(self, channel: discord.TextChannel, user: discord.Member, bot_member: discord.Member) -> dict:
        """Check if user and bot have necessary permissions"""
        # Check user permissions
        if not user.guild_permissions.administrator:
            return {
                "valid": False,
                "message": "❌ You need Administrator permission to use this command."
            }
        
        # Check bot permissions
        if not channel.permissions_for(bot_member).manage_messages:
            return {
                "valid": False,
                "message": "❌ I don't have 'Manage Messages' permission in this channel."
            }
        
        if not channel.permissions_for(bot_member).manage_channels:
            return {
                "valid": False,
                "message": "❌ I don't have 'Manage Channels' permission to recreate the channel."
            }
        
        return {"valid": True}