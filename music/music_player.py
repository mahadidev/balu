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
        self.music_messages = {}  # Store music control messages for each guild
        self.start_times = {}  # Track when songs started playing
        self.repeat_modes = {}  # Track repeat mode for each guild: 0=off, 1=track, 2=queue
        self.shuffle_modes = {}  # Track shuffle mode for each guild: True/False
        self.volumes = {}  # Track volume for each guild (0.0-1.0)
        self.url_cache = {}  # Cache extracted URLs with timestamp
        
        # yt-dlp options optimized for reliability
        self.ytdl_format_options = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': False,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'source_address': '0.0.0.0',
            'extract_flat': False,
            'retries': 2,
            'fragment_retries': 2,
            'socket_timeout': 8,
            'http_chunk_size': 10485760,
            'cookiefile': None,
            'age_limit': None,
        }
        
        # Options for playlist processing
        self.ytdl_fast_options = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'socket_timeout': 10,
            'retries': 2,
            'default_search': 'ytsearch',
            'ignoreerrors': True,
            'no_check_certificate': True,
            'prefer_insecure': True,
            'age_limit': 999,
            'http_chunk_size': 1048576,  # 1MB chunks
            'fragment_retries': 1,
            'extractor_retries': 1,
            'file_access_retries': 1,
        }
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_format_options)
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
        """Check if cached URL is still valid (not older than 30 minutes)"""
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
    
    async def get_youtube_url(self, search, preserve_playlist=False):
        """Extract YouTube URL from search query"""
        try:
            if search and ('youtube.com' in search or 'youtu.be' in search):
                # Only clean URL if we're not preserving playlist info
                if not preserve_playlist and ('?list=' in search or '&list=' in search):
                    # Extract just the video ID part
                    if 'youtu.be/' in search:
                        video_id = search.split('youtu.be/')[1].split('?')[0].split('&')[0]
                        cleaned_url = f"https://www.youtube.com/watch?v={video_id}"
                    elif 'watch?v=' in search:
                        video_id = search.split('watch?v=')[1].split('&')[0].split('#')[0]
                        cleaned_url = f"https://www.youtube.com/watch?v={video_id}"
                    else:
                        cleaned_url = search
                    return cleaned_url
                else:
                    return search
            else:
                # Search for the song asynchronously
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(f"ytsearch:{search}", download=False))
                if info and 'entries' in info and info['entries']:
                    found_url = info['entries'][0]['webpage_url']
                    return found_url
                return None
        except Exception as e:
            return None

    async def play(self, ctx, query):
        """Play music"""
        # Join voice channel if not connected
        if ctx.guild.id not in self.voice_clients:
            if not await self.join(ctx):
                return

        voice_client = self.voice_clients[ctx.guild.id]
        
        try:
            # Check if it's a playlist URL - detect YouTube Radio, Playlists, etc.
            is_playlist = False
            if 'list=' in query:
                # Extract list ID to check type
                list_id = ''
                if 'list=' in query:
                    list_id = query.split('list=')[1].split('&')[0]
                
                # Check if it's a known playlist type
                if (list_id.startswith('RD') or  # YouTube Radio
                    list_id.startswith('PL') or  # Public Playlist
                    list_id.startswith('UU') or  # User Uploads
                    'playlist?list=' in query):   # Direct playlist URL
                    is_playlist = True
                    
            if is_playlist:
                await self.add_playlist(ctx, query)
            else:
                await self.add_single_song(ctx, query)

        except Exception as e:
            print(f"Play error: {e}")
            await ctx.send('❌ An error occurred while trying to play the song!')

    async def add_single_song(self, ctx, query):
        """Add a single song to queue"""
        # Send immediate feedback
        search_msg = await ctx.send('🔍 Searching for song...')
        
        try:
            # Get YouTube URL
            url = await self.get_youtube_url(query, preserve_playlist=False)
            if not url:
                if hasattr(search_msg, 'edit'):
                    await search_msg.edit(content='❌ Could not find the song!')
                else:
                    await ctx.send('❌ Could not find the song!')
                return

            # Get song info with playable URL (optimized)
            if hasattr(search_msg, 'edit'):
                await search_msg.edit(content='⏳ Getting song info...')
            
            loop = asyncio.get_event_loop()
            # Always use regular ytdl for better reliability
            try:
                print(f"Attempting to extract info from URL: {url}")
                info = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False)),
                    timeout=20.0
                )
                print(f"Extraction successful. Info type: {type(info)}")
                if info:
                    print(f"Info keys: {info.keys() if isinstance(info, dict) else 'Not a dict'}")
            except asyncio.TimeoutError:
                print("Extraction timed out")
                if hasattr(search_msg, 'edit'):
                    await search_msg.edit(content='❌ Extraction timed out!')
                else:
                    await ctx.send('❌ Extraction timed out!')
                return
            except Exception as e:
                print(f"Extraction error: {e}")
                import traceback
                traceback.print_exc()
                if hasattr(search_msg, 'edit'):
                    await search_msg.edit(content=f'❌ Extraction error: {str(e)[:50]}...')
                else:
                    await ctx.send(f'❌ Extraction error: {str(e)[:50]}...')
                return
            
            # Validate info extraction
            if not info:
                print("No info returned from extraction")
                if hasattr(search_msg, 'edit'):
                    await search_msg.edit(content='❌ Could not extract song information!')
                else:
                    await ctx.send('❌ Could not extract song information!')
                return
            
            # Handle entries vs single video
            if 'entries' in info and info['entries']:
                song_info = self.extract_song_info(info['entries'][0], ctx.author.name)
            elif 'entries' not in info:
                song_info = self.extract_song_info(info, ctx.author.name)
            else:
                if hasattr(search_msg, 'edit'):
                    await search_msg.edit(content='❌ Could not find song in results!')
                else:
                    await ctx.send('❌ Could not find song in results!')
                return
                
            self.add_to_queue(ctx.guild.id, song_info)
            
            voice_client = self.voice_clients[ctx.guild.id]
            
            if not voice_client.is_playing():
                # Delete the search message and let play_next show the music interface
                if hasattr(search_msg, 'delete'):
                    try:
                        await search_msg.delete()
                    except:
                        pass
                await self.play_next(ctx)
            else:
                # Just update the search message for queue additions
                final_msg = f'➕ **Added to queue:** {song_info["title"]} - `{song_info["duration"]}`'
                if hasattr(search_msg, 'edit'):
                    await search_msg.edit(content=final_msg)
                else:
                    await ctx.send(final_msg)
                    
        except Exception as e:
            error_msg = f'❌ Error processing song: {str(e)[:50]}...'
            if hasattr(search_msg, 'edit'):
                await search_msg.edit(content=error_msg)
            else:
                await ctx.send(error_msg)

    async def add_playlist(self, ctx, playlist_url):
        """Add playlist to queue"""
        # Join voice channel if not connected
        if ctx.guild.id not in self.voice_clients:
            if not await self.join(ctx):
                return
        
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
                
                # Process FIRST song immediately with parallel attempts for speed
                first_song_played = False
                
                # Try first song with lightweight extraction for speed
                async def try_song_fast(entry, index):
                    try:
                        print(f"Processing first song entry: {entry}")
                        video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                        print(f"Video URL: {video_url}")
                        
                        # Create lightweight song info first for immediate queueing
                        duration_sec = int(entry.get('duration', 0) or 0)
                        song_info = {
                            'title': entry.get('title', 'Unknown Title'),
                            'duration': f"{duration_sec//60}:{duration_sec%60:02d}",
                            'duration_seconds': duration_sec,
                            'thumbnail': entry.get('thumbnail'),
                            'author': entry.get('uploader', entry.get('channel', 'Unknown Artist')),
                            'webpage_url': video_url,
                            'requested_by': ctx.author.name
                        }
                        print(f"Created song info: {song_info['title']}")
                        return song_info, index
                        
                    except Exception as e:
                        print(f"Error with song {index+1}: {e}")
                        import traceback
                        traceback.print_exc()
                        return None, index
                
                # Try first song with fast method
                tasks = [try_song_fast(entry, i) for i, entry in enumerate(entries[:1])]  # Just try first song
                
                # Process first song super fast (no extraction needed)
                try:
                    print(f"Waiting for first song task...")
                    song_info, song_index = await tasks[0]  # Just get the first one
                    print(f"Task completed: song_info={song_info}, song_index={song_index}")
                    
                    if song_info:
                        print(f"Adding song to queue: {song_info['title']}")
                        self.add_to_queue(ctx.guild.id, song_info)
                        
                        # Start playing immediately
                        voice_client = self.voice_clients.get(ctx.guild.id)
                        if voice_client and voice_client.is_connected() and not voice_client.is_playing():
                            print("Starting playback...")
                            await self.play_next(ctx)
                        elif not voice_client or not voice_client.is_connected():
                            print("Voice client not connected, attempting to join...")
                            if await self.join(ctx):
                                await self.play_next(ctx)
                        
                        await ctx.send(f'🎵 **Started playing:** {song_info["title"]}')
                        first_song_played = True
                        
                        # Remove the played song from entries list for background loading
                        entries = entries[1:]  # Remove first song
                    else:
                        print("No song info returned from task")
                            
                except Exception as e:
                    print(f"Error processing first song: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Simple fallback
                    if entries:
                        print("Using fallback method...")
                        entry = entries[0]
                        video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                        duration_sec = int(entry.get('duration', 0) or 0)
                        song_info = {
                            'title': entry.get('title', 'Unknown Title'),
                            'duration': f"{duration_sec//60}:{duration_sec%60:02d}",
                            'duration_seconds': duration_sec,
                            'thumbnail': entry.get('thumbnail'),
                            'author': entry.get('uploader', entry.get('channel', 'Unknown Artist')),
                            'webpage_url': video_url,
                            'requested_by': ctx.author.name
                        }
                        self.add_to_queue(ctx.guild.id, song_info)
                        
                        voice_client = self.voice_clients.get(ctx.guild.id)
                        if voice_client and voice_client.is_connected() and not voice_client.is_playing():
                            await self.play_next(ctx)
                        elif not voice_client or not voice_client.is_connected():
                            if await self.join(ctx):
                                await self.play_next(ctx)
                        
                        await ctx.send(f'🎵 **Started playing:** {song_info["title"]}')
                        first_song_played = True
                        entries = entries[1:]
                
                if not first_song_played:
                    await ctx.send('❌ Could not play any songs from the playlist!')
                    return
                
                # Process remaining songs in background (non-blocking)
                if len(entries) > 0:
                    asyncio.create_task(self.load_remaining_songs(ctx, entries, info.get("title", "Unknown Playlist")))
                
            else:
                await ctx.send('❌ Could not find any songs in the playlist!')
                
        except Exception as e:
            print(f"Playlist error: {e}")
            await ctx.send(f'❌ Error processing playlist: {str(e)[:100]}...')

    async def load_remaining_songs(self, ctx, entries, playlist_title):
        """Load remaining songs in background with parallel processing"""
        added_count = 1  # First song already added
        total_songs = len(entries) + 1
        
        if len(entries) == 0:
            return
            
        await ctx.send(f'⚡ Fast-loading remaining {len(entries)} songs in background...')
        
        async def process_song(entry, ctx_author_name):
            """Process a single song entry (lightweight - no URL extraction)"""
            try:
                # Only get basic info, no URL extraction to save time
                video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                
                # Create song info directly from playlist entry (much faster)
                duration_sec = int(entry.get('duration', 0) or 0)
                song_info = {
                    'title': entry.get('title', 'Unknown Title'),
                    'duration': f"{duration_sec//60}:{duration_sec%60:02d}",
                    'duration_seconds': duration_sec,
                    'thumbnail': entry.get('thumbnail'),
                    'author': entry.get('uploader', entry.get('channel', 'Unknown Artist')),
                    'webpage_url': video_url,
                    'requested_by': ctx_author_name
                    # No URL field - extracted fresh when needed
                }
                return song_info
                
            except Exception as e:
                print(f"Skipping song due to error: {e}")
                return None
        
        # Process songs in batches of 5 for optimal performance
        batch_size = 5
        successfully_added = 0
        
        for i in range(0, len(entries), batch_size):
            batch = entries[i:i + batch_size]
            
            # Process batch in parallel
            tasks = [process_song(entry, ctx.author.name) for entry in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Add successful results to queue
            for result in results:
                if result and not isinstance(result, Exception):
                    self.add_to_queue(ctx.guild.id, result)
                    successfully_added += 1
            
            # Update progress every batch
            current_total = added_count + successfully_added
            if i + batch_size < len(entries):  # Don't show progress for last batch
                await ctx.send(f'⚡ Loaded {current_total}/{total_songs} songs...')
            
            # Small delay between batches to prevent overwhelming
            await asyncio.sleep(0.1)
        
        final_count = added_count + successfully_added
        await ctx.send(f'✅ **Lightning fast! Loaded {final_count} songs from:** {playlist_title}')

    def extract_song_info(self, entry, requested_by):
        """Extract song information from yt-dlp entry (no URL caching)"""
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
            
        title = entry.get('title', 'Unknown Title') if entry else 'Unknown Title'
        duration = entry.get('duration', 0) if entry else 0
        thumbnail = entry.get('thumbnail') if entry else None
        author = entry.get('uploader', entry.get('channel', 'Unknown Artist')) if entry else 'Unknown Artist'
        webpage_url = entry.get('webpage_url', '') if entry else ''
        
        # Format duration
        duration_str = f"{duration//60}:{duration%60:02d}" if duration else "Unknown"
        
        return {
            'title': title,
            'duration': duration_str,
            'duration_seconds': duration,
            'thumbnail': thumbnail,
            'author': author,
            'webpage_url': webpage_url,
            'requested_by': requested_by
            # NOTE: No 'url' field - we extract URLs fresh each time to avoid 403 errors
        }

    def add_to_queue(self, guild_id, song_info):
        """Add song to guild queue"""
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        
        # If shuffle is on and there are already songs in queue, insert at random position
        if self.get_shuffle_mode(guild_id) and self.queues[guild_id]:
            random_index = random.randint(0, len(self.queues[guild_id]))
            self.queues[guild_id].insert(random_index, song_info)
        else:
            self.queues[guild_id].append(song_info)

    async def play_next(self, ctx):
        """Play next song in queue"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.queues or not self.queues[guild_id]:
            await ctx.send('📄 Queue is empty!')
            return

        voice_client = self.voice_clients.get(guild_id)
        if not voice_client or not voice_client.is_connected():
            await ctx.send('❌ Not connected to voice channel! Use `!join` to connect.')
            return

        # Get the song but don't remove it yet
        song_info = self.queues[guild_id][0]
        
        try:
            # Always extract fresh URL just before playing (no caching)
            webpage_url = song_info.get('webpage_url')
            
            if not webpage_url:
                await ctx.send('❌ No webpage URL available for this song!')
                # Remove the bad song and try next
                self.queues[guild_id].pop(0)
                await self.play_next(ctx)
                return
            
            # Check cache first for performance
            cached_audio_url = self.get_cached_url(webpage_url)
            
            if cached_audio_url:
                print(f"🚀 Using cached URL for: {song_info['title']}")
                audio_url = cached_audio_url
            else:
                # Extract fresh URL with faster timeout
                print(f"Extracting fresh URL for: {song_info['title']}")
                try:
                    loop = asyncio.get_event_loop()
                    fresh_info = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: self.ytdl.extract_info(webpage_url, download=False)),
                        timeout=15.0
                    )
                    
                    if not fresh_info:
                        raise Exception("No info extracted")
                    
                    # Get the best audio URL
                    audio_url = fresh_info.get('url')
                    if not audio_url and 'formats' in fresh_info:
                        # Find best audio format
                        for fmt in fresh_info['formats']:
                            if fmt.get('acodec') != 'none' and fmt.get('url'):
                                audio_url = fmt['url']
                                break
                    
                    if not audio_url:
                        raise Exception("No audio URL found")
                    
                    # Cache the URL for future use
                    self.cache_url(webpage_url, audio_url)
                    print(f"✅ Fresh URL extracted successfully for: {song_info['title']}")
                    
                except Exception as e:
                    print(f"❌ Failed to extract fresh URL: {e}")
                    await ctx.send(f'❌ Cannot get audio for "{song_info["title"]}", skipping...')
                    # Remove the bad song and try next
                    self.queues[guild_id].pop(0)
                    await self.play_next(ctx)
                    return
            
            # Create audio source with volume control
            base_source = FFmpegPCMAudio(audio_url, **self.ffmpeg_options)
            volume = self.get_volume(guild_id)
            source = PCMVolumeTransformer(base_source, volume=volume)
            
            # Only remove from queue and set as current after successful setup
            self.queues[guild_id].pop(0)
            self.current_songs[guild_id] = song_info
            
            # Record start time for progress tracking
            self.start_times[guild_id] = time.time()
            
            voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.song_finished(ctx, e), self.bot.loop
            ))

            # Create and send enhanced music interface
            try:
                embed, view = await self.create_music_interface(ctx, song_info, is_playing=True)
                
                # Update or send new music message
                if guild_id in self.music_messages:
                    try:
                        # Try to edit existing message
                        await self.music_messages[guild_id].edit(embed=embed, view=view)
                    except discord.NotFound:
                        # Message was deleted, send new one
                        self.music_messages[guild_id] = await ctx.send(embed=embed, view=view)
                    except discord.HTTPException:
                        # Other error, send new message
                        self.music_messages[guild_id] = await ctx.send(embed=embed, view=view)
                else:
                    # Send new message
                    self.music_messages[guild_id] = await ctx.send(embed=embed, view=view)
            except Exception as interface_error:
                print(f"Interface creation error: {interface_error}")
                import traceback
                traceback.print_exc()
                # Send simple fallback message
                await ctx.send(f'🎵 **Now playing:** {song_info["title"]} - `{song_info["duration"]}`')

        except Exception as e:
            print(f"Playback error: {e}")
            # Only try next song if there are more songs in queue
            if guild_id in self.queues and self.queues[guild_id]:
                await ctx.send(f'❌ Error playing "{song_info.get("title", "Unknown")}", trying next song...')
                await self.play_next(ctx)
            else:
                await ctx.send(f'❌ Error playing "{song_info.get("title", "Unknown")}"!')

    async def song_finished(self, ctx, error=None):
        """Handle when a song finishes"""
        if error:
            print(f"Playback error: {error}")
            # If there was an error, try the next song
            guild_id = ctx.guild.id
            if guild_id in self.queues and self.queues[guild_id]:
                await ctx.send(f'⚠️ Playback error, trying next song...')
            await self.play_next(ctx)
            return
            
        await asyncio.sleep(1)  # Small delay
        
        guild_id = ctx.guild.id
        repeat_mode = self.get_repeat_mode(guild_id)
        current_song = self.current_songs.get(guild_id)
        
        if repeat_mode == 1 and current_song:  # Repeat track
            # Add the same song back to the front of the queue
            if guild_id not in self.queues:
                self.queues[guild_id] = []
            self.queues[guild_id].insert(0, current_song.copy())
        elif repeat_mode == 2 and current_song:  # Repeat queue
            # Add the current song to the end of the queue
            if guild_id not in self.queues:
                self.queues[guild_id] = []
            self.queues[guild_id].append(current_song.copy())
        
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

    async def change_volume(self, ctx, volume_percent):
        """Set volume (0-100)"""
        if volume_percent < 0 or volume_percent > 100:
            await ctx.send('❌ Volume must be between 0 and 100!')
            return
        
        guild_id = ctx.guild.id
        volume = volume_percent / 100.0  # Convert to 0.0-1.0
        self.set_volume(guild_id, volume)
        
        # Update current playing audio if there is one
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

    def get_progress_bar(self, guild_id, song_info):
        """Create a progress bar for the currently playing song"""
        if guild_id not in self.start_times or not song_info.get('duration_seconds'):
            return "⚪⚪⚪⚪⚪⚪⚪⚪⚪⚪ 0:00"
        
        elapsed = time.time() - self.start_times[guild_id]
        total_seconds = song_info['duration_seconds']
        
        if elapsed > total_seconds:
            elapsed = total_seconds
        
        # Calculate progress percentage
        progress = elapsed / total_seconds if total_seconds > 0 else 0
        filled_blocks = int(progress * 10)
        
        # Create progress bar
        bar = "🔵" * filled_blocks + "⚪" * (10 - filled_blocks)
        
        # Format current time
        current_minutes = int(elapsed // 60)
        current_seconds = int(elapsed % 60)
        
        return f"{bar} {current_minutes}:{current_seconds:02d}"

    async def create_music_interface(self, ctx, song_info, is_playing=True):
        """Create enhanced music interface with buttons and embed"""
        guild_id = ctx.guild.id
        
        print(f"Creating interface for guild {guild_id}, song: {song_info.get('title', 'Unknown')}")
        
        # Create minimal embed design
        embed = discord.Embed(color=0x1DB954 if is_playing else 0xFFA500)
        
        # Song title as main description
        description = f"**{song_info['title']}**\n"
        description += f"by {song_info['author']}"
        
        # Add progress bar if playing
        if is_playing and guild_id in self.start_times:
            progress_bar = self.get_progress_bar(guild_id, song_info)
            description += f"\n\n{progress_bar} / {song_info['duration']}"
        else:
            description += f" • {song_info['duration']}"
        
        # Add queue info if available
        queue_count = len(self.queues.get(guild_id, []))
        if queue_count > 0:
            description += f" • {queue_count} in queue"
        
        # Add repeat mode if active
        if self.get_repeat_mode(guild_id) > 0:
            repeat_text = self.get_repeat_text(guild_id).replace("Repeat: ", "")
            description += f" • {repeat_text} mode"
        
        # Add shuffle mode if active
        if self.get_shuffle_mode(guild_id):
            description += f" • Shuffle on"
        
        # Add volume info
        volume_percent = self.get_volume_percentage(guild_id)
        description += f" • Volume {volume_percent}%"
        
        embed.description = description
        
        # Add thumbnail if available
        if song_info.get('thumbnail'):
            embed.set_thumbnail(url=song_info['thumbnail'])
        
        # Create buttons
        view = MusicControlView(self, ctx.guild.id)
        
        # Update repeat and shuffle buttons after view creation
        repeat_mode = self.get_repeat_mode(guild_id)
        shuffle_mode = self.get_shuffle_mode(guild_id)
        
        # Check if music is currently playing for play/pause button
        voice_client = self.voice_clients.get(guild_id)
        is_currently_playing = voice_client and voice_client.is_playing()
        
        for item in view.children:
            if hasattr(item, 'emoji'):
                # Set all buttons to primary (purple) style
                item.style = discord.ButtonStyle.primary
                # Update repeat button emoji
                if str(item.emoji) in ["🔁", "🔂"]:
                    item.emoji = self.get_repeat_emoji(guild_id)
        
        return embed, view

    def get_repeat_mode(self, guild_id):
        """Get current repeat mode for a guild"""
        return self.repeat_modes.get(guild_id, 0)
    
    def cycle_repeat_mode(self, guild_id):
        """Cycle through repeat modes: 0=off, 1=track, 2=queue"""
        current_mode = self.repeat_modes.get(guild_id, 0)
        new_mode = (current_mode + 1) % 3
        self.repeat_modes[guild_id] = new_mode
        return new_mode
    
    def get_repeat_emoji(self, guild_id):
        """Get emoji for current repeat mode"""
        mode = self.get_repeat_mode(guild_id)
        if mode == 0:
            return "🔁"  # Off
        elif mode == 1:
            return "🔂"  # Repeat track
        else:
            return "🔁"  # Repeat queue
    
    def get_repeat_text(self, guild_id):
        """Get text description for current repeat mode"""
        mode = self.get_repeat_mode(guild_id)
        if mode == 0:
            return "Repeat: Off"
        elif mode == 1:
            return "Repeat: Track"
        else:
            return "Repeat: Queue"
    
    def get_shuffle_mode(self, guild_id):
        """Get current shuffle mode for a guild"""
        return self.shuffle_modes.get(guild_id, False)
    
    def toggle_shuffle_mode(self, guild_id):
        """Toggle shuffle mode for a guild"""
        current_mode = self.shuffle_modes.get(guild_id, False)
        new_mode = not current_mode
        self.shuffle_modes[guild_id] = new_mode
        
        # If turning shuffle on, shuffle the current queue
        if new_mode and guild_id in self.queues and self.queues[guild_id]:
            random.shuffle(self.queues[guild_id])
        
        return new_mode
    
    def get_shuffle_emoji(self, guild_id):
        """Get emoji for current shuffle mode"""
        return "🔀" if self.get_shuffle_mode(guild_id) else "🔀"
    
    def get_shuffle_text(self, guild_id):
        """Get text description for current shuffle mode"""
        return "Shuffle: On" if self.get_shuffle_mode(guild_id) else "Shuffle: Off"
    
    def get_volume(self, guild_id):
        """Get current volume for a guild (0.0-1.0)"""
        return self.volumes.get(guild_id, 0.5)  # Default 50%
    
    def set_volume(self, guild_id, volume):
        """Set volume for a guild (0.0-1.0)"""
        volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
        self.volumes[guild_id] = volume
        return volume
    
    def get_volume_percentage(self, guild_id):
        """Get volume as percentage (0-100)"""
        return int(self.get_volume(guild_id) * 100)

class MusicControlView(discord.ui.View):
    def __init__(self, music_player, guild_id):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.music_player = music_player
        self.guild_id = guild_id
        
        # Update repeat button will be done after view creation
    
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
            # Clear queue
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
            
            # Clear queue and current song
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
        
        # Keep button style as primary (purple)
        
        # Update the message with new view
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
        
        # Update button emoji
        button.emoji = self.music_player.get_repeat_emoji(self.guild_id)
        
        # Keep button style as primary (purple)
        
        # Update the message with new view
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
        
        # Update current playing audio
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
        
        # Update current playing audio
        voice_client = self.music_player.voice_clients.get(self.guild_id)
        if voice_client and voice_client.source and hasattr(voice_client.source, 'volume'):
            voice_client.source.volume = volume_decimal
        
        await interaction.response.send_message(f"🔊 Volume set to {new_volume}%", ephemeral=True)