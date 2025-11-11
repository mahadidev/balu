import discord
import asyncio
import time
import re
from typing import Dict, List, Optional
from database.db_manager import DatabaseManager

class GlobalChatManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.last_message_time: Dict[str, float] = {}
        self.last_message_content: Dict[str, str] = {}
        
        # URL detection patterns
        self.url_patterns = [
            r'https?://[^\s]+',           # http:// or https:// URLs
            r'www\.[^\s]+\.[a-z]{2,}',     # www. URLs
            r'[^\s]+\.[a-z]{2,}/[^\s]*',   # domain.com/path URLs
            r'[^\s]+\.(com|org|net|edu|gov|io|co|me|tv|gg|discord\.gg)[^\s]*',  # Common TLDs
            r'discord\.gg/[^\s]+',        # Discord invites
            r'bit\.ly/[^\s]+',            # Shortened URLs
            r't\.co/[^\s]+',              # Twitter short URLs
            r'youtu\.be/[^\s]+',          # YouTube short URLs
        ]
        
        # Compile regex patterns for better performance
        self.compiled_url_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.url_patterns]
        
        # Bad words list (expandable)
        self.blocked_words = [
            'spam', 'hack', 'cheat', 'exploit', 'scam', 'fraud', 'phishing',
            'malware', 'virus', 'trojan', 'bitcoin', 'crypto', 'investment',
            'get rich quick', 'click here', 'free money'
        ]
    
    async def handle_message(self, message: discord.Message):
        """Handle incoming message from a global chat channel"""
        if message.author.bot:
            return
        
        # Check if this is a registered global chat channel and get room name
        room_name = self.db.is_global_chat_channel(str(message.guild.id), str(message.channel.id))
        if not room_name:
            return
        
        # Get room-specific permissions
        room_permissions = self.db.get_room_permissions(room_name)
        
        # Rate limiting and duplicate prevention
        user_key = f"{message.guild.id}_{message.author.id}"
        current_time = time.time()
        
        # Check rate limit using room-specific setting
        if user_key in self.last_message_time:
            time_diff = current_time - self.last_message_time[user_key]
            if time_diff < room_permissions['rate_limit_seconds']:
                await message.add_reaction("⏱️")
                return
        
        # Check for duplicate messages
        if user_key in self.last_message_content:
            if self.last_message_content[user_key] == message.content.strip():
                await message.add_reaction("🔄")
                return
        
        # Message length check using room-specific setting
        if len(message.content) > room_permissions['max_message_length']:
            await message.add_reaction("📏")
            return
        
        # URL filtering (if disabled in room settings)
        if not room_permissions['allow_urls'] and self._contains_url(message.content):
            await message.add_reaction("🔗")
            await message.author.send(f"🚫 URLs are not allowed in the **{room_name}** chat room. Your message was blocked.")
            return
        
        # File attachment filtering
        if not room_permissions['allow_files'] and message.attachments:
            await message.add_reaction("📎")
            await message.author.send(f"🚫 File attachments are not allowed in the **{room_name}** chat room. Your message was blocked.")
            return
        
        # Mention filtering
        if not room_permissions['allow_mentions'] and ('@everyone' in message.content or '@here' in message.content or message.mentions):
            await message.add_reaction("💬")
            await message.author.send(f"🚫 Mentions are not allowed in the **{room_name}** chat room. Your message was blocked.")
            return
        
        # Content filtering using room-specific setting
        if room_permissions['enable_bad_word_filter'] and self._contains_blocked_content(message.content):
            await message.add_reaction("🚫")
            await message.author.send(f"🚫 Your message contains blocked content and was not sent to the **{room_name}** chat room.")
            return
        
        # Update tracking only after all checks pass
        self.last_message_time[user_key] = current_time
        self.last_message_content[user_key] = message.content.strip()
        
        # Check if this is a reply message
        reply_data = await self._extract_reply_data(message, room_name)
        
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
    
    def _contains_blocked_content(self, content: str) -> bool:
        """Check if message contains blocked content"""
        content_lower = content.lower()
        for word in self.blocked_words:
            if word in content_lower:
                return True
        return False
    
    def _contains_url(self, content: str) -> bool:
        """Check if message contains URLs or links"""
        for pattern in self.compiled_url_patterns:
            if pattern.search(content):
                return True
        return False
    
    async def _extract_reply_data(self, message: discord.Message, room_name: str):
        """Extract reply data from a Discord message"""
        reply_data = {}
        
        # Check if the message is a reply to another message
        if message.reference and message.reference.message_id:
            print(f"🔍 Reply detected! Message ID: {message.reference.message_id}")
            try:
                # First try to get from our database (for global chat messages)
                original_msg_data = self.db.get_message_for_reply(str(message.reference.message_id), room_name)
                if original_msg_data:
                    print(f"✅ Found original message in database: {original_msg_data['username']}")
                    reply_data['reply_to_message_id'] = str(message.reference.message_id)
                    reply_data['reply_to_username'] = original_msg_data['username']
                    reply_data['reply_to_content'] = original_msg_data['content']
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
                                
                                # Check if this is a reply to a reply (nested reply)
                                if '┌─' in bot_content and '└─' in bot_content:
                                    # This is a reply message, extract the last user's message
                                    print("🔄 Detected reply to reply, extracting last user message...")
                                    # Split by └─ to get the last user's message
                                    if '└─' in bot_content:
                                        last_part = bot_content.split('└─')[-1].split('\n')[0].strip()
                                        # Extract username and message from "**Username:** message"
                                        if '**' in last_part and ':**' in last_part:
                                            username_end = last_part.find(':**')
                                            if username_end != -1:
                                                username_start = last_part.find('**') + 2
                                                reply_data['reply_to_username'] = last_part[username_start:username_end]
                                                reply_data['reply_to_content'] = last_part[username_end + 3:].strip()
                                                reply_data['reply_to_message_id'] = str(message.reference.message_id)
                                                print(f"✅ Extracted from nested reply - User: {reply_data['reply_to_username']}, Content: {reply_data['reply_to_content'][:30]}...")
                                            else:
                                                # Fallback to normal parsing
                                                reply_data['reply_to_content'] = last_part
                                                reply_data['reply_to_username'] = "Previous User"
                                        else:
                                            reply_data['reply_to_content'] = last_part
                                            reply_data['reply_to_username'] = "Previous User"
                                else:
                                    # Try different patterns to extract username and content
                                    if '**: **' in bot_content:
                                        # Pattern: "URL • @Username**: ** actual message"
                                        parts = bot_content.split('**: **')
                                        if len(parts) >= 2:
                                            # Get the actual message (remove extra formatting)
                                            actual_message = parts[1].strip().replace('*', '').strip()
                                            # Extract username from the first part
                                            first_part = parts[0]
                                            if '<@' in first_part and '>' in first_part:
                                                # Handle Discord mention format <@userid>
                                                import re
                                                mention_match = re.search(r'<@(\d+)>', first_part)
                                                if mention_match:
                                                    user_id = mention_match.group(1)
                                                    try:
                                                        # Try to get the actual username from Discord
                                                        mentioned_user = self.bot.get_user(int(user_id))
                                                        if mentioned_user:
                                                            username_part = mentioned_user.display_name
                                                        else:
                                                            # Try to fetch the user
                                                            mentioned_user = await self.bot.fetch_user(int(user_id))
                                                            username_part = mentioned_user.display_name if mentioned_user else f"User{user_id}"
                                                    except:
                                                        username_part = f"User{user_id}"
                                                else:
                                                    username_part = "Someone"
                                            else:
                                                username_part = first_part.split('**')[-1].strip() if '**' in first_part else "Someone"
                                            reply_data['reply_to_content'] = actual_message
                                            reply_data['reply_to_username'] = username_part
                                            print(f"✅ Extracted - User: {username_part}, Content: {actual_message[:30]}...")
                                        else:
                                            reply_data['reply_to_content'] = bot_content
                                    elif '**: ' in bot_content:
                                        # Pattern: "URL • **Username:** actual message"
                                        parts = bot_content.split('**: ')
                                        if len(parts) >= 2:
                                            actual_message = parts[-1].strip().replace('*', '').strip()
                                            # Extract username from before the :**
                                            before_colon = parts[-2]
                                            if '<@' in before_colon and '>' in before_colon:
                                                # Handle Discord mention format <@userid>
                                                import re
                                                mention_match = re.search(r'<@(\d+)>', before_colon)
                                                if mention_match:
                                                    user_id = mention_match.group(1)
                                                    try:
                                                        # Try to get the actual username from Discord
                                                        mentioned_user = self.bot.get_user(int(user_id))
                                                        if mentioned_user:
                                                            username_part = mentioned_user.display_name
                                                        else:
                                                            # Try to fetch the user
                                                            mentioned_user = await self.bot.fetch_user(int(user_id))
                                                            username_part = mentioned_user.display_name if mentioned_user else f"User{user_id}"
                                                    except:
                                                        username_part = f"User{user_id}"
                                                else:
                                                    username_part = "Someone"
                                            elif '**' in before_colon:
                                                username_part = before_colon.split('**')[-1].strip()
                                            else:
                                                username_part = "Someone"
                                            reply_data['reply_to_content'] = actual_message
                                            reply_data['reply_to_username'] = username_part
                                            print(f"✅ Extracted - User: {username_part}, Content: {actual_message[:30]}...")
                                        else:
                                            reply_data['reply_to_content'] = bot_content
                                    else:
                                        reply_data['reply_to_content'] = bot_content
                            else:
                                reply_data['reply_to_content'] = original_message.content
                        elif hasattr(original_message, 'embeds') and original_message.embeds:
                            # If it's an embed message (like from our bot)
                            reply_data['reply_to_content'] = original_message.embeds[0].description or "[Embed message]"
                        elif hasattr(original_message, 'attachments') and original_message.attachments:
                            reply_data['reply_to_content'] = f"[Attachment: {original_message.attachments[0].filename}]"
                        else:
                            reply_data['reply_to_content'] = "[No text content]"
                        
                        print(f"📝 Extracted content: {reply_data['reply_to_content'][:50]}...")
                    else:
                        # If all fails, show basic reply info
                        print(f"❌ Could not get original message data")
                        reply_data['reply_to_message_id'] = str(message.reference.message_id)
                        reply_data['reply_to_username'] = "Unknown User"
                        reply_data['reply_to_content'] = "[Message not found]"
            except Exception as e:
                print(f"⚠️ Error extracting reply data: {e}")
        
        return reply_data
    
    async def broadcast_message(self, original_message: discord.Message, room_name: str):
        """Broadcast message to all registered global chat channels in the same room"""
        # Get all registered channels in the same room
        channels = self.db.get_global_chat_channels(room_name)
        
        print(f"🔄 Broadcasting message from {original_message.guild.name} to room '{room_name}' - Found {len(channels)} registered channels")
        for ch in channels:
            print(f"   - {ch['guild_name']} #{ch['channel_name']} (ID: {ch['channel_id']})")

        original_message_url = f"https://discord.com/channels/{original_message.guild.id}/{original_message.channel.id}/{original_message.id}"
        
        # Check if this is a reply message
        reply_data = await self._extract_reply_data(original_message, room_name)
        
        # Create reply context if this is a reply
        reply_context = ""
        if reply_data.get('reply_to_message_id'):
            reply_to_username = reply_data['reply_to_username']
            reply_to_content = reply_data['reply_to_content']
            
            # Clean and truncate the original message content
            reply_to_content = reply_to_content.strip()
            if len(reply_to_content) > 50:
                reply_to_content = reply_to_content[:47] + "..."
            
            # Clean any extra formatting characters
            reply_to_content = reply_to_content.replace('**', '').replace('*', '').strip()
            
            reply_context = f"┌─ **💬 Replying to {reply_to_username}:** *{reply_to_content}*\n└─ "
            print(f"📝 Adding reply context: {reply_context.strip()}")
        else:
            print(f"📝 No reply data found, sending as regular message")
        
        # Create plain text message with room name and reply context
        if reply_context:
            # For replies, use the same header format as regular messages but with reply context
            message_content = f"{original_message_url} • {reply_context}{original_message.author.mention}**: ** {original_message.content} \n\n"
        else:
            # For regular messages, use the original format
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
                    await self._notify_permission_issue(channel_info, "send messages", room_name)
                    continue
                
                print(f"   ✅ Permissions OK, sending message...")
                await channel.send(message_content)
                print(f"   ✅ Message sent successfully!")
                
            except discord.Forbidden:
                print(f"   ❌ Forbidden: No permission to send message in {channel_info['guild_name']} - {channel_info['channel_name']}")
                await self._notify_permission_issue(channel_info, "send messages (Forbidden)", room_name)
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
    
    async def show_interactive_permissions(self, ctx, room_name: str, owner_id: str, room_id: int = None):
        """Show default settings overview and option to customize"""
        perms = self.db.get_room_permissions(room_name)
        
        # Get room ID if not provided
        if room_id is None:
            room_id = self.db.get_room_id_by_name(room_name)
        
        # Create comprehensive overview of default settings
        overview_embed = discord.Embed(
            title=f"Room Created: {room_name}",
            description=f"**Welcome, {ctx.author.display_name}!** Your room is ready with secure default settings.\n\n"
                       f"**Room ID:** {room_id} *(Use this ID for settings management)*\n"
                       f"**Security-First Approach:** We prioritize safety with smart defaults that prevent scams and malicious content.",
            color=0x00ff00
        )
        
        # Current settings overview
        overview_embed.add_field(
            name="Default Settings Applied",
            value=f"**URLs & Links:** {'✅ Allowed' if perms['allow_urls'] else '❌ Blocked'} *{chr(10)}    ↳ Prevents malicious links, phishing, and scam sites*\n\n"
                  f"**File Attachments:** {'✅ Allowed' if perms['allow_files'] else '❌ Blocked'} *{chr(10)}    ↳ Prevents malware, viruses, and inappropriate content*\n\n"
                  f"**Bad Word Filter:** {'✅ Enabled' if perms['enable_bad_word_filter'] else '❌ Disabled'} *{chr(10)}    ↳ Filters profanity, spam, and scam-related terms*\n\n"
                  f"**@Mentions:** {'✅ Allowed' if perms['allow_mentions'] else '❌ Blocked'} *{chr(10)}    ↳ Controls @everyone, @here, and user mentions*\n\n"
                  f"**Emojis:** {'✅ Allowed' if perms['allow_emojis'] else '❌ Blocked'} *{chr(10)}    ↳ Controls custom emojis and reactions*",
            inline=False
        )
        
        # Advanced settings info
        overview_embed.add_field(
            name="Advanced Settings",
            value=f"**Max Message Length:** {perms['max_message_length']} characters\n"
                  f"**Rate Limit:** {perms['rate_limit_seconds']} seconds between messages\n"
                  f"*Use `!roomset {room_id} <setting> <value>` to adjust these*",
            inline=False
        )
        
        # Customization option
        overview_embed.add_field(
            name="Your Room is Ready!",
            value="**These secure defaults work great for most rooms!**\n\n"
                  f"**Accept defaults:** Your room is ready to use safely\n"
                  f"**Customize:** React with ✏️ below to adjust individual permissions\n"
                  f"**Learn more:** React with ℹ️ to understand security settings\n\n"
                  f"**Later changes:** Use `!roomsettings {room_id}` anytime\n\n"
                  f"*Most room owners find the defaults perfect for safety and functionality.*",
            inline=False
        )
        
        overview_embed.set_footer(text="React below: ✏️ Customize permissions • ℹ️ Security info")
        
        overview_msg = await ctx.send(embed=overview_embed)
        
        # Add reaction options
        await overview_msg.add_reaction("✏️")  # Edit/Customize
        await overview_msg.add_reaction("ℹ️")   # Info
        
        # Store setup info
        self.pending_setups = getattr(self, 'pending_setups', {})
        setup_id = f"{ctx.guild.id}_{ctx.channel.id}_{owner_id}"
        
        self.pending_setups[setup_id] = {
            'room_name': room_name,
            'owner_id': owner_id,
            'channel_id': ctx.channel.id,
            'guild_id': ctx.guild.id,
            'overview_msg_id': overview_msg.id,
            'stage': 'overview',  # Track what stage we're in
            'messages': []
        }
        
        return overview_msg
    
    async def show_customization_options(self, setup_info):
        """Show individual permission customization messages"""
        guild = self.bot.get_guild(setup_info['guild_id'])
        channel = guild.get_channel(setup_info['channel_id'])
        room_name = setup_info['room_name']
        room_id = self.db.get_room_id_by_name(room_name)
        perms = self.db.get_room_permissions(room_name)
        
        # Send customization intro
        custom_intro = discord.Embed(
            title="Individual Permission Customization",
            description="**Great!** Let's customize each permission individually.\n"
                       "Each setting below can be toggled with ✅ (allow/enable) or ❌ (block/disable).",
            color=0x0099ff
        )
        custom_intro.set_footer(text="React to each permission below to customize your room!")
        await channel.send(embed=custom_intro)
        
        messages = []
        
        # 1. URL Permission
        url_status = "✅ ALLOWED" if perms['allow_urls'] else "❌ BLOCKED"
        url_embed = discord.Embed(
            title="URLs & Links Permission",
            description=f"**Current Status:** {url_status}\n\n"
                       f"**Security Info:** URLs can contain malicious links, phishing sites, or scams.\n"
                       f"**Recommendation:** Keep blocked for maximum safety.",
            color=0x00ff00 if perms['allow_urls'] else 0xff0000
        )
        url_embed.add_field(name="Controls", value="✅ Allow URLs\n❌ Block URLs", inline=False)
        url_msg = await channel.send(embed=url_embed)
        await url_msg.add_reaction("✅")
        await url_msg.add_reaction("❌")
        messages.append(('allow_urls', url_msg.id))
        
        # 2. File Permission
        file_status = "✅ ALLOWED" if perms['allow_files'] else "❌ BLOCKED"
        file_embed = discord.Embed(
            title="File Attachments Permission",
            description=f"**Current Status:** {file_status}\n\n"
                       f"**Security Info:** Files can contain malware, viruses, or inappropriate content.\n"
                       f"**Recommendation:** Keep blocked unless you need file sharing.",
            color=0x00ff00 if perms['allow_files'] else 0xff0000
        )
        file_embed.add_field(name="Controls", value="✅ Allow Files\n❌ Block Files", inline=False)
        file_msg = await channel.send(embed=file_embed)
        await file_msg.add_reaction("✅")
        await file_msg.add_reaction("❌")
        messages.append(('allow_files', file_msg.id))
        
        # 3. Bad Word Filter
        filter_status = "✅ ENABLED" if perms['enable_bad_word_filter'] else "❌ DISABLED"
        filter_embed = discord.Embed(
            title="Bad Word Filter",
            description=f"**Current Status:** {filter_status}\n\n"
                       f"**Security Info:** Filters out profanity, spam, and scam-related words.\n"
                       f"**Recommendation:** Keep enabled for a clean chat environment.",
            color=0x00ff00 if perms['enable_bad_word_filter'] else 0xff0000
        )
        filter_embed.add_field(name="Controls", value="✅ Enable Filter\n❌ Disable Filter", inline=False)
        filter_msg = await channel.send(embed=filter_embed)
        await filter_msg.add_reaction("✅")
        await filter_msg.add_reaction("❌")
        messages.append(('enable_bad_word_filter', filter_msg.id))
        
        # 4. Mention Permission
        mention_status = "✅ ALLOWED" if perms['allow_mentions'] else "❌ BLOCKED"
        mention_embed = discord.Embed(
            title="@Mentions Permission",
            description=f"**Current Status:** {mention_status}\n\n"
                       f"**Info:** Controls @everyone, @here, and user mentions.\n"
                       f"**Note:** Usually safe to allow for normal chat interaction.",
            color=0x00ff00 if perms['allow_mentions'] else 0xff0000
        )
        mention_embed.add_field(name="Controls", value="✅ Allow Mentions\n❌ Block Mentions", inline=False)
        mention_msg = await channel.send(embed=mention_embed)
        await mention_msg.add_reaction("✅")
        await mention_msg.add_reaction("❌")
        messages.append(('allow_mentions', mention_msg.id))
        
        # 5. Emoji Permission
        emoji_status = "✅ ALLOWED" if perms['allow_emojis'] else "❌ BLOCKED"
        emoji_embed = discord.Embed(
            title="Emojis Permission",
            description=f"**Current Status:** {emoji_status}\n\n"
                       f"**Info:** Controls custom emojis and reactions.\n"
                       f"**Note:** Usually safe to allow for fun chat interaction.",
            color=0x00ff00 if perms['allow_emojis'] else 0xff0000
        )
        emoji_embed.add_field(name="Controls", value="✅ Allow Emojis\n❌ Block Emojis", inline=False)
        emoji_msg = await channel.send(embed=emoji_embed)
        await emoji_msg.add_reaction("✅")
        await emoji_msg.add_reaction("❌")
        messages.append(('allow_emojis', emoji_msg.id))
        
        # Final completion message
        complete_embed = discord.Embed(
            title="Customization Complete!",
            description=f"**Your room settings have been customized!**\n\n"
                       f"**Current Settings:**\n"
                       f"URLs: {'✅ Allowed' if perms['allow_urls'] else '❌ Blocked'}\n"
                       f"Files: {'✅ Allowed' if perms['allow_files'] else '❌ Blocked'}\n"
                       f"Filter: {'✅ Enabled' if perms['enable_bad_word_filter'] else '❌ Disabled'}\n"
                       f"Mentions: {'✅ Allowed' if perms['allow_mentions'] else '❌ Blocked'}\n"
                       f"Emojis: {'✅ Allowed' if perms['allow_emojis'] else '❌ Blocked'}\n\n"
                       f"**Advanced Settings:**\n"
                       f"Max Length: {perms['max_message_length']} characters\n"
                       f"Rate Limit: {perms['rate_limit_seconds']} seconds\n\n"
                       f"Use `!roomsettings {room_id}` to view or change settings anytime!",
            color=0x00ff00
        )
        complete_msg = await channel.send(embed=complete_embed)
        
        # Update setup info
        setup_info['messages'] = messages
        setup_info['complete_msg_id'] = complete_msg.id
        setup_info['stage'] = 'customizing'
        
        return messages
    
    async def handle_permission_reaction(self, payload):
        """Handle reaction-based permission toggles and setup flow"""
        if not hasattr(self, 'pending_setups'):
            return
        
        # Check if this is an overview message reaction
        setup_info = None
        is_overview = False
        
        for setup_id, info in self.pending_setups.items():
            # Check if it's the overview message
            if info.get('overview_msg_id') == payload.message_id and info.get('stage') == 'overview':
                setup_info = info
                is_overview = True
                break
            # Check if it's a customization message
            elif info.get('stage') == 'customizing':
                for perm_type, msg_id in info.get('messages', []):
                    if msg_id == payload.message_id:
                        setup_info = info
                        break
        
        if not setup_info:
            return
        
        # Check if the reaction is from the room owner
        if str(payload.user_id) != setup_info['owner_id']:
            return
        
        emoji = str(payload.emoji)
        
        # Handle overview stage reactions
        if is_overview:
            if emoji == "✏️":
                # User wants to customize - show individual options
                await self.show_customization_options(setup_info)
                
            elif emoji == "ℹ️":
                # User wants security details
                await self._show_security_details(setup_info)
                
            return
        
        # Handle customization stage reactions
        if setup_info.get('stage') == 'customizing':
            # Find which permission this message belongs to
            permission_type = None
            for perm_type, msg_id in setup_info.get('messages', []):
                if msg_id == payload.message_id:
                    permission_type = perm_type
                    break
            
            if not permission_type:
                return
            
            # Only handle ✅ and ❌ reactions
            if emoji not in ["✅", "❌"]:
                return
            
            room_name = setup_info['room_name']
            
            # Determine new value based on reaction
            new_value = (emoji == "✅")
            
            # Update permission in database
            self.db.update_room_permission(room_name, permission_type, new_value, setup_info['owner_id'])
            
            # Update the specific message embed
            await self._update_individual_permission_message(payload.message_id, permission_type, room_name, new_value)
            
            # Update the completion message with current settings
            await self._update_completion_message(setup_info)
    
    async def _update_individual_permission_message(self, message_id: int, permission_type: str, room_name: str, new_value: bool):
        """Update individual permission message with new status"""
        # Get the message from any pending setup
        guild = None
        channel = None
        
        for setup_info in self.pending_setups.values():
            for perm_type, msg_id in setup_info['messages']:
                if msg_id == message_id:
                    guild = self.bot.get_guild(setup_info['guild_id'])
                    channel = guild.get_channel(setup_info['channel_id'])
                    break
        
        if not guild or not channel:
            return
        
        try:
            message = await channel.fetch_message(message_id)
        except:
            return
        
        # Create updated embed based on permission type
        permission_configs = {
            'allow_urls': {
                'title': 'URLs & Links Permission',
                'security_info': 'URLs can contain malicious links, phishing sites, or scams.',
                'recommendation': 'Keep blocked for maximum safety.',
                'controls': 'Allow URLs\nBlock URLs'
            },
            'allow_files': {
                'title': 'File Attachments Permission',
                'security_info': 'Files can contain malware, viruses, or inappropriate content.',
                'recommendation': 'Keep blocked unless you need file sharing.',
                'controls': 'Allow Files\nBlock Files'
            },
            'enable_bad_word_filter': {
                'title': 'Bad Word Filter',
                'security_info': 'Filters out profanity, spam, and scam-related words.',
                'recommendation': 'Keep enabled for a clean chat environment.',
                'controls': 'Enable Filter\nDisable Filter'
            },
            'allow_mentions': {
                'title': '@Mentions Permission',
                'security_info': 'Controls @everyone, @here, and user mentions.',
                'recommendation': 'Usually safe to allow for normal chat interaction.',
                'controls': 'Allow Mentions\nBlock Mentions'
            },
            'allow_emojis': {
                'title': 'Emojis Permission',
                'security_info': 'Controls custom emojis and reactions.',
                'recommendation': 'Usually safe to allow for fun chat interaction.',
                'controls': 'Allow Emojis\nBlock Emojis'
            }
        }
        
        config = permission_configs.get(permission_type, {})
        
        if permission_type == 'enable_bad_word_filter':
            status = "✅ ENABLED" if new_value else "❌ DISABLED"
        else:
            status = "✅ ALLOWED" if new_value else "❌ BLOCKED"
        
        embed = discord.Embed(
            title=config.get('title', 'Permission'),
            description=f"**Current Status:** {status} **UPDATED!**\n\n"
                       f"**Security Info:** {config.get('security_info', '')}\n"
                       f"**Recommendation:** {config.get('recommendation', '')}",
            color=0x00ff00 if new_value else 0xff0000
        )
        controls = config.get('controls', '').split('\n')
        control_text = f"✅ {controls[0]}\n❌ {controls[1] if len(controls) > 1 else ''}"
        embed.add_field(name="Controls", value=control_text, inline=False)
        
        await message.edit(embed=embed)
    
    async def _update_completion_message(self, setup_info: dict):
        """Update the completion message with current settings"""
        guild = self.bot.get_guild(setup_info['guild_id'])
        channel = guild.get_channel(setup_info['channel_id'])
        
        try:
            complete_msg = await channel.fetch_message(setup_info['complete_msg_id'])
        except:
            return
        
        room_name = setup_info['room_name']
        room_id = self.db.get_room_id_by_name(room_name)
        perms = self.db.get_room_permissions(room_name)
        
        complete_embed = discord.Embed(
            title="🎯 Setup Complete!",
            description=f"**Your room is ready!** 🎉\n\n"
                       f"📊 **Current Settings:**\n"
                       f"🔗 URLs: {'✅ Allowed' if perms['allow_urls'] else '❌ Blocked'}\n"
                       f"📎 Files: {'✅ Allowed' if perms['allow_files'] else '❌ Blocked'}\n"
                       f"🚫 Filter: {'✅ Enabled' if perms['enable_bad_word_filter'] else '❌ Disabled'}\n"
                       f"💬 Mentions: {'✅ Allowed' if perms['allow_mentions'] else '❌ Blocked'}\n"
                       f"😀 Emojis: {'✅ Allowed' if perms['allow_emojis'] else '❌ Blocked'}\n\n"
                       f"⚙️ **Advanced Settings:**\n"
                       f"📏 Max Length: {perms['max_message_length']} characters\n"
                       f"⏰ Rate Limit: {perms['rate_limit_seconds']} seconds\n\n"
                       f"💡 Use `!roomsettings {room_id}` to view or change settings anytime!",
            color=0x00ff00
        )
        
        await complete_msg.edit(embed=complete_embed)
    
    async def _show_final_completion(self, setup_info):
        """Show final completion message when user keeps defaults"""
        guild = self.bot.get_guild(setup_info['guild_id'])
        channel = guild.get_channel(setup_info['channel_id'])
        room_name = setup_info['room_name']
        room_id = self.db.get_room_id_by_name(room_name)
        
        final_embed = discord.Embed(
            title="Room Setup Complete!",
            description=f"**Perfect choice!** Your room **{room_name}** is ready with secure defaults.\n\n"
                       f"**Security-First Settings Applied:**\n"
                       f"URLs: ❌ Blocked (prevents malicious links)\n"
                       f"Files: ❌ Blocked (prevents malware)\n"
                       f"Filter: ✅ Enabled (blocks inappropriate content)\n"
                       f"Mentions: ✅ Allowed (normal chat interaction)\n"
                       f"Emojis: ✅ Allowed (fun interactions)\n\n"
                       f"**Need to change something later?** Use `!roomsettings {room_id}` anytime!",
            color=0x00ff00
        )
        final_embed.set_footer(text="Your room is now active and ready for secure chatting!")
        await channel.send(embed=final_embed)
        
        # Remove from pending setups
        for setup_id, info in list(self.pending_setups.items()):
            if info == setup_info:
                del self.pending_setups[setup_id]
                break
    
    async def _show_security_details(self, setup_info):
        """Show detailed security information"""
        guild = self.bot.get_guild(setup_info['guild_id'])
        channel = guild.get_channel(setup_info['channel_id'])
        
        security_embed = discord.Embed(
            title="Security Details & Recommendations",
            description="**Understanding each permission and why our defaults keep you safe:**",
            color=0xff9900
        )
        
        security_embed.add_field(
            name="URL Blocking (Default: BLOCKED)",
            value="**Why blocked?**\n"
                  "• Prevents phishing attempts\n"
                  "• Blocks malicious websites\n"
                  "• Stops cryptocurrency scams\n"
                  "• Prevents virus downloads\n"
                  "*Enable only if you trust all room members*",
            inline=False
        )
        
        security_embed.add_field(
            name="File Blocking (Default: BLOCKED)",
            value="**Why blocked?**\n"
                  "• Prevents malware distribution\n"
                  "• Blocks inappropriate images\n"
                  "• Stops virus-infected files\n"
                  "• Prevents data theft attempts\n"
                  "*Enable only for trusted file sharing*",
            inline=False
        )
        
        security_embed.add_field(
            name="Bad Word Filter (Default: ENABLED)",
            value="**Why enabled?**\n"
                  "• Filters profanity automatically\n"
                  "• Blocks spam messages\n"
                  "• Catches scam-related terms\n"
                  "• Maintains professional environment\n"
                  "*Disable only for mature audiences*",
            inline=False
        )
        
        security_embed.set_footer(text="These defaults protect 99% of rooms perfectly! • React 🎛️ on overview to customize")
        await channel.send(embed=security_embed)
    
    async def _notify_permission_issue(self, channel_info: dict, permission_type: str, room_name: str):
        """Send DM notification to user who registered the channel about permission issues"""
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
    
    
