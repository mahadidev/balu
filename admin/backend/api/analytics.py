"""
Analytics and monitoring API routes for the admin panel.
Handles statistics, message analytics, and system monitoring.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..api.auth import get_current_user
from ...shared.database.manager import db_manager
from ...shared.cache.cache_manager import cache_manager


# Response models
class LiveStatsResponse(BaseModel):
    active_rooms: int
    active_channels: int
    messages_last_hour: int
    messages_last_day: int
    websocket_connections: int = 0
    authenticated_sessions: int = 0
    cache_info: Dict[str, Any] = {}

class MessageStatsResponse(BaseModel):
    daily_stats: List[Dict[str, Any]]
    total_stats: Dict[str, Any]
    period_days: int

class SystemHealthResponse(BaseModel):
    database_status: str
    cache_status: str
    total_messages: int
    total_rooms: int
    total_channels: int
    uptime_info: Dict[str, Any]
    last_updated: datetime


# Router
router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================================================
# LIVE STATISTICS
# ============================================================================

@router.get("/live", response_model=LiveStatsResponse)
async def get_live_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get real-time system statistics."""
    try:
        # Try cache first
        cached_stats = await cache_manager.get_live_stats()
        
        if cached_stats:
            return LiveStatsResponse(**cached_stats)
        
        # Get fresh stats from database
        db_stats = await db_manager.get_live_stats()
        cache_info = await cache_manager.get_cache_info()
        
        # Combine statistics
        combined_stats = {
            **db_stats,
            'cache_info': cache_info,
            'websocket_connections': 0,  # Will be updated by WebSocket manager
            'authenticated_sessions': 0
        }
        
        # Cache the result
        await cache_manager.set_live_stats(combined_stats)
        
        return LiveStatsResponse(**combined_stats)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching live statistics: {str(e)}"
        )

@router.get("/messages", response_model=MessageStatsResponse)
async def get_message_statistics(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get message statistics for specified period."""
    try:
        # Try cache first for common periods
        cached_stats = await cache_manager.get_message_stats(days)
        
        if cached_stats:
            return MessageStatsResponse(
                **cached_stats,
                period_days=days
            )
        
        # Get fresh stats from database
        stats = await db_manager.get_message_stats(days)
        
        # Cache the result
        await cache_manager.set_message_stats(days, stats)
        
        return MessageStatsResponse(
            **stats,
            period_days=days
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching message statistics: {str(e)}"
        )

@router.get("/rooms/{room_id}/stats")
async def get_room_statistics(
    room_id: int,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get statistics for a specific room."""
    try:
        # TODO: Implement room-specific statistics
        # For now, return basic structure
        return {
            "room_id": room_id,
            "period_days": days,
            "message_count": 0,
            "unique_users": 0,
            "unique_guilds": 0,
            "daily_breakdown": [],
            "top_users": [],
            "top_guilds": [],
            "message": "Room-specific statistics not yet implemented"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching room statistics: {str(e)}"
        )


# ============================================================================
# SYSTEM HEALTH
# ============================================================================

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get comprehensive system health information."""
    try:
        # Database health
        db_health = "healthy"
        try:
            await db_manager.get_live_stats()
        except Exception:
            db_health = "error"
        
        # Cache health
        cache_health = "healthy"
        cache_info = {}
        try:
            cache_info = await cache_manager.get_cache_info()
        except Exception:
            cache_health = "error"
        
        # Get basic counts
        live_stats = await db_manager.get_live_stats()
        all_rooms = await db_manager.get_all_rooms(include_inactive=True)
        
        return SystemHealthResponse(
            database_status=db_health,
            cache_status=cache_health,
            total_messages=live_stats.get('messages_last_day', 0),
            total_rooms=len(all_rooms),
            total_channels=live_stats.get('active_channels', 0),
            uptime_info={
                "cache_keys": cache_info.get('total_keys', 0),
                "active_rate_limits": cache_info.get('active_rate_limits', 0)
            },
            last_updated=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching system health: {str(e)}"
        )


# ============================================================================
# ADVANCED ANALYTICS
# ============================================================================

@router.get("/trends")
async def get_usage_trends(
    period: str = Query("week", regex="^(day|week|month)$", description="Trend period"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get usage trends and growth patterns."""
    try:
        # Map period to days
        period_days = {
            "day": 1,
            "week": 7,
            "month": 30
        }
        
        days = period_days.get(period, 7)
        
        # Get message statistics
        stats = await db_manager.get_message_stats(days)
        
        # Calculate trends (basic implementation)
        daily_stats = stats.get('daily_stats', [])
        
        if len(daily_stats) >= 2:
            # Simple growth calculation
            recent_avg = sum(day['count'] for day in daily_stats[-3:]) / min(3, len(daily_stats))
            older_avg = sum(day['count'] for day in daily_stats[:-3]) / max(1, len(daily_stats) - 3)
            growth_rate = ((recent_avg - older_avg) / max(1, older_avg)) * 100
        else:
            growth_rate = 0
        
        return {
            "period": period,
            "days_analyzed": days,
            "daily_stats": daily_stats,
            "growth_rate_percent": round(growth_rate, 2),
            "total_messages": stats.get('total_stats', {}).get('total_messages', 0),
            "trend": "increasing" if growth_rate > 5 else "decreasing" if growth_rate < -5 else "stable"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating trends: {str(e)}"
        )

@router.get("/top-guilds")
async def get_top_guilds(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=50, description="Number of top guilds to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get most active Discord guilds by message count."""
    try:
        # TODO: Implement top guilds query
        # This would require a more complex database query
        return {
            "period_days": days,
            "top_guilds": [],
            "message": "Top guilds analysis not yet implemented"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching top guilds: {str(e)}"
        )

@router.get("/top-users")
async def get_top_users(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=50, description="Number of top users to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get most active users by message count."""
    try:
        # TODO: Implement top users query
        # This would require a more complex database query
        return {
            "period_days": days,
            "top_users": [],
            "message": "Top users analysis not yet implemented"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching top users: {str(e)}"
        )


# ============================================================================
# EXPORT FUNCTIONALITY
# ============================================================================

@router.get("/export/messages")
async def export_message_data(
    room_id: Optional[int] = Query(None, description="Specific room ID (optional)"),
    start_date: Optional[datetime] = Query(None, description="Start date for export"),
    end_date: Optional[datetime] = Query(None, description="End date for export"),
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Export message data for analysis."""
    try:
        # TODO: Implement message data export
        # This would require careful consideration of data privacy and performance
        return {
            "message": "Message export not yet implemented",
            "requested_format": format,
            "room_id": room_id,
            "start_date": start_date,
            "end_date": end_date
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting data: {str(e)}"
        )