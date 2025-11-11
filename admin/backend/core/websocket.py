"""
WebSocket manager for real-time updates in the admin panel.
Handles live statistics, message monitoring, and system notifications.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections for real-time admin panel updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.authenticated_connections: Dict[WebSocket, Dict[str, Any]] = {}
        self._stats_task: Optional[asyncio.Task] = None
        self._monitoring_active = False
    
    # ============================================================================
    # CONNECTION MANAGEMENT
    # ============================================================================
    
    async def connect(self, websocket: WebSocket, user_data: Dict[str, Any] = None):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_data:
            self.authenticated_connections[websocket] = {
                **user_data,
                'connected_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat()
            }
        
        # Start monitoring if this is the first connection
        if len(self.active_connections) == 1 and not self._monitoring_active:
            await self._start_monitoring()
        
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
        
        # Send initial connection confirmation
        await self.send_personal_message(websocket, {
            'type': 'connection_confirmed',
            'timestamp': datetime.utcnow().isoformat(),
            'total_connections': len(self.active_connections)
        })
    
    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if websocket in self.authenticated_connections:
            del self.authenticated_connections[websocket]
        
        # Stop monitoring if no connections left
        if len(self.active_connections) == 0:
            await self._stop_monitoring()
        
        logger.info(f"WebSocket disconnected. Remaining: {len(self.active_connections)}")
    
    # ============================================================================
    # MESSAGE SENDING
    # ============================================================================
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
            
            # Update last activity
            if websocket in self.authenticated_connections:
                self.authenticated_connections[websocket]['last_activity'] = datetime.utcnow().isoformat()
                
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)
    
    async def broadcast_message(self, message: Dict[str, Any], auth_required: bool = True):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
        
        # Choose connections to send to
        target_connections = []
        if auth_required:
            target_connections = list(self.authenticated_connections.keys())
        else:
            target_connections = self.active_connections.copy()
        
        # Send to all target connections
        disconnected_connections = []
        for connection in target_connections:
            try:
                await connection.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected_connections.append(connection)
        
        # Clean up failed connections
        for connection in disconnected_connections:
            await self.disconnect(connection)
    
    # ============================================================================
    # REAL-TIME STATISTICS
    # ============================================================================
    
    async def broadcast_live_stats(self, stats: Dict[str, Any]):
        """Broadcast live statistics to all authenticated connections."""
        message = {
            'type': 'live_stats',
            'data': stats,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast_message(message, auth_required=True)
    
    async def broadcast_message_activity(self, activity_data: Dict[str, Any]):
        """Broadcast real-time message activity."""
        message = {
            'type': 'message_activity',
            'data': activity_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast_message(message, auth_required=True)
    
    async def broadcast_system_notification(self, notification: Dict[str, Any]):
        """Broadcast system notifications (errors, warnings, etc.)."""
        message = {
            'type': 'system_notification',
            'data': notification,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast_message(message, auth_required=True)
    
    async def broadcast_room_update(self, room_data: Dict[str, Any]):
        """Broadcast room creation/update events."""
        message = {
            'type': 'room_update',
            'data': room_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast_message(message, auth_required=True)
    
    async def broadcast_channel_update(self, channel_data: Dict[str, Any]):
        """Broadcast channel registration/update events."""
        message = {
            'type': 'channel_update',
            'data': channel_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast_message(message, auth_required=True)
    
    # ============================================================================
    # MONITORING TASKS
    # ============================================================================
    
    async def _start_monitoring(self):
        """Start background monitoring tasks."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._stats_task = asyncio.create_task(self._stats_monitoring_loop())
        logger.info("Started WebSocket monitoring tasks")
    
    async def _stop_monitoring(self):
        """Stop background monitoring tasks."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        
        if self._stats_task and not self._stats_task.done():
            self._stats_task.cancel()
            try:
                await self._stats_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped WebSocket monitoring tasks")
    
    async def _stats_monitoring_loop(self):
        """Background task to send live statistics every 5 seconds."""
        try:
            while self._monitoring_active:
                # Import here to avoid circular imports
                from shared.database.manager import db_manager
                from shared.cache.cache_manager import cache_manager
                
                try:
                    # Get live stats from database
                    db_stats = await db_manager.get_live_stats()
                    
                    # Get cache info
                    cache_info = await cache_manager.get_cache_info()
                    
                    # Combine statistics
                    combined_stats = {
                        **db_stats,
                        'cache_info': cache_info,
                        'websocket_connections': len(self.active_connections),
                        'authenticated_sessions': len(self.authenticated_connections)
                    }
                    
                    # Broadcast to connected clients
                    await self.broadcast_live_stats(combined_stats)
                    
                except Exception as e:
                    logger.error(f"Error in stats monitoring loop: {e}")
                    # Send error notification to admin
                    await self.broadcast_system_notification({
                        'level': 'error',
                        'message': f'Statistics monitoring error: {str(e)}',
                        'component': 'websocket_monitor'
                    })
                
                # Wait 5 seconds before next update
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            logger.info("Stats monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Stats monitoring loop error: {e}")
    
    # ============================================================================
    # CONNECTION INFO
    # ============================================================================
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about current WebSocket connections."""
        authenticated_users = []
        for ws, data in self.authenticated_connections.items():
            authenticated_users.append({
                'username': data.get('username', 'Unknown'),
                'connected_at': data.get('connected_at'),
                'last_activity': data.get('last_activity'),
                'is_superuser': data.get('is_superuser', False)
            })
        
        return {
            'total_connections': len(self.active_connections),
            'authenticated_connections': len(self.authenticated_connections),
            'anonymous_connections': len(self.active_connections) - len(self.authenticated_connections),
            'authenticated_users': authenticated_users,
            'monitoring_active': self._monitoring_active
        }
    
    # ============================================================================
    # AUTHENTICATION HELPERS
    # ============================================================================
    
    async def authenticate_connection(self, websocket: WebSocket, user_data: Dict[str, Any]):
        """Authenticate an existing WebSocket connection."""
        if websocket in self.active_connections:
            self.authenticated_connections[websocket] = {
                **user_data,
                'connected_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat()
            }
            
            # Send authentication success
            await self.send_personal_message(websocket, {
                'type': 'authentication_success',
                'user_data': user_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return True
        return False
    
    def is_authenticated(self, websocket: WebSocket) -> bool:
        """Check if WebSocket connection is authenticated."""
        return websocket in self.authenticated_connections
    
    def get_user_data(self, websocket: WebSocket) -> Optional[Dict[str, Any]]:
        """Get user data for authenticated WebSocket connection."""
        return self.authenticated_connections.get(websocket)


# Global connection manager instance
connection_manager = ConnectionManager()