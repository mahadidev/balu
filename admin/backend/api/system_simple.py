"""
Simplified system management API routes for the admin panel.
Handles basic system operations without heavy dependencies.
"""

from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..api.auth import get_current_user


# Request/Response models
class ClearDataRequest(BaseModel):
    confirm: bool = False
    keep_rooms: bool = True
    keep_channels: bool = True
    
class ClearDataResponse(BaseModel):
    success: bool
    message: str
    cleared_items: Dict[str, int]


# Router
router = APIRouter(prefix="/system", tags=["system"])


@router.post("/clear-data", response_model=ClearDataResponse)
async def clear_all_data(
    request: ClearDataRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Clear all data from the system (messages, stats, etc.)."""
    if not request.confirm:
        raise HTTPException(
            status_code=400,
            detail="Must confirm data clearing by setting 'confirm' to true"
        )
    
    try:
        # Import database dependencies only when needed
        from shared.database.manager import db_manager
        from shared.cache.redis_client import redis_client
        
        cleared_items = {}
        
        # Clear messages and stats from database
        try:
            async with db_manager.session() as session:
                # Import models inside the function to avoid startup issues
                from shared.database.models import ChatMessage, DailyStats
                from sqlalchemy import select, delete, func
                
                # Count items before clearing
                message_count_result = await session.execute(select(func.count(ChatMessage.id)))
                message_count = message_count_result.scalar() or 0
                
                stats_count_result = await session.execute(select(func.count(DailyStats.id)))
                stats_count = stats_count_result.scalar() or 0
                
                # Clear messages
                if message_count > 0:
                    await session.execute(delete(ChatMessage))
                    cleared_items['messages'] = message_count
                
                # Clear daily stats
                if stats_count > 0:
                    await session.execute(delete(DailyStats))
                    cleared_items['daily_stats'] = stats_count
                
                # Optionally clear rooms and channels
                if not request.keep_rooms:
                    from shared.database.models import ChatRoom, RoomPermission
                    room_count_result = await session.execute(select(func.count(ChatRoom.id)))
                    room_count = room_count_result.scalar() or 0
                    
                    if room_count > 0:
                        # Clear permissions first due to foreign key
                        await session.execute(delete(RoomPermission))
                        await session.execute(delete(ChatRoom))
                        cleared_items['rooms'] = room_count
                
                if not request.keep_channels:
                    from shared.database.models import ChatChannel
                    channel_count_result = await session.execute(select(func.count(ChatChannel.id)))
                    channel_count = channel_count_result.scalar() or 0
                    
                    if channel_count > 0:
                        await session.execute(delete(ChatChannel))
                        cleared_items['channels'] = channel_count
                
                await session.commit()
                
        except Exception as db_error:
            # If database operations fail, log but continue
            print(f"Database error during clear: {db_error}")
            cleared_items['database_error'] = 1
        
        # Clear Redis cache
        try:
            await redis_client.client.flushdb()
            cleared_items['cache_entries'] = 1
        except Exception as cache_error:
            # Log but don't fail the whole operation
            print(f"Warning: Failed to clear Redis cache: {cache_error}")
        
        return ClearDataResponse(
            success=True,
            message=f"Successfully cleared data. Items removed: {sum(cleared_items.values())}",
            cleared_items=cleared_items
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing data: {str(e)}"
        )


@router.post("/reset-settings")
async def reset_settings(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Reset all system settings to defaults."""
    # This is a placeholder for future settings implementation
    raise HTTPException(
        status_code=501,
        detail="Settings reset not yet implemented"
    )