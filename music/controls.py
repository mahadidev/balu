import discord
import wavelink
from discord.ext import commands
from typing import cast

class MusicControlView(discord.ui.View):
    """Music control buttons matching the provided design"""
    
    def __init__(self, music_bot, guild_id):
        super().__init__(timeout=None)
        self.music_bot = music_bot
        self.guild_id = guild_id
    
    # Row 1: Main control buttons
    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.primary, row=0)
    async def previous_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Previous track"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected", ephemeral=True)
            return
        
        # Try to get previous track from playlist order first
        previous_track = self.music_bot.playlist_manager.get_previous_in_playlist(interaction.guild.id)
        
        if previous_track:
            # Set manual navigation flag to prevent auto-play
            self.music_bot.manual_navigation[interaction.guild.id] = True
            
            # Set flag to indicate we're going backwards
            self.music_bot.track_history.set_going_backwards(interaction.guild.id, True)
            
            # Update position in playlist
            self.music_bot.playlist_manager.move_to_previous_position(interaction.guild.id)
            
            # Play the previous track
            await player.play(previous_track)
            await interaction.response.send_message(f"⏮️ Playing previous: **{previous_track.title}**", ephemeral=True)
        else:
            # Fallback to history-based navigation or restart current track
            previous_track = self.music_bot.track_history.get_previous_track(interaction.guild.id)
            if previous_track:
                self.music_bot.track_history.set_going_backwards(interaction.guild.id, True)
                await player.play(previous_track)
                await interaction.response.send_message(f"⏮️ Playing previous: **{previous_track.title}**", ephemeral=True)
            elif player.current:
                await player.seek(0)
                await interaction.response.send_message("⏮️ No previous track, restarted current", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Nothing is playing", ephemeral=True)
    
    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.primary, row=0)
    async def pause_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Pause/Resume"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        if not player:
            await interaction.response.send_message("❌ Not connected", ephemeral=True)
            return
        
        if player.playing and not player.paused:
            await player.pause(True)
            await interaction.response.send_message("⏸️ Paused", ephemeral=True)
        elif player.paused:
            await player.pause(False)
            await interaction.response.send_message("▶️ Resumed", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing playing", ephemeral=True)
    
    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.primary, row=0)
    async def skip_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Next track"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected", ephemeral=True)
            return
        
        if not player.current:
            await interaction.response.send_message("❌ Nothing is playing", ephemeral=True)
            return
        
        # Check if we have a playlist with tracks
        if self.music_bot.playlist_manager.has_playlist(interaction.guild.id):
            next_track = self.music_bot.playlist_manager.get_next_in_playlist(interaction.guild.id)
            
            if next_track:
                # Set manual navigation flag to prevent auto-play
                self.music_bot.manual_navigation[interaction.guild.id] = True
                
                # Move to next position (this also returns the track)
                moved_track = self.music_bot.playlist_manager.move_to_next_position(interaction.guild.id)
                
                # Add remaining playlist tracks to queue if queue is empty
                if not player.queue:
                    remaining_tracks = self.music_bot.playlist_manager.get_remaining_tracks(interaction.guild.id)
                    for track in remaining_tracks:
                        await player.queue.put_wait(track)
                    print(f"🔄 Repopulated queue with {len(remaining_tracks)} remaining playlist tracks")
                
                # Play the next track directly
                await player.play(next_track)
                await interaction.response.send_message(f"⏭️ Playing next: **{next_track.title}**", ephemeral=True)
                return
            else:
                # At end of playlist
                current_pos, total_tracks = self.music_bot.playlist_manager.get_current_position_info(interaction.guild.id)
                await interaction.response.send_message(f"🏁 End of playlist reached ({current_pos}/{total_tracks})", ephemeral=True)
                return
        
        # Fallback to regular skip behavior when no playlist
        if player.queue:
            # There are tracks in queue - use regular skip
            next_track = list(player.queue)[0]  # Peek at next track without removing it
            await player.skip(force=True)
            await interaction.response.send_message(f"⏭️ Skipped\n▶️ Next: **{next_track.title}**", ephemeral=True)
        else:
            # Queue is empty - just skip current track
            await player.skip(force=True)
            await interaction.response.send_message("⏭️ Skipped\n📭 Queue is empty after this track", ephemeral=True)
    
    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.primary, row=0)
    async def stop_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Stop"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected", ephemeral=True)
            return
        
        if not player.current:
            await interaction.response.send_message("❌ Nothing is playing", ephemeral=True)
            return
        
        await player.stop()
        player.queue.clear()
        # Clear playlist tracking
        self.music_bot.playlist_manager.clear_playlist(interaction.guild.id)
        await interaction.response.send_message("⏹️ Stopped and cleared queue", ephemeral=True)
    
    @discord.ui.button(emoji="❌", style=discord.ButtonStyle.primary, row=0)
    async def disconnect_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Disconnect"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        if player:
            await player.disconnect()
            # Clear playlist tracking
            self.music_bot.playlist_manager.clear_playlist(interaction.guild.id)
            await interaction.response.send_message("❌ Disconnected", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Not connected", ephemeral=True)
    
    # Row 2: Secondary control buttons
    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.primary, row=1)
    async def repeat_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Repeat mode"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected", ephemeral=True)
            return
        
        # Toggle repeat mode
        if hasattr(player, 'repeat_mode'):
            player.repeat_mode = not getattr(player, 'repeat_mode', False)
            status = "enabled" if player.repeat_mode else "disabled"
            await interaction.response.send_message(f"🔄 Repeat mode {status}", ephemeral=True)
        else:
            # Add repeat mode attribute if it doesn't exist
            player.repeat_mode = True
            await interaction.response.send_message("🔄 Repeat mode enabled", ephemeral=True)
    
    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.primary, row=1)
    async def shuffle_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Shuffle"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected", ephemeral=True)
            return
        
        if len(player.queue) < 2:
            await interaction.response.send_message("❌ Need at least 2 tracks in queue to shuffle", ephemeral=True)
            return
        
        player.queue.shuffle()
        await interaction.response.send_message(f"🔀 Shuffled {len(player.queue)} tracks in queue", ephemeral=True)
    
    @discord.ui.button(emoji="📜", style=discord.ButtonStyle.primary, row=1)
    async def queue_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Queue"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected", ephemeral=True)
            return
        
        if not player.current and not player.queue:
            await interaction.response.send_message("📄 The queue is empty!", ephemeral=True)
            return
        
        queue_text = ""
        if player.current:
            current_info = f"**{player.current.title}** by {player.current.author}"
            
            # Show playlist position if available
            current_pos, total_tracks = self.music_bot.playlist_manager.get_current_position_info(interaction.guild.id)
            if current_pos and total_tracks:
                current_info += f"\n📊 Position: {current_pos}/{total_tracks}"
            
            queue_text += f"**▶️ Currently Playing:**\n{current_info}\n\n"
        
        if player.queue:
            queue_text += "**📜 Up Next:**\n"
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
            
            for i, track in enumerate(list(player.queue)[:10], 1):
                thumbnail_icon = "🖼️" if hasattr(track, 'artwork') and track.artwork else "🎵"
                queue_text += f"{i}. {thumbnail_icon} {track.title}\n"
            
            if len(player.queue) > 10:
                queue_text += f"\n... and {len(player.queue) - 10} more tracks"
            
            queue_text += thumbnails_text
        
        embed = discord.Embed(
            title="🎵 Music Queue",
            description=queue_text,
            color=0x1DB954
        )
        
        if player.current and player.current.artwork:
            embed.set_thumbnail(url=player.current.artwork)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.primary, row=1)
    async def volume_down_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Volume down"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected", ephemeral=True)
            return
        
        current_volume = player.volume
        new_volume = max(0, current_volume - 10)
        
        if new_volume == current_volume:
            await interaction.response.send_message("🔇 Volume already at minimum (0%)", ephemeral=True)
            return
        
        await player.set_volume(new_volume)
        await interaction.response.send_message(f"🔉 Volume: {new_volume}%", ephemeral=True)
    
    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.primary, row=1)
    async def volume_up_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Volume up"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ Not connected", ephemeral=True)
            return
        
        current_volume = player.volume
        new_volume = min(100, current_volume + 10)
        
        if new_volume == current_volume:
            await interaction.response.send_message("🔊 Volume already at maximum (100%)", ephemeral=True)
            return
        
        await player.set_volume(new_volume)
        await interaction.response.send_message(f"🔊 Volume: {new_volume}%", ephemeral=True)