# Global Chat System - Scalable Architecture

A high-performance Discord global chat system with real-time admin panel, designed to handle 40-50+ servers with continuous message flow.

## ✨ Features

### Discord Bot
- **Cross-server messaging** with reply support
- **Modular architecture** with separate components
- **Permission management** with DM notifications
- **Content filtering** and rate limiting
- **Database migration** from SQLite to PostgreSQL

### Admin Panel
- **Real-time dashboard** with live statistics
- **Room management** with permissions
- **Server monitoring** and analytics
- **WebSocket updates** for live data
- **Modern React interface** with Tailwind CSS

### Architecture
- **PostgreSQL + Redis** for high performance
- **Async operations** with connection pooling
- **FastAPI backend** with JWT authentication
- **Docker deployment** ready
- **Horizontal scaling** support

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Discord Bot Token
- Basic understanding of Discord bot setup

### 1. Clone and Setup
```bash
git clone <repository>
cd unbot

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Required Environment Variables
```bash
# Discord Bot Token (Required)
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Database Password (Required)
POSTGRES_PASSWORD=your_secure_password

# Admin Panel Secret (Required) 
SECRET_KEY=your-super-secret-key-minimum-32-characters
```

### 3. Deploy with Docker
```bash
# Make deploy script executable
chmod +x scripts/deploy.sh

# Deploy in development mode
./scripts/deploy.sh

# Or deploy in production mode
./scripts/deploy.sh production
```

### 4. Access Admin Panel
- **URL**: http://localhost:8000
- **Username**: admin
- **Password**: admin123 (change in production!)

## 📁 Project Structure

```
unbot/
├── 🤖 chat/                     # Discord Bot
│   ├── main.py                  # Bot entry point
│   ├── chat_manager_new.py      # Main chat logic
│   ├── formatters.py            # Message formatting
│   ├── reply_handler.py         # Reply processing
│   ├── content_filter.py        # Content validation
│   ├── permission_manager.py    # Permissions
│   └── commands.py              # Discord commands
│
├── 📊 admin/                    # Admin Panel
│   ├── backend/                 # FastAPI Backend
│   │   ├── main.py              # FastAPI entry point
│   │   ├── api/                 # API routes
│   │   │   ├── auth.py          # Authentication
│   │   │   ├── rooms.py         # Room management
│   │   │   ├── servers.py       # Server management
│   │   │   └── analytics.py     # Statistics
│   │   └── core/                # Core functionality
│   │       ├── config.py        # Configuration
│   │       ├── security.py      # Auth & security
│   │       └── websocket.py     # Real-time updates
│   └── frontend/                # React Frontend
│       ├── src/
│       │   ├── components/      # UI components
│       │   ├── pages/           # Dashboard pages
│       │   ├── hooks/           # React hooks
│       │   └── services/        # API calls
│       └── package.json
│
├── 🗄️ shared/                  # Shared Components
│   ├── database/
│   │   ├── models.py            # SQLAlchemy models
│   │   └── manager.py           # Database manager
│   └── cache/
│       ├── redis_client.py      # Redis connection
│       └── cache_manager.py     # Caching logic
│
└── 🚀 scripts/                 # Deployment
    ├── deploy.sh                # Deployment script
    └── migrate.py               # Database migrations
```

## 🛠️ Development

### Local Development Setup

1. **Install Python dependencies**:
```bash
# Bot dependencies
cd chat
pip install -r requirements.txt

# Backend dependencies  
cd ../admin/backend
pip install -r requirements.txt
```

2. **Install Node.js dependencies**:
```bash
cd ../frontend
npm install
```

3. **Start services individually**:
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run migrations
python scripts/migrate.py

# Start bot
cd chat
python main.py

# Start backend (in new terminal)
cd admin/backend  
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (in new terminal)
cd admin/frontend
npm start
```

### Frontend Development

The React frontend uses:
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Chart.js** for analytics
- **WebSocket** for real-time updates

```bash
cd admin/frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_BOT_TOKEN` | Discord bot token | Required |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT secret key | Required |
| `ADMIN_USERNAME` | Admin panel username | `admin` |
| `ADMIN_PASSWORD` | Admin panel password | `admin123` |
| `DEBUG` | Debug mode | `false` |

### Database Configuration

- **Connection Pool**: 20 base connections, 30 overflow
- **Async Operations**: Full async/await support  
- **Indexes**: Optimized for message volume
- **Migrations**: Automated schema management

### Redis Configuration

- **Connection Pool**: 20 max connections
- **Caching Strategy**: Intelligent TTL-based caching
- **Session Storage**: JWT token validation
- **Rate Limiting**: Per-user message limits

## 📊 Performance

### Designed for Scale
- **40-50+ servers** sending messages continuously
- **1000+ messages/second** throughput
- **100+ concurrent** admin panel users
- **90%+ cache hit ratio** for frequent queries
- **<100ms average** API response time

### Database Optimization
- **Proper indexing** for high-volume queries
- **Connection pooling** to handle concurrent load
- **Async operations** for non-blocking performance
- **Raw SQL** for critical paths (message logging)

### Caching Strategy
- **Room data**: 1 hour TTL
- **Permissions**: 30 minutes TTL
- **Channel lookups**: 2 hours TTL
- **Live stats**: 1 minute TTL
- **Rate limiting**: 5 minutes TTL

## 🔐 Security

### Authentication
- **JWT tokens** with configurable expiration
- **Password hashing** with bcrypt
- **Session management** with Redis
- **CORS protection** for API endpoints

### Data Protection
- **Input validation** on all endpoints
- **SQL injection** prevention with parameterized queries
- **XSS protection** with proper sanitization
- **Rate limiting** to prevent abuse

### Production Security
- **Environment variables** for sensitive data
- **HTTPS enforcement** (with Nginx)
- **Container isolation** with Docker
- **Non-root users** in containers

## 🚢 Deployment

### Docker Production Deployment

1. **Prepare environment**:
```bash
# Copy and configure environment
cp .env.example .env
nano .env

# Set production values
SECRET_KEY=your-super-secret-production-key
POSTGRES_PASSWORD=secure-database-password
ADMIN_PASSWORD=secure-admin-password
DEBUG=false
```

2. **Deploy with backup**:
```bash
# Deploy with automatic backup
./scripts/deploy.sh production true
```

3. **Verify deployment**:
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Test admin panel
curl http://localhost:8000/api/status
```

### VPS Deployment

For VPS deployment without domain:

1. **Install Docker**:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
```

2. **Clone and deploy**:
```bash
git clone <repository>
cd unbot
cp .env.example .env
# Edit .env with your settings
./scripts/deploy.sh production
```

3. **Access via IP**:
- Admin Panel: `http://your-vps-ip:8000`
- API Docs: `http://your-vps-ip:8000/api/docs`

## 📚 API Documentation

### REST API Endpoints

**Authentication**:
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout  
- `GET /api/auth/me` - Current user info

**Room Management**:
- `GET /api/rooms` - List all rooms
- `POST /api/rooms` - Create new room
- `GET /api/rooms/{id}` - Get room details
- `GET /api/rooms/{id}/permissions` - Get room permissions
- `GET /api/rooms/{id}/channels` - List room channels

**Analytics**:
- `GET /api/analytics/live` - Live statistics
- `GET /api/analytics/messages` - Message statistics  
- `GET /api/analytics/health` - System health

**Server Management**:
- `GET /api/servers` - List connected servers
- `GET /api/servers/{guild_id}` - Server details
- `GET /api/servers/channels` - All registered channels

### WebSocket API

Connect to `/ws` for real-time updates:

```javascript
// Authentication
ws.send(JSON.stringify({
  type: 'authenticate', 
  token: 'your-jwt-token'
}));

// Message types received
{
  type: 'live_stats',
  data: { /* live statistics */ }
}

{
  type: 'system_notification',
  data: { level: 'info', message: '...' }
}
```

## 🐛 Troubleshooting

### Common Issues

**Bot not connecting**:
- Verify `DISCORD_BOT_TOKEN` in `.env`
- Check bot permissions in Discord server
- Review bot logs: `docker-compose logs discord_bot`

**Database connection failed**:
- Ensure PostgreSQL is running: `docker-compose ps postgres`
- Check database URL format in `.env`
- Run migration: `python scripts/migrate.py`

**Admin panel not loading**:
- Verify admin panel is running: `docker-compose ps admin_panel`
- Check for port conflicts on 8000
- Review backend logs: `docker-compose logs admin_panel`

**WebSocket connection issues**:
- Check firewall settings
- Verify CORS configuration
- Test WebSocket endpoint directly

### Logs and Debugging

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f discord_bot
docker-compose logs -f admin_panel

# Check service status
docker-compose ps

# Restart services
docker-compose restart discord_bot
docker-compose restart admin_panel
```

## 🔄 Migration from SQLite

If migrating from the previous SQLite version:

1. **Backup your data**:
```bash
# Export existing rooms and messages
python export_sqlite_data.py
```

2. **Deploy new system**:
```bash
./scripts/deploy.sh development
```

3. **Import data** (if migration script available):
```bash
python scripts/import_sqlite_data.py
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Development Guidelines

- Follow existing code style and patterns
- Add tests for new features
- Update documentation for API changes
- Use TypeScript for frontend components
- Write clear commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README and code comments
- **Issues**: Open GitHub issues for bugs and features
- **Discord**: Contact the development team
- **Email**: Send support requests to team

## 🏗️ Future Enhancements

- **Mobile app** with React Native
- **Voice message** support
- **File sharing** with cloud storage
- **Advanced analytics** with ML insights
- **Multi-language** support
- **Plugin system** for extensions

---

Made with ❤️ for the Discord community