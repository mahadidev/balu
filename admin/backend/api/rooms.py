"""
Room management API routes for the admin panel.
Handles room CRUD operations, permissions, and channel management.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..api.auth import get_current_user
from shared.database.manager import db_manager
from shared.cache.cache_manager import cache_manager
from ..core.websocket import connection_manager


def format_message_for_display(message: Dict[str, Any]) -> str:
    """Format a message for display in the admin panel to match Discord appearance."""
    # Create the Discord message URL
    message_url = f"https://discord.com/channels/{message.get('guild_id', 'unknown')}/{message.get('channel_id', 'unknown')}/{message['message_id']}"
    
    # Format reply context if this is a reply
    reply_context = ""
    if message.get('reply_to_username'):
        reply_content = message.get('reply_to_content', '').strip()
        if len(reply_content) > 50:
            reply_content = reply_content[:47] + "..."
        reply_context = f"┌─ Replying to {message['reply_to_username']}: *{reply_content}*\n└─ "
    
    # Create the formatted message content
    formatted_content = f"{reply_context}{message_url} • **{message['username']}**: ** {message['content']} \n\n"
    
    return formatted_content


# Request/Response models
class RoomResponse(BaseModel):
    id: int
    name: str
    created_by: str
    created_at: datetime
    is_active: bool
    max_servers: int
    channel_count: int
    messages_today: int

class CreateRoomRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Room name")
    max_servers: int = Field(50, ge=1, le=200, description="Maximum servers allowed")
    permissions: Optional[Dict[str, Any]] = Field(None, description="Room permissions")

class UpdateRoomRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    max_servers: Optional[int] = Field(None, ge=1, le=200)
    is_active: Optional[bool] = None

class RoomPermissionsResponse(BaseModel):
    room_id: int
    allow_urls: bool
    allow_files: bool
    allow_mentions: bool
    allow_emojis: bool
    enable_bad_word_filter: bool
    max_message_length: int
    rate_limit_seconds: int
    updated_by: str
    updated_at: datetime

class UpdatePermissionsRequest(BaseModel):
    allow_urls: Optional[bool] = None
    allow_files: Optional[bool] = None
    allow_mentions: Optional[bool] = None
    allow_emojis: Optional[bool] = None
    enable_bad_word_filter: Optional[bool] = None
    max_message_length: Optional[int] = Field(None, ge=1, le=4000)
    rate_limit_seconds: Optional[int] = Field(None, ge=0, le=60)

class ChannelResponse(BaseModel):
    guild_id: str
    channel_id: str
    guild_name: str
    channel_name: str
    registered_by: str
    registered_at: datetime

class RegisterChannelRequest(BaseModel):
    guild_id: str
    channel_id: str
    guild_name: str
    channel_name: str

class MessageResponse(BaseModel):
    message_id: str
    user_id: str
    username: str
    guild_name: str
    content: str
    reply_to_message_id: Optional[str] = None
    reply_to_username: Optional[str] = None
    reply_to_content: Optional[str] = None
    timestamp: datetime
    channel_name: Optional[str] = None
    formatted_content: str


# Router
router = APIRouter(prefix="/rooms", tags=["rooms"])


# ============================================================================
# ROOM OPERATIONS
# ============================================================================

@router.get("", response_model=List[RoomResponse])
@router.get("/", response_model=List[RoomResponse])
async def list_rooms(
    include_inactive: bool = Query(False, description="Include inactive rooms"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all chat rooms with channel counts."""
    try:
        rooms = await db_manager.get_all_rooms(include_inactive=include_inactive)
        return [RoomResponse(**room) for room in rooms]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching rooms: {str(e)}"
        )

@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get specific room details."""
    try:
        # Try cache first
        room_data = await cache_manager.get_room_by_id(room_id)
        
        if not room_data:
            # Get from database
            rooms = await db_manager.get_all_rooms(include_inactive=True)
            room_data = next((r for r in rooms if r['id'] == room_id), None)
            
            if not room_data:
                raise HTTPException(status_code=404, detail="Room not found")
            
            # Cache the result
            await cache_manager.set_room_by_id(room_id, room_data)
        
        return RoomResponse(**room_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching room: {str(e)}"
        )

@router.post("/clear-data")
async def clear_all_system_data(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """COMPLETELY CLEAR ALL DATABASE DATA - messages, channels, rooms, stats, etc."""
    try:
        cleared_items = {}
        
        # Clear ALL data from database
        async with db_manager.session() as session:
            from shared.database.models import ChatMessage, DailyStats, ChatChannel, ChatRoom, RoomPermission
            from sqlalchemy import select, delete, func
            
            # Count all items first
            message_count = (await session.execute(select(func.count(ChatMessage.id)))).scalar() or 0
            stats_count = (await session.execute(select(func.count(DailyStats.id)))).scalar() or 0
            channel_count = (await session.execute(select(func.count(ChatChannel.id)))).scalar() or 0
            room_count = (await session.execute(select(func.count(ChatRoom.id)))).scalar() or 0
            permission_count = (await session.execute(select(func.count(RoomPermission.id)))).scalar() or 0
            
            # Clear in the correct order to avoid foreign key constraints
            
            # 1. Clear messages first
            if message_count > 0:
                await session.execute(delete(ChatMessage))
                cleared_items['messages'] = message_count
            
            # 2. Clear daily stats
            if stats_count > 0:
                await session.execute(delete(DailyStats))
                cleared_items['daily_stats'] = stats_count
            
            # 3. Clear channels
            if channel_count > 0:
                await session.execute(delete(ChatChannel))
                cleared_items['channels'] = channel_count
            
            # 4. Clear room permissions (depends on rooms)
            if permission_count > 0:
                await session.execute(delete(RoomPermission))
                cleared_items['room_permissions'] = permission_count
            
            # 5. Clear rooms last
            if room_count > 0:
                await session.execute(delete(ChatRoom))
                cleared_items['rooms'] = room_count
            
            await session.commit()
        
        # Clear Redis cache completely
        try:
            from shared.cache.redis_client import redis_client
            await redis_client.client.flushdb()
            cleared_items['cache_entries'] = 1
        except Exception as cache_error:
            print(f"Warning: Failed to clear Redis cache: {cache_error}")
        
        return {
            "success": True,
            "message": f"DATABASE COMPLETELY CLEARED! Removed {sum(cleared_items.values())} items. All messages, channels, rooms, and stats have been deleted.",
            "cleared_items": cleared_items,
            "warning": "All data has been permanently deleted and cannot be recovered."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing all data: {str(e)}"
        )

@router.post("/", response_model=RoomResponse)
async def create_room(
    request: CreateRoomRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create new chat room."""
    try:
        # Check if room name already exists
        existing_room = await db_manager.get_room_by_name(request.name)
        if existing_room:
            raise HTTPException(
                status_code=400,
                detail="Room name already exists"
            )
        
        # Create room
        room_id = await db_manager.create_room(
            name=request.name,
            created_by=current_user.get("username", "admin"),
            max_servers=request.max_servers
        )
        
        if not room_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to create room"
            )
        
        # Get channels for cache warmup
        channels = await db_manager.get_room_channels(room_id)
        
        # Set permissions if provided in request
        if request.permissions:
            # TODO: Implement permission setting in database manager
            # For now, we'll just get default permissions
            permissions = await db_manager.get_room_permissions(room_id)
        else:
            # Get default permissions
            permissions = await db_manager.get_room_permissions(room_id)
        
        # Construct room data manually since get_room_by_name doesn't include channel_count
        room_data = {
            'id': room_id,
            'name': request.name,
            'created_by': current_user.get("username", "admin"),
            'created_at': datetime.utcnow(),
            'is_active': True,
            'max_servers': request.max_servers,
            'channel_count': len(channels),
            'messages_today': 0  # New rooms start with 0 messages
        }
        
        # Warmup cache
        await cache_manager.warmup_cache(room_data, channels, permissions)
        
        # Broadcast room creation
        await connection_manager.broadcast_room_update({
            'action': 'created',
            'room': room_data
        })
        
        return RoomResponse(**room_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating room: {str(e)}"
        )

@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: int,
    request: UpdateRoomRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update room settings."""
    try:
        # Update room in database
        success = await db_manager.update_room(
            room_id=room_id,
            name=request.name,
            max_servers=request.max_servers,
            is_active=request.is_active
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update room"
            )
        
        # Get updated room data
        rooms = await db_manager.get_all_rooms(include_inactive=True)
        room_data = next((r for r in rooms if r['id'] == room_id), None)
        
        if not room_data:
            raise HTTPException(status_code=404, detail="Room not found after update")
        
        # Clear cache
        await cache_manager.invalidate_room_cache(room_id)
        
        # Broadcast room update
        await connection_manager.broadcast_room_update({
            'action': 'updated',
            'room': room_data
        })
        
        return RoomResponse(**room_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating room: {str(e)}"
        )

@router.delete("/{room_id}")
async def delete_room(
    room_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deactivate/delete room."""
    try:
        # TODO: Implement room deactivation in database
        # For now, return not implemented
        raise HTTPException(
            status_code=501,
            detail="Room deletion not yet implemented"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting room: {str(e)}"
        )


# ============================================================================
# ROOM PERMISSIONS
# ============================================================================

@router.get("/{room_id}/permissions", response_model=Dict[str, Any])
async def get_room_permissions(
    room_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get room permissions."""
    try:
        # Try cache first
        permissions = await cache_manager.get_room_permissions(room_id)
        
        if not permissions:
            # Get from database
            permissions = await db_manager.get_room_permissions(room_id)
            if permissions:
                # Cache the result
                await cache_manager.set_room_permissions(room_id, permissions)
        
        if not permissions:
            raise HTTPException(status_code=404, detail="Room permissions not found")
        
        return permissions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching permissions: {str(e)}"
        )

@router.put("/{room_id}/permissions")
async def update_room_permissions(
    room_id: int,
    request: UpdatePermissionsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update room permissions."""
    try:
        # TODO: Implement permissions update in database
        # For now, return not implemented
        raise HTTPException(
            status_code=501,
            detail="Permission update not yet implemented"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating permissions: {str(e)}"
        )


# ============================================================================
# SYSTEM MANAGEMENT
# ============================================================================

@router.post("/system/clear-data")
async def clear_all_data(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Clear all data from the system (messages, stats, etc.)."""
    try:
        cleared_items = {}
        
        # Clear messages and stats from database
        async with db_manager.session() as session:
            from shared.database.models import ChatMessage, DailyStats
            from sqlalchemy import select, delete, func
            
            # Count and clear messages
            message_count_result = await session.execute(select(func.count(ChatMessage.id)))
            message_count = message_count_result.scalar() or 0
            
            if message_count > 0:
                await session.execute(delete(ChatMessage))
                cleared_items['messages'] = message_count
            
            # Count and clear daily stats  
            stats_count_result = await session.execute(select(func.count(DailyStats.id)))
            stats_count = stats_count_result.scalar() or 0
            
            if stats_count > 0:
                await session.execute(delete(DailyStats))
                cleared_items['daily_stats'] = stats_count
            
            await session.commit()
        
        # Clear Redis cache
        try:
            from shared.cache.redis_client import redis_client
            await redis_client.client.flushdb()
            cleared_items['cache_entries'] = 1
        except Exception as cache_error:
            print(f"Warning: Failed to clear Redis cache: {cache_error}")
        
        return {
            "success": True,
            "message": f"Data cleared successfully! Removed {sum(cleared_items.values())} items.",
            "cleared_items": cleared_items
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing data: {str(e)}"
        )


# ============================================================================
# CHANNEL MANAGEMENT
# ============================================================================

@router.get("/{room_id}/channels", response_model=List[ChannelResponse])
async def list_room_channels(
    room_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all channels registered to a room."""
    try:
        # Try cache first
        channels = await cache_manager.get_room_channels(room_id)
        
        if not channels:
            # Get from database
            channels = await db_manager.get_room_channels(room_id)
            if channels:
                # Cache the result
                await cache_manager.set_room_channels(room_id, channels)
        
        # Add registered_at field for response model
        for channel in channels:
            channel['registered_at'] = datetime.utcnow()  # TODO: Get actual timestamp from DB
        
        return [ChannelResponse(**channel) for channel in channels]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching channels: {str(e)}"
        )

@router.post("/{room_id}/channels")
async def register_channel_to_room(
    room_id: int,
    request: RegisterChannelRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Register a Discord channel to a room."""
    try:
        success = await db_manager.register_channel(
            guild_id=request.guild_id,
            channel_id=request.channel_id,
            room_id=room_id,
            guild_name=request.guild_name,
            channel_name=request.channel_name,
            registered_by=current_user.get("username", "admin")
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to register channel"
            )
        
        # Invalidate related caches
        await cache_manager.invalidate_channel_registration(request.guild_id, request.channel_id)
        await cache_manager.invalidate_room_channels(room_id)
        
        # Broadcast channel registration
        await connection_manager.broadcast_channel_update({
            'action': 'registered',
            'room_id': room_id,
            'channel': {
                'guild_id': request.guild_id,
                'channel_id': request.channel_id,
                'guild_name': request.guild_name,
                'channel_name': request.channel_name
            }
        })
        
        return {"message": "Channel registered successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error registering channel: {str(e)}"
        )

@router.delete("/{room_id}/channels/{guild_id}/{channel_id}")
async def unregister_channel_from_room(
    room_id: int,
    guild_id: str,
    channel_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Unregister a Discord channel from a room."""
    try:
        # Unregister channel from database
        success = await db_manager.unregister_channel(
            guild_id=guild_id,
            channel_id=channel_id,
            room_id=room_id
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to unregister channel"
            )
        
        # Invalidate related caches
        await cache_manager.invalidate_channel_registration(guild_id, channel_id)
        await cache_manager.invalidate_room_channels(room_id)
        
        # Broadcast channel unregistration
        await connection_manager.broadcast_channel_update({
            'action': 'unregistered',
            'room_id': room_id,
            'channel': {
                'guild_id': guild_id,
                'channel_id': channel_id
            }
        })
        
        return {"message": "Channel unregistered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error unregistering channel: {str(e)}"
        )

@router.get("/{room_id}/messages", response_model=List[MessageResponse])
async def get_room_messages(
    room_id: int,
    limit: int = Query(50, ge=1, le=100, description="Number of messages to fetch"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get messages for a room."""
    try:
        messages = await db_manager.get_room_messages(room_id, limit, offset)
        
        # Format each message for display
        formatted_messages = []
        for message in messages:
            formatted_content = format_message_for_display(message)
            message['formatted_content'] = formatted_content
            formatted_messages.append(MessageResponse(**message))
        
        return formatted_messages
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching room messages: {str(e)}"
        )