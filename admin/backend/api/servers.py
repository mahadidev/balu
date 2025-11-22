"""
Server and channel management API routes for the admin panel.
Handles Discord server monitoring and channel registration management.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..api.auth import get_current_user
from shared.database.manager import db_manager
from shared.cache.cache_manager import cache_manager


# Response models
class ServerResponse(BaseModel):
    guild_id: str
    guild_name: str
    total_channels: int
    active_channels: int
    rooms_connected: List[str]
    last_activity: Optional[datetime]
    message_count_7d: int
    status: str

class ChannelResponse(BaseModel):
    guild_id: str
    channel_id: str
    guild_name: str
    channel_name: str
    room_id: int
    room_name: str
    registered_by: str
    registered_at: datetime
    is_active: bool
    message_count_7d: int

class ServerDetailsResponse(BaseModel):
    guild_id: str
    guild_name: str
    channels: List[ChannelResponse]
    statistics: Dict[str, Any]
    permissions: Dict[str, Any]

class ServerBanResponse(BaseModel):
    guild_id: str
    guild_name: str
    banned_by: str
    banned_at: datetime
    reason: Optional[str]
    is_active: bool
    unbanned_by: Optional[str]
    unbanned_at: Optional[datetime]

class BanServerRequest(BaseModel):
    guild_id: str
    guild_name: str
    reason: Optional[str] = Field(None, max_length=500, description="Reason for banning")

class UnbanServerRequest(BaseModel):
    guild_id: str


# Router
router = APIRouter(prefix="/servers", tags=["servers"])


# ============================================================================
# SERVER OVERVIEW
# ============================================================================

@router.get("/", response_model=List[ServerResponse])
async def list_servers(
    active_only: bool = Query(True, description="Show only active servers"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all Discord servers using the global chat system."""
    try:
        # Get all rooms to build server list
        all_rooms = await db_manager.get_all_rooms(include_inactive=not active_only)
        
        # Build server mapping
        servers_map = {}
        
        for room in all_rooms:
            channels = await db_manager.get_room_channels(room['id'])
            
            for channel in channels:
                guild_id = channel['guild_id']
                guild_name = channel['guild_name']
                
                if guild_id not in servers_map:
                    servers_map[guild_id] = {
                        'guild_id': guild_id,
                        'guild_name': guild_name,
                        'total_channels': 0,
                        'active_channels': 0,
                        'rooms_connected': set(),
                        'last_activity': None,
                        'message_count_7d': 0,
                        'status': 'active'
                    }
                
                server_info = servers_map[guild_id]
                server_info['total_channels'] += 1
                server_info['active_channels'] += 1  # All channels from DB are active
                server_info['rooms_connected'].add(room['name'])
        
        # Convert sets to lists and finalize response
        servers = []
        for server_info in servers_map.values():
            server_info['rooms_connected'] = list(server_info['rooms_connected'])
            servers.append(ServerResponse(**server_info))
        
        # Sort by guild name
        servers.sort(key=lambda x: x.guild_name.lower())
        
        return servers
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching servers: {str(e)}"
        )


# ============================================================================
# SERVER BANNING
# ============================================================================

@router.get("/banned-list", response_model=List[ServerBanResponse])
async def list_banned_servers(
    include_inactive: bool = Query(False, description="Include unbanned servers"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get list of all banned servers."""
    try:
        banned_servers = await db_manager.get_banned_servers(include_inactive=include_inactive)
        return [ServerBanResponse(**server) for server in banned_servers]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching banned servers: {str(e)}"
        )

@router.post("/bans")
async def ban_server(
    request: BanServerRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Ban a Discord server from subscribing to any chat rooms."""
    try:
        # Check if server is already banned
        is_banned = await db_manager.is_server_banned(request.guild_id)
        if is_banned:
            raise HTTPException(
                status_code=400,
                detail=f"Server {request.guild_id} is already banned"
            )
        
        # Ban the server
        success = await db_manager.ban_server(
            guild_id=request.guild_id,
            guild_name=request.guild_name,
            banned_by=current_user.get("username", "admin"),
            reason=request.reason
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to ban server"
            )
        
        # Clear related caches - invalidate all cache entries for this server
        await cache_manager.invalidate_server_cache(request.guild_id)
        
        return {
            "success": True,
            "message": f"Server {request.guild_name} ({request.guild_id}) has been banned",
            "guild_id": request.guild_id,
            "banned_by": current_user.get("username", "admin"),
            "reason": request.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error banning server: {str(e)}"
        )

@router.delete("/bans/{guild_id}")
async def unban_server(
    guild_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Unban a Discord server, allowing them to subscribe to chat rooms again."""
    try:
        # Check if server is actually banned
        is_banned = await db_manager.is_server_banned(guild_id)
        if not is_banned:
            raise HTTPException(
                status_code=400,
                detail=f"Server {guild_id} is not currently banned"
            )
        
        # Unban the server
        success = await db_manager.unban_server(
            guild_id=guild_id,
            unbanned_by=current_user.get("username", "admin")
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to unban server"
            )
        
        # Clear related caches - invalidate all cache entries for this server
        await cache_manager.invalidate_server_cache(guild_id)
        
        return {
            "success": True,
            "message": f"Server {guild_id} has been unbanned",
            "guild_id": guild_id,
            "unbanned_by": current_user.get("username", "admin")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error unbanning server: {str(e)}"
        )

@router.get("/bans/{guild_id}")
async def check_server_ban_status(
    guild_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Check if a specific server is banned."""
    try:
        is_banned = await db_manager.is_server_banned(guild_id)
        
        ban_details = None
        if is_banned:
            # Get ban details
            banned_servers = await db_manager.get_banned_servers(include_inactive=False)
            ban_details = next((server for server in banned_servers if server['guild_id'] == guild_id), None)
        
        return {
            "guild_id": guild_id,
            "is_banned": is_banned,
            "ban_details": ban_details
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking server ban status: {str(e)}"
        )


# ============================================================================
# SERVER DETAILS
# ============================================================================

@router.get("/{guild_id}", response_model=ServerDetailsResponse)
async def get_server_details(
    guild_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed information about a specific Discord server."""
    try:
        server_channels = []
        server_name = "Unknown Server"
        
        # Get all rooms to find channels for this guild
        all_rooms = await db_manager.get_all_rooms(include_inactive=True)
        
        for room in all_rooms:
            channels = await db_manager.get_room_channels(room['id'])
            
            for channel in channels:
                if channel['guild_id'] == guild_id:
                    server_name = channel['guild_name']
                    channel_response = ChannelResponse(
                        guild_id=channel['guild_id'],
                        channel_id=channel['channel_id'],
                        guild_name=channel['guild_name'],
                        channel_name=channel['channel_name'],
                        room_id=room['id'],
                        room_name=room['name'],
                        registered_by=channel['registered_by'],
                        registered_at=datetime.utcnow(),  # TODO: Get actual from DB
                        is_active=True,
                        message_count_7d=0  # TODO: Calculate from message stats
                    )
                    server_channels.append(channel_response)
        
        if not server_channels:
            raise HTTPException(
                status_code=404,
                detail="Server not found or has no registered channels"
            )
        
        # Calculate server statistics
        statistics = {
            "total_channels": len(server_channels),
            "active_rooms": len(set(ch.room_id for ch in server_channels)),
            "total_messages_7d": sum(ch.message_count_7d for ch in server_channels),
            "registration_dates": [ch.registered_at for ch in server_channels],
            "most_active_room": None  # TODO: Calculate from message counts
        }
        
        # Get permissions (use first room's permissions as example)
        first_room_id = server_channels[0].room_id
        permissions = await db_manager.get_room_permissions(first_room_id)
        
        return ServerDetailsResponse(
            guild_id=guild_id,
            guild_name=server_name,
            channels=server_channels,
            statistics=statistics,
            permissions=permissions
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching server details: {str(e)}"
        )


# ============================================================================
# CHANNEL MANAGEMENT
# ============================================================================

@router.get("/channels", response_model=List[ChannelResponse])
async def list_all_channels(
    room_id: Optional[int] = Query(None, description="Filter by room ID"),
    guild_id: Optional[str] = Query(None, description="Filter by guild ID"),
    active_only: bool = Query(True, description="Show only active channels"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all registered Discord channels across all rooms."""
    try:
        all_channels = []
        
        # Get rooms based on filter
        if room_id:
            # Get specific room
            all_rooms = await db_manager.get_all_rooms(include_inactive=True)
            rooms = [room for room in all_rooms if room['id'] == room_id]
            if not rooms:
                raise HTTPException(status_code=404, detail="Room not found")
        else:
            # Get all rooms
            rooms = await db_manager.get_all_rooms(include_inactive=not active_only)
        
        # Collect channels from rooms
        for room in rooms:
            channels = await db_manager.get_room_channels(room['id'])
            
            for channel in channels:
                # Apply guild filter if specified
                if guild_id and channel['guild_id'] != guild_id:
                    continue
                
                channel_response = ChannelResponse(
                    guild_id=channel['guild_id'],
                    channel_id=channel['channel_id'],
                    guild_name=channel['guild_name'],
                    channel_name=channel['channel_name'],
                    room_id=room['id'],
                    room_name=room['name'],
                    registered_by=channel['registered_by'],
                    registered_at=datetime.utcnow(),  # TODO: Get actual from DB
                    is_active=room['is_active'],
                    message_count_7d=0  # TODO: Calculate from message stats
                )
                all_channels.append(channel_response)
        
        # Sort by guild name, then channel name
        all_channels.sort(key=lambda x: (x.guild_name.lower(), x.channel_name.lower()))
        
        return all_channels
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching channels: {str(e)}"
        )

@router.delete("/channels/{guild_id}/{channel_id}")
async def unregister_channel(
    guild_id: str,
    channel_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Unregister a Discord channel from all rooms."""
    try:
        # TODO: Implement channel unregistration
        # This requires adding an unregister method to database manager
        
        # For now, invalidate caches
        await cache_manager.invalidate_channel_registration(guild_id, channel_id)
        
        return {
            "message": "Channel unregistration not yet implemented",
            "guild_id": guild_id,
            "channel_id": channel_id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error unregistering channel: {str(e)}"
        )


# ============================================================================
# SERVER STATISTICS
# ============================================================================

@router.get("/{guild_id}/stats")
async def get_server_statistics(
    guild_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed statistics for a specific Discord server."""
    try:
        # TODO: Implement server-specific statistics
        # This would require complex queries to aggregate message data by guild
        
        return {
            "guild_id": guild_id,
            "period_days": days,
            "message_count": 0,
            "unique_users": 0,
            "channels_active": 0,
            "rooms_participated": 0,
            "daily_breakdown": [],
            "peak_activity_hour": None,
            "most_active_channel": None,
            "message": "Server-specific statistics not yet implemented"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching server statistics: {str(e)}"
        )

@router.get("/{guild_id}/activity")
async def get_server_activity(
    guild_id: str,
    hours: int = Query(24, ge=1, le=168, description="Number of hours to analyze"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get recent activity for a specific Discord server."""
    try:
        # TODO: Implement server activity tracking
        # This would show recent message activity, user activity, etc.
        
        return {
            "guild_id": guild_id,
            "period_hours": hours,
            "recent_messages": [],
            "active_users": [],
            "active_channels": [],
            "activity_timeline": [],
            "message": "Server activity tracking not yet implemented"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching server activity: {str(e)}"
        )


# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/bulk/refresh-cache")
async def refresh_server_cache(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Refresh cache for all server and channel data."""
    try:
        # Get all rooms and their channels
        all_rooms = await db_manager.get_all_rooms(include_inactive=True)
        
        refreshed_count = 0
        for room in all_rooms:
            # Get fresh data
            channels = await db_manager.get_room_channels(room['id'])
            permissions = await db_manager.get_room_permissions(room['id'])
            
            # Refresh cache
            await cache_manager.warmup_cache(room, channels, permissions)
            refreshed_count += 1
        
        return {
            "message": f"Cache refreshed for {refreshed_count} rooms",
            "rooms_refreshed": refreshed_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing cache: {str(e)}"
        )