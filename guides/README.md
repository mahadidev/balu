# Guides Directory

This directory contains comprehensive guides for the Global Chat System. Choose the guide that matches your needs.

## 📚 Available Guides

### 🏠 [Local Development](local-development.md)
Complete guide for setting up and running the system on your local machine for development and testing.

**Use this if you want to:**
- Develop new features
- Test changes locally
- Debug issues
- Learn how the system works

**Key Topics:**
- Docker setup for development
- Manual installation steps
- Frontend/backend development workflow
- Database and Redis setup
- Hot reload configuration

### 🐍 [Virtual Environment Development](venv-development.md)
Alternative development setup using Python virtual environments (.venv) for faster local development.

**Use this if you want to:**
- Faster startup times (5 seconds vs 60 seconds)
- Direct IDE debugging support
- Lower resource usage
- Quick prototyping and testing

**Key Topics:**
- .venv setup and activation
- Hybrid approach (Docker for services, .venv for apps)
- IDE configuration for debugging
- Performance comparison
- Switching between Docker and .venv

---

### ☁️ [VPS Deployment](vps-deployment.md)
Step-by-step guide for deploying the system on a Virtual Private Server for production use.

**Use this if you want to:**
- Deploy to a VPS (DigitalOcean, Linode, AWS, etc.)
- Run the system in production
- Serve multiple Discord servers (40-50+)
- Have external access to the admin panel

**Key Topics:**
- VPS requirements and setup
- Docker installation on different Linux distributions
- Production environment configuration
- Firewall and security setup
- Domain and SSL configuration
- Performance optimization

---

### 🐛 [Troubleshooting](troubleshooting.md)
Comprehensive troubleshooting guide for common issues and their solutions.

**Use this if you:**
- Encounter errors during setup or operation
- Need to debug specific problems
- Want to understand system health checks
- Need emergency recovery procedures

**Key Topics:**
- Discord bot issues
- Admin panel problems
- Database and Redis issues
- Network connectivity problems
- Performance and security issues
- Emergency recovery procedures

---

### 📡 [API Reference](api-reference.md)
Complete API documentation for developers and integrators.

**Use this if you:**
- Want to integrate with the system
- Need to understand API endpoints
- Are building custom tools or extensions
- Want to understand WebSocket communication

**Key Topics:**
- Authentication and JWT tokens
- Room and channel management APIs
- Analytics and statistics endpoints
- WebSocket real-time communication
- Error codes and responses

---

## 🚀 Quick Start

### For Development
```bash
# Follow local development guide
cd /Users/mahadihasan/Desktop/unbot
cp .env.example .env
# Edit .env with your Discord bot token
./scripts/deploy.sh development
```

### For Production (VPS)
```bash
# Follow VPS deployment guide
git clone <your-repository>
cd unbot
cp .env.example .env
# Edit .env with production values
./scripts/deploy.sh production
```

### Need Help?
1. **Check [Troubleshooting Guide](troubleshooting.md)** first
2. **Review logs**: `docker-compose logs -f`
3. **Verify status**: `docker-compose ps`
4. **Test API**: `curl http://localhost:8000/api/status`

---

## 📖 Guide Features

Each guide includes:
- ✅ **Step-by-step instructions**
- ✅ **Command examples with explanations**
- ✅ **Troubleshooting sections**
- ✅ **Verification steps**
- ✅ **Best practices and tips**
- ✅ **Security considerations**

---

## 🎯 Choose Your Path

| Goal | Guide | Time Required |
|------|-------|---------------|
| **Learn the system** | [Local Development](local-development.md) | 30-60 minutes |
| **Fast local development** | [Virtual Environment Development](venv-development.md) | 15-30 minutes |
| **Deploy for production** | [VPS Deployment](vps-deployment.md) | 1-2 hours |
| **Fix issues** | [Troubleshooting](troubleshooting.md) | 10-30 minutes |
| **Build integrations** | [API Reference](api-reference.md) | As needed |

---

## 🔧 Common Commands Reference

### Check System Status
```bash
docker-compose ps
docker-compose logs -f
curl http://localhost:8000/api/status
```

### Restart Services
```bash
docker-compose restart
docker-compose restart discord_bot
docker-compose restart admin_panel
```

### View Logs
```bash
docker-compose logs -f
docker-compose logs discord_bot
docker-compose logs admin_panel
```

### Emergency Reset (⚠️ Loses Data)
```bash
docker-compose down -v
docker-compose up --build -d
```

---

**💡 Pro Tip:** Bookmark this page for quick access to all guides!

**🎉 Ready to get started? Pick a guide above and follow the step-by-step instructions!**