"""
Configuration settings for the FastAPI admin backend.
Environment-based configuration for different deployment environments.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Global Chat Admin Panel"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/globalchat"
    database_pool_size: int = 20
    database_max_overflow: int = 30
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 20
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Admin Panel
    admin_username: str = "admin"
    admin_password: str = "admin123"  # Change in production!
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # File paths
    static_files_path: str = "/app/admin/backend/static"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
        # Environment variable mappings
        fields = {
            'database_url': {'env': 'DATABASE_URL'},
            'redis_url': {'env': 'REDIS_URL'},
            'secret_key': {'env': 'SECRET_KEY'},
            'admin_username': {'env': 'ADMIN_USERNAME'},
            'admin_password': {'env': 'ADMIN_PASSWORD'},
            'debug': {'env': 'DEBUG'}
        }


# Global settings instance
settings = Settings()