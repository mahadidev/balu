import discord
import asyncio
import yt_dlp
from discord import FFmpegPCMAudio, FFmpegOpusAudio

class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.queues = {}
        self.current_songs = {}
        
        # yt-dlp options
        self.ytdl_format_options = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': False,  # Allow playlists
            'nocheckcertificate': True,
            'ignoreerrors': True,  # Skip problematic videos
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'extract_flat': False,  # Get full info for playlist items
            'retries': 3,  # Retry failed extractions
            'fragment_retries': 3,  # Retry failed fragments
        }
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_format_options)

    async def join(self, ctx):
        """Join voice channel"""
        if ctx.author.voice is None:
            await ctx.send('❌ You need to be in a voice channel!')
            return False
            
        channel = ctx.author.voice.channel
        
        if ctx.guild.id in self.voice_clients:
            await self.voice_clients[ctx.guild.id].move_to(channel)
        else:
            self.voice_clients[ctx.guild.id] = await channel.connect()
            
        await ctx.send(f'🎵 Joined **{channel.name}**')
        return True

    async def leave(self, ctx):
        """Leave voice channel"""
        if ctx.guild.id in self.voice_clients:
            await self.voice_clients[ctx.guild.id].disconnect()
            del self.voice_clients[ctx.guild.id]
            
            # Clear queue and current song
            if ctx.guild.id in self.queues:
                del self.queues[ctx.guild.id]
            if ctx.guild.id in self.current_songs:
                del self.current_songs[ctx.guild.id]
                
            await ctx.send('👋 Left voice channel!')
        else:
            await ctx.send('❌ Not connected to a voice channel!')

    def get_youtube_url(self, search):
        """Extract YouTube URL from search query"""
        try:
            if 'youtube.com' in search or 'youtu.be' in search:
                return search
            else:
                # Search for the song
                info = self.ytdl.extract_info(f"ytsearch:{search}", download=False)
                if info['entries']:
                    return info['entries'][0]['webpage_url']
                return None
        except Exception as e:
            print(f"Search error: {e}")
            return None

    async def play(self, ctx, query):
        """Play music"""
        # Join voice channel if not connected
        if ctx.guild.id not in self.voice_clients:
            if not await self.join(ctx):
                return

        voice_client = self.voice_clients[ctx.guild.id]
        
        try:
            # Check if it's a playlist URL (more specific detection)
            if ('playlist?list=' in query or '&list=' in query) and 'watch?v=' not in query:
                await self.add_playlist(ctx, query)
            else:
                await self.add_single_song(ctx, query)

        except Exception as e:
            print(f"Play error: {e}")
            await ctx.send('❌ An error occurred while trying to play the song!')

    async def add_single_song(self, ctx, query):
        """Add a single song to queue"""
        # Get YouTube URL
        url = self.get_youtube_url(query)
        if not url:
            await ctx.send('❌ Could not find the song!')
            return

        # Extract song info
        info = self.ytdl.extract_info(url, download=False)
        
        # Handle single video
        if 'entries' not in info:
            song_info = self.extract_song_info(info, ctx.author.name)
            self.add_to_queue(ctx.guild.id, song_info)
            
            voice_client = self.voice_clients[ctx.guild.id]
            if voice_client.is_playing():
                await ctx.send(f'➕ **Added to queue:** {song_info["title"]} - `{song_info["duration"]}`')
            else:
                await self.play_next(ctx)

    async def add_playlist(self, ctx, playlist_url):
        """Add playlist to queue"""
        await ctx.send('🔄 Getting first song from playlist...')
        
        try:
            # Use extract_flat for faster playlist processing
            playlist_opts = self.ytdl_format_options.copy()
            playlist_opts['extract_flat'] = True
            playlist_opts['ignoreerrors'] = True
            
            playlist_ytdl = yt_dlp.YoutubeDL(playlist_opts)
            info = playlist_ytdl.extract_info(playlist_url, download=False)
            
            if 'entries' in info and info['entries']:
                entries = [entry for entry in info['entries'] if entry][:10]  # Only first 10
                
                if not entries:
                    await ctx.send('❌ Could not find any songs in the playlist!')
                    return
                
                await ctx.send(f'📋 Found {len(entries)} songs. Starting first song, loading others...')
                
                # Process FIRST song immediately
                first_entry = entries[0]
                try:
                    video_url = first_entry.get('url') or f"https://www.youtube.com/watch?v={first_entry.get('id')}"
                    detailed_info = self.ytdl.extract_info(video_url, download=False)
                    song_info = self.extract_song_info(detailed_info, ctx.author.name)
                    self.add_to_queue(ctx.guild.id, song_info)
                    
                    # Start playing immediately
                    voice_client = self.voice_clients[ctx.guild.id]
                    if not voice_client.is_playing():
                        await self.play_next(ctx)
                    
                    await ctx.send(f'🎵 **Started playing:** {song_info["title"]}')
                    
                except Exception as e:
                    print(f"Error with first song: {e}")
                    await ctx.send('❌ Error with first song, trying next...')
                
                # Process remaining songs in background (non-blocking)
                if len(entries) > 1:
                    asyncio.create_task(self.load_remaining_songs(ctx, entries[1:], info.get("title", "Unknown Playlist")))
                
            else:
                await ctx.send('❌ Could not find any songs in the playlist!')
                
        except Exception as e:
            print(f"Playlist error: {e}")
            await ctx.send(f'❌ Error processing playlist: {str(e)[:100]}...')

    async def load_remaining_songs(self, ctx, entries, playlist_title):
        """Load remaining songs in background"""
        added_count = 1  # First song already added
        total_songs = len(entries) + 1
        
        await ctx.send(f'⏳ Loading remaining {len(entries)} songs in background...')
        
        for i, entry in enumerate(entries):
            try:
                video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                detailed_info = self.ytdl.extract_info(video_url, download=False)
                song_info = self.extract_song_info(detailed_info, ctx.author.name)
                self.add_to_queue(ctx.guild.id, song_info)
                added_count += 1
                
                # Update progress every 3 songs
                if (i + 2) % 3 == 0:  # +2 because we start from index 0 but already have 1 song
                    await ctx.send(f'⏳ Loaded {added_count}/{total_songs} songs...')
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Skipping song due to error: {e}")
                continue
        
        await ctx.send(f'✅ **Finished loading {added_count} songs from:** {playlist_title}')

    def extract_song_info(self, entry, requested_by):
        """Extract song information from yt-dlp entry"""
        title = entry.get('title', 'Unknown Title')
        url = entry.get('url', entry.get('webpage_url', ''))
        duration = entry.get('duration', 0)
        
        # Format duration
        duration_str = f"{duration//60}:{duration%60:02d}" if duration else "Unknown"
        
        return {
            'title': title,
            'url': url,
            'duration': duration_str,
            'requested_by': requested_by
        }

    def add_to_queue(self, guild_id, song_info):
        """Add song to guild queue"""
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        self.queues[guild_id].append(song_info)

    async def play_next(self, ctx):
        """Play next song in queue"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.queues or not self.queues[guild_id]:
            await ctx.send('📄 Queue is empty!')
            return

        voice_client = self.voice_clients.get(guild_id)
        if not voice_client:
            return

        song_info = self.queues[guild_id].pop(0)
        self.current_songs[guild_id] = song_info

        try:
            source = FFmpegPCMAudio(song_info['url'], **self.ffmpeg_options)
            voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.song_finished(ctx), self.bot.loop
            ))

            await ctx.send(f'🎵 **Now playing:** {song_info["title"]} - `{song_info["duration"]}`')

        except Exception as e:
            print(f"Playback error: {e}")
            await ctx.send('❌ Error playing the song!')
            await self.play_next(ctx)

    async def song_finished(self, ctx):
        """Handle when a song finishes"""
        await asyncio.sleep(1)  # Small delay
        await self.play_next(ctx)

    async def skip(self, ctx):
        """Skip current song"""
        voice_client = self.voice_clients.get(ctx.guild.id)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await ctx.send('⏭️ Skipped!')
        else:
            await ctx.send('❌ No music is playing!')

    async def stop(self, ctx):
        """Stop music and clear queue"""
        guild_id = ctx.guild.id
        voice_client = self.voice_clients.get(guild_id)
        
        if voice_client:
            voice_client.stop()
            
        # Clear queue
        if guild_id in self.queues:
            self.queues[guild_id].clear()
        if guild_id in self.current_songs:
            del self.current_songs[guild_id]
            
        await ctx.send('⏹️ Music stopped and queue cleared!')

    async def pause(self, ctx):
        """Pause music"""
        voice_client = self.voice_clients.get(ctx.guild.id)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await ctx.send('⏸️ Music paused!')
        else:
            await ctx.send('❌ No music is playing!')

    async def resume(self, ctx):
        """Resume music"""
        voice_client = self.voice_clients.get(ctx.guild.id)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.send('▶️ Music resumed!')
        else:
            await ctx.send('❌ Music is not paused!')

    async def set_volume(self, ctx, volume):
        """Set volume (0-100)"""
        if volume < 0 or volume > 100:
            await ctx.send('❌ Volume must be between 0 and 100!')
            return
            
        # Note: FFmpeg volume control is limited in discord.py
        # For better volume control, you'd need a more complex audio source
        await ctx.send(f'🔊 Volume set to {volume}% (Note: Volume control is limited)')

    async def show_queue(self, ctx):
        """Show current queue"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.queues or not self.queues[guild_id]:
            current = self.current_songs.get(guild_id)
            if current:
                await ctx.send(f'🎵 **Now Playing:** {current["title"]} - `{current["duration"]}`\n📄 Queue is empty!')
            else:
                await ctx.send('📄 Queue is empty!')
            return

        current = self.current_songs.get(guild_id)
        queue_list = ""
        
        if current:
            queue_list += f'🎵 **Now Playing:** {current["title"]} - `{current["duration"]}`\n\n'
        
        queue_list += "**Upcoming:**\n"
        for i, song in enumerate(self.queues[guild_id][:10], 1):
            queue_list += f'{i}. {song["title"]} - `{song["duration"]}`\n'
        
        if len(self.queues[guild_id]) > 10:
            queue_list += f'\n...and {len(self.queues[guild_id]) - 10} more songs'

        await ctx.send(queue_list)