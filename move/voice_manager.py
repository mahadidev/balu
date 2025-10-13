import discord
from discord.ext import commands

class VoiceManager:
    def __init__(self, bot):
        self.bot = bot

    async def move_bot_to_channel(self, ctx, channel_name=None):
        """Move bot to a specific voice channel"""
        guild = ctx.guild
        
        # If no channel name provided, move to user's current channel
        if not channel_name:
            if ctx.author.voice and ctx.author.voice.channel:
                target_channel = ctx.author.voice.channel
                await ctx.send(f'🎯 Moving to your current channel: **{target_channel.name}**')
            else:
                await ctx.send('❌ You need to be in a voice channel or specify a channel name!')
                return
        else:
            # Find the channel by name
            target_channel = None
            for channel in guild.voice_channels:
                if channel.name.lower() == channel_name.lower():
                    target_channel = channel
                    break
            
            if not target_channel:
                # Show available voice channels
                voice_channels = [vc.name for vc in guild.voice_channels]
                await ctx.send(f'❌ Channel "{channel_name}" not found!\n**Available voice channels:** {", ".join(voice_channels)}')
                return

        # Move the bot
        try:
            # Check if bot is currently in a voice channel
            voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
            
            if voice_client:
                await voice_client.move_to(target_channel)
                await ctx.send(f'✅ Moved to **{target_channel.name}**!')
            else:
                # Bot not in voice, join the target channel
                await target_channel.connect()
                await ctx.send(f'✅ Joined **{target_channel.name}**!')
                
        except Exception as e:
            print(f"Move error: {e}")
            await ctx.send(f'❌ Failed to move to **{target_channel.name}**!')

    async def move_all_users_to_channel(self, ctx, channel_name=None):
        """Move all users from bot's current channel to target channel"""
        guild = ctx.guild
        
        # Check if user has permissions
        if not ctx.author.guild_permissions.move_members:
            await ctx.send('❌ You need "Move Members" permission to use this command!')
            return
        
        # Get bot's current voice channel
        voice_client = discord.utils.get(self.bot.voice_clients, guild=guild)
        if not voice_client or not voice_client.channel:
            await ctx.send('❌ Bot is not in a voice channel!')
            return
        
        current_channel = voice_client.channel
        
        # If no channel name provided, show selection menu
        if not channel_name:
            voice_channels = [vc for vc in guild.voice_channels if vc != current_channel]
            
            if not voice_channels:
                await ctx.send('❌ No other voice channels available to move to!')
                return
            
            # Create numbered list
            channel_list = f"🔊 **Select a voice channel to move everyone to:**\n"
            channel_list += f"*Currently in: **{current_channel.name}** ({len(current_channel.members)} members)*\n\n"
            
            for i, channel in enumerate(voice_channels, 1):
                member_count = len(channel.members)
                member_info = f" ({member_count} members)" if member_count > 0 else " (empty)"
                channel_list += f"`{i}.` **{channel.name}**{member_info}\n"
            
            channel_list += f"\n💡 **Usage:** `!moveall <channel_name>` or `!moveall <number>`"
            
            await ctx.send(channel_list)
            return
        
        # Check if input is a number (for selection from list)
        target_channel = None
        if channel_name.isdigit():
            channel_num = int(channel_name)
            voice_channels = [vc for vc in guild.voice_channels if vc != current_channel]
            
            if 1 <= channel_num <= len(voice_channels):
                target_channel = voice_channels[channel_num - 1]
            else:
                await ctx.send(f'❌ Invalid number! Please choose between 1 and {len(voice_channels)}')
                return
        else:
            # Find target channel by name
            for channel in guild.voice_channels:
                if channel.name.lower() == channel_name.lower():
                    target_channel = channel
                    break
        
        if not target_channel:
            voice_channels = [vc.name for vc in guild.voice_channels if vc != current_channel]
            await ctx.send(f'❌ Channel "{channel_name}" not found!\n**Available voice channels:** {", ".join(voice_channels)}')
            return

        # Don't move to same channel
        if target_channel == current_channel:
            await ctx.send('❌ Already in that channel!')
            return

        # Move all members
        try:
            members_to_move = current_channel.members.copy()
            moved_count = 0
            
            for member in members_to_move:
                if member != guild.me:  # Don't move the bot itself
                    try:
                        await member.move_to(target_channel)
                        moved_count += 1
                    except:
                        continue  # Skip if can't move (no permission, etc.)
            
            # Move bot too
            await voice_client.move_to(target_channel)
            
            await ctx.send(f'✅ Moved {moved_count} members and bot to **{target_channel.name}**!')
            
        except Exception as e:
            print(f"Move all error: {e}")
            await ctx.send(f'❌ Failed to move members to **{target_channel.name}**!')

    async def list_voice_channels(self, ctx):
        """List all voice channels in the server"""
        voice_channels = ctx.guild.voice_channels
        
        if not voice_channels:
            await ctx.send('❌ No voice channels found in this server!')
            return
        
        channel_list = "🔊 **Voice Channels:**\n"
        for i, channel in enumerate(voice_channels, 1):
            member_count = len(channel.members)
            member_info = f" ({member_count} members)" if member_count > 0 else " (empty)"
            channel_list += f"{i}. **{channel.name}**{member_info}\n"
        
        await ctx.send(channel_list)

    async def show_current_channel_info(self, ctx):
        """Show information about bot's current voice channel"""
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        
        if not voice_client or not voice_client.channel:
            await ctx.send('❌ Bot is not in a voice channel!')
            return
        
        current_channel = voice_client.channel
        members = current_channel.members
        
        info = f"🎵 **Current Voice Channel:** {current_channel.name}\n"
        info += f"👥 **Members ({len(members)}):**\n"
        
        for member in members:
            status = "🎵 (Bot)" if member.bot else "👤"
            info += f"{status} {member.display_name}\n"
        
        await ctx.send(info)