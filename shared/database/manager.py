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
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, ChatRoom, ChatChannel, ChatMessage, RoomPermission, AdminUser, DailyStats, ServerBan


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
                
                room_data = []
                for room in rooms:
                    # Get today's message count for this room
                    messages_today_query = text("""
                        SELECT COUNT(*) as count
                        FROM chat_messages 
                        WHERE room_id = :room_id 
                        AND DATE(timestamp) = CURRENT_DATE
                    """)
                    messages_result = await session.execute(messages_today_query, {"room_id": room.id})
                    messages_today = messages_result.scalar() or 0
                    
                    room_data.append({
                        'id': room.id,
                        'name': room.name,
                        'created_by': room.created_by,
                        'created_at': room.created_at,
                        'is_active': room.is_active,
                        'max_servers': room.max_servers,
                        'channel_count': len([c for c in room.channels if c.is_active]),
                        'messages_today': messages_today
                    })
                
                return room_data
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
            # First check if server is banned
            if await self.is_server_banned(guild_id):
                print(f"❌ Cannot register channel: Server {guild_id} ({guild_name}) is banned")
                return False
            
            async with self.session() as session:
                from sqlalchemy import text
                from datetime import datetime
                
                # Try insert, update if exists using SQLAlchemy
                await session.execute(text("""
                    INSERT INTO chat_channels (
                        guild_id, channel_id, guild_name, channel_name, 
                        room_id, registered_by, registered_at, is_active
                    ) VALUES (:guild_id, :channel_id, :guild_name, :channel_name, :room_id, :registered_by, :registered_at, true)
                    ON CONFLICT (guild_id, channel_id) 
                    DO UPDATE SET 
                        room_id = :room_id, 
                        guild_name = :guild_name, 
                        channel_name = :channel_name,
                        registered_at = :registered_at,
                        is_active = true
                """), {
                    'guild_id': guild_id, 
                    'channel_id': channel_id, 
                    'guild_name': guild_name, 
                    'channel_name': channel_name, 
                    'room_id': room_id, 
                    'registered_by': registered_by,
                    'registered_at': datetime.utcnow()
                })
                await session.commit()
            return True
        except Exception as e:
            print(f"❌ Register channel error: {e}")
            print(f"   Guild ID: {guild_id}")
            print(f"   Channel ID: {channel_id}")
            print(f"   Room ID: {room_id}")
            print(f"   Guild Name: {guild_name}")
            print(f"   Channel Name: {channel_name}")
            import traceback
            traceback.print_exc()
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
    
    async def get_room_messages(self, room_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent messages for a room."""
        try:
            async with self.pool.acquire() as conn:
                results = await conn.fetch("""
                    SELECT 
                        cm.message_id,
                        cm.guild_id,
                        cm.channel_id,
                        cm.user_id,
                        cm.username,
                        cm.guild_name,
                        cm.content,
                        cm.reply_to_message_id,
                        cm.reply_to_username,
                        cm.reply_to_content,
                        cm.timestamp,
                        cc.channel_name
                    FROM chat_messages cm
                    LEFT JOIN chat_channels cc ON cm.channel_id = cc.channel_id 
                        AND cm.guild_id = cc.guild_id
                    WHERE cm.room_id = $1 
                    ORDER BY cm.timestamp DESC 
                    LIMIT $2 OFFSET $3
                """, room_id, limit, offset)
                
                return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Get room messages error: {e}")
            return []
    
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
                    WHERE timestamp >= NOW() - INTERVAL '%s days'
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
                    WHERE timestamp >= NOW() - INTERVAL '%s days'
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
    
    async def update_room(self, room_id: int, name: str = None, max_servers: int = None, is_active: bool = None) -> bool:
        """Update room settings."""
        try:
            updates = []
            params = []
            param_index = 1
            
            if name is not None:
                updates.append(f"name = ${param_index}")
                params.append(name)
                param_index += 1
            
            if max_servers is not None:
                updates.append(f"max_servers = ${param_index}")
                params.append(max_servers)
                param_index += 1
                
            if is_active is not None:
                updates.append(f"is_active = ${param_index}")
                params.append(is_active)
                param_index += 1
            
            if not updates:
                return True  # Nothing to update
            
            params.append(room_id)
            query = f"""
                UPDATE chat_rooms 
                SET {', '.join(updates)}
                WHERE id = ${param_index}
            """
            
            async with self.pool.acquire() as conn:
                await conn.execute(query, *params)
                print(f"✅ Updated room {room_id}")
                return True
                
        except Exception as e:
            print(f"❌ Update room error: {e}")
            return False
    
    async def unregister_channel(self, guild_id: str, channel_id: str, room_id: int) -> bool:
        """Unregister a channel from a room by setting it as inactive."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE chat_channels 
                    SET is_active = false
                    WHERE guild_id = $1 AND channel_id = $2 AND room_id = $3
                """, guild_id, channel_id, room_id)
                
                print(f"✅ Unregistered channel {channel_id} from room {room_id}")
                return True
                
        except Exception as e:
            print(f"❌ Unregister channel error: {e}")
            return False
    
    async def ban_server(self, guild_id: str, guild_name: str, banned_by: str, reason: str = None) -> bool:
        """Ban a server from subscribing to any chat rooms."""
        try:
            async with self.pool.acquire() as conn:
                # Check if already banned
                existing_ban = await conn.fetchval("""
                    SELECT id FROM server_bans 
                    WHERE guild_id = $1 AND is_active = true
                """, guild_id)
                
                if existing_ban:
                    print(f"⚠️ Server {guild_id} is already banned")
                    return True
                
                # Insert new ban
                await conn.execute("""
                    INSERT INTO server_bans (guild_id, guild_name, banned_by, reason)
                    VALUES ($1, $2, $3, $4)
                """, guild_id, guild_name, banned_by, reason)
                
                # Deactivate all channels for this server
                await conn.execute("""
                    UPDATE chat_channels 
                    SET is_active = false
                    WHERE guild_id = $1
                """, guild_id)
                
                print(f"✅ Banned server {guild_id} ({guild_name})")
                return True
                
        except Exception as e:
            print(f"❌ Ban server error: {e}")
            return False
    
    async def unban_server(self, guild_id: str, unbanned_by: str) -> bool:
        """Unban a server, allowing them to subscribe to chat rooms again."""
        try:
            async with self.pool.acquire() as conn:
                # Update the ban record
                result = await conn.execute("""
                    UPDATE server_bans 
                    SET is_active = false, unbanned_by = $2, unbanned_at = NOW()
                    WHERE guild_id = $1 AND is_active = true
                """, guild_id, unbanned_by)
                
                print(f"✅ Unbanned server {guild_id}")
                return True
                
        except Exception as e:
            print(f"❌ Unban server error: {e}")
            return False
    
    async def is_server_banned(self, guild_id: str) -> bool:
        """Check if a server is currently banned."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1 FROM server_bans 
                        WHERE guild_id = $1 AND is_active = true
                    )
                """, guild_id)
                
                return bool(result)
                
        except Exception as e:
            print(f"❌ Check server ban error: {e}")
            return False
    
    async def get_banned_servers(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all banned servers."""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT guild_id, guild_name, banned_by, banned_at, reason, is_active,
                           unbanned_by, unbanned_at
                    FROM server_bans 
                """
                
                if not include_inactive:
                    query += " WHERE is_active = true"
                
                query += " ORDER BY banned_at DESC"
                
                results = await conn.fetch(query)
                return [dict(row) for row in results]
                
        except Exception as e:
            print(f"❌ Get banned servers error: {e}")
            return []


# Global instance
db_manager = DatabaseManager()