#!/usr/bin/env python3
"""
Simple test script for the system API endpoint
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import json

# Mock dependencies
class MockDBManager:
    async def session(self):
        return MockSession()
    
class MockSession:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass
        
    async def execute(self, query):
        return MockResult()
    
    async def commit(self):
        pass

class MockResult:
    def scalar(self):
        return 100  # Mock count

class MockRedisClient:
    class MockClient:
        async def flushdb(self):
            pass
    
    def __init__(self):
        self.client = self.MockClient()

# Mock instances
db_manager = MockDBManager()
redis_client = MockRedisClient()

# Request/Response models
class ClearDataRequest(BaseModel):
    confirm: bool = False
    keep_rooms: bool = True
    keep_channels: bool = True
    
class ClearDataResponse(BaseModel):
    success: bool
    message: str
    cleared_items: Dict[str, int]

# Mock auth
async def get_current_user():
    return {"username": "test_user", "id": 1}

# Create test app
app = FastAPI()

@app.post("/system/clear-data", response_model=ClearDataResponse)
async def clear_all_data(request: ClearDataRequest):
    """Clear all data from the system (messages, stats, etc.)."""
    if not request.confirm:
        raise HTTPException(
            status_code=400,
            detail="Must confirm data clearing by setting 'confirm' to true"
        )
    
    try:
        cleared_items = {"messages": 50, "daily_stats": 10, "cache_entries": 1}
        
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

if __name__ == "__main__":
    import uvicorn
    print("🧪 Starting test API server...")
    print("📡 Test endpoint: http://localhost:8001/system/clear-data")
    print("📋 Test with: curl -X POST http://localhost:8001/system/clear-data -H 'Content-Type: application/json' -d '{\"confirm\": true}'")
    uvicorn.run(app, host="0.0.0.0", port=8001)