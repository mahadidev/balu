import discord
import asyncio
import yt_dlp
import time
import random
from datetime import datetime, timedelta
from discord import FFmpegPCMAudio, FFmpegOpusAudio, PCMVolumeTransformer

class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.queues = {}
        self.current_songs = {}
        self.music_messages = {}
        self.start_times = {}
        self.repeat_modes = {}
        self.shuffle_modes = {}
        self.volumes = {}
        self.url_cache = {}
        
        # Optimized yt-dlp options for speed
        self.ytdl_format_options = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,  # Don't process playlists by default
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch1',
            'source_address': '0.0.0.0',
            'extract_flat': False,
            'retries': 2,
            'fragment_retries': 2,
            'socket_timeout': 8,
            'http_chunk_size': 4194304,
            'cookiefile': None,
            'age_limit': None,
        }
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2',
            'options': '-vn -bufsize 1024k'
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
            
            if ctx.guild.id in self.queues:
                del self.queues[ctx.guild.id]
            if ctx.guild.id in self.current_songs:
                del self.current_songs[ctx.guild.id]
            if ctx.guild.id in self.repeat_modes:
                del self.repeat_modes[ctx.guild.id]
            if ctx.guild.id in self.shuffle_modes:
                del self.shuffle_modes[ctx.guild.id]
            if ctx.guild.id in self.start_times:
                del self.start_times[ctx.guild.id]
            if ctx.guild.id in self.music_messages:
                del self.music_messages[ctx.guild.id]
            if ctx.guild.id in self.volumes:
                del self.volumes[ctx.guild.id]
                
            await ctx.send('👋 Left voice channel!')
        else:
            await ctx.send('❌ Not connected to a voice channel!')

    def is_cache_valid(self, webpage_url):
        """Check if cached URL is still valid"""
        if webpage_url not in self.url_cache:
            return False
        
        cached_time = self.url_cache[webpage_url].get('timestamp')
        if not cached_time:
            return False
        
        return (datetime.now() - cached_time) < timedelta(minutes=30)
    
    def get_cached_url(self, webpage_url):
        """Get cached audio URL if valid"""
        if self.is_cache_valid(webpage_url):
            return self.url_cache[webpage_url].get('audio_url')
        return None
    
    def cache_url(self, webpage_url, audio_url):
        """Cache audio URL with timestamp"""
        self.url_cache[webpage_url] = {
            'audio_url': audio_url,
            'timestamp': datetime.now()
        }

    async def get_playable_url(self, search):
        """Get playable audio URL in one efficient step"""
        try:
            # Check cache first
            cached_url = self.get_cached_url(search)
            if cached_url:
                return cached_url
            
            # Extract info and get URL in one go
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None, 
                lambda: self.ytdl.extract_info(search, download=False)
            )
            
            if not info:
                return None
                
            # Get the actual entry
            if 'entries' in info:
                entry = info['entries'][0]
            else:
                entry = info
                
            # Extract the playable URL
            url = entry.get('url')
            if not url and 'formats' in entry:
                for fmt in entry['formats']:
                    if fmt.get('acodec') != 'none' and fmt.get('url'):
                        url = fmt['url']
                        break
            
            if url:
                self.cache_url(search, url)
                
            return url
            
        except Exception as e:
            print(f"URL extraction error: {e}")
            return None

    async def play(self, ctx, query):
        """Fast play music - play immediately then show interface"""
        # Ensure user is in voice channel
        if not ctx.author.voice:
            await ctx.send('❌ You need to be in a voice channel!')
            return

        if ctx.guild.id not in self.voice_clients:
            if not await self.join(ctx):
                return

        voice_client = self.voice_clients[ctx.guild.id]
        
        # Double-check connection
        if not voice_client.is_connected():
            try:
                channel = ctx.author.voice.channel
                voice_client = await channel.connect()
                self.voice_clients[ctx.guild.id] = voice_client
            except Exception as e:
                await ctx.send('❌ Could not connect to voice channel!')
                return
        
        # Handle YouTube Radio/Playlists differently - extract just the video ID
        if 'list=' in query and 'start_radio=1' in query:
            # Extract just the video ID for faster processing
            if 'watch?v=' in query:
                video_id = query.split('watch?v=')[1].split('&')[0]
                query = f"https://www.youtube.com/watch?v={video_id}"
        
        search_msg = await ctx.send('🔍 Getting song...')
        
        try:
            # Get playable URL directly
            audio_url = await self.get_playable_url(query)
            if not audio_url:
                await search_msg.edit(content='❌ Could not find playable audio!')
                return
                
            # Get basic info for display
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None, 
                lambda: self.ytdl.extract_info(query, download=False)
            )
            
            if 'entries' in info and info['entries']:
                entry = info['entries'][0]
            else:
                entry = info
                
            song_info = self.extract_song_info(entry, ctx.author.name)
            song_info['url'] = audio_url  # Store the playable URL
            
            self.add_to_queue(ctx.guild.id, song_info)
            
            if not voice_client.is_playing():
                await search_msg.delete()
                await self.play_next(ctx)
            else:
                await search_msg.edit(content=f'➕ Added: {song_info["title"]}')
                
        except Exception as e:
            await search_msg.edit(content=f'❌ Error: {str(e)[:50]}')

    async def add_playlist(self, ctx, playlist_url):
        """Fast playlist handling - just play the first song immediately"""
        if ctx.guild.id not in self.voice_clients:
            if not await self.join(ctx):
                return
        
        # Extract just the first video from playlist URLs for speed
        if 'list=' in playlist_url and 'watch?v=' in playlist_url:
            # Extract video ID and use single video URL
            video_id = playlist_url.split('watch?v=')[1].split('&')[0]
            single_url = f"https://www.youtube.com/watch?v={video_id}"
            await ctx.send('🎵 Playing first song from playlist...')
            await self.play(ctx, single_url)
            return
        
        await ctx.send('🔄 Getting first song from playlist...')
        
        try:
            # For direct playlist URLs, use faster processing
            playlist_opts = self.ytdl_format_options.copy()
            playlist_opts['extract_flat'] = True
            playlist_opts['ignoreerrors'] = True
            playlist_opts['noplaylist'] = False
            
            playlist_ytdl = yt_dlp.YoutubeDL(playlist_opts)
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None, 
                lambda: playlist_ytdl.extract_info(playlist_url, download=False)
            )
            
            if 'entries' in info and info['entries']:
                first_entry = info['entries'][0]
                
                # Get the first video URL directly
                if first_entry.get('url'):
                    first_url = first_entry['url']
                else:
                    first_url = f"https://www.youtube.com/watch?v={first_entry.get('id')}"
                
                # Play the first song immediately using regular play method
                await self.play(ctx, first_url)
                
                # Load remaining songs in background
                remaining_entries = info['entries'][1:5]  # Only next 4 songs
                if remaining_entries:
                    asyncio.create_task(self.load_remaining_songs(ctx, remaining_entries))
                
            else:
                await ctx.send('❌ Could not find any songs in the playlist!')
                
        except Exception as e:
            print(f"Playlist error: {e}")
            await ctx.send(f'❌ Error processing playlist, trying single video...')
            # Fallback: try as single video
            await self.play(ctx, playlist_url)

    async def load_remaining_songs(self, ctx, entries):
        """Load remaining songs in background"""
        if not entries:
            return
            
        added_count = 0
        
        for entry in entries:
            try:
                if entry.get('url'):
                    video_url = entry['url']
                else:
                    video_url = f"https://www.youtube.com/watch?v={entry.get('id')}"
                
                # Get playable URL
                audio_url = await self.get_playable_url(video_url)
                if audio_url:
                    duration_sec = int(entry.get('duration', 0) or 0)
                    song_info = {
                        'title': entry.get('title', 'Unknown Title'),
                        'duration': f"{duration_sec//60}:{duration_sec%60:02d}",
                        'duration_seconds': duration_sec,
                        'thumbnail': entry.get('thumbnail'),
                        'author': entry.get('uploader', 'Unknown Artist'),
                        'webpage_url': video_url,
                        'url': audio_url,
                        'requested_by': ctx.author.name
                    }
                    self.add_to_queue(ctx.guild.id, song_info)
                    added_count += 1
                    
            except Exception:
                continue
        
        if added_count > 0:
            await ctx.send(f'✅ Added {added_count} more songs to queue!')

    def extract_song_info(self, entry, requested_by):
        """Extract song information from yt-dlp entry"""
        if not entry:
            return {
                'title': 'Unknown Title',
                'duration': 'Unknown',
                'duration_seconds': 0,
                'thumbnail': None,
                'author': 'Unknown Artist',
                'webpage_url': '',
                'requested_by': requested_by
            }
            
        title = entry.get('title', 'Unknown Title')
        duration = entry.get('duration', 0)
        thumbnail = entry.get('thumbnail')
        author = entry.get('uploader', entry.get('channel', 'Unknown Artist'))
        webpage_url = entry.get('webpage_url', '')
        
        duration_str = f"{duration//60}:{duration%60:02d}" if duration else "Unknown"
        
        return {
            'title': title,
            'duration': duration_str,
            'duration_seconds': duration,
            'thumbnail': thumbnail,
            'author': author,
            'webpage_url': webpage_url,
            'requested_by': requested_by
        }

    def add_to_queue(self, guild_id, song_info):
        """Add song to guild queue"""
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        
        if self.get_shuffle_mode(guild_id) and self.queues[guild_id]:
            random_index = random.randint(0, len(self.queues[guild_id]))
            self.queues[guild_id].insert(random_index, song_info)
        else:
            self.queues[guild_id].append(song_info)

    async def play_next(self, ctx):
        """Fast play next song with music interface"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.queues or not self.queues[guild_id]:
            # Clear current song if queue is empty
            if guild_id in self.current_songs:
                del self.current_songs[guild_id]
            return

        voice_client = self.voice_clients.get(guild_id)
        if not voice_client or not voice_client.is_connected():
            # Try to reconnect if not connected
            if ctx.author.voice and ctx.author.voice.channel:
                try:
                    channel = ctx.author.voice.channel
                    if guild_id in self.voice_clients:
                        voice_client = await self.voice_clients[guild_id].move_to(channel)
                    else:
                        voice_client = await channel.connect()
                        self.voice_clients[guild_id] = voice_client
                except Exception as e:
                    await ctx.send('❌ Could not connect to voice channel!')
                    return
            else:
                await ctx.send('❌ Not connected to voice channel!')
                return

        # Get song with pre-extracted URL
        song_info = self.queues[guild_id][0]
        
        try:
            # Use pre-extracted URL for immediate playback
            source = PCMVolumeTransformer(
                FFmpegPCMAudio(song_info['url'], **self.ffmpeg_options),
                volume=self.get_volume(guild_id)
            )
            
            self.queues[guild_id].pop(0)
            self.current_songs[guild_id] = song_info
            self.start_times[guild_id] = time.time()
            
            def after_play(error):
                if error:
                    print(f"Playback error: {error}")
                asyncio.run_coroutine_threadsafe(
                    self.song_finished(ctx, error), self.bot.loop
                )
            
            voice_client.play(source, after=after_play)

            # Create and send music interface AFTER playback starts
            await self.create_music_interface(ctx, song_info)
            
        except Exception as e:
            print(f"Playback error: {e}")
            if guild_id in self.queues and self.queues[guild_id]:
                await self.play_next(ctx)

    async def song_finished(self, ctx, error=None):
        """Handle when a song finishes"""
        if error:
            print(f"Playback finished with error: {error}")
        
        await asyncio.sleep(1)
        
        guild_id = ctx.guild.id
        
        # Check if still connected to voice
        voice_client = self.voice_clients.get(guild_id)
        if not voice_client or not voice_client.is_connected():
            print("Not connected to voice, skipping next song")
            return
        
        repeat_mode = self.get_repeat_mode(guild_id)
        current_song = self.current_songs.get(guild_id)
        
        if repeat_mode == 1 and current_song:
            if guild_id not in self.queues:
                self.queues[guild_id] = []
            self.queues[guild_id].insert(0, current_song.copy())
        elif repeat_mode == 2 and current_song:
            if guild_id not in self.queues:
                self.queues[guild_id] = []
            self.queues[guild_id].append(current_song.copy())
        
        await self.play_next(ctx)

    async def create_music_interface(self, ctx, song_info):
        """Create and send the music interface"""
        guild_id = ctx.guild.id
        
        embed = discord.Embed(color=0x1DB954)
        
        # Build description with all info
        description = f"**{song_info['title']}**\n"
        description += f"by {song_info['author']}\n\n"
        
        # Add progress info
        description += f"⏱️ {song_info['duration']}"
        
        # Add queue info
        queue_count = len(self.queues.get(guild_id, []))
        if queue_count > 0:
            description += f" • {queue_count} in queue"
        
        # Add repeat mode if active
        repeat_mode = self.get_repeat_mode(guild_id)
        if repeat_mode > 0:
            repeat_text = "Track" if repeat_mode == 1 else "Queue"
            description += f" • 🔁 {repeat_text}"
        
        # Add shuffle mode if active
        if self.get_shuffle_mode(guild_id):
            description += f" • 🔀 Shuffle"
        
        # Add volume info
        volume_percent = self.get_volume_percentage(guild_id)
        description += f" • 🔊 {volume_percent}%"
        
        embed.description = description
        
        # Add thumbnail if available
        if song_info.get('thumbnail'):
            embed.set_thumbnail(url=song_info['thumbnail'])
        
        # Add requested by
        embed.set_footer(text=f"Requested by {song_info['requested_by']}")
        
        # Create buttons view
        view = MusicControlView(self, ctx.guild.id)
        
        # Send or update music message
        if guild_id in self.music_messages:
            try:
                await self.music_messages[guild_id].edit(embed=embed, view=view)
            except:
                self.music_messages[guild_id] = await ctx.send(embed=embed, view=view)
        else:
            self.music_messages[guild_id] = await ctx.send(embed=embed, view=view)

    def get_progress_bar(self, guild_id, song_info):
        """Create a progress bar for the currently playing song"""
        if guild_id not in self.start_times or not song_info.get('duration_seconds'):
            return "⚪⚪⚪⚪⚪⚪⚪⚪⚪⚪ 0:00"
        
        elapsed = time.time() - self.start_times[guild_id]
        total_seconds = song_info['duration_seconds']
        
        if elapsed > total_seconds:
            elapsed = total_seconds
        
        progress = elapsed / total_seconds if total_seconds > 0 else 0
        filled_blocks = int(progress * 10)
        
        bar = "🔵" * filled_blocks + "⚪" * (10 - filled_blocks)
        
        current_minutes = int(elapsed // 60)
        current_seconds = int(elapsed % 60)
        
        return f"{bar} {current_minutes}:{current_seconds:02d}"

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

    async def change_volume(self, ctx, volume_percent):
        """Set volume (0-100)"""
        if volume_percent < 0 or volume_percent > 100:
            await ctx.send('❌ Volume must be between 0 and 100!')
            return
        
        guild_id = ctx.guild.id
        volume = volume_percent / 100.0
        self.set_volume(guild_id, volume)
        
        voice_client = self.voice_clients.get(guild_id)
        if voice_client and voice_client.source:
            if hasattr(voice_client.source, 'volume'):
                voice_client.source.volume = volume
        
        await ctx.send(f'🔊 Volume set to {volume_percent}%')

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

    def get_repeat_mode(self, guild_id):
        return self.repeat_modes.get(guild_id, 0)
    
    def cycle_repeat_mode(self, guild_id):
        current_mode = self.repeat_modes.get(guild_id, 0)
        new_mode = (current_mode + 1) % 3
        self.repeat_modes[guild_id] = new_mode
        return new_mode
    
    def get_repeat_emoji(self, guild_id):
        mode = self.get_repeat_mode(guild_id)
        if mode == 0:
            return "🔁"
        elif mode == 1:
            return "🔂"
        else:
            return "🔁"
    
    def get_repeat_text(self, guild_id):
        mode = self.get_repeat_mode(guild_id)
        if mode == 0:
            return "Repeat: Off"
        elif mode == 1:
            return "Repeat: Track"
        else:
            return "Repeat: Queue"
    
    def get_shuffle_mode(self, guild_id):
        return self.shuffle_modes.get(guild_id, False)
    
    def toggle_shuffle_mode(self, guild_id):
        current_mode = self.shuffle_modes.get(guild_id, False)
        new_mode = not current_mode
        self.shuffle_modes[guild_id] = new_mode
        
        if new_mode and guild_id in self.queues and self.queues[guild_id]:
            random.shuffle(self.queues[guild_id])
        
        return new_mode
    
    def get_shuffle_emoji(self, guild_id):
        return "🔀" if self.get_shuffle_mode(guild_id) else "🔀"
    
    def get_shuffle_text(self, guild_id):
        return "Shuffle: On" if self.get_shuffle_mode(guild_id) else "Shuffle: Off"
    
    def get_volume(self, guild_id):
        return self.volumes.get(guild_id, 0.5)
    
    def set_volume(self, guild_id, volume):
        volume = max(0.0, min(1.0, volume))
        self.volumes[guild_id] = volume
        return volume
    
    def get_volume_percentage(self, guild_id):
        return int(self.get_volume(guild_id) * 100)


class MusicControlView(discord.ui.View):
    def __init__(self, music_player, guild_id):
        super().__init__(timeout=300)
        self.music_player = music_player
        self.guild_id = guild_id
    
    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.primary, row=0)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⏪ Previous track feature coming soon!", ephemeral=True)
    
    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.primary, row=0)
    async def play_pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = self.music_player.voice_clients.get(self.guild_id)
        if not voice_client:
            await interaction.response.send_message("❌ Not connected to voice channel!", ephemeral=True)
            return
        
        if voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("⏸️ Music paused!", ephemeral=True)
        elif voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("▶️ Music resumed!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No music is playing!", ephemeral=True)
    
    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.primary, row=0)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = self.music_player.voice_clients.get(self.guild_id)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("⏩ Skipped!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No music is playing!", ephemeral=True)
    
    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.primary, row=0)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = self.music_player.voice_clients.get(self.guild_id)
        if voice_client:
            voice_client.stop()
            if self.guild_id in self.music_player.queues:
                self.music_player.queues[self.guild_id].clear()
            if self.guild_id in self.music_player.current_songs:
                del self.music_player.current_songs[self.guild_id]
            await interaction.response.send_message("⏹️ Music stopped and queue cleared!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Not connected to voice channel!", ephemeral=True)
    
    @discord.ui.button(emoji="❌", style=discord.ButtonStyle.primary, row=0)
    async def disconnect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = self.music_player.voice_clients.get(self.guild_id)
        if voice_client:
            await voice_client.disconnect()
            del self.music_player.voice_clients[self.guild_id]
            
            if self.guild_id in self.music_player.queues:
                del self.music_player.queues[self.guild_id]
            if self.guild_id in self.music_player.current_songs:
                del self.music_player.current_songs[self.guild_id]
            if self.guild_id in self.music_player.repeat_modes:
                del self.music_player.repeat_modes[self.guild_id]
            if self.guild_id in self.music_player.shuffle_modes:
                del self.music_player.shuffle_modes[self.guild_id]
            if self.guild_id in self.music_player.start_times:
                del self.music_player.start_times[self.guild_id]
            if self.guild_id in self.music_player.music_messages:
                del self.music_player.music_messages[self.guild_id]
            if self.guild_id in self.music_player.volumes:
                del self.music_player.volumes[self.guild_id]
                
            await interaction.response.send_message("👋 Left voice channel!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Not connected to voice channel!", ephemeral=True)
    
    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.primary, row=1)
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_mode = self.music_player.toggle_shuffle_mode(self.guild_id)
        shuffle_text = self.music_player.get_shuffle_text(self.guild_id)
        
        try:
            await interaction.response.edit_message(view=self)
            if new_mode:
                queue_count = len(self.music_player.queues.get(self.guild_id, []))
                await interaction.followup.send(f"🔄 {shuffle_text} - Shuffled {queue_count} songs!", ephemeral=True)
            else:
                await interaction.followup.send(f"🔄 {shuffle_text}", ephemeral=True)
        except discord.errors.InteractionResponded:
            if new_mode:
                queue_count = len(self.music_player.queues.get(self.guild_id, []))
                await interaction.followup.send(f"🔄 {shuffle_text} - Shuffled {queue_count} songs!", ephemeral=True)
            else:
                await interaction.followup.send(f"🔄 {shuffle_text}", ephemeral=True)
    
    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.primary, row=1)
    async def repeat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_mode = self.music_player.cycle_repeat_mode(self.guild_id)
        repeat_text = self.music_player.get_repeat_text(self.guild_id)
        
        button.emoji = self.music_player.get_repeat_emoji(self.guild_id)
        
        try:
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"🔁 {repeat_text}", ephemeral=True)
        except discord.errors.InteractionResponded:
            await interaction.followup.send(f"🔁 {repeat_text}", ephemeral=True)
    
    @discord.ui.button(emoji="📄", style=discord.ButtonStyle.primary, row=1)
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = self.guild_id
        
        if guild_id not in self.music_player.queues or not self.music_player.queues[guild_id]:
            current = self.music_player.current_songs.get(guild_id)
            if current:
                embed = discord.Embed(
                    title="📋 Music Queue",
                    description=f'🎵 **Now Playing:** {current["title"]} - `{current["duration"]}`\n\n📄 Queue is empty!',
                    color=0x1DB954
                )
            else:
                embed = discord.Embed(
                    title="📋 Music Queue",
                    description="📄 Queue is empty!",
                    color=0x1DB954
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        current = self.music_player.current_songs.get(guild_id)
        embed = discord.Embed(
            title="📋 Music Queue",
            color=0x1DB954
        )
        
        queue_list = ""
        if current:
            queue_list += f'🎵 **Now Playing:** {current["title"]} - `{current["duration"]}`\n\n'
        
        queue_list += "**Upcoming:**\n"
        for i, song in enumerate(self.music_player.queues[guild_id][:10], 1):
            queue_list += f'{i}. {song["title"]} - `{song["duration"]}`\n'
        
        if len(self.music_player.queues[guild_id]) > 10:
            queue_list += f'\n...and {len(self.music_player.queues[guild_id]) - 10} more songs'

        embed.description = queue_list
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.primary, row=1)
    async def volume_down_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_volume = self.music_player.get_volume_percentage(self.guild_id)
        new_volume = max(0, current_volume - 10)
        
        volume_decimal = new_volume / 100.0
        self.music_player.set_volume(self.guild_id, volume_decimal)
        
        voice_client = self.music_player.voice_clients.get(self.guild_id)
        if voice_client and voice_client.source and hasattr(voice_client.source, 'volume'):
            voice_client.source.volume = volume_decimal
        
        await interaction.response.send_message(f"🔉 Volume set to {new_volume}%", ephemeral=True)
    
    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.primary, row=1)
    async def volume_up_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_volume = self.music_player.get_volume_percentage(self.guild_id)
        new_volume = min(100, current_volume + 10)
        
        volume_decimal = new_volume / 100.0
        self.music_player.set_volume(self.guild_id, volume_decimal)
        
        voice_client = self.music_player.voice_clients.get(self.guild_id)
        if voice_client and voice_client.source and hasattr(voice_client.source, 'volume'):
            voice_client.source.volume = volume_decimal
        
        await interaction.response.send_message(f"🔊 Volume set to {new_volume}%", ephemeral=True)