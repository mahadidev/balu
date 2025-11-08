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
        self.song_history = {}  # Track previous songs for each guild
        
        # ULTRA FAST yt-dlp options - optimized for VPS stability
        self.ytdl_fast_options = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extract_flat': False,
            'socket_timeout': 15,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3,
            'ignoreerrors': True,
            'no_check_certificate': True,
            'prefer_insecure': False,
            'nocheckcertificate': True,
            'cachedir': False,
            'no_cache_dir': True,
            'rm_cache_dir': True,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_music', 'android_embedded', 'android'],
                    'player_skip': ['configs', 'webpage'],
                    'skip': ['hls', 'dash']
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'X-YouTube-Client-Name': '21',
                'X-YouTube-Client-Version': '6.0',
            },
        }
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -reconnect_at_eof 1 -multiple_requests 1',
            'options': '-vn -bufsize 512k -thread_queue_size 1024'
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
            if ctx.guild.id in self.song_history:
                del self.song_history[ctx.guild.id]
                
            await ctx.send('👋 Left voice channel!')
        else:
            await ctx.send('❌ Not connected to a voice channel!')

    async def get_audio_url_ultra_fast(self, query):
        """ULTRA FAST audio URL extraction with VPS bot detection bypass"""
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
            
            # Try multiple extraction methods to bypass bot detection
            extraction_methods = [
                self.ytdl_fast,
                self.create_fallback_ytdl(),
                self.create_mobile_ytdl()
            ]
            
            for i, ytdl_instance in enumerate(extraction_methods):
                try:
                    timeout = 8.0 + (i * 2)  # Increase timeout for each attempt
                    
                    info = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: ytdl_instance.extract_info(query, download=False)),
                        timeout=timeout
                    )
                    
                    if not info:
                        continue
                    
                    # Get the entry
                    if 'entries' in info:
                        if not info['entries']:
                            continue
                        entry = info['entries'][0]
                    else:
                        entry = info
                    
                    # Get the audio URL - prioritize direct URLs
                    url = entry.get('url')
                    if not url:
                        # Quick format search
                        if 'formats' in entry:
                            formats = entry['formats'][:8]  # Check more formats on VPS
                            for fmt in formats:
                                if fmt.get('acodec') != 'none' and fmt.get('url'):
                                    url = fmt['url']
                                    break
                    
                    if not url:
                        continue
                    
                    # Get basic title
                    title = entry.get('title', 'Unknown Title')
                    
                    # Cache the result
                    self.url_cache[query] = {
                        'url': url,
                        'title': title,
                        'timestamp': datetime.now()
                    }
                    
                    print(f"Successfully extracted using method {i+1}: {title}")
                    return url, title
                    
                except Exception as e:
                    print(f"Extraction method {i+1} failed: {e}")
                    continue
            
            print(f"All extraction methods failed for: {query}")
            return None, None
            
        except Exception as e:
            print(f"Critical error getting audio URL: {e}")
            return None, None
    
    def create_fallback_ytdl(self):
        """Create fallback yt-dlp instance for bot detection bypass"""
        fallback_options = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extract_flat': False,
            'socket_timeout': 20,
            'retries': 2,
            'ignoreerrors': True,
            'no_check_certificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'android_embedded'],
                    'player_skip': ['configs']
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        return yt_dlp.YoutubeDL(fallback_options)
    
    def create_mobile_ytdl(self):
        """Create mobile yt-dlp instance as last resort"""
        mobile_options = {
            'format': 'best[height<=480]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'socket_timeout': 25,
            'retries': 1,
            'ignoreerrors': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
                'Accept': '*/*',
            }
        }
        return yt_dlp.YoutubeDL(mobile_options)

    async def play(self, ctx, query, related=False):
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
            await self.handle_single_song(ctx, query, voice_client, related=related)

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

    def generate_smart_related_songs(self, title, query):
        """Generate related song suggestions using smart keyword matching"""
        related_songs = []
        
        # Analyze the song to determine genre/style
        title_lower = title.lower()
        query_lower = query.lower()
        
        # Extract year if present
        import re
        year_match = re.search(r'20\d{2}', title)
        year = year_match.group() if year_match else "2024"
        
        # Language/Region detection
        if any(word in title_lower for word in ['bangla', 'bengali', 'bangladesh']):
            related_songs.extend([
                "Amar Shonar Bangla",
                "Ekla Cholo Re", 
                "Chol Rabi Chole Jabo",
                "Ami Banglay Gaan Gai"
            ])
        
        elif any(word in title_lower for word in ['hindi', 'bollywood', 'bhangra']):
            related_songs.extend([
                "Tum Hi Ho",
                "Kal Ho Naa Ho",
                "Gerua",
                "Dil Diyan Gallan"
            ])
            
        # Genre detection
        elif any(word in title_lower for word in ['rock', 'metal', 'guitar']):
            related_songs.extend([
                "Bohemian Rhapsody",
                "Sweet Child O Mine",
                "Hotel California",
                "Stairway to Heaven"
            ])
            
        elif any(word in title_lower for word in ['pop', 'dance', 'party']):
            related_songs.extend([
                "Shape of You",
                "Blinding Lights", 
                "As It Was",
                "Anti Hero"
            ])
            
        elif any(word in title_lower for word in ['rap', 'hip hop', 'drake', 'eminem']):
            related_songs.extend([
                "Gods Plan",
                "Lose Yourself",
                "HUMBLE",
                "Sicko Mode"
            ])
            
        elif any(word in title_lower for word in ['love', 'romantic', 'heart']):
            related_songs.extend([
                "Perfect Ed Sheeran",
                "All of Me",
                "Thinking Out Loud",
                "A Thousand Years"
            ])
            
        # Default popular songs if no specific genre detected
        if not related_songs:
            related_songs.extend([
                "Heat Waves",
                "Stay",
                "Levitating",
                "Watermelon Sugar",
                "Bad Habits",
                "Peaches"
            ])
        
        return related_songs[:6]  # Return max 6 suggestions

    async def load_related_songs(self, ctx, original_query, original_title):
        """Load related songs using smart keyword matching - IMPROVED VERSION"""
        try:
            guild_id = ctx.guild.id
            loaded_count = 0
            
            # Smart keyword matching based on song characteristics
            related_songs = self.generate_smart_related_songs(original_title, original_query)
            print(f"Generated related songs for '{original_title}': {related_songs}")
            
            # Search for songs individually for better accuracy
            for song_query in related_songs[:3]:  # Only search for top 3 to avoid timeout
                try:
                    search_query = f"ytsearch1:{song_query}"
                    print(f"Searching for: {search_query}")
                    
                    loop = asyncio.get_event_loop()
                    info = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda sq=search_query: self.ytdl_fast.extract_info(sq, download=False)),
                        timeout=4.0  # Increased timeout
                    )
                    
                    if info and 'entries' in info and info['entries'] and info['entries'][0]:
                        entry = info['entries'][0]
                        print(f"Found: {entry.get('title', 'Unknown')}")
                        
                        # Add song to queue quickly
                        song_info = {
                            'title': entry.get('title', 'Unknown Title'),
                            'duration': entry.get('duration_string', 'Unknown'),
                            'duration_seconds': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail'),
                            'author': entry.get('uploader', 'Unknown Artist'),
                            'webpage_url': f"https://www.youtube.com/watch?v={entry['id']}",
                            'url': None,  # Will be resolved when playing
                            'video_id': entry['id'],
                            'requested_by': ctx.author.name
                        }
                        
                        self.add_to_queue(guild_id, song_info)
                        loaded_count += 1
                        
                        # Small delay between searches
                        await asyncio.sleep(0.3)
                        
                    else:
                        print(f"No results for: {song_query}")
                        
                except Exception as e:
                    print(f"Error searching for '{song_query}': {e}")
                    continue
            
            if loaded_count > 0:
                await ctx.send(f'✅ **Found {loaded_count} related songs and added them to queue!**')
            else:
                print("No related songs found, trying fallback...")
                # Try fallback with popular songs
                await self.load_fallback_songs(ctx, guild_id)
                
        except Exception as e:
            print(f"Error loading related songs: {e}")
            # Try fallback instead of showing warning
            try:
                await self.load_fallback_songs(ctx, guild_id)
            except Exception as fallback_error:
                print(f"Fallback also failed: {fallback_error}")
                await ctx.send('⚠️ **Had trouble finding related songs, but your song is playing!**')

    async def load_fallback_songs(self, ctx, guild_id):
        """Load popular fallback songs when related search fails"""
        try:
            # Use very simple, popular song names that should always work
            fallback_songs = [
                "Shape of You",
                "Blinding Lights", 
                "Heat Waves"
            ]
            
            loaded_count = 0
            for song_query in fallback_songs:
                try:
                    search_query = f"ytsearch1:{song_query}"
                    
                    loop = asyncio.get_event_loop()
                    info = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: self.ytdl_fast.extract_info(search_query, download=False)),
                        timeout=4.0  # Slightly longer timeout for fallback
                    )
                    
                    if info and 'entries' in info and info['entries'] and info['entries'][0]:
                        entry = info['entries'][0]
                        
                        song_info = {
                            'title': entry.get('title', 'Unknown Title'),
                            'duration': entry.get('duration_string', 'Unknown'),
                            'duration_seconds': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail'),
                            'author': entry.get('uploader', 'Unknown Artist'),
                            'webpage_url': f"https://www.youtube.com/watch?v={entry['id']}",
                            'url': None,
                            'video_id': entry['id'],
                            'requested_by': ctx.author.name
                        }
                        
                        self.add_to_queue(guild_id, song_info)
                        loaded_count += 1
                        
                        await asyncio.sleep(0.3)
                        
                except Exception as e:
                    print(f"Fallback search failed for '{song_query}': {e}")
                    continue
            
            if loaded_count > 0:
                await ctx.send(f'✅ **Added {loaded_count} popular songs to queue!**')
            else:
                await ctx.send('⚠️ **Could not find related songs at the moment. Try manually adding songs!**')
                
        except Exception as e:
            print(f"Fallback system failed: {e}")
            await ctx.send('⚠️ **Had trouble finding related songs, but your song is playing!**')

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
                                
                        except Exception:
                            continue
                    
                    if loaded_count > 0:
                        await ctx.send(f'✅ **Added {loaded_count} more songs from YouTube Radio**')
                        
        except Exception:
            # Silent failure - we already have the first song playing
            pass

    async def handle_single_song(self, ctx, query, voice_client, related=False):
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
                
                # If --related flag is used, load similar songs in background
                if related:
                    await ctx.send(f'🎵 **Now Playing:** {title}\n🔍 **Finding related songs...**')
                    asyncio.create_task(self.load_related_songs(ctx, query, title))
            else:
                await search_msg.edit(content=f'✅ **Added to queue:** {title}')
                
                # If --related flag is used, load similar songs in background
                if related:
                    asyncio.create_task(self.load_related_songs(ctx, query, title))
                
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
            # If no URL is stored, extract it now
            if not current_song.get('url'):
                if current_song.get('video_id'):
                    video_url = f"https://www.youtube.com/watch?v={current_song['video_id']}"
                    audio_url, title = await self.get_audio_url_ultra_fast(video_url)
                    current_song['url'] = audio_url
                elif current_song.get('webpage_url'):
                    audio_url, title = await self.get_audio_url_ultra_fast(current_song['webpage_url'])
                    current_song['url'] = audio_url
            
            # Use the URL for ULTRA FAST playback
            source = PCMVolumeTransformer(
                FFmpegPCMAudio(current_song['url'], **self.ffmpeg_options),
                volume=self.get_volume(guild_id)
            )
            
            # Add current song to history before changing it
            if guild_id in self.current_songs:
                old_song = self.current_songs[guild_id]
                if guild_id not in self.song_history:
                    self.song_history[guild_id] = []
                self.song_history[guild_id].append(old_song.copy())
                
                # Keep only last 10 songs in history
                if len(self.song_history[guild_id]) > 10:
                    self.song_history[guild_id].pop(0)
            
            # Remove from queue and set as current
            self.queues[guild_id].pop(0)
            self.current_songs[guild_id] = current_song
            self.start_times[guild_id] = time.time()
            
            def after_play(error):
                if error:
                    print(f"Playback error: {error}")
                    # Check if it's a network error that we can retry
                    error_str = str(error).lower()
                    if any(keyword in error_str for keyword in ['connection', 'network', 'timeout', 'keepalive', 'invalid argument']):
                        print("Network error detected, will attempt to continue with next song")
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
            print(f"Song finished with error: {error}")
            error_str = str(error).lower()
            # If it's a network error, send a brief notice
            if any(keyword in error_str for keyword in ['connection', 'network', 'timeout', 'keepalive', 'invalid argument']):
                try:
                    await ctx.send('🔄 **Connection issue detected, continuing with next song...**')
                except:
                    pass  # Don't fail if we can't send the message
        
        await asyncio.sleep(0.5)
        
        guild_id = ctx.guild.id
        
        voice_client = self.voice_clients.get(guild_id)
        if not voice_client or not voice_client.is_connected():
            return
        
        repeat_mode = self.get_repeat_mode(guild_id)
        current_song = self.current_songs.get(guild_id)
        
        # Handle repeat modes
        if repeat_mode == 1 and current_song:
            # Repeat current track
            if guild_id not in self.queues:
                self.queues[guild_id] = []
            self.queues[guild_id].insert(0, current_song.copy())
        elif repeat_mode == 2 and current_song:
            # Add current track to end of queue
            if guild_id not in self.queues:
                self.queues[guild_id] = []
            self.queues[guild_id].append(current_song.copy())
        
        # Play next song
        if guild_id in self.queues and self.queues[guild_id]:
            next_song = self.queues[guild_id][0]
            await self.play_instant(ctx, next_song)
        else:
            # No more songs in queue
            try:
                await ctx.send('🎵 **Queue finished! Add more songs or use `--related` to find similar music.**')
            except:
                pass

    def add_to_queue(self, guild_id, song_info):
        """Add song to guild queue"""
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        
        if self.get_shuffle_mode(guild_id) and self.queues[guild_id]:
            random_index = random.randint(0, len(self.queues[guild_id]))
            self.queues[guild_id].insert(random_index, song_info)
        else:
            self.queues[guild_id].append(song_info)

    async def skip(self, ctx):
        """Skip current song"""
        voice_client = self.voice_clients.get(ctx.guild.id)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await ctx.send('⏭️ Skipped!')
        else:
            await ctx.send('❌ No music is playing!')

    async def previous(self, ctx):
        """Play previous song"""
        guild_id = ctx.guild.id
        
        # Check if there's a song history
        if guild_id not in self.song_history or not self.song_history[guild_id]:
            await ctx.send('❌ No previous songs in history!')
            return
        
        voice_client = self.voice_clients.get(guild_id)
        if not voice_client:
            await ctx.send('❌ Not connected to a voice channel!')
            return
        
        # Get the last song from history
        previous_song = self.song_history[guild_id].pop()
        
        # Add current song back to the front of queue if it exists
        if guild_id in self.current_songs:
            current_song = self.current_songs[guild_id]
            if guild_id not in self.queues:
                self.queues[guild_id] = []
            self.queues[guild_id].insert(0, current_song.copy())
        
        # Add previous song to front of queue
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        self.queues[guild_id].insert(0, previous_song)
        
        # Stop current playback to trigger next song
        if voice_client.is_playing():
            voice_client.stop()
        else:
            # If nothing is playing, start the previous song directly
            await self.play_instant(ctx, previous_song)
        
        await ctx.send('⏪ Playing previous song!')

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
        return self.volumes.get(guild_id, 0.2)  # Default 20% volume
    
    def set_volume(self, guild_id, volume):
        volume = max(0.0, min(1.0, volume))
        self.volumes[guild_id] = volume
        return volume
    
    def get_volume_percentage(self, guild_id):
        return int(self.get_volume(guild_id) * 100)  # Returns 20% by default
    
    def get_shuffle_text(self, guild_id):
        """Get shuffle mode text"""
        return "Shuffle: On" if self.get_shuffle_mode(guild_id) else "Shuffle: Off"


# Keep the same MusicControlView class from your previous code
class MusicControlView(discord.ui.View):
    def __init__(self, music_player, guild_id):
        super().__init__(timeout=300)
        self.music_player = music_player
        self.guild_id = guild_id
    
    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.primary, row=0)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = self.guild_id
        
        # Check if there's a song history
        if guild_id not in self.music_player.song_history or not self.music_player.song_history[guild_id]:
            await interaction.response.send_message('❌ No previous songs in history!', ephemeral=True)
            return
        
        voice_client = self.music_player.voice_clients.get(guild_id)
        if not voice_client:
            await interaction.response.send_message('❌ Not connected to a voice channel!', ephemeral=True)
            return
        
        # Get the last song from history
        previous_song = self.music_player.song_history[guild_id].pop()
        
        # Add current song back to the front of queue if it exists
        if guild_id in self.music_player.current_songs:
            current_song = self.music_player.current_songs[guild_id]
            if guild_id not in self.music_player.queues:
                self.music_player.queues[guild_id] = []
            self.music_player.queues[guild_id].insert(0, current_song.copy())
        
        # Add previous song to front of queue
        if guild_id not in self.music_player.queues:
            self.music_player.queues[guild_id] = []
        self.music_player.queues[guild_id].insert(0, previous_song)
        
        # Stop current playback to trigger next song
        if voice_client.is_playing():
            voice_client.stop()
        
        await interaction.response.send_message('⏪ Playing previous song!', ephemeral=True)
    
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
            if self.guild_id in self.music_player.song_history:
                del self.music_player.song_history[self.guild_id]
                
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