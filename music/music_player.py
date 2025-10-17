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
        
        # ULTRA FAST yt-dlp options
        self.ytdl_fast_options = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extract_flat': False,
            'socket_timeout': 5,
            'retries': 1,
            'fragment_retries': 1,
            'extractor_retries': 1,
            'ignoreerrors': True,
            'no_check_certificate': True,
            'prefer_insecure': True,
            'nocheckcertificate': True,
            'source_address': '0.0.0.0',
            'forceipv4': True,
            'cachedir': False,
            'no_cache_dir': True,
            'rm_cache_dir': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_embedded'],
                    'player_skip': ['configs', 'webpage', 'js']
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                'Accept': '*/*',
            },
        }
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2',
            'options': '-vn -bufsize 256k'
        }
        
        self.ytdl_fast = yt_dlp.YoutubeDL(self.ytdl_fast_options)

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

    async def get_audio_url_ultra_fast(self, query):
        """ULTRA FAST audio URL extraction"""
        try:
            # Check cache first
            if query in self.url_cache:
                cached_data = self.url_cache[query]
                if (datetime.now() - cached_data['timestamp']) < timedelta(minutes=30):
                    return cached_data['url'], cached_data['title']
            
            # For search queries, use ytsearch1
            if not any(domain in query.lower() for domain in ['youtube.com', 'youtu.be', 'http', 'www.']):
                query = f"ytsearch1:{query}"
            
            loop = asyncio.get_event_loop()
            
            # Use faster extraction with shorter timeout
            info = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self.ytdl_fast.extract_info(query, download=False)),
                timeout=6.0
            )
            
            if not info:
                return None, None
            
            # Get the entry
            if 'entries' in info:
                if not info['entries']:
                    return None, None
                entry = info['entries'][0]
            else:
                entry = info
            
            # Get the audio URL - prioritize direct URLs
            url = entry.get('url')
            if not url:
                # Quick format search
                if 'formats' in entry:
                    formats = entry['formats'][:5]  # Only check first 5 formats
                    for fmt in formats:
                        if fmt.get('acodec') != 'none' and fmt.get('url'):
                            url = fmt['url']
                            break
            
            if not url:
                return None, None
            
            # Get basic title
            title = entry.get('title', 'Unknown Title')
            
            # Cache the result
            self.url_cache[query] = {
                'url': url,
                'title': title,
                'timestamp': datetime.now()
            }
            
            return url, title
            
        except asyncio.TimeoutError:
            print(f"Timeout getting URL for: {query}")
            return None, None
        except Exception as e:
            print(f"Error getting audio URL: {e}")
            return None, None

    async def play(self, ctx, query):
        """BULLETPROOF play - always play something"""
        # Ensure user is in voice channel
        if not ctx.author.voice:
            await ctx.send('❌ You need to be in a voice channel!')
            return

        if ctx.guild.id not in self.voice_clients:
            if not await self.join(ctx):
                return

        voice_client = self.voice_clients[ctx.guild.id]
        
        # Check if it's a playlist URL with video ID
        is_playlist_with_video = 'watch?v=' in query and 'list=' in query
        
        if is_playlist_with_video:
            await self.handle_playlist_url(ctx, query, voice_client)
        else:
            await self.handle_single_song(ctx, query, voice_client)

    async def handle_playlist_url(self, ctx, playlist_url, voice_client):
        """Handle playlist URLs by extracting the single video first"""
        search_msg = await ctx.send('🎵 **Processing YouTube link...**')
        
        try:
            # Extract video ID from the URL
            video_id = self.extract_video_id(playlist_url)
            if not video_id:
                await search_msg.edit(content='❌ **Invalid YouTube URL!**')
                return
            
            # Create single video URL
            single_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Try to play the single video
            audio_url, title = await self.get_audio_url_ultra_fast(single_url)
            
            if not audio_url:
                await search_msg.edit(content='❌ **Could not play this video!**')
                return
            
            # Create song info
            song_info = {
                'title': title,
                'duration': 'Loading...',
                'duration_seconds': 0,
                'thumbnail': None,
                'author': 'Loading...',
                'webpage_url': single_url,
                'url': audio_url,
                'requested_by': ctx.author.name
            }
            
            # Add to queue
            self.add_to_queue(ctx.guild.id, song_info)
            
            if not voice_client.is_playing():
                await search_msg.delete()
                await self.play_instant(ctx, song_info)
                
                # Send success message
                await ctx.send(f'🎵 **Now Playing:** {title}')
            else:
                await search_msg.edit(content=f'✅ **Added to queue:** {title}')
            
            # Try to load more songs from playlist in background (silently)
            asyncio.create_task(self.try_load_playlist_songs(ctx, playlist_url))
                
        except Exception as e:
            print(f"Playlist URL error: {e}")
            await search_msg.edit(content='❌ **Error processing YouTube link!**')

    def extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        try:
            if 'watch?v=' in url:
                return url.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in url:
                return url.split('youtu.be/')[1].split('?')[0]
            return None
        except:
            return None

    async def try_load_playlist_songs(self, ctx, playlist_url):
        """Try to load playlist songs in background (silent failure)"""
        try:
            # Use a separate yt-dlp instance for playlist extraction
            playlist_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'noplaylist': False,
                'extract_flat': True,
                'socket_timeout': 8,
                'retries': 1,
                'ignoreerrors': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android_embedded'],
                    }
                },
            }
            
            playlist_ytdl = yt_dlp.YoutubeDL(playlist_opts)
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None, lambda: playlist_ytdl.extract_info(playlist_url, download=False)
            )
            
            if info and 'entries' in info and info['entries']:
                entries = [entry for entry in info['entries'] if entry][:10]  # Limit to 10
                
                if len(entries) > 1:
                    guild_id = ctx.guild.id
                    loaded_count = 0
                    
                    # Skip first entry (already playing)
                    for entry in entries[1:]:
                        try:
                            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            audio_url, title = await self.get_audio_url_ultra_fast(video_url)
                            
                            if audio_url:
                                song_info = {
                                    'title': entry.get('title', title),
                                    'duration': 'Loading...',
                                    'duration_seconds': 0,
                                    'thumbnail': None,
                                    'author': entry.get('uploader', 'Unknown Artist'),
                                    'webpage_url': video_url,
                                    'url': audio_url,
                                    'requested_by': ctx.author.name
                                }
                                
                                self.add_to_queue(guild_id, song_info)
                                loaded_count += 1
                                
                                await asyncio.sleep(0.1)  # Small delay
                                
                        except Exception as e:
                            continue
                    
                    if loaded_count > 0:
                        await ctx.send(f'✅ **Added {loaded_count} more songs from YouTube Radio**')
                        
        except Exception as e:
            # Silent failure - we already have the first song playing
            pass

    async def handle_single_song(self, ctx, query, voice_client):
        """Handle single song playback"""
        search_msg = await ctx.send('⚡ **Getting song...**')
        
        try:
            # Get audio URL ULTRA FAST
            audio_url, title = await self.get_audio_url_ultra_fast(query)
            
            if not audio_url:
                await search_msg.edit(content='❌ **Could not find playable audio!**')
                return
            
            # Create minimal song info
            song_info = {
                'title': title,
                'duration': 'Loading...',
                'duration_seconds': 0,
                'thumbnail': None,
                'author': 'Loading...',
                'webpage_url': query if query.startswith('http') else f'search:{query}',
                'url': audio_url,
                'requested_by': ctx.author.name
            }
            
            # Add to queue
            self.add_to_queue(ctx.guild.id, song_info)
            
            if not voice_client.is_playing():
                await search_msg.delete()
                await self.play_instant(ctx, song_info)
            else:
                await search_msg.edit(content=f'✅ **Added to queue:** {title}')
                
        except Exception as e:
            print(f"Play error: {e}")
            await search_msg.edit(content='❌ **Error loading song!**')

    async def play_instant(self, ctx, song_info):
        """INSTANT playback - start within 1 second"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.queues or not self.queues[guild_id]:
            return

        voice_client = self.voice_clients.get(guild_id)
        if not voice_client or not voice_client.is_connected():
            if ctx.author.voice and ctx.author.voice.channel:
                try:
                    channel = ctx.author.voice.channel
                    voice_client = await channel.connect()
                    self.voice_clients[guild_id] = voice_client
                except Exception as e:
                    await ctx.send('❌ Could not connect to voice channel!')
                    return
            else:
                return

        # Get next song
        current_song = self.queues[guild_id][0]
        
        try:
            # Use the URL for ULTRA FAST playback
            source = PCMVolumeTransformer(
                FFmpegPCMAudio(current_song['url'], **self.ffmpeg_options),
                volume=self.get_volume(guild_id)
            )
            
            # Remove from queue and set as current
            self.queues[guild_id].pop(0)
            self.current_songs[guild_id] = current_song
            self.start_times[guild_id] = time.time()
            
            def after_play(error):
                if error:
                    print(f"Playback error: {error}")
                asyncio.run_coroutine_threadsafe(
                    self.song_finished(ctx, error), self.bot.loop
                )
            
            # START PLAYBACK IMMEDIATELY (within 1 second)
            voice_client.play(source, after=after_play)

            # Show basic interface instantly
            await self.create_basic_music_interface(ctx, current_song)
            
            # Fetch additional details in background (non-blocking)
            asyncio.create_task(self.fetch_additional_details(ctx, current_song))
            
        except Exception as e:
            print(f"Playback error: {e}")
            if guild_id in self.queues and self.queues[guild_id]:
                await self.play_instant(ctx, song_info)

    async def fetch_additional_details(self, ctx, basic_song_info):
        """Fetch additional song details in background"""
        try:
            # Only fetch if we have a valid URL
            if basic_song_info['webpage_url'].startswith('http'):
                loop = asyncio.get_event_loop()
                detailed_info = await loop.run_in_executor(
                    None, 
                    lambda: self.ytdl_fast.extract_info(basic_song_info['webpage_url'], download=False)
                )
                
                if detailed_info:
                    # Update current song with detailed info
                    guild_id = ctx.guild.id
                    if guild_id in self.current_songs:
                        self.current_songs[guild_id].update({
                            'title': detailed_info.get('title', basic_song_info['title']),
                            'duration': str(detailed_info.get('duration', 'Unknown')),
                            'duration_seconds': detailed_info.get('duration', 0),
                            'author': detailed_info.get('uploader', 'Unknown Artist'),
                            'thumbnail': detailed_info.get('thumbnail')
                        })
                        
                        # Update interface
                        await self.create_music_interface(ctx, self.current_songs[guild_id])
                        
        except Exception as e:
            # Silently fail - we already have basic info
            pass

    async def create_basic_music_interface(self, ctx, song_info):
        """Create basic music interface instantly"""
        guild_id = ctx.guild.id
        
        embed = discord.Embed(color=0x1DB954)
        
        # Minimal description for speed
        description = f"**{song_info['title']}**\n"
        description += f"🎵 Now Playing\n\n"
        description += f"⏱️ Loading..."
        
        embed.description = description
        embed.set_footer(text=f"Requested by {song_info['requested_by']}")
        
        # Create buttons view
        view = MusicControlView(self, ctx.guild.id)
        
        # Send music message
        try:
            if guild_id in self.music_messages:
                await self.music_messages[guild_id].edit(embed=embed, view=view)
            else:
                self.music_messages[guild_id] = await ctx.send(embed=embed, view=view)
        except:
            self.music_messages[guild_id] = await ctx.send(embed=embed, view=view)

    async def create_music_interface(self, ctx, song_info):
        """Create full music interface"""
        guild_id = ctx.guild.id
        
        embed = discord.Embed(color=0x1DB954)
        
        # Complete description
        description = f"**{song_info['title']}**\n"
        description += f"by {song_info['author']}\n\n"
        
        # Format duration
        if song_info['duration_seconds'] > 0:
            mins = song_info['duration_seconds'] // 60
            secs = song_info['duration_seconds'] % 60
            duration_str = f"{mins}:{secs:02d}"
        else:
            duration_str = str(song_info['duration'])
        
        description += f"⏱️ {duration_str}"
        
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
        
        embed.set_footer(text=f"Requested by {song_info['requested_by']}")
        
        # Create buttons view
        view = MusicControlView(self, ctx.guild.id)
        
        # Update music message
        try:
            if guild_id in self.music_messages:
                await self.music_messages[guild_id].edit(embed=embed, view=view)
        except:
            pass

    async def song_finished(self, ctx, error=None):
        """Handle when a song finishes"""
        if error:
            print(f"Playback error: {error}")
        
        await asyncio.sleep(0.5)
        
        guild_id = ctx.guild.id
        
        voice_client = self.voice_clients.get(guild_id)
        if not voice_client or not voice_client.is_connected():
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
        
        # Play next song
        if guild_id in self.queues and self.queues[guild_id]:
            next_song = self.queues[guild_id][0]
            await self.play_instant(ctx, next_song)

    def add_to_queue(self, guild_id, song_info):
        """Add song to guild queue"""
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        
        if self.get_shuffle_mode(guild_id) and self.queues[guild_id]:
            random_index = random.randint(0, len(self.queues[guild_id]))
            self.queues[guild_id].insert(random_index, song_info)
        else:
            self.queues[guild_id].append(song_info)

    # ... (keep all the other methods the same)

# Keep the same MusicControlView class as before

    # ... (keep all the other methods the same: skip, stop, pause, resume, change_volume, show_queue, etc.)

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
                await ctx.send(f'🎵 **Now Playing:** {current["title"]}\n📄 Queue is empty!')
            else:
                await ctx.send('📄 Queue is empty!')
            return

        current = self.current_songs.get(guild_id)
        queue_list = ""
        
        if current:
            queue_list += f'🎵 **Now Playing:** {current["title"]}\n\n'
        
        queue_list += "**Upcoming:**\n"
        for i, song in enumerate(self.queues[guild_id][:8], 1):
            queue_list += f'{i}. {song["title"]}\n'
        
        if len(self.queues[guild_id]) > 8:
            queue_list += f'\n...and {len(self.queues[guild_id]) - 8} more songs'

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
    
    def get_volume(self, guild_id):
        return self.volumes.get(guild_id, 0.5)
    
    def set_volume(self, guild_id, volume):
        volume = max(0.0, min(1.0, volume))
        self.volumes[guild_id] = volume
        return volume
    
    def get_volume_percentage(self, guild_id):
        return int(self.get_volume(guild_id) * 100)


# Keep the same MusicControlView class from your previous code
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
        shuffle_text = "Shuffle: On" if new_mode else "Shuffle: Off"
        
        try:
            await interaction.response.edit_message(view=self)
            if new_mode:
                queue_count = len(self.music_player.queues.get(self.guild_id, []))
                await interaction.followup.send(f"🔄 {shuffle_text} - Shuffled {queue_count} songs!", ephemeral=True)
            else:
                await interaction.followup.send(f"🔄 {shuffle_text}", ephemeral=True)
        except:
            await interaction.followup.send(f"🔄 {shuffle_text}", ephemeral=True)
    
    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.primary, row=1)
    async def repeat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_mode = self.music_player.cycle_repeat_mode(self.guild_id)
        repeat_text = self.music_player.get_repeat_text(self.guild_id)
        
        button.emoji = self.music_player.get_repeat_emoji(self.guild_id)
        
        try:
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"🔁 {repeat_text}", ephemeral=True)
        except:
            await interaction.followup.send(f"🔁 {repeat_text}", ephemeral=True)
    
    @discord.ui.button(emoji="📄", style=discord.ButtonStyle.primary, row=1)
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = self.guild_id
        
        if guild_id not in self.music_player.queues or not self.music_player.queues[guild_id]:
            current = self.music_player.current_songs.get(guild_id)
            if current:
                embed = discord.Embed(
                    title="📋 Music Queue",
                    description=f'🎵 **Now Playing:** {current["title"]}\n\n📄 Queue is empty!',
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
            queue_list += f'🎵 **Now Playing:** {current["title"]}\n\n'
        
        queue_list += "**Upcoming:**\n"
        for i, song in enumerate(self.music_player.queues[guild_id][:8], 1):
            queue_list += f'{i}. {song["title"]}\n'
        
        if len(self.music_player.queues[guild_id]) > 8:
            queue_list += f'\n...and {len(self.music_player.queues[guild_id]) - 8} more songs'

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