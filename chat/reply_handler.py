"""
Reply handling utilities for global chat system.
Handles reply detection, parsing, and data extraction.
"""

import discord
import re
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from typing import Dict, Optional
from shared.database.manager import DatabaseManager
from formatters import MessageFormatter


class ReplyHandler:
    """Handles reply detection and data extraction for global chat messages."""
    
    def __init__(self, bot, db_manager: DatabaseManager, formatter: MessageFormatter = None):
        self.bot = bot
        self.db = db_manager
        self.formatter = formatter or MessageFormatter()
    
    async def extract_reply_data(self, message: discord.Message, room_id: int) -> Dict[str, str]:
        """
        Extract reply data from a Discord message.
        
        Args:
            message: Discord message to analyze
            room_id: ID of the chat room
            
        Returns:
            Dict containing reply data (reply_to_message_id, reply_to_username, reply_to_content)
        """
        reply_data = {}
        
        # Check if the message is a reply to another message
        if message.reference and message.reference.message_id:
            print(f"🔍 Reply detected! Message ID: {message.reference.message_id}")
            try:
                # First try to get from our database (for global chat messages)
                original_msg_data = await self.db.get_message_for_reply(str(message.reference.message_id), room_id)
                if original_msg_data:
                    print(f"✅ Found original message in database: {original_msg_data['username']}")
                    reply_data['reply_to_message_id'] = str(message.reference.message_id)
                    reply_data['reply_to_username'] = original_msg_data['username']
                    reply_data['reply_to_content'] = original_msg_data['content']
                    reply_data['reply_to_user_id'] = original_msg_data.get('user_id')
                else:
                    print(f"📋 Message not in database, trying Discord API...")
                    # If not in our database, try to get the original message from Discord
                    original_message = None
                    
                    # Try resolved reference first
                    if message.reference.resolved:
                        original_message = message.reference.resolved
                        print(f"✅ Found via resolved reference: {original_message.author.display_name}")
                    else:
                        # Try to fetch the message manually
                        try:
                            print(f"🔍 Fetching message manually from Discord...")
                            original_message = await message.channel.fetch_message(message.reference.message_id)
                            print(f"✅ Found via manual fetch: {original_message.author.display_name}")
                        except Exception as fetch_error:
                            print(f"❌ Could not fetch original message: {fetch_error}")
                    
                    # Process the found message
                    if original_message and hasattr(original_message, 'author'):
                        reply_data['reply_to_message_id'] = str(message.reference.message_id)
                        reply_data['reply_to_username'] = original_message.author.display_name
                        
                        # Get the content, handling different message types
                        if hasattr(original_message, 'content') and original_message.content:
                            # Check if this is a global chat message from our bot
                            if original_message.author.bot and original_message.author.id == self.bot.user.id:
                                # Parse bot's global chat message to extract original content
                                bot_content = original_message.content
                                print(f"🔍 Bot message content: {bot_content[:100]}...")
                                
                                # Use formatter to parse bot message consistently
                                parsed_data = self.formatter.parse_bot_message_content(bot_content)
                                processed_data = await self._process_parsed_bot_message(parsed_data, str(message.reference.message_id))
                                reply_data.update(processed_data)
                            else:
                                reply_data['reply_to_content'] = original_message.content
                        elif hasattr(original_message, 'embeds') and original_message.embeds:
                            # If it's an embed message (like from our bot)
                            reply_data['reply_to_content'] = original_message.embeds[0].description or "[Embed message]"
                        elif hasattr(original_message, 'attachments') and original_message.attachments:
                            reply_data['reply_to_content'] = f"[Attachment: {original_message.attachments[0].filename}]"
                        else:
                            reply_data['reply_to_content'] = "[No text content]"
                        
                        print(f"📝 Extracted content: {reply_data.get('reply_to_content', '')[:50]}...")
                    else:
                        # If all fails, show basic reply info
                        print(f"❌ Could not get original message data")
                        reply_data['reply_to_message_id'] = str(message.reference.message_id)
                        reply_data['reply_to_username'] = "Unknown User"
                        reply_data['reply_to_content'] = "[Message not found]"
            except Exception as e:
                print(f"⚠️ Error extracting reply data: {e}")
        
        return reply_data
    
    async def _process_parsed_bot_message(self, parsed_data: dict, message_id: str) -> Dict[str, str]:
        """
        Process parsed bot message data from MessageFormatter.
        
        Args:
            parsed_data: Parsed data from MessageFormatter
            message_id: ID of the message being replied to
            
        Returns:
            Dict with processed reply data
        """
        reply_data = {
            'reply_to_message_id': message_id,
            'reply_to_content': parsed_data.get('content', '[Unknown content]')
        }
        
        message_type = parsed_data.get('type', 'unknown')
        
        if message_type == 'nested_reply':
            # Direct username from nested reply parsing
            reply_data['reply_to_username'] = parsed_data.get('username', 'Previous User')
            print(f"🔄 Detected reply to reply, extracting last user message...")
            print(f"✅ Extracted from nested reply - User: {reply_data['reply_to_username']}, Content: {reply_data['reply_to_content'][:30]}...")
            
        elif message_type in ['regular_with_mention', 'regular_with_username']:
            # Need to resolve username from mention text
            mention_text = parsed_data.get('mention_text', '')
            username = await self._extract_username_from_mention(mention_text)
            reply_data['reply_to_username'] = username
            print(f"✅ Extracted - User: {username}, Content: {reply_data['reply_to_content'][:30]}...")
            
        else:
            # Fallback
            reply_data['reply_to_username'] = parsed_data.get('username', 'Someone')
            print(f"⚠️ Using fallback parsing for message type: {message_type}")
        
        return reply_data
    
    async def _extract_username_from_mention(self, text: str) -> str:
        """
        Extract username from Discord mention format.
        
        Args:
            text: Text containing Discord mention
            
        Returns:
            str: Username or fallback
        """
        if '<@' in text and '>' in text:
            # Handle Discord mention format <@userid>
            mention_match = re.search(r'<@(\d+)>', text)
            if mention_match:
                user_id = mention_match.group(1)
                try:
                    # Try to get the actual username from Discord
                    mentioned_user = self.bot.get_user(int(user_id))
                    if mentioned_user:
                        return mentioned_user.display_name
                    else:
                        # Try to fetch the user
                        mentioned_user = await self.bot.fetch_user(int(user_id))
                        return mentioned_user.display_name if mentioned_user else f"User{user_id}"
                except:
                    return f"User{user_id}"
            else:
                return "Someone"
        elif '**' in text:
            return text.split('**')[-1].strip()
        else:
            return "Someone"