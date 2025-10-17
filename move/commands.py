import discord
from discord.ext import commands
from discord import app_commands

def setup_voice_commands(bot, voice_manager):
    """Setup voice management commands"""
    

    @bot.command()
    async def moveall(ctx, *, channel_name=None):
        """Move all users from current channel to target channel (requires Move Members permission)"""
        if not voice_manager:
            await ctx.send('⚠️ Voice system is still starting up. Please try again in a moment.')
            return
        await voice_manager.move_all_users_to_channel(ctx, channel_name)

    @bot.command()
    async def channels(ctx):
        """List all voice channels in the server"""
        if not voice_manager:
            await ctx.send('⚠️ Voice system is still starting up. Please try again in a moment.')
            return
        await voice_manager.list_voice_channels(ctx)

    @bot.command()
    async def vcinfo(ctx):
        """Show current voice channel information"""
        if not voice_manager:
            await ctx.send('⚠️ Voice system is still starting up. Please try again in a moment.')
            return
        await voice_manager.show_current_channel_info(ctx)

    # Slash Commands with Channel Selector
    @bot.tree.command(name="moveall", description="Move all users to a selected voice channel")
    @app_commands.describe(channel="Select the voice channel to move everyone to")
    async def moveall_slash(interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Move all users from current channel to selected voice channel with dropdown"""
        # Check if user has permissions
        if not interaction.user.guild_permissions.move_members:
            await interaction.response.send_message('❌ You need "Move Members" permission to use this command!', ephemeral=True)
            return
        
        # Get bot's current voice channel
        voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
        
        # If bot is not in a voice channel, join the user's channel first
        if not voice_client or not voice_client.channel:
            if not interaction.user.voice or not interaction.user.voice.channel:
                await interaction.response.send_message('❌ You need to be in a voice channel for me to join!', ephemeral=True)
                return
            
            await interaction.response.defer()
            
            try:
                # Join user's voice channel
                voice_client = await interaction.user.voice.channel.connect()
                current_channel = voice_client.channel
                await interaction.followup.send(f'🎯 Joined **{current_channel.name}**! Now moving everyone to **{channel.name}**...')
            except Exception as e:
                print(f"Failed to join voice channel: {e}")
                await interaction.followup.send('❌ Failed to join your voice channel!')
                return
        else:
            current_channel = voice_client.channel
            await interaction.response.defer()
        
        # Don't move to same channel
        if channel == current_channel:
            await interaction.followup.send('❌ Already in that channel!')
            return

        try:
            members_to_move = current_channel.members.copy()
            moved_count = 0
            
            for member in members_to_move:
                if member != interaction.guild.me:  # Don't move the bot itself
                    try:
                        await member.move_to(channel)
                        moved_count += 1
                    except:
                        continue  # Skip if can't move (no permission, etc.)
            
            # Move bot too
            await voice_client.move_to(channel)
            
            await interaction.followup.send(f'✅ Moved {moved_count} members and bot to **{channel.name}**!')
            
        except Exception as e:
            print(f"Slash moveall error: {e}")
            await interaction.followup.send(f'❌ Failed to move members to **{channel.name}**!')

