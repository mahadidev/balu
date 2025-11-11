"""
Room management API routes for the admin panel.
Handles room CRUD operations, permissions, and channel management.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..api.auth import get_current_user
from ...shared.database.manager import db_manager
from ...shared.cache.cache_manager import cache_manager
from ..core.websocket import connection_manager


# Request/Response models
class RoomResponse(BaseModel):
    id: int
    name: str
    created_by: str
    created_at: datetime
    is_active: bool
    max_servers: int
    channel_count: int

class CreateRoomRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Room name")
    max_servers: int = Field(50, ge=1, le=200, description="Maximum servers allowed")

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


# Router
router = APIRouter(prefix="/rooms", tags=["rooms"])


# ============================================================================
# ROOM OPERATIONS
# ============================================================================

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
        
        # Get created room data
        room_data = await db_manager.get_room_by_name(request.name)
        if not room_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve created room"
            )
        
        # Get permissions and channels for cache warmup
        permissions = await db_manager.get_room_permissions(room_id)
        channels = await db_manager.get_room_channels(room_id)
        
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
        # TODO: Implement room update in database
        # For now, return not implemented
        raise HTTPException(
            status_code=501,
            detail="Room update not yet implemented"
        )
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
        # TODO: Implement channel unregistration in database
        # For now, return not implemented
        raise HTTPException(
            status_code=501,
            detail="Channel unregistration not yet implemented"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error unregistering channel: {str(e)}"
        )