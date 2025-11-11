# API Reference Guide - Global Chat System

Complete API documentation for the Global Chat System backend.

## 📡 Base Information

- **Base URL**: `http://localhost:8000/api` (local) or `http://your-vps-ip:8000/api` (VPS)
- **API Documentation**: `http://localhost:8000/api/docs` (Swagger UI)
- **Authentication**: JWT Bearer tokens
- **Content-Type**: `application/json`

## 🔐 Authentication

### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_info": {
    "id": 0,
    "username": "admin",
    "is_superuser": true
  }
}
```

### Using the Token
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Get Current User
```http
GET /api/auth/me
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "user_id": 0,
  "username": "admin",
  "is_superuser": true,
  "authenticated_at": 1645123456,
  "token_valid": true
}
```

### Logout
```http
POST /api/auth/logout
Authorization: Bearer TOKEN
```

### Refresh Token
```http
POST /api/auth/refresh
Authorization: Bearer TOKEN
```

---

## 🏠 Room Management

### List All Rooms
```http
GET /api/rooms?include_inactive=false
Authorization: Bearer TOKEN
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "general",
    "created_by": "admin",
    "created_at": "2024-01-01T00:00:00",
    "is_active": true,
    "max_servers": 50,
    "channel_count": 5
  }
]
```

### Get Specific Room
```http
GET /api/rooms/{room_id}
Authorization: Bearer TOKEN
```

### Create Room
```http
POST /api/rooms
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "name": "gaming",
  "max_servers": 25
}
```

**Response:**
```json
{
  "id": 2,
  "name": "gaming",
  "created_by": "admin",
  "created_at": "2024-01-01T12:00:00",
  "is_active": true,
  "max_servers": 25,
  "channel_count": 0
}
```

### Update Room
```http
PUT /api/rooms/{room_id}
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "name": "updated-name",
  "max_servers": 30,
  "is_active": true
}
```

### Delete Room
```http
DELETE /api/rooms/{room_id}
Authorization: Bearer TOKEN
```

---

## ⚙️ Room Permissions

### Get Room Permissions
```http
GET /api/rooms/{room_id}/permissions
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "allow_urls": false,
  "allow_files": false,
  "allow_mentions": true,
  "allow_emojis": true,
  "enable_bad_word_filter": true,
  "max_message_length": 2000,
  "rate_limit_seconds": 3
}
```

### Update Room Permissions
```http
PUT /api/rooms/{room_id}/permissions
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "allow_urls": true,
  "allow_files": false,
  "max_message_length": 1500,
  "rate_limit_seconds": 5
}
```

---

## 📺 Channel Management

### List Room Channels
```http
GET /api/rooms/{room_id}/channels
Authorization: Bearer TOKEN
```

**Response:**
```json
[
  {
    "guild_id": "123456789012345678",
    "channel_id": "987654321098765432",
    "guild_name": "My Discord Server",
    "channel_name": "global-chat",
    "registered_by": "admin",
    "registered_at": "2024-01-01T10:00:00"
  }
]
```

### Register Channel to Room
```http
POST /api/rooms/{room_id}/channels
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "guild_id": "123456789012345678",
  "channel_id": "987654321098765432",
  "guild_name": "My Discord Server",
  "channel_name": "global-chat"
}
```

### Unregister Channel
```http
DELETE /api/rooms/{room_id}/channels/{guild_id}/{channel_id}
Authorization: Bearer TOKEN
```

---

## 🖥️ Server Management

### List All Connected Servers
```http
GET /api/servers?active_only=true
Authorization: Bearer TOKEN
```

**Response:**
```json
[
  {
    "guild_id": "123456789012345678",
    "guild_name": "My Discord Server",
    "total_channels": 3,
    "active_channels": 2,
    "rooms_connected": ["general", "gaming"],
    "last_activity": "2024-01-01T15:30:00",
    "message_count_7d": 1250,
    "status": "active"
  }
]
```

### Get Server Details
```http
GET /api/servers/{guild_id}
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "guild_id": "123456789012345678",
  "guild_name": "My Discord Server",
  "channels": [
    {
      "guild_id": "123456789012345678",
      "channel_id": "987654321098765432",
      "guild_name": "My Discord Server",
      "channel_name": "global-chat",
      "room_id": 1,
      "room_name": "general",
      "registered_by": "admin",
      "registered_at": "2024-01-01T10:00:00",
      "is_active": true,
      "message_count_7d": 850
    }
  ],
  "statistics": {
    "total_channels": 3,
    "active_rooms": 2,
    "total_messages_7d": 1250
  },
  "permissions": {
    "allow_urls": false,
    "allow_files": false,
    "allow_mentions": true,
    "allow_emojis": true
  }
}
```

### List All Registered Channels
```http
GET /api/servers/channels?room_id=1&guild_id=123456789012345678&active_only=true
Authorization: Bearer TOKEN
```

### Server Statistics
```http
GET /api/servers/{guild_id}/stats?days=7
Authorization: Bearer TOKEN
```

### Server Activity
```http
GET /api/servers/{guild_id}/activity?hours=24
Authorization: Bearer TOKEN
```

### Refresh Server Cache
```http
POST /api/servers/bulk/refresh-cache
Authorization: Bearer TOKEN
```

---

## 📊 Analytics & Statistics

### Live Statistics
```http
GET /api/analytics/live
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "active_rooms": 3,
  "active_channels": 12,
  "messages_last_hour": 45,
  "messages_last_day": 892,
  "websocket_connections": 2,
  "authenticated_sessions": 1,
  "cache_info": {
    "rooms_cached": 3,
    "permissions_cached": 3,
    "channels_cached": 12,
    "total_keys": 25
  }
}
```

### Message Statistics
```http
GET /api/analytics/messages?days=7
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "daily_stats": [
    {
      "date": "2024-01-01",
      "count": 125
    },
    {
      "date": "2024-01-02", 
      "count": 156
    }
  ],
  "total_stats": {
    "total_messages": 892,
    "unique_users": 45,
    "unique_guilds": 8,
    "active_rooms": 3
  },
  "period_days": 7
}
```

### Room-specific Statistics
```http
GET /api/analytics/rooms/{room_id}/stats?days=7
Authorization: Bearer TOKEN
```

### System Health
```http
GET /api/analytics/health
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "database_status": "healthy",
  "cache_status": "healthy",
  "total_messages": 892,
  "total_rooms": 3,
  "total_channels": 12,
  "uptime_info": {
    "cache_keys": 25,
    "active_rate_limits": 2
  },
  "last_updated": "2024-01-01T16:00:00"
}
```

### Usage Trends
```http
GET /api/analytics/trends?period=week
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "period": "week",
  "days_analyzed": 7,
  "daily_stats": [...],
  "growth_rate_percent": 12.5,
  "total_messages": 892,
  "trend": "increasing"
}
```

### Export Data
```http
GET /api/analytics/export/messages?room_id=1&start_date=2024-01-01&end_date=2024-01-07&format=json
Authorization: Bearer TOKEN
```

---

## 🔧 System Endpoints

### API Status (Public)
```http
GET /api/status
```

**Response:**
```json
{
  "status": "online",
  "version": "1.0.0",
  "database": "healthy",
  "cache": "healthy",
  "websocket": {
    "total_connections": 2,
    "authenticated_connections": 1
  },
  "debug_mode": false
}
```

### System Information (Authenticated)
```http
GET /api/info
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "app_name": "Global Chat Admin Panel",
  "version": "1.0.0",
  "user_info": {
    "user_id": 0,
    "username": "admin",
    "is_superuser": true
  },
  "system_stats": {
    "active_rooms": 3,
    "active_channels": 12,
    "messages_last_day": 892
  },
  "configuration": {
    "max_page_size": 100,
    "rate_limit_requests": 100,
    "token_expire_minutes": 1440
  }
}
```

---

## 🔌 WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

// Authenticate after connection
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'authenticate',
    token: 'your-jwt-token'
  }));
};
```

### Message Types

#### Authentication
```javascript
// Send authentication
{
  "type": "authenticate",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

// Receive confirmation
{
  "type": "authentication_success",
  "user_data": {
    "username": "admin",
    "is_superuser": true
  },
  "timestamp": "2024-01-01T16:00:00"
}
```

#### Live Statistics Updates
```javascript
// Receive live stats (every 5 seconds)
{
  "type": "live_stats",
  "data": {
    "active_rooms": 3,
    "active_channels": 12,
    "messages_last_hour": 45,
    "cache_info": {
      "total_keys": 25
    }
  },
  "timestamp": "2024-01-01T16:00:00"
}
```

#### System Notifications
```javascript
// Receive system notifications
{
  "type": "system_notification",
  "data": {
    "level": "warning",
    "message": "High memory usage detected",
    "component": "database"
  },
  "timestamp": "2024-01-01T16:00:00"
}
```

#### Room Updates
```javascript
// Receive room creation/updates
{
  "type": "room_update",
  "data": {
    "action": "created",
    "room": {
      "id": 4,
      "name": "new-room",
      "created_by": "admin"
    }
  },
  "timestamp": "2024-01-01T16:00:00"
}
```

#### Channel Updates
```javascript
// Receive channel registration/updates
{
  "type": "channel_update",
  "data": {
    "action": "registered",
    "room_id": 1,
    "channel": {
      "guild_id": "123456789012345678",
      "channel_id": "987654321098765432",
      "guild_name": "New Server",
      "channel_name": "global-chat"
    }
  },
  "timestamp": "2024-01-01T16:00:00"
}
```

#### Keep-Alive
```javascript
// Send ping
{
  "type": "ping",
  "timestamp": 1645123456789
}

// Receive pong
{
  "type": "pong",
  "timestamp": 1645123456789
}
```

---

## 📝 Request/Response Examples

### Complete Authentication Flow
```bash
# 1. Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Response: {"access_token": "TOKEN", ...}

# 2. Use token for authenticated request
curl -X GET http://localhost:8000/api/rooms \
  -H "Authorization: Bearer TOKEN"

# 3. Refresh token when needed
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Authorization: Bearer TOKEN"
```

### Create Room and Register Channel
```bash
# 1. Create room
curl -X POST http://localhost:8000/api/rooms \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test-room","max_servers":25}'

# Response: {"id": 2, "name": "test-room", ...}

# 2. Register channel to room
curl -X POST http://localhost:8000/api/rooms/2/channels \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "guild_id": "123456789012345678",
    "channel_id": "987654321098765432", 
    "guild_name": "Test Server",
    "channel_name": "global-chat"
  }'
```

### Get Analytics Data
```bash
# Get live stats
curl -X GET http://localhost:8000/api/analytics/live \
  -H "Authorization: Bearer TOKEN"

# Get message statistics for last 30 days
curl -X GET "http://localhost:8000/api/analytics/messages?days=30" \
  -H "Authorization: Bearer TOKEN"

# Get system health
curl -X GET http://localhost:8000/api/analytics/health \
  -H "Authorization: Bearer TOKEN"
```

---

## ❌ Error Responses

### Authentication Errors
```json
{
  "detail": "Invalid authentication token",
  "status_code": 401
}
```

### Validation Errors
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "status_code": 422
}
```

### Not Found Errors
```json
{
  "detail": "Room not found",
  "status_code": 404
}
```

### Server Errors
```json
{
  "detail": "Internal server error",
  "status_code": 500
}
```

---

## 📋 HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

---

## 🔧 Rate Limiting

- **Default Limit**: 100 requests per minute per user
- **Headers**: Rate limit info in response headers
- **Exceeded**: HTTP 429 with retry-after header

```bash
# Rate limit headers in response
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1645123456
```

---

## 📖 Interactive API Documentation

Visit the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc` (if enabled)

The interactive docs allow you to:
- Browse all available endpoints
- See request/response schemas
- Test API calls directly
- Download OpenAPI specification

---

**🔗 Quick Reference:**
- **Base URL**: `http://localhost:8000/api`
- **Authentication**: `Authorization: Bearer TOKEN`
- **WebSocket**: `ws://localhost:8000/ws`
- **Docs**: `http://localhost:8000/api/docs`