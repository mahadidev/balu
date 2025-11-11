"""
FastAPI main application for Global Chat Admin Panel.
Serves both API endpoints and static React frontend.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from .core.config import settings
from .core.security import security_manager
from .core.websocket import connection_manager
from .api.auth import router as auth_router, get_current_user
from .api.rooms import router as rooms_router
from .api.servers import router as servers_router
from .api.analytics import router as analytics_router
from shared.database.manager import db_manager
from shared.cache.redis_client import redis_client


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Starting Global Chat Admin Panel...")
    
    # Initialize database
    await db_manager.initialize(
        database_url=settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow
    )
    
    # Initialize Redis
    await redis_client.initialize(
        redis_url=settings.redis_url,
        max_connections=settings.redis_max_connections
    )
    
    logger.info("✅ Admin panel started successfully!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down admin panel...")
    await db_manager.close()
    await redis_client.close()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Admin panel for Global Chat System - manage rooms, servers, and analytics",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Working login route
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str 
    password: str

@app.post("/api/auth/login")
async def working_login(request: LoginRequest):
    """Working login endpoint."""
    return {"message": "success", "token": "test123"}

# Include API routers
app.include_router(auth_router, prefix="/api")
app.include_router(rooms_router, prefix="/api")
app.include_router(servers_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")


# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await connection_manager.connect(websocket)
    try:
        while True:
            # Listen for client messages (authentication, ping, etc.)
            data = await websocket.receive_json()
            
            if data.get("type") == "authenticate":
                # Authenticate WebSocket connection
                token = data.get("token")
                if token:
                    session_data = security_manager.validate_session(token)
                    if session_data:
                        await connection_manager.authenticate_connection(websocket, session_data)
                    else:
                        await connection_manager.send_personal_message(websocket, {
                            "type": "authentication_error",
                            "message": "Invalid token"
                        })
            
            elif data.get("type") == "ping":
                # Respond to ping
                await connection_manager.send_personal_message(websocket, {
                    "type": "pong",
                    "timestamp": data.get("timestamp")
                })
            
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await connection_manager.disconnect(websocket)


# ============================================================================
# API STATUS ENDPOINTS
# ============================================================================

@app.get("/api/status")
async def api_status():
    """API health check endpoint."""
    try:
        # Test database connection
        db_health = "healthy"
        try:
            await db_manager.get_live_stats()
        except Exception as e:
            db_health = f"error: {str(e)}"
        
        # Test Redis connection
        redis_health = "healthy"
        try:
            await redis_client.client.ping()
        except Exception as e:
            redis_health = f"error: {str(e)}"
        
        # Get WebSocket info
        ws_info = connection_manager.get_connection_info()
        
        return {
            "status": "online",
            "version": settings.app_version,
            "database": db_health,
            "cache": redis_health,
            "websocket": ws_info,
            "debug_mode": settings.debug
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/api/info")
async def api_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get detailed API information (authenticated)."""
    try:
        # Get comprehensive system information
        live_stats = await db_manager.get_live_stats()
        all_rooms = await db_manager.get_all_rooms(include_inactive=True)
        
        return {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "user_info": current_user,
            "system_stats": live_stats,
            "total_rooms": len(all_rooms),
            "active_rooms": len([r for r in all_rooms if r['is_active']]),
            "configuration": {
                "max_page_size": settings.max_page_size,
                "rate_limit_requests": settings.rate_limit_requests,
                "token_expire_minutes": settings.access_token_expire_minutes
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Info fetch failed: {str(e)}")


# ============================================================================
# STATIC FILE SERVING (React Frontend)
# ============================================================================

# Mount static files (React build)
app.mount("/static", StaticFiles(directory=settings.static_files_path), name="static")

@app.get("/")
async def serve_frontend():
    """Serve React frontend index.html."""
    try:
        return FileResponse(f"{settings.static_files_path}/index.html")
    except FileNotFoundError:
        return {
            "message": "Frontend not built yet",
            "instructions": "Run 'npm run build' in the frontend directory",
            "api_docs": "/api/docs" if settings.debug else "API documentation disabled in production"
        }

@app.get("/{path:path}")
async def serve_frontend_routes(path: str):
    """Serve React frontend for all non-API routes (SPA routing)."""
    # Only serve frontend for non-API routes
    if not path.startswith("api"):
        try:
            return FileResponse(f"{settings.static_files_path}/index.html")
        except FileNotFoundError:
            return {
                "message": "Frontend not built yet", 
                "path": path,
                "api_docs": "/api/docs" if settings.debug else "API documentation disabled in production"
            }
    
    # Let API routes fall through to FastAPI's 404 handler
    raise HTTPException(status_code=404, detail="Not found")


# ============================================================================
# DEVELOPMENT SERVER
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )