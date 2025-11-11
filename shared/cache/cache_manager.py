"""
High-level cache manager for Global Chat System.
Handles caching strategies for rooms, channels, permissions, and analytics.
Optimized for 40-50 servers with continuous message flow.
"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .redis_client import redis_client


class CacheManager:
    """High-performance cache manager with intelligent caching strategies."""
    
    # Cache TTLs (in seconds)
    TTL_ROOM_DATA = 3600           # 1 hour - rooms rarely change
    TTL_ROOM_PERMISSIONS = 1800    # 30 minutes - permissions change occasionally
    TTL_CHANNEL_LOOKUP = 7200      # 2 hours - channel registrations are stable
    TTL_ROOM_CHANNELS = 1800       # 30 minutes - active channels list
    TTL_MESSAGE_REPLY = 300        # 5 minutes - recent messages for replies
    TTL_LIVE_STATS = 60           # 1 minute - live statistics
    TTL_USER_RATE_LIMIT = 300     # 5 minutes - rate limiting
    
    # Cache key prefixes
    KEY_PREFIX_ROOM = "room"
    KEY_PREFIX_PERMISSION = "perm"
    KEY_PREFIX_CHANNEL = "chan"
    KEY_PREFIX_ROOM_CHANNELS = "room_chans"
    KEY_PREFIX_MESSAGE = "msg"
    KEY_PREFIX_STATS = "stats"
    KEY_PREFIX_RATE_LIMIT = "rate"
    
    # ============================================================================
    # ROOM CACHING
    # ============================================================================
    
    async def get_room_by_name(self, room_name: str) -> Optional[Dict[str, Any]]:
        """Get room data from cache."""
        cache_key = f"{self.KEY_PREFIX_ROOM}:name:{room_name}"
        return await redis_client.get_json(cache_key)
    
    async def set_room_by_name(self, room_name: str, room_data: Dict[str, Any]) -> bool:
        """Cache room data by name."""
        cache_key = f"{self.KEY_PREFIX_ROOM}:name:{room_name}"
        return await redis_client.set_json(cache_key, room_data, self.TTL_ROOM_DATA)
    
    async def get_room_by_id(self, room_id: int) -> Optional[Dict[str, Any]]:
        """Get room data by ID from cache."""
        cache_key = f"{self.KEY_PREFIX_ROOM}:id:{room_id}"
        return await redis_client.get_json(cache_key)
    
    async def set_room_by_id(self, room_id: int, room_data: Dict[str, Any]) -> bool:
        """Cache room data by ID."""
        cache_key = f"{self.KEY_PREFIX_ROOM}:id:{room_id}"
        return await redis_client.set_json(cache_key, room_data, self.TTL_ROOM_DATA)
    
    async def invalidate_room(self, room_id: int, room_name: str = None):
        """Invalidate all room cache entries."""
        keys_to_delete = [f"{self.KEY_PREFIX_ROOM}:id:{room_id}"]
        if room_name:
            keys_to_delete.append(f"{self.KEY_PREFIX_ROOM}:name:{room_name}")
        
        for key in keys_to_delete:
            await redis_client.delete(key)
    
    # ============================================================================
    # ROOM PERMISSIONS CACHING
    # ============================================================================
    
    async def get_room_permissions(self, room_id: int) -> Optional[Dict[str, Any]]:
        """Get room permissions from cache."""
        cache_key = f"{self.KEY_PREFIX_PERMISSION}:{room_id}"
        return await redis_client.get_json(cache_key)
    
    async def set_room_permissions(self, room_id: int, permissions: Dict[str, Any]) -> bool:
        """Cache room permissions."""
        cache_key = f"{self.KEY_PREFIX_PERMISSION}:{room_id}"
        return await redis_client.set_json(cache_key, permissions, self.TTL_ROOM_PERMISSIONS)
    
    async def invalidate_room_permissions(self, room_id: int):
        """Invalidate room permissions cache."""
        cache_key = f"{self.KEY_PREFIX_PERMISSION}:{room_id}"
        await redis_client.delete(cache_key)
    
    # ============================================================================
    # CHANNEL REGISTRATION CACHING
    # ============================================================================
    
    async def get_channel_room_id(self, guild_id: str, channel_id: str) -> Optional[int]:
        """Get room ID for a Discord channel from cache."""
        cache_key = f"{self.KEY_PREFIX_CHANNEL}:{guild_id}:{channel_id}"
        result = await redis_client.get(cache_key)
        return int(result) if result else None
    
    async def set_channel_room_id(self, guild_id: str, channel_id: str, room_id: int) -> bool:
        """Cache channel to room mapping."""
        cache_key = f"{self.KEY_PREFIX_CHANNEL}:{guild_id}:{channel_id}"
        return await redis_client.set(cache_key, str(room_id), self.TTL_CHANNEL_LOOKUP)
    
    async def invalidate_channel_registration(self, guild_id: str, channel_id: str):
        """Invalidate channel registration cache."""
        cache_key = f"{self.KEY_PREFIX_CHANNEL}:{guild_id}:{channel_id}"
        await redis_client.delete(cache_key)
    
    async def get_room_channels(self, room_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get list of channels for a room from cache."""
        cache_key = f"{self.KEY_PREFIX_ROOM_CHANNELS}:{room_id}"
        return await redis_client.get_json(cache_key)
    
    async def set_room_channels(self, room_id: int, channels: List[Dict[str, Any]]) -> bool:
        """Cache list of channels for a room."""
        cache_key = f"{self.KEY_PREFIX_ROOM_CHANNELS}:{room_id}"
        return await redis_client.set_json(cache_key, channels, self.TTL_ROOM_CHANNELS)
    
    async def invalidate_room_channels(self, room_id: int):
        """Invalidate room channels cache."""
        cache_key = f"{self.KEY_PREFIX_ROOM_CHANNELS}:{room_id}"
        await redis_client.delete(cache_key)
    
    # ============================================================================
    # MESSAGE REPLY CACHING (For recent messages)
    # ============================================================================
    
    async def get_message_for_reply(self, message_id: str, room_id: int) -> Optional[Dict[str, Any]]:
        """Get cached message data for reply functionality."""
        cache_key = f"{self.KEY_PREFIX_MESSAGE}:{room_id}:{message_id}"
        return await redis_client.get_json(cache_key)
    
    async def set_message_for_reply(self, message_id: str, room_id: int, message_data: Dict[str, Any]) -> bool:
        """Cache message data for reply functionality."""
        cache_key = f"{self.KEY_PREFIX_MESSAGE}:{room_id}:{message_id}"
        return await redis_client.set_json(cache_key, message_data, self.TTL_MESSAGE_REPLY)
    
    # ============================================================================
    # ANALYTICS & STATISTICS CACHING
    # ============================================================================
    
    async def get_live_stats(self) -> Optional[Dict[str, Any]]:
        """Get cached live statistics."""
        cache_key = f"{self.KEY_PREFIX_STATS}:live"
        return await redis_client.get_json(cache_key)
    
    async def set_live_stats(self, stats: Dict[str, Any]) -> bool:
        """Cache live statistics."""
        cache_key = f"{self.KEY_PREFIX_STATS}:live"
        return await redis_client.set_json(cache_key, stats, self.TTL_LIVE_STATS)
    
    async def get_message_stats(self, days: int) -> Optional[Dict[str, Any]]:
        """Get cached message statistics."""
        cache_key = f"{self.KEY_PREFIX_STATS}:messages:{days}d"
        return await redis_client.get_json(cache_key)
    
    async def set_message_stats(self, days: int, stats: Dict[str, Any]) -> bool:
        """Cache message statistics."""
        cache_key = f"{self.KEY_PREFIX_STATS}:messages:{days}d"
        return await redis_client.set_json(cache_key, stats, self.TTL_LIVE_STATS * 5)  # 5 minutes
    
    # ============================================================================
    # RATE LIMITING
    # ============================================================================
    
    async def check_rate_limit(self, user_id: str, room_id: int, limit_seconds: int) -> bool:
        """Check if user is rate limited. Returns True if allowed."""
        cache_key = f"{self.KEY_PREFIX_RATE_LIMIT}:{room_id}:{user_id}"
        
        if await redis_client.exists(cache_key):
            return False  # Rate limited
        
        # Set rate limit
        await redis_client.set(cache_key, "1", limit_seconds)
        return True  # Allowed
    
    async def reset_rate_limit(self, user_id: str, room_id: int):
        """Reset rate limit for user in room."""
        cache_key = f"{self.KEY_PREFIX_RATE_LIMIT}:{room_id}:{user_id}"
        await redis_client.delete(cache_key)
    
    # ============================================================================
    # BULK OPERATIONS
    # ============================================================================
    
    async def invalidate_room_all_cache(self, room_id: int, room_name: str = None):
        """Invalidate all cache entries related to a room."""
        await self.invalidate_room(room_id, room_name)
        await self.invalidate_room_permissions(room_id)
        await self.invalidate_room_channels(room_id)
        
        # Invalidate channel mappings for this room
        pattern = f"{self.KEY_PREFIX_CHANNEL}:*"
        channel_keys = await redis_client.keys(pattern)
        
        for key in channel_keys:
            cached_room_id = await redis_client.get(key)
            if cached_room_id and int(cached_room_id) == room_id:
                await redis_client.delete(key)
    
    async def warmup_cache(self, room_data: Dict[str, Any], channels: List[Dict[str, Any]], 
                          permissions: Dict[str, Any]):
        """Warmup cache with fresh data (useful after database updates)."""
        room_id = room_data['id']
        room_name = room_data['name']
        
        # Cache room data
        await self.set_room_by_id(room_id, room_data)
        await self.set_room_by_name(room_name, room_data)
        
        # Cache permissions
        await self.set_room_permissions(room_id, permissions)
        
        # Cache channels
        await self.set_room_channels(room_id, channels)
        
        # Cache individual channel mappings
        for channel in channels:
            await self.set_channel_room_id(
                channel['guild_id'], 
                channel['channel_id'], 
                room_id
            )
    
    # ============================================================================
    # HEALTH & MONITORING
    # ============================================================================
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """Get cache usage statistics."""
        try:
            # Count keys by prefix
            room_keys = len(await redis_client.keys(f"{self.KEY_PREFIX_ROOM}:*"))
            perm_keys = len(await redis_client.keys(f"{self.KEY_PREFIX_PERMISSION}:*"))
            channel_keys = len(await redis_client.keys(f"{self.KEY_PREFIX_CHANNEL}:*"))
            stats_keys = len(await redis_client.keys(f"{self.KEY_PREFIX_STATS}:*"))
            rate_limit_keys = len(await redis_client.keys(f"{self.KEY_PREFIX_RATE_LIMIT}:*"))
            
            return {
                'rooms_cached': room_keys,
                'permissions_cached': perm_keys,
                'channels_cached': channel_keys,
                'stats_cached': stats_keys,
                'active_rate_limits': rate_limit_keys,
                'total_keys': room_keys + perm_keys + channel_keys + stats_keys + rate_limit_keys,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"❌ Cache info error: {e}")
            return {}
    
    async def clear_expired_keys(self):
        """Manual cleanup of expired keys (Redis handles this automatically, but useful for monitoring)."""
        try:
            # Get all keys with TTL -1 (no expiration) that shouldn't be permanent
            all_patterns = [
                f"{self.KEY_PREFIX_RATE_LIMIT}:*",
                f"{self.KEY_PREFIX_MESSAGE}:*",
                f"{self.KEY_PREFIX_STATS}:*"
            ]
            
            expired_count = 0
            for pattern in all_patterns:
                keys = await redis_client.keys(pattern)
                for key in keys:
                    ttl = await redis_client.ttl(key)
                    if ttl == -1:  # No expiration set
                        await redis_client.delete(key)
                        expired_count += 1
            
            return expired_count
        except Exception as e:
            print(f"❌ Clear expired keys error: {e}")
            return 0


# Global instance
cache_manager = CacheManager()