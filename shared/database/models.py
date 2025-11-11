"""
PostgreSQL database models for Global Chat System.
Optimized for high throughput with proper indexes and relationships.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class ChatRoom(Base):
    """Chat rooms for cross-server communication."""
    __tablename__ = "chat_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    created_by = Column(String(20), nullable=False)  # Discord user ID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    max_servers = Column(Integer, default=50)
    
    # Relationships
    channels = relationship("ChatChannel", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")
    permissions = relationship("RoomPermission", back_populates="room", uselist=False, cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_room_active_created', 'is_active', 'created_at'),
    )

class ChatChannel(Base):
    """Registered Discord channels for each room."""
    __tablename__ = "chat_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(String(20), nullable=False, index=True)  # Discord guild ID
    channel_id = Column(String(20), nullable=False, index=True)  # Discord channel ID
    guild_name = Column(String(100), nullable=False)
    channel_name = Column(String(100), nullable=False)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    registered_by = Column(String(20), nullable=False)  # Discord user ID
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    room = relationship("ChatRoom", back_populates="channels")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_channel_guild_channel', 'guild_id', 'channel_id', unique=True),
        Index('ix_channel_room_active', 'room_id', 'is_active'),
        Index('ix_channel_registered', 'registered_at'),
    )

class ChatMessage(Base):
    """All chat messages for analytics and reply functionality."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(20), nullable=False, index=True)  # Discord message ID
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False, index=True)
    guild_id = Column(String(20), nullable=False, index=True)
    channel_id = Column(String(20), nullable=False, index=True)
    user_id = Column(String(20), nullable=False, index=True)  # Discord user ID
    username = Column(String(100), nullable=False)
    guild_name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    
    # Reply functionality
    reply_to_message_id = Column(String(20), nullable=True, index=True)
    reply_to_username = Column(String(100), nullable=True)
    reply_to_content = Column(Text, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    room = relationship("ChatRoom", back_populates="messages")
    
    # Indexes for performance (critical for high volume)
    __table_args__ = (
        Index('ix_message_room_timestamp', 'room_id', 'timestamp'),
        Index('ix_message_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_message_reply', 'reply_to_message_id'),
        Index('ix_message_guild_timestamp', 'guild_id', 'timestamp'),
    )

class RoomPermission(Base):
    """Permission settings for each chat room."""
    __tablename__ = "room_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), unique=True, nullable=False)
    
    # Content permissions
    allow_urls = Column(Boolean, default=False)
    allow_files = Column(Boolean, default=False)
    allow_mentions = Column(Boolean, default=True)
    allow_emojis = Column(Boolean, default=True)
    enable_bad_word_filter = Column(Boolean, default=True)
    
    # Rate limiting
    max_message_length = Column(Integer, default=2000)
    rate_limit_seconds = Column(Integer, default=3)
    
    # Metadata
    updated_by = Column(String(20), nullable=False)  # Discord user ID
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    room = relationship("ChatRoom", back_populates="permissions")

class SystemSettings(Base):
    """Global system settings."""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AdminUser(Base):
    """Admin panel users."""
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    discord_id = Column(String(20), nullable=True, unique=True, index=True)  # Link to Discord
    is_active = Column(Boolean, default=True, index=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_admin_active_created', 'is_active', 'created_at'),
    )

# Analytics Views (for admin panel performance)
class DailyStats(Base):
    """Daily message statistics (materialized view or updated via background job)."""
    __tablename__ = "daily_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False, index=True)
    message_count = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    unique_guilds = Column(Integer, default=0)
    
    # Relationships
    room = relationship("ChatRoom")
    
    # Indexes
    __table_args__ = (
        Index('ix_stats_date_room', 'date', 'room_id', unique=True),
    )