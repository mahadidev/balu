import discord
from discord.ext import commands
from datetime import datetime
import pytz
import sqlite3
from .groq_client import GroqClient

class TeamManager:
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db_manager = db_manager
        self.timezone = pytz.timezone('Asia/Dhaka')
        self.groq_client = None
        self.pending_registrations = {}  # Store pending team registrations
        
        # Initialize Groq client if API key is available
        try:
            self.groq_client = GroqClient()
        except ValueError:
            print("⚠️ GROQ_API_KEY not found. Team registration will use fallback parsing.")
            self.groq_client = None
    
    async def register_team(self, ctx, *, registration_data=None):
        """
        Register a team with mandatory category selection
        Supports various formats like:
        - !entry UNKNOWN PC 2 https://www.facebook.com/mrakuji/
        - !entry UNKNOWN PC 2 (uses current Discord server URL)
        - !entry (uses Discord server name as team name, prompts for category)
        """
        category_id = None
        
        # If no data provided, use server name as team name
        if not registration_data:
            team_name = ctx.guild.name
            server_link = None
        else:
            # Check if registration data contains category number (1-5)
            import re
            category_match = re.search(r'\b([1-5])\b', registration_data)
            
            if category_match:
                category_id = int(category_match.group(1))
                # Remove category number from registration data
                registration_data_cleaned = re.sub(r'\b[1-5]\b', '', registration_data).strip()
            else:
                registration_data_cleaned = registration_data
                
            # Parse the cleaned registration data using AI
            if self.groq_client:
                parsed_data = await self.groq_client.parse_team_registration(registration_data_cleaned)
            else:
                # Fallback parsing if no Groq API key
                parsed_data = self._fallback_parse(registration_data_cleaned)
            
            team_name = parsed_data.get('team_name')
            server_link = parsed_data.get('server_link')
        
        # If no category provided, use AI to detect with confidence
        if category_id is None:
            if self.groq_client and team_name:
                try:
                    ai_result = await self.groq_client.detect_challenge_category(team_name, server_link)
                    
                    # If AI is confident, auto-register with server name as team name
                    if ai_result['confidence'] == 'high':
                        category_id = ai_result['category_id']
                        team_name = ctx.guild.name  # Use server name when category is auto-detected
                    else:
                        # If AI is not confident, show interactive category selection
                        await self._show_category_selection(ctx, team_name, server_link)
                        return
                except Exception as e:
                    print(f"AI category detection failed: {e}")
                    # Show interactive category selection on AI failure
                    await self._show_category_selection(ctx, team_name, server_link)
                    return
            else:
                # No AI available - show interactive category selection
                await self._show_category_selection(ctx, team_name, server_link)
                return
        
        # If no server link provided, try to create Discord server invite
        if not server_link:
            try:
                server_link = await self._get_discord_server_invite(ctx)
            except Exception as e:
                print(f"Failed to create invite: {e}")
                # Continue without server link
        
        # Category ID is already set from user input, no need for AI detection
        
        # Check for duplicate team names (exclude current user if updating)
        if team_name:
            existing_team = self.db_manager.check_team_name_exists(
                str(ctx.guild.id), 
                team_name, 
                exclude_user_id=str(ctx.author.id)
            )
            
            if existing_team:
                # Get the existing user's display name
                try:
                    existing_user = self.bot.get_user(int(existing_team[0]))
                    existing_user_name = existing_user.display_name if existing_user else "Unknown User"
                except:
                    existing_user_name = "Unknown User"
                
                # Generate AI response for duplicate team name
                if self.groq_client:
                    ai_message = await self.groq_client.generate_duplicate_team_message(
                        team_name, ctx.guild.name, existing_user_name
                    )
                    await ctx.send(ai_message)
                else:
                    # Fallback message
                    await ctx.send(f"⚠️ Team name **{team_name}** is already taken by **{existing_user_name}** in this server!\nTry: `{team_name} 2`, `{team_name} Elite`, or be creative! 🎯")
                return
        
        # Store in database
        try:
            result = self.db_manager.register_team(
                discord_user_id=str(ctx.author.id),
                guild_id=str(ctx.guild.id),
                guild_name=ctx.guild.name,
                server_link=server_link,
                team_name=team_name,
                created_by=str(ctx.author.id),
                category_id=category_id
            )
            
            # Create response message with current Dhaka time
            dhaka_now = datetime.now(self.timezone)
            formatted_time = dhaka_now.strftime('%Y-%m-%d %I:%M %p')
            
            # Get category name
            category = self.db_manager.get_category_by_id(category_id)
            category_name = category['name'] if category else "Custom"
            
            if result == "updated":
                response = "✅ **Team registration updated!**\n"
            else:
                response = "✅ **Team registered successfully!**\n"
            
            response += f"👤 **Player:** {ctx.author.display_name}\n"
            if team_name:
                response += f"🏆 **Team:** {team_name}\n"
            response += f"🎯 **Category:** {category_name}\n"
            if server_link:
                response += f"🔗 **Server:** {server_link}\n"
            response += f"🎮 **Guild:** {ctx.guild.name}\n"
            response += f"🕐 **Time:** {formatted_time}"
            
            await ctx.send(response)
            
            # Send notifications to subscribed channels for both new and updated registrations
            if result in ["created", "updated"]:
                await self.send_global_notification({
                    'team_name': team_name,
                    'guild_name': ctx.guild.name,
                    'created_by': str(ctx.author.id),
                    'category_id': category_id
                })
            
        except Exception as e:
            print(f"Database error: {e}")
            await ctx.send('❌ Failed to register team. Please try again later.')
    
    async def show_team_info(self, ctx, user: discord.Member = None):
        """Show team registration info for a user"""
        target_user = user or ctx.author
        
        registration = self.db_manager.get_team_registration(
            str(target_user.id), 
            str(ctx.guild.id)
        )
        
        if not registration:
            if target_user == ctx.author:
                await ctx.send('❌ You haven\'t registered a team yet!\n**Usage:** `!entry <team name> <server link>`')
            else:
                await ctx.send(f'❌ {target_user.display_name} hasn\'t registered a team yet!')
            return
        
        response = f"🏆 **Team Registration Info**\n"
        response += f"👤 **Player:** {target_user.display_name}\n"
        
        if registration['team_name']:
            response += f"🎯 **Team:** {registration['team_name']}\n"
        if registration['server_link']:
            response += f"🔗 **Server:** {registration['server_link']}\n"
        
        response += f"🎮 **Guild:** {registration.get('guild_name', ctx.guild.name)}\n"
        
        # Show who created the team entry
        if registration.get('created_by'):
            try:
                creator = self.bot.get_user(int(registration['created_by']))
                creator_name = creator.display_name if creator else "Unknown User"
                response += f"👑 **Created by:** {creator_name}\n"
            except:
                response += f"👑 **Created by:** Unknown User\n"
        
        response += f"📅 **Registered:** {registration['created_at'][:10]}"
        
        await ctx.send(response)
    
    async def list_teams(self, ctx):
        """List all registered teams in the current guild"""
        teams = self.db_manager.get_all_team_registrations(str(ctx.guild.id))
        
        if not teams:
            await ctx.send('❌ No teams registered in this server yet!')
            return
        
        response = f"🏆 **Registered Teams in {ctx.guild.name}**\n\n"
        
        for i, team in enumerate(teams, 1):
            try:
                user = self.bot.get_user(int(team['discord_user_id']))
                username = user.display_name if user else "Unknown User"
            except:
                username = "Unknown User"
            
            response += f"`{i}.` **{username}**"
            if team['team_name']:
                response += f" - *{team['team_name']}*"
            response += "\n"
            
            if team['server_link']:
                response += f"   🔗 {team['server_link']}\n"
            response += "\n"
        
        # Split long messages
        if len(response) > 2000:
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(response)
    
    async def delete_team_registration(self, ctx):
        """Delete user's team registration"""
        success = self.db_manager.delete_team_registration(
            str(ctx.author.id), 
            str(ctx.guild.id)
        )
        
        if success:
            await ctx.send('✅ Your team registration has been deleted!')
        else:
            await ctx.send('❌ You don\'t have a team registration to delete!')
    
    def _fallback_parse(self, input_text: str):
        """Fallback parsing if Groq is not available"""
        import re
        
        # Extract URL
        url_pattern = r'https?://[^\s]+|(?:www\.)?(?:facebook|discord|twitter|instagram)\.(?:com|gg)/[^\s]+'
        url_match = re.search(url_pattern, input_text, re.IGNORECASE)
        server_link = url_match.group(0) if url_match else None
        
        # Extract team name (everything except the URL)
        if server_link:
            team_name = input_text.replace(server_link, '').strip()
        else:
            team_name = input_text.strip()
        
        # Clean up team name
        if team_name and len(team_name) > 0:
            team_name = ' '.join(team_name.split())
        else:
            team_name = None
            
        return {
            'team_name': team_name,
            'server_link': server_link
        }
    
    async def show_recent_players(self, ctx):
        """Show the last 10 updated teams across all servers who are ready to play"""
        try:
            recent_teams = self.db_manager.get_global_recent_teams(limit=10)
            
            if not recent_teams:
                await ctx.send('❌ No teams registered globally yet!\nUse `!entry <team name>` to register.')
                return
        except Exception as e:
            print(f"Error in show_recent_players: {e}")
            await ctx.send('❌ Error retrieving team data. Please try again later.')
            return
        
        # Create display with clickable @mentions
        response = "🌍 **Global Players Ready to Play (All Servers)**\n\n"
        
        for i, team in enumerate(recent_teams, 1):
            # Get guild name from team data
            guild_name = team.get('guild_name', 'Unknown Server')
            
            # Get creator mention
            creator_mention = "Unknown User"
            try:
                creator_id = int(team['created_by']) if team.get('created_by') else None
                if creator_id:
                    creator_mention = f"<@{creator_id}>"
            except:
                creator_mention = "Unknown User"
            
            team_name = team['team_name']
            
            # Format time (extract just time from datetime)
            try:
                time_str = team['updated_at'].split(' ')[1][:5]  # Get HH:MM
            except:
                time_str = "Unknown"
            
            response += f"**{i}.** 🏆 **{team_name}**\n"
            response += f"   🌐 Server: {guild_name}\n"
            response += f"   👑 Created by: {creator_mention}\n"
            response += f"   🕐 Last Active: {time_str}\n"
            if team.get('server_link'):
                response += f"   🔗 Link: {team['server_link']}\n"
            response += "\n"
        response += f"🌐 **Total Global Teams:** {len(recent_teams)}\n"
        response += f"📍 **Current Server:** {ctx.guild.name}\n"
        response += f"🔗 Use `!teaminfo @player` to see team details\n"
        response += f"⚡ Use `!entry` to join the global competition!"
        
        await ctx.send(response)
    
    async def subscribe_to_updates(self, ctx, *, category_input=None):
        """Subscribe this channel to receive team registration notifications for specific category or all categories"""
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send('❌ You need "Manage Channels" permission to subscribe to updates!')
            return
        
        category_id = None
        category_name = "All Categories"
        
        # Parse category input if provided
        if category_input:
            # Use manual mapping first for reliability
            category_map = {
                'cs limited': 1, 'clash squad limited': 1, 'limited': 1,
                'cs unlimited': 2, 'clash squad unlimited': 2, 'unlimited': 2,
                'cs quantra': 3, 'clash squad quantra': 3, 'quantra': 3,
                'full map': 4, 'br': 4, 'battle royale': 4,
                'custom': 5
            }
            category_id = category_map.get(category_input.lower())
            
            if category_id:
                # Manual mapping found
                category = self.db_manager.get_category_by_id(category_id)
                category_name = category['name'] if category else f"Category {category_id}"
            elif self.groq_client:
                # Fallback to AI for unknown inputs
                try:
                    ai_result = await self.groq_client.detect_challenge_category(category_input)
                    if ai_result['confidence'] == 'high':
                        category_id = ai_result['category_id']
                        category = self.db_manager.get_category_by_id(category_id)
                        category_name = category['name'] if category else f"Category {category_id}"
                    else:
                        await ctx.send(f'❌ Could not identify category from "{category_input}". Try: "cs limited", "cs unlimited", "quantra", "full map", or "custom"')
                        return
                except Exception as e:
                    print(f"AI category detection failed: {e}")
                    await ctx.send(f'❌ Could not identify category from "{category_input}". Try: "cs limited", "cs unlimited", "quantra", "full map", or "custom"')
                    return
            else:
                # No AI available and manual mapping failed
                await ctx.send(f'❌ Unknown category "{category_input}". Try: "cs limited", "cs unlimited", "quantra", "full map", or "custom"')
                return
        
        result = self.db_manager.subscribe_to_notifications(str(ctx.guild.id), str(ctx.channel.id), category_id)
        
        if result == True:
            # New subscription
            if category_id is None:
                await ctx.send(f'✅ **Subscribed to All Global Team Updates!**\n'
                              f'📂 **Category:** {category_name}\n'
                              f'This channel will now receive notifications for all team registrations.\n'
                              f'Previous specific category subscriptions have been replaced.\n'
                              f'Use `!unsubscribe` to unsubscribe.')
            else:
                await ctx.send(f'✅ **Subscribed to Global Team Updates!**\n'
                              f'📂 **Category:** {category_name}\n'
                              f'This channel will now receive notifications when new teams register in this category.\n'
                              f'💡 **Tip:** You can subscribe to multiple specific categories!\n'
                              f'Use `!unsubscribe` to unsubscribe from all categories or `!unsubscribe {category_input}` for this specific category.')
        elif result == "refreshed":
            # Refreshed existing subscription
            await ctx.send(f'🔄 **Subscription Refreshed!**\n'
                          f'📂 **Category:** {category_name}\n'
                          f'Your subscription has been updated with the latest timestamp.')
        elif result == False:
            # Blocked because already subscribed to all categories
            await ctx.send(f'⚠️ This channel is already subscribed to **All Categories**!\n'
                          f'You already receive **{category_name}** notifications.\n'
                          f'Use `!unsubscribe` to manage subscriptions.')
        else:
            # Fallback error message
            await ctx.send(f'❌ Failed to subscribe to **{category_name}** updates.')
    
    async def show_subscriptions(self, ctx):
        """Show current subscription status for this channel"""
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send('❌ You need "Manage Channels" permission to view subscriptions!')
            return
        
        subscriptions = self.db_manager.get_channel_subscriptions(str(ctx.guild.id), str(ctx.channel.id))
        
        if not subscriptions:
            await ctx.send('📭 **No Subscriptions**\nThis channel is not subscribed to any team registration notifications.\n'
                          'Use `!subscribe` for all categories or `!subscribe [category]` for specific categories.')
            return
        
        response = '📋 **Current Subscriptions:**\n'
        
        if None in subscriptions:
            response += '🌍 **All Categories** - Receiving all team registration notifications\n'
        else:
            response += '📂 **Specific Categories:**\n'
            for category_id in subscriptions:
                if category_id is not None:
                    category = self.db_manager.get_category_by_id(category_id)
                    category_name = category['name'] if category else f"Category {category_id}"
                    response += f'  • **{category_name}**\n'
        
        response += '\n💡 Use `!subscribe [category]` to add more categories or `!unsubscribe` to manage subscriptions.'
        await ctx.send(response)
    
    async def unsubscribe_from_updates(self, ctx, *, category_input=None):
        """Unsubscribe this channel from team registration notifications for specific category or all categories"""
        if not ctx.author.guild_permissions.manage_channels:
            await ctx.send('❌ You need "Manage Channels" permission to manage update subscriptions!')
            return
        
        category_id = None
        category_name = "All Categories"
        
        # Parse category input if provided
        if category_input:
            # Use manual mapping first for reliability
            category_map = {
                'cs limited': 1, 'clash squad limited': 1, 'limited': 1,
                'cs unlimited': 2, 'clash squad unlimited': 2, 'unlimited': 2,
                'cs quantra': 3, 'clash squad quantra': 3, 'quantra': 3,
                'full map': 4, 'br': 4, 'battle royale': 4,
                'custom': 5
            }
            category_id = category_map.get(category_input.lower())
            
            if category_id:
                # Manual mapping found
                category = self.db_manager.get_category_by_id(category_id)
                category_name = category['name'] if category else f"Category {category_id}"
            elif self.groq_client:
                # Fallback to AI for unknown inputs
                try:
                    ai_result = await self.groq_client.detect_challenge_category(category_input)
                    if ai_result['confidence'] == 'high':
                        category_id = ai_result['category_id']
                        category = self.db_manager.get_category_by_id(category_id)
                        category_name = category['name'] if category else f"Category {category_id}"
                    else:
                        await ctx.send(f'❌ Could not identify category from "{category_input}". Try: "cs limited", "cs unlimited", "quantra", "full map", or "custom"')
                        return
                except Exception as e:
                    print(f"AI category detection failed: {e}")
                    await ctx.send(f'❌ Could not identify category from "{category_input}". Try: "cs limited", "cs unlimited", "quantra", "full map", or "custom"')
                    return
            else:
                # No AI available and manual mapping failed
                await ctx.send(f'❌ Unknown category "{category_input}". Try: "cs limited", "cs unlimited", "quantra", "full map", or "custom"')
                return
        
        success = self.db_manager.unsubscribe_from_notifications(str(ctx.guild.id), str(ctx.channel.id), category_id)
        
        if success:
            await ctx.send(f'✅ **Unsubscribed from Global Team Updates!**\n'
                          f'📂 **Category:** {category_name}\n'
                          f'This channel will no longer receive notifications for this category.')
        else:
            if category_input:
                await ctx.send(f'❌ This channel is not subscribed to **{category_name}** updates.')
            else:
                await ctx.send('❌ This channel is not subscribed to any global team updates.')
    
    async def send_global_notification(self, new_team_info):
        """Send notification with latest 5 players list to all subscribed channels"""
        try:
            # Get category from new team info
            category_id = new_team_info.get('category_id')
            category = self.db_manager.get_category_by_id(category_id) if category_id else None
            category_name = category['name'] if category else "Custom"
            
            # Get subscribers for this specific category (includes those subscribed to all categories)
            subscribers = self.db_manager.get_notification_subscribers(category_id)
            
            # Get latest 5 teams
            recent_teams = self.db_manager.get_global_recent_teams(limit=5)
            
            # Create notification message header
            team_name = new_team_info.get('team_name', 'Unknown Team')
            guild_name = new_team_info.get('guild_name', 'Unknown Server')
            creator_id = new_team_info.get('created_by')
            creator_mention = f"<@{creator_id}>" if creator_id else "Unknown User"
            
            notification_msg = f"🚨 **New Team Registered!**\n"
            notification_msg += f"🏆 **{team_name}** from **{guild_name}** by {creator_mention}\n"
            notification_msg += f"📂 **Category:** {category_name}\n\n"
            
            # Add latest 5 players table
            notification_msg += f"🌍 **Latest 5 Global Teams:**\n"
            notification_msg += "```\n"
            notification_msg += "Team Name           Guild           Created By      Last Active\n"
            notification_msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            for i, team in enumerate(recent_teams[:5], 1):
                # Get guild name from team data
                guild_name_list = team.get('guild_name', 'Unknown Server')
                guild_name_list = guild_name_list[:12] if len(guild_name_list) > 12 else guild_name_list
                
                # Get creator mention for table
                creator_mention = "Unknown"
                try:
                    creator_id_list = int(team['created_by']) if team.get('created_by') else None
                    if creator_id_list:
                        creator_mention = f"<@{creator_id_list}>"
                except:
                    creator_mention = "Unknown"
                
                team_name_list = team['team_name'][:15] if len(team['team_name']) > 15 else team['team_name']
                
                # Format time
                try:
                    time_str = team['updated_at'].split(' ')[1][:5]  # Get HH:MM
                except:
                    time_str = "Unknown"
                
                notification_msg += f"{team_name_list:<18} {guild_name_list:<14} {creator_mention:<12} {time_str}\n"
            
            notification_msg += "```\n"
            notification_msg += f"💡 Use `!players` to see all global teams!"
            
            # Send to all subscribed channels
            for subscriber in subscribers:
                guild_id = subscriber[0]
                channel_id = subscriber[1]
                try:
                    guild = self.bot.get_guild(int(guild_id))
                    if guild:
                        channel = guild.get_channel(int(channel_id))
                        if channel:
                            await channel.send(notification_msg)
                except Exception as e:
                    print(f"Failed to send notification to {guild_id}/{channel_id}: {e}")
                    
        except Exception as e:
            print(f"Error sending global notifications: {e}")
    
    async def _get_discord_server_invite(self, ctx):
        """
        Create or get an invite link for the current Discord server
        """
        guild = ctx.guild
        
        # Try to find an existing permanent invite first
        try:
            invites = await guild.invites()
            for invite in invites:
                if invite.max_age == 0:  # Permanent invite
                    return f"https://discord.gg/{invite.code}"
        except discord.Forbidden:
            pass
        
        # Try to create a new invite
        try:
            # Find a suitable channel to create invite from
            channel = None
            
            # Prefer text channels over voice channels
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).create_instant_invite:
                    channel = ch
                    break
            
            # If no text channel available, try voice channels
            if not channel:
                for ch in guild.voice_channels:
                    if ch.permissions_for(guild.me).create_instant_invite:
                        channel = ch
                        break
            
            # If still no channel, try the system channel
            if not channel and guild.system_channel:
                if guild.system_channel.permissions_for(guild.me).create_instant_invite:
                    channel = guild.system_channel
            
            if channel:
                # Create a permanent invite (max_age=0) that doesn't expire
                invite = await channel.create_invite(
                    max_age=0,      # Never expires
                    max_uses=0,     # Unlimited uses
                    unique=False,   # Don't create if similar invite exists
                    reason="Team registration auto-invite"
                )
                return f"https://discord.gg/{invite.code}"
        
        except discord.Forbidden:
            # Bot doesn't have permission to create invites
            pass
        except Exception as e:
            print(f"Error creating invite: {e}")
        
        # Fallback: return a generic Discord server link (won't work but shows intent)
        return f"Discord Server: {guild.name} (ID: {guild.id})"
    
    async def _show_category_selection(self, ctx, team_name, server_link):
        """Show interactive category selection with reactions"""
        # Store pending registration data
        user_id = ctx.author.id
        self.pending_registrations[user_id] = {
            'team_name': team_name,
            'server_link': server_link,
            'guild_id': str(ctx.guild.id),
            'guild_name': ctx.guild.name,
            'created_by': str(ctx.author.id)
        }
        
        # Create category selection message
        embed = discord.Embed(
            title="🎯 Select Category for Your Team",
            description=f"**Team Name:** {team_name}\n\nChoose the category that best fits your team:",
            color=0x00ff00
        )
        
        categories = self.db_manager.get_challenge_categories()
        category_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        
        for i, category in enumerate(categories):
            embed.add_field(
                name=f"{category_emojis[i]} {category['name']}",
                value=category['description'],
                inline=False
            )
        
        embed.set_footer(text="Click on a reaction below to select your category")
        
        # Send message and add reactions
        message = await ctx.send(embed=embed)
        
        # Add reaction emojis
        for i in range(len(categories)):
            await message.add_reaction(category_emojis[i])
        
        # Store message ID for reaction handling
        self.pending_registrations[user_id]['message_id'] = message.id
        self.pending_registrations[user_id]['channel_id'] = ctx.channel.id
    
    async def handle_category_selection(self, payload):
        """Handle reaction-based category selection"""
        user_id = payload.user_id
        
        # Check if this is a pending registration
        if user_id not in self.pending_registrations:
            return
        
        pending = self.pending_registrations[user_id]
        
        # Check if this is the right message
        if payload.message_id != pending['message_id']:
            return
        
        # Check if reaction is valid category emoji
        category_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        if str(payload.emoji) not in category_emojis:
            return
        
        # Get category ID from emoji
        category_id = category_emojis.index(str(payload.emoji)) + 1
        
        # Get the channel and user
        channel = self.bot.get_channel(payload.channel_id)
        user = self.bot.get_user(user_id)
        
        if not channel or not user:
            return
        
        try:
            # Create fake context for registration
            class FakeContext:
                def __init__(self, channel, user, guild):
                    self.channel = channel
                    self.author = user
                    self.guild = guild
                    self.send = channel.send
            
            guild = self.bot.get_guild(int(pending['guild_id']))
            fake_ctx = FakeContext(channel, user, guild)
            
            # Complete the registration
            await self._complete_registration(
                fake_ctx,
                pending['team_name'],
                pending['server_link'],
                category_id,
                pending['guild_name'],
                pending['created_by']
            )
            
            # Clean up pending registration
            del self.pending_registrations[user_id]
            
            # Try to delete the selection message
            try:
                message = await channel.fetch_message(pending['message_id'])
                await message.delete()
            except:
                pass
                
        except Exception as e:
            print(f"Error completing registration: {e}")
            await channel.send(f"❌ Error completing registration. Please try again with `!entry {pending['team_name']} [category number]`")
    
    async def _complete_registration(self, ctx, team_name, server_link, category_id, guild_name, created_by):
        """Complete the team registration with all required data"""
        # If no server link provided, try to create Discord server invite
        if not server_link:
            try:
                server_link = await self._get_discord_server_invite(ctx)
            except Exception as e:
                print(f"Failed to create invite: {e}")
                # Continue without server link
        
        # Check for duplicate team names (exclude current user if updating)
        if team_name:
            existing_team = self.db_manager.check_team_name_exists(
                str(ctx.guild.id), 
                team_name, 
                exclude_user_id=str(ctx.author.id)
            )
            
            if existing_team:
                # Get the existing user's display name
                try:
                    existing_user = self.bot.get_user(int(existing_team[0]))
                    existing_user_name = existing_user.display_name if existing_user else "Unknown User"
                except:
                    existing_user_name = "Unknown User"
                
                # Generate AI response for duplicate team name
                if self.groq_client:
                    ai_message = await self.groq_client.generate_duplicate_team_message(
                        team_name, ctx.guild.name, existing_user_name
                    )
                    await ctx.send(ai_message)
                else:
                    # Fallback message
                    await ctx.send(f"⚠️ Team name **{team_name}** is already taken by **{existing_user_name}** in this server!\nTry: `{team_name} 2`, `{team_name} Elite`, or be creative! 🎯")
                return
        
        # Store in database
        try:
            result = self.db_manager.register_team(
                discord_user_id=str(ctx.author.id),
                guild_id=str(ctx.guild.id),
                guild_name=guild_name,
                server_link=server_link,
                team_name=team_name,
                created_by=created_by,
                category_id=category_id
            )
            
            # Create response message with current Dhaka time
            dhaka_now = datetime.now(self.timezone)
            formatted_time = dhaka_now.strftime('%Y-%m-%d %I:%M %p')
            
            # Get category name
            category = self.db_manager.get_category_by_id(category_id)
            category_name = category['name'] if category else "Custom"
            
            if result == "updated":
                response = "✅ **Team registration updated!**\n"
            else:
                response = "✅ **Team registered successfully!**\n"
            
            response += f"👤 **Player:** {ctx.author.display_name}\n"
            if team_name:
                response += f"🏆 **Team:** {team_name}\n"
            response += f"🎯 **Category:** {category_name}\n"
            if server_link:
                response += f"🔗 **Server:** {server_link}\n"
            response += f"🎮 **Guild:** {guild_name}\n"
            response += f"🕐 **Time:** {formatted_time}"
            
            await ctx.send(response)
            
            # Send notifications to subscribed channels for both new and updated registrations
            if result in ["created", "updated"]:
                await self.send_global_notification({
                    'team_name': team_name,
                    'guild_name': guild_name,
                    'created_by': created_by,
                    'category_id': selected_category_id
                })
            
        except Exception as e:
            print(f"Database error: {e}")
            await ctx.send('❌ Failed to register team. Please try again later.')