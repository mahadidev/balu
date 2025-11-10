import discord
import wavelink
import asyncio
import os
from discord.ext import commands
from typing import cast

# Import our modular components
from .playlist_manager import PlaylistManager
from .track_history import TrackHistory
from .controls import MusicControlView

class MusicBot(commands.Cog):
    """Music bot using Wavelink and Lavalink with modular structure"""
    
    def __init__(self, bot):
        self.bot = bot
        # Initialize modular components
        self.playlist_manager = PlaylistManager()
        self.track_history = TrackHistory()
        # Track manual navigation to prevent auto-play interference
        self.manual_navigation = {}  # guild_id -> bool
        
    async def setup_hook(self):
        """Connect to Lavalink server"""
        try:
            # Get Lavalink mode (server or local)
            lavalink_mode = os.getenv("LAVALINK_MODE", "server").lower()
            
            if lavalink_mode == "local":
                lavalink_uri = os.getenv("LAVALINK_LOCAL_URI", "http://localhost:2333")
                lavalink_password = os.getenv("LAVALINK_LOCAL_PASSWORD", "youshallnotpass")
                print(f"🔧 Using LOCAL Lavalink: {lavalink_uri}")
            else:
                lavalink_uri = os.getenv("LAVALINK_SERVER_URI", "http://185.210.144.147:2333")
                lavalink_password = os.getenv("LAVALINK_SERVER_PASSWORD", "youshallnotpass")
                print(f"🌐 Using SERVER Lavalink: {lavalink_uri}")
            
            nodes = [wavelink.Node(uri=lavalink_uri, password=lavalink_password)]
            await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=100)
            print("✅ Connected to Lavalink server")
        except Exception as e:
            print(f"❌ Failed to connect to Lavalink: {e}")
    
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        """Called when the Wavelink node has finished connecting"""
        print(f"🎵 Wavelink Node: {payload.node!r} | Resumed: {payload.resumed}")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """Called when a track starts playing"""
        player: wavelink.Player | None = payload.player
        if not player:
            return

        track: wavelink.Playable = payload.track
        
        # Check if we're going backwards
        going_backwards = self.track_history.is_going_backwards(player.guild.id)
        
        # Add track to history only if we're not going backwards
        if not going_backwards:
            self.track_history.add_to_history(player.guild.id, track)
            
            # Update playlist position for tracking
            self.playlist_manager.update_playlist_position(player.guild.id, track)
        else:
            # Reset the backwards flag
            self.track_history.set_going_backwards(player.guild.id, False)

        embed = discord.Embed(
            title=f"**{track.title}**",
            description=f"by {track.author}",
            color=0x1DB954
        )
        
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        
        # Row 1: Duration, Source, Volume
        embed.add_field(name="⏱️ Duration", value=self.format_time(track.length), inline=True)
        source_display = getattr(track, 'search_source', track.source.title() if track.source else 'Unknown')
        embed.add_field(name="📺 Source", value=source_display, inline=True)
        embed.add_field(name="🔊 Volume", value=f"{player.volume}%", inline=True)
        
        # Row 2: Requested By, Position (and empty field to complete the row)
        if hasattr(track, 'requester') and track.requester:
            embed.add_field(name="🎧 Requested By", value=track.requester.mention, inline=True)
        else:
            embed.add_field(name="🎧 Requested By", value="Unknown", inline=True)
        
        # Show position in playlist if available
        current_pos, total_tracks = self.playlist_manager.get_current_position_info(player.guild.id)
        if current_pos and total_tracks:
            embed.add_field(name="📊 Position", value=f"{current_pos}/{total_tracks}", inline=True)
        else:
            embed.add_field(name="📊 Position", value="1/1" if not player.queue else f"1/{len(player.queue) + 1}", inline=True)
        
        # Empty field to complete the row of 3
        embed.add_field(name="​", value="​", inline=True)
        
        # Don't send controls from track start event - only from play commands
        # This prevents duplicate controls when playing playlists
        print("🎵 Track started - controls handled by play command")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Called when a track ends"""
        player: wavelink.Player | None = payload.player
        if not player:
            return
        
        # Check if manual navigation is active (skip auto-play)
        if self.manual_navigation.get(player.guild.id, False):
            print(f"🎯 Skipping auto-play - manual navigation mode active")
            # Reset manual navigation flag
            self.manual_navigation[player.guild.id] = False
            # Don't auto-play next track when manually navigating
            return
        
        # Check if repeat mode is enabled for current track
        if hasattr(player, 'repeat_mode') and getattr(player, 'repeat_mode', False):
            if payload.track:
                try:
                    await player.play(payload.track)
                    print(f"🔄 Repeating track: {payload.track.title}")
                    return
                except Exception as e:
                    print(f"❌ Failed to repeat track: {e}")
        
        # Check if there are tracks in the queue to play next
        if player.queue:
            try:
                next_track = await player.queue.get_wait()
                
                # Update playlist position BEFORE playing (for proper tracking)
                if self.playlist_manager.has_playlist(player.guild.id):
                    self.playlist_manager.move_to_next_position(player.guild.id)
                    print(f"🎯 Moving to next position in playlist")
                
                # Play the next track
                await player.play(next_track)
                
                print(f"✅ Auto-playing next track: {next_track.title}")
            except Exception as e:
                print(f"❌ Failed to play next track: {e}")
        else:
            # Check if we have a playlist and can move to the next track
            if self.playlist_manager.has_playlist(player.guild.id):
                next_playlist_track = self.playlist_manager.get_next_in_playlist(player.guild.id)
                if next_playlist_track:
                    try:
                        # Update playlist position
                        self.playlist_manager.move_to_next_position(player.guild.id)
                        
                        # Repopulate queue with remaining playlist tracks
                        remaining_tracks = self.playlist_manager.get_remaining_tracks(player.guild.id)
                        for track in remaining_tracks:
                            await player.queue.put_wait(track)
                        print(f"🔄 Repopulated queue with {len(remaining_tracks)} remaining playlist tracks")
                        
                        # Play the next track from playlist
                        await player.play(next_playlist_track)
                        print(f"✅ Auto-playing next playlist track: {next_playlist_track.title}")
                        return
                    except Exception as e:
                        print(f"❌ Failed to play next playlist track: {e}")
            
            # If no queue and no playlist tracks, disconnect after a delay
            await asyncio.sleep(300)  # Wait 5 minutes
            if not player.queue and not player.playing:
                await player.disconnect()

    def format_time(self, milliseconds: int) -> str:
        """Format milliseconds to MM:SS or HH:MM:SS"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        hours = minutes // 60
        
        if hours > 0:
            return f"{hours}:{minutes%60:02d}:{seconds%60:02d}"
        else:
            return f"{minutes}:{seconds%60:02d}"

    def create_thumbnail_grid(self, tracks: list, max_thumbnails: int = 4) -> str:
        """Create a grid of thumbnails for multiple tracks"""
        thumbnails = []
        for track in tracks[:max_thumbnails]:
            if hasattr(track, 'artwork') and track.artwork:
                thumbnails.append(track.artwork)
        
        if not thumbnails:
            return None
        
        # For Discord embeds, we can only set one thumbnail, but we can create a collage URL
        # For now, return the first thumbnail. In the future, you could create a collage service
        return thumbnails[0]

    async def get_player(self, interaction: discord.Interaction) -> wavelink.Player:
        """Get or create a player for the guild"""
        player: wavelink.Player | None = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            try:
                player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
            except AttributeError:
                raise discord.ApplicationCommandError("You must be in a voice channel to use music commands!")
            except discord.ClientException:
                raise discord.ApplicationCommandError("I couldn't connect to your voice channel!")
        
        # Store the text channel for messages
        player.message_channel = interaction.channel
        return player

    async def search_tracks(self, query: str) -> list[wavelink.Playable]:
        """Search for tracks using LavaSrc provider priority: Spotify -> SoundCloud -> YouTube"""
        
        # If it's a URL, search directly
        if query.startswith(('http://', 'https://')):
            tracks = await wavelink.Playable.search(query)
            if tracks:
                # Add search source info for URLs
                for track in tracks:
                    if hasattr(track, 'uri') and track.uri:
                        if 'spotify.com' in track.uri:
                            track.search_source = "Spotify"
                        elif 'soundcloud.com' in track.uri:
                            track.search_source = "SoundCloud"
                        elif 'youtube.com' in track.uri or 'youtu.be' in track.uri:
                            track.search_source = "YouTube"
                        else:
                            track.search_source = "URL"
                return tracks
        
        # Use LavaSrc provider order: Spotify first, then SoundCloud, then YouTube
        # LavaSrc will handle the priority automatically based on our configuration
        try:
            tracks = await wavelink.Playable.search(query)  # Let LavaSrc handle the search order
            if tracks:
                # Determine which source was used and add custom attribute
                search_source = "Spotify"  # Default assumption (Spotify-only mode)
                
                # Check if this was likely found via Spotify by analyzing track properties
                for track in tracks:
                    # Check various properties to determine the search source
                    if hasattr(track, 'uri') and track.uri:
                        if 'spotify:' in track.uri or 'spotify.com' in track.uri:
                            search_source = "Spotify"
                        elif 'soundcloud.com' in track.uri:
                            search_source = "SoundCloud"
                    elif hasattr(track, 'identifier') and track.identifier:
                        # Check if identifier looks like Spotify format
                        if track.identifier.startswith('sp'):
                            search_source = "Spotify"
                        elif track.identifier.startswith('sc'):
                            search_source = "SoundCloud"
                    
                    # Add custom attribute to store the search source
                    track.search_source = search_source
                
                print(f"✅ Found tracks using {search_source} (streaming via {tracks[0].source.title() if tracks[0].source else 'Unknown'})")
                return tracks
        except Exception as e:
            print(f"❌ LavaSrc search failed: {e}")
        
        # No fallback - Spotify only
        print(f"❌ No tracks found - Spotify only mode")
        return []

    @discord.app_commands.command(name="play", description="Play a song")
    @discord.app_commands.describe(query="Song name, artist, or URL")
    async def play_command(self, interaction: discord.Interaction, query: str):
        """Play a song"""
        try:
            await interaction.response.defer()
            
            player = await self.get_player(interaction)
            tracks = await self.search_tracks(query)
            
            if not tracks:
                await interaction.followup.send("❌ No tracks found!", ephemeral=True)
                return
            
            # Check if it's a playlist (multiple tracks from URL)
            if len(tracks) > 1 and query.startswith(('http://', 'https://')):
                # Handle playlist
                first_track = tracks[0]
                
                # Set requester for all tracks
                for track in tracks:
                    track.requester = interaction.user
                
                # Set the playlist order for proper navigation
                self.playlist_manager.set_playlist_order(interaction.guild.id, tracks)
                
                if player.playing:
                    # Add all tracks to queue
                    for track in tracks:
                        await player.queue.put_wait(track)
                    
                    # Create playlist embed with thumbnails
                    embed = discord.Embed(
                        title=f"✅ Playlist Added to Queue",
                        description=f"**{len(tracks)} tracks** added to queue",
                        color=0x1DB954
                    )
                    
                    # Show thumbnails for up to 4 tracks from playlist
                    playlist_tracks = tracks[:4]
                    if playlist_tracks and any(hasattr(track, 'artwork') and track.artwork for track in playlist_tracks):
                        thumbnail_urls = []
                        for track in playlist_tracks:
                            if hasattr(track, 'artwork') and track.artwork:
                                thumbnail_urls.append(f"[🖼️]({track.artwork})")
                        if thumbnail_urls:
                            embed.add_field(
                                name="🎨 Track Thumbnails",
                                value=" ".join(thumbnail_urls[:4]),
                                inline=False
                            )
                    
                    # Set main thumbnail to first track
                    if tracks[0].artwork:
                        embed.set_thumbnail(url=tracks[0].artwork)
                    
                    await interaction.followup.send(embed=embed)
                else:
                    # Play first track and queue the rest
                    await player.play(first_track)
                    for track in tracks[1:]:
                        await player.queue.put_wait(track)
                    
                    # Create the now playing embed with playlist info
                    embed = discord.Embed(title=f"**{first_track.title}**", description=f"by {first_track.author}", color=0x1DB954)
                    
                    # Row 1: Duration, Source, Volume
                    embed.add_field(name="⏱️ Duration", value=self.format_time(first_track.length), inline=True)
                    source_display = getattr(first_track, 'search_source', first_track.source.title() if first_track.source else 'Unknown')
                    embed.add_field(name="📺 Source", value=source_display, inline=True)
                    embed.add_field(name="🔊 Volume", value=f"{player.volume}%", inline=True)
                    
                    # Row 2: Requested By, Position, Playlist Info
                    embed.add_field(name="🎧 Requested By", value=interaction.user.mention, inline=True)
                    embed.add_field(name="📊 Position", value=f"1/{len(tracks)}", inline=True)
                    if len(tracks) > 1:
                        embed.add_field(name="🎶 Playlist", value=f"{len(tracks)-1} in queue", inline=True)
                    else:
                        embed.add_field(name="​", value="​", inline=True)
                    
                    # Add control buttons - send only once here
                    view = MusicControlView(self, interaction.guild_id)
                    await interaction.followup.send(embed=embed, view=view)
            else:
                # Handle single track
                track = tracks[0]
                track.requester = interaction.user  # Set requester for single track
                
                if player.playing:
                    await player.queue.put_wait(track)
                    await interaction.followup.send(f"✅ Added to queue: **{track.title}** by {track.author}")
                else:
                    await player.play(track)
                    # For single tracks, also set them as a "playlist" of one for navigation consistency
                    self.playlist_manager.set_playlist_order(interaction.guild.id, [track])
                    
                    # Send controls for single track
                    embed = discord.Embed(title=f"**{track.title}**", description=f"by {track.author}", color=0x1DB954)
                    
                    # Row 1: Duration, Source, Volume
                    embed.add_field(name="⏱️ Duration", value=self.format_time(track.length), inline=True)
                    source_display = getattr(track, 'search_source', track.source.title() if track.source else 'Unknown')
                    embed.add_field(name="📺 Source", value=source_display, inline=True)
                    embed.add_field(name="🔊 Volume", value=f"{player.volume}%", inline=True)
                    
                    # Row 2: Requested By, Position, Empty field
                    embed.add_field(name="🎧 Requested By", value=interaction.user.mention, inline=True)
                    embed.add_field(name="📊 Position", value="1/1", inline=True)
                    embed.add_field(name="​", value="​", inline=True)
                    
                    if track.artwork:
                        embed.set_thumbnail(url=track.artwork)
                    
                    view = MusicControlView(self, interaction.guild_id)
                    await interaction.followup.send(embed=embed, view=view)
                
        except discord.ApplicationCommandError as e:
            print(f"❌ Application command error: {e}")
            try:
                await interaction.followup.send(f"❌ {e}", ephemeral=True)
            except:
                print(f"❌ Failed to send error message: {e}")
        except Exception as e:
            print(f"❌ Unexpected error in play command: {e}")
            try:
                await interaction.followup.send(f"❌ An error occurred: {e}", ephemeral=True)
            except:
                print(f"❌ Failed to send error message: {e}")

    @discord.app_commands.command(name="pause", description="Pause the current song")
    async def pause_command(self, interaction: discord.Interaction):
        """Pause the current song"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected to a voice channel!", ephemeral=True)
            return
        
        if player.paused:
            await interaction.response.send_message("❌ Player is already paused!", ephemeral=True)
            return
        
        await player.pause(True)
        await interaction.response.send_message("⏸️ Paused the music!")

    @discord.app_commands.command(name="resume", description="Resume the current song")
    async def resume_command(self, interaction: discord.Interaction):
        """Resume the current song"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected to a voice channel!", ephemeral=True)
            return
        
        if not player.paused:
            await interaction.response.send_message("❌ Player is not paused!", ephemeral=True)
            return
        
        await player.pause(False)
        await interaction.response.send_message("▶️ Resumed the music!")

    @discord.app_commands.command(name="skip", description="Skip the current song")
    async def skip_command(self, interaction: discord.Interaction):
        """Skip the current song"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected to a voice channel!", ephemeral=True)
            return
        
        if not player.playing:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)
            return
        
        await player.skip(force=True)
        await interaction.response.send_message("⏭️ Skipped the current song!")

    @discord.app_commands.command(name="stop", description="Stop the music and clear the queue")
    async def stop_command(self, interaction: discord.Interaction):
        """Stop the music and clear the queue"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected to a voice channel!", ephemeral=True)
            return
        
        await player.stop()
        player.queue.clear()
        # Clear playlist tracking
        self.playlist_manager.clear_playlist(interaction.guild.id)
        await interaction.response.send_message("⏹️ Stopped the music and cleared the queue!")

    @discord.app_commands.command(name="queue", description="Show the current queue")
    async def queue_command(self, interaction: discord.Interaction):
        """Show the current queue"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected to a voice channel!", ephemeral=True)
            return
        
        if not player.current and not player.queue:
            await interaction.response.send_message("📄 The queue is empty!", ephemeral=True)
            return
        
        embed = discord.Embed(title="🎵 Music Queue", color=0x1DB954)
        
        if player.current:
            current_info = f"**{player.current.title}** by {player.current.author}"
            
            # Show playlist position if available
            current_pos, total_tracks = self.playlist_manager.get_current_position_info(interaction.guild.id)
            if current_pos and total_tracks:
                current_info += f"\n📊 Position: {current_pos}/{total_tracks}"
            
            embed.add_field(
                name="▶️ Currently Playing",
                value=current_info,
                inline=False
            )
            if player.current.artwork:
                embed.set_thumbnail(url=player.current.artwork)
        
        if player.queue:
            queue_list = []
            thumbnails_text = ""
            
            # Show thumbnails for up to 4 upcoming tracks
            upcoming_tracks = list(player.queue)[:4]
            if upcoming_tracks and any(hasattr(track, 'artwork') and track.artwork for track in upcoming_tracks):
                thumbnail_urls = []
                for track in upcoming_tracks:
                    if hasattr(track, 'artwork') and track.artwork:
                        thumbnail_urls.append(f"[🖼️]({track.artwork})")
                if thumbnail_urls:
                    thumbnails_text = f"\n\n**🎨 Upcoming Track Thumbnails:** {' '.join(thumbnail_urls[:4])}"
            
            for i, track in enumerate(player.queue[:10], 1):
                thumbnail_icon = "🖼️" if hasattr(track, 'artwork') and track.artwork else "🎵"
                queue_list.append(f"{i}. {thumbnail_icon} **{track.title}** by {track.author}")
            
            if len(player.queue) > 10:
                queue_list.append(f"... and {len(player.queue) - 10} more songs")
            
            embed.add_field(
                name="📋 Up Next",
                value="\n".join(queue_list) + thumbnails_text,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="volume", description="Set the volume")
    @discord.app_commands.describe(volume="Volume level (0-100)")
    async def volume_command(self, interaction: discord.Interaction, volume: int):
        """Set the volume"""
        if not 0 <= volume <= 100:
            await interaction.response.send_message("❌ Volume must be between 0 and 100!", ephemeral=True)
            return
        
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected to a voice channel!", ephemeral=True)
            return
        
        await player.set_volume(volume)
        await interaction.response.send_message(f"🔊 Volume set to {volume}%!")

    @discord.app_commands.command(name="controls", description="Show music controls")
    async def controls_slash(self, interaction: discord.Interaction):
        """Show music controls interface"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected to a voice channel!", ephemeral=True)
            return
        
        if not player.current:
            embed = discord.Embed(
                title="🎛️ Controls",
                description="No music currently playing, but controls are ready!",
                color=0x1DB954
            )
        else:
            embed = discord.Embed(
                title=f"**{player.current.title}**",
                description=f"by {player.current.author}",
                color=0x1DB954
            )
            
            if player.current.artwork:
                embed.set_thumbnail(url=player.current.artwork)
        
        view = MusicControlView(self, interaction.guild.id)
        await interaction.response.send_message(embed=embed, view=view)

    @discord.app_commands.command(name="disconnect", description="Disconnect from the voice channel")
    async def disconnect_command(self, interaction: discord.Interaction):
        """Disconnect from the voice channel"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected to a voice channel!", ephemeral=True)
            return
        
        await player.disconnect()
        await interaction.response.send_message("👋 Disconnected from the voice channel!")

    # Traditional ! Commands for backward compatibility
    
    @commands.command(name="play")
    async def play_traditional(self, ctx, *, query: str):
        """Play a song using traditional ! command"""
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel!")
            return
        
        try:
            player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)
            
            if not player:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            
            player.message_channel = ctx.channel
            tracks = await self.search_tracks(query)
            
            if not tracks:
                await ctx.send("❌ No tracks found!")
                return
            
            # Check if it's a playlist (multiple tracks from URL)
            if len(tracks) > 1 and query.startswith(('http://', 'https://')):
                # Handle playlist
                first_track = tracks[0]
                
                # Set requester for all tracks
                for track in tracks:
                    track.requester = ctx.author
                
                # Set the playlist order for proper navigation
                self.playlist_manager.set_playlist_order(ctx.guild.id, tracks)
                
                if player.playing:
                    # Add all tracks to queue
                    for track in tracks:
                        await player.queue.put_wait(track)
                    
                    embed = discord.Embed(
                        title=f"✅ Playlist Added to Queue",
                        description=f"**{len(tracks)} tracks** added to queue",
                        color=0x1DB954
                    )
                    
                    if tracks[0].artwork:
                        embed.set_thumbnail(url=tracks[0].artwork)
                    
                    await ctx.send(embed=embed)
                else:
                    # Play first track and queue the rest
                    await player.play(first_track)
                    for track in tracks[1:]:
                        await player.queue.put_wait(track)
                    
                    # Create embed with controls for playlist
                    embed = discord.Embed(title=f"**{first_track.title}**", description=f"by {first_track.author}", color=0x1DB954)
                    
                    # Row 1: Duration, Source, Volume
                    embed.add_field(name="⏱️ Duration", value=self.format_time(first_track.length), inline=True)
                    source_display = getattr(first_track, 'search_source', first_track.source.title() if first_track.source else 'Unknown')
                    embed.add_field(name="📺 Source", value=source_display, inline=True)
                    embed.add_field(name="🔊 Volume", value=f"{player.volume}%", inline=True)
                    
                    # Row 2: Requested By, Position, Playlist Info
                    embed.add_field(name="🎧 Requested By", value=ctx.author.mention, inline=True)
                    embed.add_field(name="📊 Position", value=f"1/{len(tracks)}", inline=True)
                    embed.add_field(name="🎶 Playlist", value=f"{len(tracks)-1} in queue", inline=True)
                    
                    if first_track.artwork:
                        embed.set_thumbnail(url=first_track.artwork)
                    
                    view = MusicControlView(self, ctx.guild.id)
                    await ctx.send(embed=embed, view=view)
            else:
                # Handle single track
                track = tracks[0]
                track.requester = ctx.author  # Set requester for single track
                
                if player.playing:
                    await player.queue.put_wait(track)
                    await ctx.send(f"✅ Added to queue: **{track.title}** by {track.author}")
                else:
                    await player.play(track)
                    # For single tracks, also set them as a "playlist" of one for navigation consistency
                    self.playlist_manager.set_playlist_order(ctx.guild.id, [track])
                    
                    # Send controls for single track
                    embed = discord.Embed(title=f"**{track.title}**", description=f"by {track.author}", color=0x1DB954)
                    
                    # Row 1: Duration, Source, Volume
                    embed.add_field(name="⏱️ Duration", value=self.format_time(track.length), inline=True)
                    source_display = getattr(track, 'search_source', track.source.title() if track.source else 'Unknown')
                    embed.add_field(name="📺 Source", value=source_display, inline=True)
                    embed.add_field(name="🔊 Volume", value=f"{player.volume}%", inline=True)
                    
                    # Row 2: Requested By, Position, Empty field
                    embed.add_field(name="🎧 Requested By", value=ctx.author.mention, inline=True)
                    embed.add_field(name="📊 Position", value="1/1", inline=True)
                    embed.add_field(name="​", value="​", inline=True)
                    
                    if track.artwork:
                        embed.set_thumbnail(url=track.artwork)
                    
                    view = MusicControlView(self, ctx.guild.id)
                    await ctx.send(embed=embed, view=view)
                
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {e}")

    @commands.command(name="skip")
    async def skip_traditional(self, ctx):
        """Skip the current song"""
        player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)
        
        if not player or not player.playing:
            await ctx.send("❌ Nothing is playing!")
            return
        
        await player.skip(force=True)
        await ctx.send("⏭️ Skipped the current song!")

    @commands.command(name="pause")
    async def pause_traditional(self, ctx):
        """Pause the current song"""
        player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)
        
        if not player:
            await ctx.send("❌ Not connected to a voice channel!")
            return
        
        if player.paused:
            await ctx.send("❌ Player is already paused!")
            return
        
        await player.pause(True)
        await ctx.send("⏸️ Paused the music!")

    @commands.command(name="resume")
    async def resume_traditional(self, ctx):
        """Resume the current song"""
        player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)
        
        if not player:
            await ctx.send("❌ Not connected to a voice channel!")
            return
        
        if not player.paused:
            await ctx.send("❌ Player is not paused!")
            return
        
        await player.pause(False)
        await ctx.send("▶️ Resumed the music!")

    @commands.command(name="stop")
    async def stop_traditional(self, ctx):
        """Stop the music and clear the queue"""
        player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)
        
        if not player:
            await ctx.send("❌ Not connected to a voice channel!")
            return
        
        await player.stop()
        player.queue.clear()
        # Clear playlist tracking
        self.playlist_manager.clear_playlist(ctx.guild.id)
        await ctx.send("⏹️ Stopped the music and cleared the queue!")

    @commands.command(name="controls")
    async def controls_command(self, ctx):
        """Show music controls interface"""
        player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)
        
        if not player:
            await ctx.send("❌ Not connected to a voice channel!")
            return
        
        if not player.current:
            embed = discord.Embed(
                title="🎛️ Controls",
                description="No music currently playing, but controls are ready!",
                color=0x1DB954
            )
        else:
            embed = discord.Embed(
                title=f"**{player.current.title}**",
                description=f"by {player.current.author}",
                color=0x1DB954
            )
            
            if player.current.artwork:
                embed.set_thumbnail(url=player.current.artwork)
        
        view = MusicControlView(self, ctx.guild.id)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    """Setup function for the cog"""
    music_cog = MusicBot(bot)
    await bot.add_cog(music_cog)
    # Setup the Lavalink connection
    await music_cog.setup_hook()