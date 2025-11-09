import wavelink
from typing import Optional, List
from collections import deque

class PlaylistSequence:
    """Thread-safe playlist sequence manager using deque"""
    
    def __init__(self, tracks=None):
        self.tracks = deque(tracks or [])
        self.current_index = 0
        self.history = deque(maxlen=50)  # Keep last 50 tracks for previous navigation
    
    def add_tracks(self, tracks):
        """Set new playlist tracks"""
        self.tracks = deque(tracks)
        self.current_index = 0
        self.history.clear()
        return len(self.tracks)
    
    def current_track(self):
        """Get current track"""
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]
        return None
    
    def next_track(self):
        """Move to and return next track"""
        if self.current_index < len(self.tracks) - 1:
            # Add current track to history before moving
            current = self.current_track()
            if current:
                self.history.append(current)
            
            self.current_index += 1
            return self.current_track()
        return None
    
    def prev_track(self):
        """Move to and return previous track"""
        if self.current_index > 0:
            self.current_index -= 1
            return self.current_track()
        elif self.history:
            # If at beginning, get from history
            return self.history[-1]
        return None
    
    def peek_next(self):
        """Look at next track without moving"""
        if self.current_index < len(self.tracks) - 1:
            return self.tracks[self.current_index + 1]
        return None
    
    def peek_prev(self):
        """Look at previous track without moving"""
        if self.current_index > 0:
            return self.tracks[self.current_index - 1]
        elif self.history:
            return self.history[-1]
        return None
    
    def get_position_info(self):
        """Get current position and total"""
        return (self.current_index + 1, len(self.tracks)) if self.tracks else (0, 0)
    
    def has_next(self):
        """Check if there's a next track"""
        return self.current_index < len(self.tracks) - 1
    
    def has_prev(self):
        """Check if there's a previous track"""
        return self.current_index > 0 or bool(self.history)
    
    def remaining_tracks(self):
        """Get all tracks after current position"""
        if self.current_index < len(self.tracks) - 1:
            return list(self.tracks)[self.current_index + 1:]
        return []
    
    def is_empty(self):
        """Check if playlist is empty"""
        return len(self.tracks) == 0
    
    def clear(self):
        """Clear the playlist"""
        self.tracks.clear()
        self.history.clear()
        self.current_index = 0

class PlaylistManager:
    """Manages playlist order and navigation for proper prev/next controls"""
    
    def __init__(self):
        # Use deque-based sequence managers per guild
        self.playlists = {}  # guild_id -> PlaylistSequence
    
    def set_playlist_order(self, guild_id: int, tracks):
        """Set the playlist order for proper navigation"""
        # Convert to list if it's a Playlist object or other iterable
        if hasattr(tracks, '__iter__'):
            track_list = list(tracks)
        else:
            track_list = [tracks]
        
        # Create or update playlist sequence
        if guild_id not in self.playlists:
            self.playlists[guild_id] = PlaylistSequence()
        
        count = self.playlists[guild_id].add_tracks(track_list)
        print(f"🎵 Set playlist order with {count} tracks for guild {guild_id}")

    def get_previous_in_playlist(self, guild_id: int) -> Optional[wavelink.Playable]:
        """Get the previous track in the original playlist order"""
        if guild_id not in self.playlists:
            return None
        
        playlist = self.playlists[guild_id]
        prev_track = playlist.peek_prev()
        if prev_track:
            current_pos, total = playlist.get_position_info()
            print(f"🔍 Previous in playlist: {prev_track.title} (would be position {current_pos - 1})")
        return prev_track

    def get_next_in_playlist(self, guild_id: int) -> Optional[wavelink.Playable]:
        """Get the next track in the original playlist order"""
        if guild_id not in self.playlists:
            return None
        
        playlist = self.playlists[guild_id]
        next_track = playlist.peek_next()
        if next_track:
            current_pos, total = playlist.get_position_info()
            print(f"🔍 Next in playlist: {next_track.title} (position {current_pos + 1})")
        return next_track

    def move_to_previous_position(self, guild_id: int):
        """Move current position to previous in playlist"""
        if guild_id not in self.playlists:
            return
        
        playlist = self.playlists[guild_id]
        prev_track = playlist.prev_track()
        if prev_track:
            current_pos, total = playlist.get_position_info()
            print(f"⬅️ Moved to previous position: {current_pos}/{total}")
            return prev_track
        return None

    def move_to_next_position(self, guild_id: int):
        """Move current position to next in playlist"""
        if guild_id not in self.playlists:
            return
        
        playlist = self.playlists[guild_id]
        next_track = playlist.next_track()
        if next_track:
            current_pos, total = playlist.get_position_info()
            print(f"➡️ Moved to next position: {current_pos}/{total}")
            return next_track
        return None

    def update_playlist_position(self, guild_id: int, track: wavelink.Playable):
        """Update the current position in the playlist based on the playing track"""
        if guild_id not in self.playlists:
            return
        
        playlist = self.playlists[guild_id]
        current_track = playlist.current_track()
        
        # Check if the current track matches the playing track
        if (current_track and hasattr(current_track, 'identifier') and 
            hasattr(track, 'identifier') and current_track.identifier == track.identifier):
            current_pos, total = playlist.get_position_info()
            print(f"🎯 Position confirmed: {current_pos}/{total} for track: {track.title}")
        else:
            print(f"🎯 Track mismatch - manual sync may be needed for: {track.title}")

    def get_current_position_info(self, guild_id: int) -> tuple[int, int]:
        """Get current position and total tracks in playlist"""
        if guild_id not in self.playlists:
            return None, None
        
        return self.playlists[guild_id].get_position_info()

    def clear_playlist(self, guild_id: int):
        """Clear playlist tracking for a guild"""
        if guild_id in self.playlists:
            self.playlists[guild_id].clear()
            del self.playlists[guild_id]
        print(f"🧹 Cleared playlist tracking for guild {guild_id}")

    def has_playlist(self, guild_id: int) -> bool:
        """Check if guild has a playlist set"""
        return guild_id in self.playlists and not self.playlists[guild_id].is_empty()
    
    def get_remaining_tracks(self, guild_id: int) -> List[wavelink.Playable]:
        """Get all tracks after current position"""
        if guild_id not in self.playlists:
            return []
        
        return self.playlists[guild_id].remaining_tracks()