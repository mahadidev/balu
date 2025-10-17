import discord
import asyncio
import time
from typing import Dict, List, Optional, Tuple
from database.db_manager import DatabaseManager
import difflib
import re

class CategoryChatManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.last_message_time: Dict[str, float] = {}
        self.rate_limit_seconds = 3
        self.max_message_length = 2000
        
        # Simple profanity filter (expandable)
        self.blocked_words = [
            'spam', 'hack', 'cheat', 'exploit', 'scam'
        ]
    
    async def handle_category_message(self, message: discord.Message):
        """Handle incoming message from a category chat channel"""
        if message.author.bot:
            return
        
        # Get all categories this channel is subscribed to
        subscriptions = self.db.get_channel_subscriptions(str(message.guild.id), str(message.channel.id))
        
        if not subscriptions:
            return
        
        # Rate limiting per user per category
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
        if self._contains_blocked_content(message.content):
            await message.add_reaction("🚫")
            return
        
        # If message starts with category prefix, send to specific category
        content = message.content.strip()
        target_category = None
        
        # Check for category prefix (e.g., "[Clash Squad] hello everyone")
        if content.startswith('[') and ']' in content:
            end_bracket = content.find(']')
            if end_bracket != -1:
                category_prefix = content[1:end_bracket].strip()
                # Check if this channel is subscribed to this category (case-insensitive)
                for sub in subscriptions:
                    if sub['category_name'].lower() == category_prefix.lower():
                        target_category = sub['category_name']  # Use the actual category name
                        content = content[end_bracket + 1:].strip()
                        break
        
        # If no specific category, send to all subscribed categories
        if target_category:
            categories_to_send = [target_category]
        else:
            categories_to_send = [sub['category_name'] for sub in subscriptions]
        
        # Send message to each category
        for category_name in categories_to_send:
            # Log the message
            self.db.log_category_message(
                str(message.id),
                category_name,
                str(message.guild.id),
                str(message.channel.id),
                str(message.author.id),
                message.author.display_name,
                message.guild.name,
                content
            )
            
            # Broadcast to category subscribers
            await self.broadcast_to_category(message, category_name, content)
    
    def _contains_blocked_content(self, content: str) -> bool:
        """Check if message contains blocked content"""
        content_lower = content.lower()
        for word in self.blocked_words:
            if word in content_lower:
                return True
        return False
    
    async def broadcast_to_category(self, original_message: discord.Message, category_name: str, content: str):
        """Broadcast message to all subscribers of a specific category"""
        # Get all subscribers of this category
        subscribers = self.db.get_category_subscribers(category_name)
        
        # Create formatted message
        if content.strip():
            message_content = f"**{content}**\n\n-# [{category_name.upper()}] {original_message.guild.name} • {original_message.author.mention}"
        else:
            message_content = f"-# [{category_name.upper()}] {original_message.guild.name} • {original_message.author.mention}"
        
        # Handle attachments
        if original_message.attachments:
            attachment = original_message.attachments[0]
            if attachment.content_type and attachment.content_type.startswith('image/'):
                message_content += f"\n🖼️ Image: {attachment.url}"
            else:
                message_content += f"\n📎 Attachment: [{attachment.filename}]({attachment.url})"
        
        # Send to all subscribers except the original channel
        for subscriber in subscribers:
            # Skip the original channel
            if (subscriber['guild_id'] == str(original_message.guild.id) and 
                subscriber['channel_id'] == str(original_message.channel.id)):
                continue
            
            try:
                guild = self.bot.get_guild(int(subscriber['guild_id']))
                if not guild:
                    continue
                
                channel = guild.get_channel(int(subscriber['channel_id']))
                if not channel:
                    continue
                
                # Check if bot has permission to send messages
                if not channel.permissions_for(guild.me).send_messages:
                    continue
                
                await channel.send(message_content)
                
                # Add a small delay between messages to separate them visually
                await asyncio.sleep(0.5)
                
            except discord.Forbidden:
                print(f"No permission to send message in {subscriber['guild_name']} - {subscriber['channel_name']}")
            except discord.NotFound:
                print(f"Channel not found: {subscriber['guild_name']} - {subscriber['channel_name']}")
            except Exception as e:
                print(f"Error sending category message to {subscriber['guild_name']}: {e}")
    
    async def create_category(self, category_name: str, created_by: str, max_servers: int = 50) -> str:
        """Create a new chat category"""
        # Validate category name
        category_name = category_name.strip()
        
        if not category_name or len(category_name) < 2 or len(category_name) > 30:
            return "❌ Category name must be between 2-30 characters!"
        
        # Allow letters, numbers, spaces, and basic punctuation
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_')
        if not all(char in allowed_chars for char in category_name):
            return "❌ Category name can only contain letters, numbers, spaces, hyphens, and underscores!"
        
        result = self.db.create_chat_category(category_name, created_by, max_servers)
        
        if result:
            return f"✅ Successfully created category **{category_name}**!"
        else:
            return f"❌ Category **{category_name}** already exists!"
    
    async def delete_category(self, category_name: str, deleted_by: str) -> str:
        """Delete a chat category"""
        result = self.db.delete_chat_category(category_name, deleted_by)
        
        if result == "not_found":
            return f"❌ Category **{category_name}** not found!"
        elif result == "no_permission":
            return "❌ You can only delete categories you created!"
        elif result == "success":
            return f"✅ Successfully deleted category **{category_name}** and all its subscriptions!"
        else:
            return "❌ Failed to delete category!"
    
    async def subscribe_channel(self, guild: discord.Guild, channel: discord.TextChannel, category_name: str, subscribed_by: discord.Member) -> str:
        """Subscribe a channel to a category"""
        # Check permissions
        if not subscribed_by.guild_permissions.manage_channels:
            return "❌ You need 'Manage Channels' permission to subscribe to categories!"
        
        result = self.db.subscribe_to_category(
            category_name,
            str(guild.id),
            str(channel.id),
            guild.name,
            channel.name,
            str(subscribed_by.id)
        )
        
        if result == "category_not_found":
            return f"❌ Category **{category_name}** not found!"
        elif result == "category_full":
            return f"❌ Category **{category_name}** is full!"
        elif result == "success":
            return f"✅ Successfully subscribed {channel.mention} to **{category_name}**!"
        elif result == "updated":
            return f"✅ Updated subscription for {channel.mention} to **{category_name}**!"
        else:
            return "❌ Failed to subscribe to category!"
    
    async def unsubscribe_channel(self, guild: discord.Guild, channel: discord.TextChannel, category_name: str, requested_by: discord.Member) -> str:
        """Unsubscribe a channel from a category"""
        # Check permissions
        if not requested_by.guild_permissions.manage_channels:
            return "❌ You need 'Manage Channels' permission to unsubscribe from categories!"
        
        success = self.db.unsubscribe_from_category(category_name, str(guild.id), str(channel.id))
        
        if success:
            return f"✅ Successfully unsubscribed {channel.mention} from **{category_name}**!"
        else:
            return f"❌ {channel.mention} was not subscribed to **{category_name}**!"
    
    def get_all_categories(self) -> List[Dict]:
        """Get all available categories"""
        return self.db.get_chat_categories()
    
    def get_category_info(self, category_name: str) -> Optional[Dict]:
        """Get information about a specific category"""
        categories = self.db.get_chat_categories()
        for category in categories:
            if category['category_name'].lower() == category_name.lower():
                return category
        return None
    
    def get_channel_subscriptions(self, guild_id: str, channel_id: str) -> List[Dict]:
        """Get all categories a channel is subscribed to"""
        return self.db.get_channel_subscriptions(guild_id, channel_id)
    
    def get_category_subscribers(self, category_name: str) -> List[Dict]:
        """Get all subscribers of a category"""
        return self.db.get_category_subscribers(category_name)
    
    def smart_category_match(self, user_input: str) -> Tuple[Optional[str], float, List[Tuple[str, float]]]:
        """
        AI-powered category matching using multiple algorithms
        Returns: (best_match, confidence_score, all_matches_with_scores)
        """
        user_input = user_input.strip().lower()
        if not user_input:
            return None, 0.0, []
        
        all_categories = self.get_all_categories()
        if not all_categories:
            return None, 0.0, []
        
        category_names = [cat['category_name'] for cat in all_categories]
        matches_with_scores = []
        
        for category_name in category_names:
            category_lower = category_name.lower()
            
            # Algorithm 1: Exact substring match (highest priority)
            if user_input in category_lower:
                if user_input == category_lower:
                    # Exact match gets maximum score
                    score = 1.0
                else:
                    # Substring match gets high score based on coverage
                    score = 0.9 + (len(user_input) / len(category_lower)) * 0.09
                matches_with_scores.append((category_name, score))
                continue
            
            # Algorithm 2: Word-based matching
            user_words = re.findall(r'\w+', user_input)
            category_words = re.findall(r'\w+', category_lower)
            
            word_matches = 0
            total_user_words = len(user_words)
            
            if total_user_words > 0:
                for user_word in user_words:
                    for cat_word in category_words:
                        if user_word in cat_word or cat_word in user_word:
                            word_matches += 1
                            break
                
                word_score = word_matches / total_user_words
                if word_score > 0.5:  # At least 50% word match
                    matches_with_scores.append((category_name, 0.7 + word_score * 0.2))
                    continue
            
            # Algorithm 3: Fuzzy string matching using difflib
            similarity = difflib.SequenceMatcher(None, user_input, category_lower).ratio()
            if similarity > 0.4:  # 40% similarity threshold
                matches_with_scores.append((category_name, 0.3 + similarity * 0.4))
                continue
            
            # Algorithm 4: Initials matching (e.g., "csl" -> "Clash Squad Limited")
            category_initials = ''.join([word[0] for word in category_words if word])
            if len(user_input) >= 2 and user_input == category_initials:
                matches_with_scores.append((category_name, 0.8))
                continue
            
            # Algorithm 5: Partial initials (e.g., "cs" -> "Clash Squad")
            if len(user_input) >= 2 and category_initials.startswith(user_input):
                matches_with_scores.append((category_name, 0.6))
        
        # Sort by score (highest first)
        matches_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return best match with confidence
        if matches_with_scores:
            best_match, best_score = matches_with_scores[0]
            return best_match, best_score, matches_with_scores[:5]  # Return top 5 matches
        
        return None, 0.0, []
    
    async def smart_subscribe_channel(self, guild: discord.Guild, channel: discord.TextChannel, user_input: str, subscribed_by: discord.Member) -> str:
        """Subscribe to a category using AI-powered matching"""
        # Check permissions
        if not subscribed_by.guild_permissions.manage_channels:
            return "❌ You need 'Manage Channels' permission to subscribe to categories!"
        
        # Try smart matching
        best_match, confidence, all_matches = self.smart_category_match(user_input)
        
        if not best_match:
            available_cats = [cat['category_name'] for cat in self.get_all_categories()[:5]]
            if available_cats:
                cats_list = ", ".join(f"**{cat}**" for cat in available_cats)
                return f"❌ No category found matching **{user_input}**!\n\n📂 Available categories: {cats_list}\n\nUse `!chat list` to see all categories."
            else:
                return "❌ No categories available! Create one with `!chat create <name>`"
        
        # If confidence is high, auto-subscribe
        if confidence >= 0.85:
            result = await self.subscribe_channel(guild, channel, best_match, subscribed_by)
            return f"🤖 **AI Match:** {result}"
        
        # If confidence is medium, ask for confirmation with options
        elif confidence >= 0.5:
            matches_text = []
            for i, (match_name, score) in enumerate(all_matches[:3], 1):
                confidence_emoji = "🎯" if score >= 0.8 else "✅" if score >= 0.6 else "❓"
                matches_text.append(f"{i}. {confidence_emoji} **{match_name}** ({score*100:.0f}% match)")
            
            matches_str = "\n".join(matches_text)
            return f"🤖 **AI found multiple matches for** `{user_input}`:\n\n{matches_str}\n\n💡 Use the exact name to subscribe: `!chat subscribe {best_match}`"
        
        # Low confidence, show suggestions
        else:
            if len(all_matches) >= 2:
                suggestions = [match[0] for match in all_matches[:3]]
                suggestions_text = ", ".join(f"**{cat}**" for cat in suggestions)
                return f"❌ No clear match for **{user_input}**.\n\n🤔 Did you mean: {suggestions_text}?\n\nUse `!chat list` to see all categories."
            else:
                return f"❌ No category found matching **{user_input}**!\n\nUse `!chat list` to see available categories."
    
    async def send_category_help(self, channel: discord.TextChannel):
        """Send help message about category chat system"""
        embed = discord.Embed(
            title="📂 Category Chat System",
            color=0x00ff00,
            description="Create categories and connect servers for organized cross-server communication!"
        )
        
        embed.add_field(
            name="🏷️ How it works",
            value="• Create categories for different topics (gaming, art, music, etc.)\n"
                  "• Subscribe your channels to categories you're interested in\n"
                  "• Messages are shared between all servers subscribed to the same category\n"
                  "• Use `[category]` prefix to send to specific category",
            inline=False
        )
        
        embed.add_field(
            name="📝 Message Format",
            value="`[gaming] Looking for teammates!` - Send to gaming category\n"
                  "`Hello everyone!` - Send to all subscribed categories",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Benefits",
            value="• Organized by topic\n"
                  "• Better than global chat\n"
                  "• Find like-minded communities\n"
                  "• Cross-server networking",
            inline=True
        )
        
        embed.add_field(
            name="⚙️ Commands",
            value="Use `!chat help` for full command list",
            inline=True
        )
        
        embed.set_footer(text="Category chat brings communities together! 🌍")
        
        await channel.send(embed=embed)