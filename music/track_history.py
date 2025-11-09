import wavelink
from typing import Optional, List

class TrackHistory:
    """Manages track history for music playback"""
    
    def __init__(self):
        # Track history for each guild
        self.track_history = {}  # guild_id -> list of tracks
        # Flag to prevent adding to history when going backwards
        self.going_backwards = {}  # guild_id -> bool

    def add_to_history(self, guild_id: int, track: wavelink.Playable):
        """Add a track to the guild's history"""
        if guild_id not in self.track_history:
            self.track_history[guild_id] = []
        
        # Add to beginning of history and limit to 20 tracks
        self.track_history[guild_id].insert(0, track)
        if len(self.track_history[guild_id]) > 20:
            self.track_history[guild_id] = self.track_history[guild_id][:20]

    def get_previous_track(self, guild_id: int) -> Optional[wavelink.Playable]:
        """Get the previous track from history"""
        if guild_id not in self.track_history or len(self.track_history[guild_id]) < 2:
            return None
        
        # Return the second track in history (first is current track)
        return self.track_history[guild_id][1]

    def go_to_previous_track(self, guild_id: int) -> Optional[wavelink.Playable]:
        """Go to previous track and manage history properly"""
        if guild_id not in self.track_history or len(self.track_history[guild_id]) < 2:
            return None
        
        # Remove current track (first item) and return the previous track (now first item)
        self.track_history[guild_id].pop(0)
        return self.track_history[guild_id][0] if self.track_history[guild_id] else None

    def set_going_backwards(self, guild_id: int, value: bool):
        """Set the backwards flag for a guild"""
        self.going_backwards[guild_id] = value

    def is_going_backwards(self, guild_id: int) -> bool:
        """Check if we're currently going backwards for a guild"""
        return self.going_backwards.get(guild_id, False)

    def clear_history(self, guild_id: int):
        """Clear history for a guild"""
        if guild_id in self.track_history:
            del self.track_history[guild_id]
        if guild_id in self.going_backwards:
            del self.going_backwards[guild_id]