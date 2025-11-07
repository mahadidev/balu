import discord
from discord.ext import commands
from discord import app_commands

def setup_music_commands(bot, music_player):
    """Setup music-related commands"""
    
    @bot.command()
    async def play(ctx, *, query):
        """Play music from YouTube. Use --related to add similar songs to queue"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
            
        if not query:
            await ctx.send('❌ Please provide a song name or YouTube URL!')
            return
        
        # Check for --related flag
        related = False
        if '--related' in query:
            related = True
            query = query.replace('--related', '').strip()
        
        await music_player.play(ctx, query, related=related)

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
        await music_player.change_volume(ctx, vol)

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

    @bot.tree.command(name="play", description="Play music from YouTube. Add --related for similar songs")
    @app_commands.describe(query="Enter the song name, artist, or YouTube URL. Add --related for playlist mix")
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
        
        # Check for --related flag
        related = False
        if '--related' in query:
            related = True
            query = query.replace('--related', '').strip()
        
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
        await music_player.play(ctx, query, related=related)



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

    @bot.command()
    async def shuffle(ctx):
        """Toggle shuffle mode"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
        
        guild_id = ctx.guild.id
        new_mode = music_player.toggle_shuffle_mode(guild_id)
        shuffle_text = music_player.get_shuffle_text(guild_id)
        
        if new_mode:
            queue_count = len(music_player.queues.get(guild_id, []))
            if queue_count > 0:
                await ctx.send(f'🔀 {shuffle_text} - Shuffled {queue_count} songs!')
            else:
                await ctx.send(f'🔀 {shuffle_text} - Next songs will be shuffled!')
        else:
            await ctx.send(f'🔀 {shuffle_text}')

    @bot.command()
    async def testui(ctx):
        """Test music interface"""
        if not music_player:
            await ctx.send('⚠️ Music system is still starting up. Please try again in a moment.')
            return
        
        # Create test song info
        test_song = {
            'title': 'Test Song',
            'author': 'Test Artist',
            'duration': '3:30',
            'duration_seconds': 210,
            'thumbnail': None,
            'webpage_url': 'https://example.com',
            'requested_by': str(ctx.author.id)
        }
        
        try:
            embed, view = await music_player.create_music_interface(ctx, test_song, is_playing=True)
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            await ctx.send(f'❌ Interface test failed: {e}')
            import traceback
            traceback.print_exc()