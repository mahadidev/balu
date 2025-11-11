"""
Async PostgreSQL database manager with connection pooling.
Optimized for high throughput (40-50 servers sending messages continuously).
"""

import asyncio
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, ChatRoom, ChatChannel, ChatMessage, RoomPermission, AdminUser, DailyStats


class DatabaseManager:
    """Async database manager with connection pooling for high performance."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.pool = None
        self._initialized = False
    
    async def initialize(self, database_url: str = None, pool_size: int = 20, max_overflow: int = 30):
        """Initialize database connections with pooling."""
        if self._initialized:
            return
            
        # Default database URL from environment
        if not database_url:
            database_url = os.getenv(
                "DATABASE_URL", 
                "postgresql+asyncpg://postgres:password@localhost:5432/globalchat"
            )
        
        # Create async engine with connection pooling
        self.engine = create_async_engine(
            database_url,
            pool_size=pool_size,          # Number of persistent connections
            max_overflow=max_overflow,     # Additional connections when needed
            pool_timeout=30,               # Wait time for connection
            pool_recycle=3600,            # Recycle connections every hour
            pool_pre_ping=True,           # Verify connections before use
            echo=False                    # Set to True for SQL debugging
        )
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create raw asyncpg pool for high-performance inserts
        pool_url = database_url.replace('+asyncpg', '')
        self.pool = await asyncpg.create_pool(
            pool_url,
            min_size=5,
            max_size=15,
            command_timeout=10
        )
        
        self._initialized = True
        print(f"✅ Database initialized with {pool_size} base connections")
    
    async def close(self):
        """Close all database connections."""
        if self.engine:
            await self.engine.dispose()
        if self.pool:
            await self.pool.close()
        self._initialized = False
    
    @asynccontextmanager
    async def session(self):
        """Get async database session with automatic cleanup."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    # ============================================================================
    # HIGH-PERFORMANCE MESSAGE OPERATIONS (Critical for 40-50 servers)
    # ============================================================================
    
    async def log_message_fast(self, message_data: Dict[str, Any]) -> bool:
        """Ultra-fast message logging using raw asyncpg for maximum performance."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO chat_messages (
                        message_id, room_id, guild_id, channel_id, user_id, 
                        username, guild_name, content, reply_to_message_id, 
                        reply_to_username, reply_to_content, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                    message_data['message_id'],
                    message_data['room_id'], 
                    message_data['guild_id'],
                    message_data['channel_id'],
                    message_data['user_id'],
                    message_data['username'],
                    message_data['guild_name'],
                    message_data['content'],
                    message_data.get('reply_to_message_id'),
                    message_data.get('reply_to_username'),
                    message_data.get('reply_to_content'),
                    message_data.get('timestamp', datetime.utcnow())
                )
            return True
        except Exception as e:
            print(f"❌ Fast message log error: {e}")
            return False
    
    async def get_message_for_reply(self, message_id: str, room_id: int) -> Optional[Dict[str, Any]]:
        """Get message data for reply functionality with caching."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT username, content, user_id 
                    FROM chat_messages 
                    WHERE message_id = $1 AND room_id = $2
                    ORDER BY timestamp DESC LIMIT 1
                """, message_id, room_id)
                
                if result:
                    return {
                        'username': result['username'],
                        'content': result['content'],
                        'user_id': result['user_id']
                    }
                return None
        except Exception as e:
            print(f"❌ Get message for reply error: {e}")
            return None
    
    # ============================================================================
    # ROOM OPERATIONS
    # ============================================================================
    
    async def create_room(self, name: str, created_by: str, max_servers: int = 50) -> Optional[int]:
        """Create a new chat room with default permissions."""
        try:
            async with self.session() as session:
                # Create room
                room = ChatRoom(
                    name=name.strip(),
                    created_by=created_by,
                    max_servers=max_servers
                )
                session.add(room)
                await session.flush()  # Get the room ID
                
                # Create default permissions
                permissions = RoomPermission(
                    room_id=room.id,
                    updated_by=created_by
                )
                session.add(permissions)
                
                await session.commit()
                return room.id
        except SQLAlchemyError as e:
            print(f"❌ Create room error: {e}")
            return None
    
    async def get_room_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get room by name with caching."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT id, name, created_by, created_at, is_active, max_servers
                    FROM chat_rooms 
                    WHERE name = $1 AND is_active = true
                """, name)
                
                if result:
                    return dict(result)
                return None
        except Exception as e:
            print(f"❌ Get room by name error: {e}")
            return None
    
    async def get_all_rooms(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all chat rooms with channel counts."""
        try:
            async with self.session() as session:
                query = select(ChatRoom).options(selectinload(ChatRoom.channels))
                if not include_inactive:
                    query = query.where(ChatRoom.is_active == True)
                
                result = await session.execute(query)
                rooms = result.scalars().all()
                
                return [
                    {
                        'id': room.id,
                        'name': room.name,
                        'created_by': room.created_by,
                        'created_at': room.created_at,
                        'is_active': room.is_active,
                        'max_servers': room.max_servers,
                        'channel_count': len([c for c in room.channels if c.is_active])
                    }
                    for room in rooms
                ]
        except Exception as e:
            print(f"❌ Get all rooms error: {e}")
            return []
    
    async def get_room_permissions(self, room_id: int) -> Dict[str, Any]:
        """Get room permissions with defaults."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT allow_urls, allow_files, enable_bad_word_filter, 
                           max_message_length, rate_limit_seconds, allow_mentions, allow_emojis
                    FROM room_permissions 
                    WHERE room_id = $1
                """, room_id)
                
                if result:
                    return dict(result)
                else:
                    # Return defaults if no permissions found
                    return {
                        'allow_urls': False,
                        'allow_files': False,
                        'enable_bad_word_filter': True,
                        'max_message_length': 2000,
                        'rate_limit_seconds': 3,
                        'allow_mentions': True,
                        'allow_emojis': True
                    }
        except Exception as e:
            print(f"❌ Get room permissions error: {e}")
            return {}
    
    # ============================================================================
    # CHANNEL OPERATIONS
    # ============================================================================
    
    async def register_channel(self, guild_id: str, channel_id: str, room_id: int, 
                             guild_name: str, channel_name: str, registered_by: str) -> bool:
        """Register a Discord channel to a chat room."""
        try:
            async with self.pool.acquire() as conn:
                # Try insert, update if exists
                await conn.execute("""
                    INSERT INTO chat_channels (
                        guild_id, channel_id, guild_name, channel_name, 
                        room_id, registered_by, is_active
                    ) VALUES ($1, $2, $3, $4, $5, $6, true)
                    ON CONFLICT (guild_id, channel_id) 
                    DO UPDATE SET 
                        room_id = $5, 
                        guild_name = $3, 
                        channel_name = $4,
                        registered_at = NOW(),
                        is_active = true
                """, guild_id, channel_id, guild_name, channel_name, room_id, registered_by)
            return True
        except Exception as e:
            print(f"❌ Register channel error: {e}")
            return False
    
    async def get_room_channels(self, room_id: int) -> List[Dict[str, Any]]:
        """Get all active channels for a room."""
        try:
            async with self.pool.acquire() as conn:
                results = await conn.fetch("""
                    SELECT guild_id, channel_id, guild_name, channel_name, registered_by
                    FROM chat_channels 
                    WHERE room_id = $1 AND is_active = true
                    ORDER BY guild_name
                """, room_id)
                
                return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Get room channels error: {e}")
            return []
    
    async def is_channel_registered(self, guild_id: str, channel_id: str) -> Optional[int]:
        """Check if channel is registered and return room_id."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT room_id FROM chat_channels 
                    WHERE guild_id = $1 AND channel_id = $2 AND is_active = true
                """, guild_id, channel_id)
                return result
        except Exception as e:
            print(f"❌ Is channel registered error: {e}")
            return None
    
    # ============================================================================
    # ANALYTICS & MONITORING (For Admin Panel)
    # ============================================================================
    
    async def get_message_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get message statistics for the admin panel."""
        try:
            async with self.pool.acquire() as conn:
                # Get daily message counts
                daily_stats = await conn.fetch("""
                    SELECT DATE(timestamp) as date, COUNT(*) as count
                    FROM chat_messages 
                    WHERE timestamp >= NOW() - INTERVAL %s DAY
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, days)
                
                # Get total stats
                total_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_messages,
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(DISTINCT guild_id) as unique_guilds,
                        COUNT(DISTINCT room_id) as active_rooms
                    FROM chat_messages 
                    WHERE timestamp >= NOW() - INTERVAL %s DAY
                """, days)
                
                return {
                    'daily_stats': [dict(row) for row in daily_stats],
                    'total_stats': dict(total_stats) if total_stats else {}
                }
        except Exception as e:
            print(f"❌ Get message stats error: {e}")
            return {'daily_stats': [], 'total_stats': {}}
    
    async def get_live_stats(self) -> Dict[str, Any]:
        """Get real-time statistics for monitoring."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT 
                        (SELECT COUNT(*) FROM chat_rooms WHERE is_active = true) as active_rooms,
                        (SELECT COUNT(*) FROM chat_channels WHERE is_active = true) as active_channels,
                        (SELECT COUNT(*) FROM chat_messages WHERE timestamp >= NOW() - INTERVAL '1 hour') as messages_last_hour,
                        (SELECT COUNT(*) FROM chat_messages WHERE timestamp >= NOW() - INTERVAL '1 day') as messages_last_day
                """)
                
                return dict(result) if result else {}
        except Exception as e:
            print(f"❌ Get live stats error: {e}")
            return {}


# Global instance
db_manager = DatabaseManager()