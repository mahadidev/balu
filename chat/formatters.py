"""
Message formatting utilities for global chat system.
Handles consistent message formatting across all channels.
"""

import discord
from typing import Optional


class MessageFormatter:
    """Handles all message formatting for global chat messages."""
    
    # Message format constants for consistent parsing
    REPLY_START_MARKER = "┌─"
    REPLY_END_MARKER = "└─"
    REPLY_SEPARATOR = "**: **"
    USERNAME_WRAPPER = "**"
    
    def format_global_message(self, original_message: discord.Message, reply_context: str = "") -> str:
        """
        Reusable message formatter for global chat messages.
        Creates consistent formatting for both regular and reply messages.
        
        Args:
            original_message: The Discord message object
            reply_context: Optional reply context (e.g., "┌─ 💬 Replying to User: content\n└─ ")
        
        Returns:
            str: Formatted message content
        """
        # Create the message URL
        message_url = f"https://discord.com/channels/{original_message.guild.id}/{original_message.channel.id}/{original_message.id}"
        
        # Format attachments if any
        attachment_text = self._format_attachments(original_message)
        
        if reply_context:
            # For replies, use the same format as regular messages but with reply context
            formatted_content = f"{reply_context}{message_url} • {original_message.author.mention}**: ** {original_message.content}{attachment_text} \n\n"
        else:
            # For regular messages, use the original format
            formatted_content = f"{message_url} • {original_message.author.mention}**: ** {original_message.content}{attachment_text} \n\n"
        
        return formatted_content
    
    def format_reply_context(self, reply_to_username: str, reply_to_content: str, reply_to_user_id: str = None) -> str:
        """
        Format reply context with consistent styling.
        
        Args:
            reply_to_username: Username being replied to
            reply_to_content: Content of the message being replied to
            reply_to_user_id: Optional user ID for mention
        
        Returns:
            str: Formatted reply context
        """
        # Clean and truncate the original message content
        content = reply_to_content.strip()
        if len(content) > 50:
            content = content[:47] + "..."
        
        # Clean any extra formatting characters
        content = content.replace('**', '').replace('*', '').strip()
        
        # Create user reference (mention if ID available, otherwise username)
        user_reference = f"<@{reply_to_user_id}>" if reply_to_user_id else reply_to_username
        
        # Create the reply context with thinner text and user mention
        return f"┌─ Replying to {user_reference}: *{content}*\n└─ "
    
    def _format_attachments(self, message: discord.Message) -> str:
        """
        Format attachment information for global chat messages.
        
        Args:
            message: Discord message with attachments
        
        Returns:
            str: Formatted attachment text or empty string
        """
        if not message.attachments:
            return ""
        
        attachment = message.attachments[0]
        if attachment.content_type and attachment.content_type.startswith('image/'):
            return f"\n🖼️ Image: {attachment.url}"
        else:
            return f"\n📎 Attachment: [{attachment.filename}]({attachment.url})"
    
    def parse_bot_message_content(self, bot_content: str) -> dict:
        """
        Parse bot's global chat message to extract original content.
        Handles both regular and reply messages.
        
        Args:
            bot_content: Content of the bot message
            
        Returns:
            dict: Parsed data with username and content
        """
        # Check if this is a reply message (has our reply markers)
        if self.REPLY_START_MARKER in bot_content and self.REPLY_END_MARKER in bot_content:
            return self._parse_reply_message(bot_content)
        else:
            return self._parse_regular_message(bot_content)
    
    def _parse_reply_message(self, bot_content: str) -> dict:
        """Parse a reply message to extract the last user's message."""
        # Split by └─ to get the last user's message
        if self.REPLY_END_MARKER in bot_content:
            last_part = bot_content.split(self.REPLY_END_MARKER)[-1].split('\n')[0].strip()
            # Extract username and message from "**Username:** message"
            if self.USERNAME_WRAPPER in last_part and ':**' in last_part:
                username_end = last_part.find(':**')
                if username_end != -1:
                    username_start = last_part.find(self.USERNAME_WRAPPER) + 2
                    username = last_part[username_start:username_end]
                    content = last_part[username_end + 3:].strip()
                    return {
                        'username': username,
                        'content': content,
                        'type': 'nested_reply'
                    }
        
        return {
            'username': "Previous User",
            'content': bot_content,
            'type': 'unknown'
        }
    
    def _parse_regular_message(self, bot_content: str) -> dict:
        """Parse a regular global chat message."""
        if self.REPLY_SEPARATOR in bot_content:
            # Pattern: "URL • @Username**: ** actual message"
            parts = bot_content.split(self.REPLY_SEPARATOR)
            if len(parts) >= 2:
                actual_message = parts[1].strip().replace('*', '').strip()
                first_part = parts[0]
                return {
                    'username': None,  # Will be resolved by mention parsing
                    'content': actual_message,
                    'mention_text': first_part,
                    'type': 'regular_with_mention'
                }
        elif '**: ' in bot_content:
            # Pattern: "URL • **Username:** actual message"  
            parts = bot_content.split('**: ')
            if len(parts) >= 2:
                actual_message = parts[-1].strip().replace('*', '').strip()
                before_colon = parts[-2]
                return {
                    'username': None,  # Will be resolved by mention parsing
                    'content': actual_message,
                    'mention_text': before_colon,
                    'type': 'regular_with_username'
                }
        
        return {
            'username': "Someone",
            'content': bot_content,
            'type': 'fallback'
        }