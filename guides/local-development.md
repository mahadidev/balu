# Local Development Guide - Global Chat System

Complete guide for setting up and running the Global Chat System on your local machine for development and testing.

## 📋 Prerequisites

### Required Software
- **Git** (for cloning repository)
- **Docker** and **Docker Compose** (recommended)
- **Node.js 18+** and **npm** (for frontend development)
- **Python 3.11+** (for backend development)
- **Discord Bot Token** (create at https://discord.com/developers/applications)

### Discord Bot Setup
1. Go to https://discord.com/developers/applications
2. Click "New Application" → Enter name → Create
3. Go to "Bot" section → Click "Add Bot"
4. Copy the **Token** (you'll need this)
5. Enable these **Privileged Gateway Intents**:
   - Message Content Intent ✅
   - Server Members Intent ✅
6. Go to "OAuth2" → "URL Generator":
   - Scopes: `bot`
   - Permissions: `Send Messages`, `Read Message History`, `Use Slash Commands`
7. Use generated URL to invite bot to your Discord servers

---

## 🚀 Quick Start (Docker - Recommended)

### Step 1: Environment Setup
```bash
# Navigate to project directory
cd /Users/mahadihasan/Desktop/unbot

# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

**Edit .env file with these values:**
```bash
# Discord Bot Token (REQUIRED)
DISCORD_BOT_TOKEN=your_actual_bot_token_here

# Database Password
POSTGRES_PASSWORD=mypassword123

# Admin Panel Security
SECRET_KEY=your-super-secret-key-minimum-32-characters-long
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Development settings
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Step 2: Deploy with Docker
```bash
# Make deploy script executable
chmod +x scripts/deploy.sh

# Deploy in development mode
./scripts/deploy.sh development

# Or deploy with database backup
./scripts/deploy.sh development true
```

### Step 3: Access Applications
- **Admin Panel**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Database**: localhost:5432 (username: postgres, password: from .env)

**Login Credentials:**
- Username: `admin`
- Password: `admin123`

---

## 🛠️ Manual Development Setup

### Step 1: Environment Setup
```bash
cd /Users/mahadihasan/Desktop/unbot
cp .env.example .env
nano .env  # Add your Discord bot token and settings
```

### Step 2: Install Dependencies

#### Python Backend Dependencies
```bash
# Install FastAPI backend dependencies
cd admin/backend
python -m pip install -r requirements.txt
cd ../..

# Install Discord bot dependencies
cd chat
python -m pip install -r requirements.txt
cd ..
```

#### Node.js Frontend Dependencies
```bash
# Install React frontend dependencies
cd admin/frontend
npm install
cd ../..
```

### Step 3: Start Infrastructure Services
```bash
# Start PostgreSQL and Redis only
docker-compose up -d postgres redis

# Wait for services to be ready
sleep 30

# Run database migrations
python scripts/migrate.py
```

### Step 4: Start Application Services

#### Terminal 1: Discord Bot
```bash
cd chat
python main.py
```

#### Terminal 2: FastAPI Backend
```bash
cd admin/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 3: React Frontend (Optional)
```bash
cd admin/frontend
npm start
```

This will start the frontend on http://localhost:3000

### Step 5: Access Applications
- **Admin Panel**: http://localhost:8000 (FastAPI serving React build)
- **Frontend Dev Server**: http://localhost:3000 (if running npm start)
- **API Documentation**: http://localhost:8000/api/docs

---

## 🔧 Development Workflow

### Frontend Development
```bash
# Navigate to frontend directory
cd admin/frontend

# Start development server
npm start

# Build for production
npm run build

# Build and copy to backend static files
npm run build && npm run copy-build
```

### Backend Development
```bash
# Navigate to backend directory
cd admin/backend

# Start with auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start with debug mode
DEBUG=true python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Bot Development
```bash
# Navigate to bot directory
cd chat

# Start bot with debug logging
DEBUG=true python main.py

# Test specific components
python -c "from formatters import MessageFormatter; print('Formatter loaded')"
```

### Database Development
```bash
# Connect to local database
docker-compose exec postgres psql -U postgres -d globalchat

# Run custom queries
SELECT * FROM chat_rooms;
SELECT COUNT(*) FROM chat_messages;

# Exit database
\q

# Run migrations
python scripts/migrate.py

# Reset database (DANGER: Loses all data)
docker-compose down -v postgres
docker-compose up -d postgres
sleep 30
python scripts/migrate.py
```

---

## 🐳 Docker Development Commands

### Service Management
```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres redis

# Stop all services
docker-compose down

# Stop and remove volumes (DANGER: Loses data)
docker-compose down -v

# Restart specific service
docker-compose restart discord_bot
docker-compose restart admin_panel
```

### Building and Debugging
```bash
# Build images without cache
docker-compose build --no-cache

# Build specific service
docker-compose build admin_panel
docker-compose build discord_bot

# View logs
docker-compose logs -f
docker-compose logs -f discord_bot
docker-compose logs -f admin_panel

# Execute commands in container
docker-compose exec admin_panel bash
docker-compose exec postgres psql -U postgres -d globalchat
```

### Development with File Watching
```bash
# Mount local code for development
# Edit docker-compose.yml to add volumes:
services:
  discord_bot:
    volumes:
      - ./chat:/app/chat
      - ./shared:/app/shared
  
  admin_panel:
    volumes:
      - ./admin/backend:/app/admin/backend
      - ./shared:/app/shared
```

---

## 🧪 Testing and Debugging

### Test Admin Panel
```bash
# Check API status
curl http://localhost:8000/api/status

# Test authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Test rooms endpoint
curl http://localhost:8000/api/rooms \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Database
```bash
# Check database connection
docker-compose exec postgres pg_isready -U postgres -d globalchat

# View tables
docker-compose exec postgres psql -U postgres -d globalchat -c "\dt"

# Check room data
docker-compose exec postgres psql -U postgres -d globalchat -c "SELECT * FROM chat_rooms;"
```

### Test Redis Cache
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Test cache operations
set test_key "test_value"
get test_key
keys *
exit
```

### Debug Discord Bot
```bash
# View bot logs
docker-compose logs -f discord_bot

# Test bot locally
cd chat
DEBUG=true python main.py

# Check bot permissions in Discord
# Ensure bot has Message Content Intent enabled
```

---

## 📁 Project Structure for Development

```
unbot/
├── chat/                        # Discord Bot
│   ├── main.py                  # Bot entry point
│   ├── chat_manager_new.py      # Main chat logic
│   ├── formatters.py            # Message formatting  
│   ├── reply_handler.py         # Reply processing
│   ├── content_filter.py        # Content validation
│   ├── permission_manager.py    # Permissions
│   └── commands.py              # Discord commands
│
├── admin/
│   ├── backend/                 # FastAPI Backend
│   │   ├── main.py              # FastAPI app
│   │   ├── api/                 # REST endpoints
│   │   │   ├── auth.py          # Authentication
│   │   │   ├── rooms.py         # Room management
│   │   │   ├── servers.py       # Server management
│   │   │   └── analytics.py     # Statistics
│   │   ├── core/                # Core functionality
│   │   │   ├── config.py        # Configuration
│   │   │   ├── security.py      # Auth & JWT
│   │   │   └── websocket.py     # Real-time updates
│   │   └── static/              # Built React files
│   └── frontend/                # React Frontend
│       ├── src/
│       │   ├── components/      # UI components
│       │   ├── pages/           # Dashboard pages
│       │   ├── hooks/           # React hooks
│       │   └── services/        # API calls
│       ├── package.json
│       └── build/               # Built files
│
├── shared/                      # Shared Components
│   ├── database/
│   │   ├── models.py            # SQLAlchemy models
│   │   └── manager.py           # Database manager
│   └── cache/
│       ├── redis_client.py      # Redis connection
│       └── cache_manager.py     # Caching logic
│
├── scripts/                     # Deployment Scripts
│   ├── deploy.sh                # Main deployment
│   └── migrate.py               # Database migrations
│
├── docker-compose.yml           # Container orchestration
├── .env                         # Environment variables
└── guides/                      # Documentation
    ├── local-development.md     # This file
    ├── vps-deployment.md        # VPS guide
    └── troubleshooting.md       # Debug guide
```

---

## 🔄 Hot Reload Development

### Frontend Hot Reload
When running `npm start` in `admin/frontend/`, changes to React components will automatically reload the browser.

### Backend Hot Reload
When running with `--reload` flag, FastAPI will automatically restart when Python files change.

### Bot Hot Reload
For bot development, you'll need to manually restart. Consider using a process manager:

```bash
# Install nodemon for auto-restart
npm install -g nodemon

# Use nodemon to watch Python files
nodemon --exec python main.py --ext py --watch chat/ --watch shared/
```

---

## 🐛 Common Development Issues

### Issue: "Discord bot not responding"
```bash
# Check bot token
cat .env | grep DISCORD_BOT_TOKEN

# Check bot logs
docker-compose logs discord_bot

# Verify bot permissions in Discord Developer Portal
```

### Issue: "Admin panel 404 error"
```bash
# Check if admin panel is running
docker-compose ps admin_panel

# Build React frontend
cd admin/frontend
npm run build

# Check static files
ls admin/backend/static/
```

### Issue: "Database connection error"
```bash
# Check if postgres is running
docker-compose ps postgres

# Wait for postgres to be ready
sleep 30

# Run migrations
python scripts/migrate.py
```

### Issue: "Port already in use"
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process if needed
kill -9 <PID>

# Or change port in docker-compose.yml
```

---

## 📊 Development Monitoring

### Service Health
```bash
# Check all services
docker-compose ps

# Expected output:
# globalchat_postgres   Up (healthy)
# globalchat_redis      Up (healthy)
# globalchat_bot        Up
# globalchat_admin      Up
```

### Real-time Logs
```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f admin_panel

# Filter logs
docker-compose logs -f | grep ERROR
```

### Performance Monitoring
- **Admin Panel**: http://localhost:8000 (Dashboard shows real-time stats)
- **API Docs**: http://localhost:8000/api/docs (Test endpoints)
- **Database**: Use pgAdmin or connect directly via psql

---

## 🔧 Advanced Development

### Custom Configuration
Create a `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'

services:
  admin_panel:
    volumes:
      - ./admin/backend:/app/admin/backend
      - ./shared:/app/shared
    environment:
      - DEBUG=true
    ports:
      - "8001:8000"  # Use different port if needed
  
  discord_bot:
    volumes:
      - ./chat:/app/chat
      - ./shared:/app/shared
    environment:
      - DEBUG=true
```

### Database Seeding
Create test data for development:

```python
# scripts/seed_dev_data.py
import asyncio
from shared.database.manager import db_manager

async def seed_data():
    # Create test rooms
    await db_manager.create_room("general", "dev", 50)
    await db_manager.create_room("testing", "dev", 25)
    
if __name__ == "__main__":
    asyncio.run(seed_data())
```

### Environment Switching
```bash
# Development environment
cp .env.development .env

# Testing environment  
cp .env.testing .env

# Local production test
cp .env.production.local .env
```

---

## ✅ Development Checklist

### Before Starting Development
- [ ] Discord bot token is valid
- [ ] Docker and Docker Compose installed
- [ ] Node.js and Python installed (for manual setup)
- [ ] .env file configured
- [ ] All dependencies installed

### Daily Development Workflow
- [ ] Start services: `docker-compose up -d`
- [ ] Check service status: `docker-compose ps`
- [ ] Monitor logs: `docker-compose logs -f`
- [ ] Test changes in admin panel and Discord
- [ ] Stop services when done: `docker-compose down`

### Before Committing Code
- [ ] All services start successfully
- [ ] No errors in logs
- [ ] Admin panel loads correctly
- [ ] Bot responds to Discord messages
- [ ] Tests pass (if any)
- [ ] Code follows project style

---

**🎉 Happy coding! Your local development environment is ready for building amazing features!**

**Quick Access:**
- **Admin Panel**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs  
- **Login**: admin / admin123