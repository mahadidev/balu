import discord
from discord.ext import commands
from discord import app_commands

def setup_music_commands(bot, music_player):
    """Setup music-related commands"""
    
    @bot.command()
    async def play(ctx, *, query):
        """Play music from YouTube"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
            
        if not query:
            await ctx.send('❌ Please provide a song name or YouTube URL!')
            return
        
        await music_player.play(ctx, query)

    @bot.command()
    async def skip(ctx):
        """Skip current song"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
        await music_player.skip(ctx)

    @bot.command()
    async def stop(ctx):
        """Stop music and clear queue"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
        await music_player.stop(ctx)

    @bot.command()
    async def pause(ctx):
        """Pause music"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
        await music_player.pause(ctx)

    @bot.command()
    async def resume(ctx):
        """Resume music"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
        await music_player.resume(ctx)

    @bot.command()
    async def queue(ctx):
        """Show current queue"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
        await music_player.show_queue(ctx)

    @bot.command()
    async def volume(ctx, vol: int):
        """Set volume (0-100)"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
        await music_player.set_volume(ctx, vol)

    @bot.command()
    async def leave(ctx):
        """Leave voice channel"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
        await music_player.leave(ctx)

    @bot.command()
    async def join(ctx):
        """Join voice channel"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
        await music_player.join(ctx)

    @bot.command()
    async def playlist(ctx, *, query):
        """Force load entire playlist from YouTube"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
            
        if not query:
            await ctx.send('❌ Please provide a playlist URL!')
            return
        
        await music_player.add_playlist(ctx, query)

    @bot.tree.command(name="play", description="Play music from YouTube")
    @app_commands.describe(query="Enter the song name, artist, or YouTube URL")
    async def play_slash(interaction: discord.Interaction, query: str):
        """Play music with slash command and text input field"""
        if not music_player:
            await interaction.response.send_message('⚠️ Music system is still starting up. Please try again in a moment.', ephemeral=True)
            return
            
        if not query:
            await interaction.response.send_message('❌ Please provide a song name or YouTube URL!', ephemeral=True)
            return
        
        # Defer the interaction immediately to prevent timeout
        await interaction.response.defer()
        
        # Convert interaction to context-like object for compatibility with existing music_player
        class SlashContext:
            def __init__(self, interaction):
                self.interaction = interaction
                self.author = interaction.user
                self.guild = interaction.guild
                self.channel = interaction.channel
                self.voice_client = discord.utils.get(interaction.client.voice_clients, guild=interaction.guild)
                self._responded = True  # Already deferred
                self._last_message = None
            
            async def send(self, content=None, **kwargs):
                try:
                    # Always use followup since we already deferred
                    msg = await self.interaction.followup.send(content, **kwargs)
                    self._last_message = msg
                    return msg
                except discord.errors.NotFound:
                    # Interaction has expired, ignore silently
                    pass
                except Exception as e:
                    print(f"Error sending slash command response: {e}")
                    return None
        
        ctx = SlashContext(interaction)
        await music_player.play(ctx, query)

    @bot.tree.command(name="nowplaying", description="Show the current music player interface")
    async def nowplaying_slash(interaction: discord.Interaction):
        """Show current music player interface with controls"""
        if not music_player:
            await interaction.response.send_message('⚠️ Music system is still starting up. Please try again in a moment.', ephemeral=True)
            return
        
        guild_id = interaction.guild.id
        
        # Check if music is playing
        voice_client = music_player.voice_clients.get(guild_id)
        if not voice_client or not voice_client.is_connected():
            await interaction.response.send_message('❌ Not connected to a voice channel!', ephemeral=True)
            return
        
        current_song = music_player.current_songs.get(guild_id)
        if not current_song:
            await interaction.response.send_message('❌ No music is currently playing!', ephemeral=True)
            return
        
        # Create enhanced interface
        embed, view = await music_player.create_music_interface(
            type('Context', (), {'guild': interaction.guild, 'author': interaction.user})(),
            current_song,
            is_playing=voice_client.is_playing()
        )
        
        await interaction.response.send_message(embed=embed, view=view)

    @bot.command()
    async def repeat(ctx, mode=None):
        """Set repeat mode: off, track, queue"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
        
        guild_id = ctx.guild.id
        
        if mode is None:
            # Cycle through modes
            new_mode = music_player.cycle_repeat_mode(guild_id)
        else:
            mode = mode.lower()
            if mode in ['off', '0']:
                music_player.repeat_modes[guild_id] = 0
                new_mode = 0
            elif mode in ['track', 'song', '1']:
                music_player.repeat_modes[guild_id] = 1
                new_mode = 1
            elif mode in ['queue', 'all', '2']:
                music_player.repeat_modes[guild_id] = 2
                new_mode = 2
            else:
                await ctx.send('❌ Invalid repeat mode! Use: `off`, `track`, or `queue`')
                return
        
        repeat_text = music_player.get_repeat_text(guild_id)
        await ctx.send(f'🔁 {repeat_text}')