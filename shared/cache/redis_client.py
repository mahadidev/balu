"""
Async Redis client with connection pooling for caching and sessions.
Optimized for high throughput (40-50 servers with continuous messages).
"""

import asyncio
import json
import os
from typing import Optional, Dict, Any, List
from datetime import timedelta

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool


class RedisClient:
    """Async Redis client with connection pooling for high performance caching."""
    
    def __init__(self):
        self.pool = None
        self.client = None
        self._initialized = False
    
    async def initialize(self, redis_url: str = None, max_connections: int = 20):
        """Initialize Redis connection pool."""
        if self._initialized:
            return
            
        # Default Redis URL from environment
        if not redis_url:
            redis_url = os.getenv(
                "REDIS_URL", 
                "redis://localhost:6379/0"
            )
        
        # Create connection pool
        self.pool = ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            retry_on_timeout=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            health_check_interval=30
        )
        
        # Create Redis client
        self.client = redis.Redis(connection_pool=self.pool)
        
        # Test connection
        await self.client.ping()
        self._initialized = True
        print(f"✅ Redis initialized with {max_connections} max connections")
    
    async def close(self):
        """Close Redis connections."""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
        self._initialized = False
    
    # ============================================================================
    # KEY-VALUE OPERATIONS
    # ============================================================================
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        try:
            return await self.client.get(key)
        except Exception as e:
            print(f"❌ Redis GET error for {key}: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set key-value with optional TTL in seconds."""
        try:
            if ttl:
                return await self.client.setex(key, ttl, value)
            else:
                return await self.client.set(key, value)
        except Exception as e:
            print(f"❌ Redis SET error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key."""
        try:
            return bool(await self.client.delete(key))
        except Exception as e:
            print(f"❌ Redis DELETE error for {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            print(f"❌ Redis EXISTS error for {key}: {e}")
            return False
    
    # ============================================================================
    # JSON OPERATIONS (For complex data structures)
    # ============================================================================
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON object by key."""
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
        except Exception as e:
            print(f"❌ Redis GET_JSON error for {key}: {e}")
            return None
    
    async def set_json(self, key: str, value: Dict[str, Any], ttl: int = None) -> bool:
        """Set JSON object with optional TTL."""
        try:
            json_data = json.dumps(value, default=str)
            return await self.set(key, json_data, ttl)
        except Exception as e:
            print(f"❌ Redis SET_JSON error for {key}: {e}")
            return False
    
    # ============================================================================
    # HASH OPERATIONS (For related data)
    # ============================================================================
    
    async def hget(self, hash_key: str, field: str) -> Optional[str]:
        """Get hash field value."""
        try:
            return await self.client.hget(hash_key, field)
        except Exception as e:
            print(f"❌ Redis HGET error for {hash_key}.{field}: {e}")
            return None
    
    async def hset(self, hash_key: str, field: str, value: str) -> bool:
        """Set hash field value."""
        try:
            return bool(await self.client.hset(hash_key, field, value))
        except Exception as e:
            print(f"❌ Redis HSET error for {hash_key}.{field}: {e}")
            return False
    
    async def hgetall(self, hash_key: str) -> Dict[str, str]:
        """Get all hash fields."""
        try:
            return await self.client.hgetall(hash_key)
        except Exception as e:
            print(f"❌ Redis HGETALL error for {hash_key}: {e}")
            return {}
    
    async def hdel(self, hash_key: str, *fields: str) -> int:
        """Delete hash fields."""
        try:
            return await self.client.hdel(hash_key, *fields)
        except Exception as e:
            print(f"❌ Redis HDEL error for {hash_key}: {e}")
            return 0
    
    # ============================================================================
    # SET OPERATIONS (For lists/collections)
    # ============================================================================
    
    async def sadd(self, set_key: str, *values: str) -> int:
        """Add members to set."""
        try:
            return await self.client.sadd(set_key, *values)
        except Exception as e:
            print(f"❌ Redis SADD error for {set_key}: {e}")
            return 0
    
    async def srem(self, set_key: str, *values: str) -> int:
        """Remove members from set."""
        try:
            return await self.client.srem(set_key, *values)
        except Exception as e:
            print(f"❌ Redis SREM error for {set_key}: {e}")
            return 0
    
    async def smembers(self, set_key: str) -> set:
        """Get all set members."""
        try:
            return await self.client.smembers(set_key)
        except Exception as e:
            print(f"❌ Redis SMEMBERS error for {set_key}: {e}")
            return set()
    
    async def sismember(self, set_key: str, value: str) -> bool:
        """Check if value is in set."""
        try:
            return bool(await self.client.sismember(set_key, value))
        except Exception as e:
            print(f"❌ Redis SISMEMBER error for {set_key}: {e}")
            return False
    
    # ============================================================================
    # TTL OPERATIONS
    # ============================================================================
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for key."""
        try:
            return bool(await self.client.expire(key, ttl))
        except Exception as e:
            print(f"❌ Redis EXPIRE error for {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL for key."""
        try:
            return await self.client.ttl(key)
        except Exception as e:
            print(f"❌ Redis TTL error for {key}: {e}")
            return -2
    
    # ============================================================================
    # PATTERN OPERATIONS
    # ============================================================================
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern."""
        try:
            keys = await self.client.keys(pattern)
            return [key.decode('utf-8') for key in keys]
        except Exception as e:
            print(f"❌ Redis KEYS error for pattern {pattern}: {e}")
            return []
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = await self.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"❌ Redis DELETE_PATTERN error for {pattern}: {e}")
            return 0


# Global instance
redis_client = RedisClient()