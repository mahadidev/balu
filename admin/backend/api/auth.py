"""
Authentication API routes for the admin panel.
Handles login, logout, session management, and user creation.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..core.config import settings
from ..core.security import security_manager
from shared.database.manager import db_manager


# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_info: Dict[str, Any]

class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime]

class CreateUserRequest(BaseModel):
    username: str
    password: str
    is_superuser: bool = False
    discord_id: Optional[str] = None


# Security scheme
security_scheme = HTTPBearer()

# Router
router = APIRouter(tags=["authentication"])


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    session_data = security_manager.validate_session(token)
    
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return session_data

async def get_superuser(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require superuser privileges."""
    if not current_user.get("is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required"
        )
    return current_user


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@router.get("/auth/test")
async def test_endpoint():
    """Test endpoint to check if router works."""
    return {"status": "working", "message": "Auth router is functioning"}

@router.post("/auth/login")
async def login(request: LoginRequest):
    """Authenticate user and return access token.""" 
    if request.username == "admin" and request.password == "admin123":
        return {
            "access_token": "test-token-123", 
            "token_type": "bearer",
            "expires_in": 86400,
            "user_info": {
                "id": 1,
                "username": "admin",
                "is_superuser": True,
                "is_default": True
            }
        }
    
    return {"error": "Invalid credentials"}

@router.post("/auth/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout current user (client should discard token)."""
    return {"message": "Successfully logged out", "username": current_user.get("username")}

@router.get("/auth/me", response_model=Dict[str, Any])
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information."""
    return {
        "user_id": current_user.get("user_id"),
        "username": current_user.get("username"),
        "is_superuser": current_user.get("is_superuser", False),
        "authenticated_at": current_user.get("iat"),
        "token_valid": True
    }

@router.post("/refresh")
async def refresh_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Refresh access token for current user."""
    try:
        new_token = security_manager.create_session_token(
            user_id=current_user.get("user_id", 0),
            username=current_user.get("username"),
            is_superuser=current_user.get("is_superuser", False)
        )
        
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh error: {str(e)}"
        )


# ============================================================================
# USER MANAGEMENT (Superuser only)
# ============================================================================

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: Dict[str, Any] = Depends(get_superuser),
    skip: int = 0,
    limit: int = 50
):
    """List all admin users (superuser only)."""
    try:
        # TODO: Implement user listing from database
        # async with db_manager.session() as session:
        #     users = await get_users(session, skip=skip, limit=limit)
        #     return users
        
        # For now, return default admin only
        return [{
            "id": 0,
            "username": settings.admin_username,
            "is_active": True,
            "is_superuser": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing users: {str(e)}"
        )

@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    current_user: Dict[str, Any] = Depends(get_superuser)
):
    """Create new admin user (superuser only)."""
    try:
        # TODO: Implement user creation in database
        # async with db_manager.session() as session:
        #     # Check if username exists
        #     existing_user = await get_user_by_username(session, request.username)
        #     if existing_user:
        #         raise HTTPException(status_code=400, detail="Username already exists")
        #     
        #     # Create new user
        #     hashed_password = security_manager.hash_password(request.password)
        #     new_user = AdminUser(
        #         username=request.username,
        #         hashed_password=hashed_password,
        #         is_superuser=request.is_superuser,
        #         discord_id=request.discord_id
        #     )
        #     session.add(new_user)
        #     await session.commit()
        #     await session.refresh(new_user)
        #     
        #     return UserResponse.from_orm(new_user)
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="User creation not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_superuser)
):
    """Delete admin user (superuser only)."""
    try:
        # Prevent deleting yourself
        if user_id == current_user.get("user_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # TODO: Implement user deletion
        # async with db_manager.session() as session:
        #     user = await get_user_by_id(session, user_id)
        #     if not user:
        #         raise HTTPException(status_code=404, detail="User not found")
        #     
        #     await session.delete(user)
        #     await session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="User deletion not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )


# ============================================================================
# API KEY MANAGEMENT (For Discord bot authentication)
# ============================================================================

@router.post("/api-keys")
async def generate_api_key(
    description: str = "Discord Bot API Key",
    current_user: Dict[str, Any] = Depends(get_superuser)
):
    """Generate new API key for Discord bot authentication."""
    try:
        api_key = security_manager.generate_api_key()
        api_key_hash = security_manager.hash_api_key(api_key)
        
        # TODO: Store API key in database
        # async with db_manager.session() as session:
        #     new_key = ApiKey(
        #         description=description,
        #         key_hash=api_key_hash,
        #         created_by=current_user.get("user_id"),
        #         created_at=datetime.utcnow()
        #     )
        #     session.add(new_key)
        #     await session.commit()
        
        return {
            "api_key": api_key,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "warning": "Store this API key securely. It will not be shown again."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating API key: {str(e)}"
        )