import wavelink
from typing import Optional, List

class PlaylistManager:
    """Manages playlist order and navigation for proper prev/next controls"""
    
    def __init__(self):
        # Track the original playlist order for proper navigation
        self.playlist_order = {}  # guild_id -> list of tracks
        self.current_position = {}  # guild_id -> current position in playlist
    
    def set_playlist_order(self, guild_id: int, tracks):
        """Set the playlist order for proper navigation"""
        # Convert to list if it's a Playlist object or other iterable
        if hasattr(tracks, '__iter__'):
            self.playlist_order[guild_id] = list(tracks)
        else:
            self.playlist_order[guild_id] = [tracks]
        self.current_position[guild_id] = 0
        print(f"🎵 Set playlist order with {len(self.playlist_order[guild_id])} tracks for guild {guild_id}")

    def get_previous_in_playlist(self, guild_id: int) -> Optional[wavelink.Playable]:
        """Get the previous track in the original playlist order"""
        if guild_id not in self.playlist_order or guild_id not in self.current_position:
            return None
        
        current_pos = self.current_position[guild_id]
        if current_pos > 0:
            previous_track = self.playlist_order[guild_id][current_pos - 1]
            print(f"🔍 Previous in playlist: {previous_track.title} (position {current_pos})")
            return previous_track
        return None

    def get_next_in_playlist(self, guild_id: int) -> Optional[wavelink.Playable]:
        """Get the next track in the original playlist order"""
        if guild_id not in self.playlist_order or guild_id not in self.current_position:
            return None
        
        current_pos = self.current_position[guild_id]
        playlist = self.playlist_order[guild_id]
        if current_pos < len(playlist) - 1:
            next_track = playlist[current_pos + 1]
            print(f"🔍 Next in playlist: {next_track.title} (position {current_pos + 2})")
            return next_track
        return None

    def move_to_previous_position(self, guild_id: int):
        """Move current position to previous in playlist"""
        if guild_id in self.current_position and self.current_position[guild_id] > 0:
            self.current_position[guild_id] -= 1
            print(f"⬅️ Moved to previous position: {self.current_position[guild_id] + 1}")

    def move_to_next_position(self, guild_id: int):
        """Move current position to next in playlist"""
        if guild_id in self.current_position and guild_id in self.playlist_order:
            if self.current_position[guild_id] < len(self.playlist_order[guild_id]) - 1:
                self.current_position[guild_id] += 1
                print(f"➡️ Moved to next position: {self.current_position[guild_id] + 1}")

    def update_playlist_position(self, guild_id: int, track: wavelink.Playable):
        """Update the current position in the playlist based on the playing track"""
        if guild_id not in self.playlist_order:
            return
            
        playlist = self.playlist_order[guild_id]
        
        # Find the track in the playlist and update position
        for i, playlist_track in enumerate(playlist):
            if (hasattr(playlist_track, 'identifier') and hasattr(track, 'identifier') and 
                playlist_track.identifier == track.identifier):
                self.current_position[guild_id] = i
                print(f"🎯 Updated position to {i+1}/{len(playlist)} for track: {track.title}")
                return
        
        # If track not found in playlist, check if it's the next logical position
        if guild_id in self.current_position:
            current_pos = self.current_position[guild_id]
            if current_pos + 1 < len(playlist) and playlist[current_pos + 1].identifier == track.identifier:
                self.current_position[guild_id] = current_pos + 1
                print(f"🎯 Advanced position to {current_pos+2}/{len(playlist)} for track: {track.title}")

    def get_current_position_info(self, guild_id: int) -> tuple[int, int]:
        """Get current position and total tracks in playlist"""
        if guild_id in self.current_position and guild_id in self.playlist_order:
            current_pos = self.current_position[guild_id] + 1  # 1-based for display
            total_tracks = len(self.playlist_order[guild_id])
            return current_pos, total_tracks
        return None, None

    def clear_playlist(self, guild_id: int):
        """Clear playlist tracking for a guild"""
        if guild_id in self.playlist_order:
            del self.playlist_order[guild_id]
        if guild_id in self.current_position:
            del self.current_position[guild_id]
        print(f"🧹 Cleared playlist tracking for guild {guild_id}")

    def has_playlist(self, guild_id: int) -> bool:
        """Check if guild has a playlist set"""
        return guild_id in self.playlist_order and guild_id in self.current_position