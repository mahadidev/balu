"""
Security utilities for the FastAPI admin backend.
JWT token handling, password hashing, and authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import secrets
import jwt
from passlib.context import CryptContext

from .config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """Handle authentication and authorization for the admin panel."""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    # ============================================================================
    # PASSWORD OPERATIONS
    # ============================================================================
    
    def hash_password(self, password: str) -> str:
        """Hash a password for storing in the database."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password."""
        return pwd_context.verify(plain_password, hashed_password)
    
    # ============================================================================
    # JWT TOKEN OPERATIONS
    # ============================================================================
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a new JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None
    
    def decode_access_token(self, token: str) -> Optional[str]:
        """Decode access token and return username."""
        payload = self.verify_token(token)
        if payload:
            username: str = payload.get("sub")
            return username
        return None
    
    # ============================================================================
    # API KEY OPERATIONS (For Discord bot authentication)
    # ============================================================================
    
    def generate_api_key(self) -> str:
        """Generate a secure API key for bot authentication."""
        return secrets.token_urlsafe(32)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str, hashed_api_key: str) -> bool:
        """Verify an API key against its hash."""
        return hashlib.sha256(api_key.encode()).hexdigest() == hashed_api_key
    
    # ============================================================================
    # SESSION MANAGEMENT
    # ============================================================================
    
    def create_session_token(self, user_id: int, username: str, is_superuser: bool = False) -> str:
        """Create a session token for admin users."""
        token_data = {
            "sub": username,
            "user_id": user_id,
            "is_superuser": is_superuser,
            "type": "access_token",
            "iat": datetime.utcnow().timestamp()
        }
        return self.create_access_token(token_data)
    
    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and return user data."""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        # Check if token is still valid
        if payload.get("type") != "access_token":
            return None
        
        return {
            "username": payload.get("sub"),
            "user_id": payload.get("user_id"),
            "is_superuser": payload.get("is_superuser", False),
            "iat": payload.get("iat")
        }
    
    # ============================================================================
    # ADMIN USER AUTHENTICATION
    # ============================================================================
    
    def authenticate_admin(self, username: str, password: str, stored_hash: str) -> bool:
        """Authenticate admin user with username and password."""
        return self.verify_password(password, stored_hash)
    
    def create_default_admin_hash(self) -> str:
        """Create hash for default admin password (for initial setup)."""
        return self.hash_password(settings.admin_password)
    
    # ============================================================================
    # PERMISSION CHECKS
    # ============================================================================
    
    def check_admin_permission(self, session_data: Dict[str, Any], required_superuser: bool = False) -> bool:
        """Check if user has required admin permissions."""
        if not session_data:
            return False
        
        if required_superuser:
            return session_data.get("is_superuser", False)
        
        return True  # Basic admin access
    
    # ============================================================================
    # SECURITY HELPERS
    # ============================================================================
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token for form protection."""
        return secrets.token_urlsafe(32)
    
    def is_safe_redirect_url(self, url: str) -> bool:
        """Check if redirect URL is safe (prevent open redirect attacks)."""
        if not url:
            return False
        
        # Only allow relative URLs and specific allowed origins
        if url.startswith('/'):
            return True
        
        for origin in settings.allowed_origins:
            if url.startswith(origin):
                return True
        
        return False


# Global security instance
security_manager = SecurityManager()