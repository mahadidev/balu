# Virtual Environment Development Guide

Guide for local development using Python virtual environments (.venv) instead of Docker.

## 🐍 Why Use .venv?

### Advantages of .venv:
- **⚡ Faster startup** - No container overhead
- **🔧 Direct debugging** - Use IDE debugger directly
- **💾 Less resource usage** - No Docker daemon required
- **🔄 Instant code reload** - No rebuilding containers

### When to Use .venv:
- **Local development** and testing
- **IDE debugging** sessions  
- **Quick prototyping** of features
- **Learning** the codebase

### When to Use Docker:
- **Production deployment**
- **Full system testing**
- **CI/CD pipelines**
- **Team collaboration** (consistent environment)

---

## 🚀 Quick Setup

### Step 1: Run Setup Script
```bash
# Make setup script executable
chmod +x scripts/setup-venv.sh

# Run the setup
./scripts/setup-venv.sh
```

This creates:
- `chat/.venv` - Discord bot virtual environment
- `admin/backend/.venv` - Admin backend virtual environment  
- Helper scripts for activation
- Frontend dependencies (Node.js)

### Step 2: Start Development Environment
```bash
# Start core services (PostgreSQL, Redis) + setup .venv apps
./dev-venv.sh
```

This will:
1. Start PostgreSQL and Redis with Docker
2. Run database migrations
3. Provide instructions for starting each component

### Step 3: Start Individual Components

#### Terminal 1: Discord Bot
```bash
./activate-bot.sh
python main.py
```

#### Terminal 2: Admin Backend  
```bash
./activate-admin.sh
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 3: Frontend (Optional)
```bash
cd admin/frontend
npm start
```

---

## 📁 Project Structure with .venv

```
unbot/
├── chat/
│   ├── .venv/              # Bot virtual environment
│   ├── requirements.txt    # Bot dependencies
│   └── main.py            # Bot entry point
├── admin/
│   ├── backend/
│   │   ├── .venv/         # Backend virtual environment  
│   │   ├── requirements.txt # Backend dependencies
│   │   └── main.py        # FastAPI entry point
│   └── frontend/
│       ├── node_modules/   # Frontend dependencies
│       └── package.json
├── scripts/
│   └── setup-venv.sh      # .venv setup script
├── activate-bot.sh        # Bot activation helper
├── activate-admin.sh      # Admin activation helper  
├── dev-venv.sh            # Combined development script
└── docker-compose.yml     # For PostgreSQL/Redis only
```

---

## 🔧 Manual Setup (Alternative)

If you prefer manual setup:

### Setup Bot Environment
```bash
cd chat
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..
```

### Setup Admin Backend Environment  
```bash
cd admin/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ../..
```

### Setup Frontend
```bash
cd admin/frontend
npm install
cd ../..
```

---

## 🚀 Development Workflow

### Daily Development Routine

#### 1. Start Core Services
```bash
# Start PostgreSQL and Redis (Docker)
docker-compose up -d postgres redis

# Check they're ready
docker-compose ps
```

#### 2. Activate Bot Environment
```bash
# Method 1: Use helper script
./activate-bot.sh
python main.py

# Method 2: Manual activation
cd chat
source .venv/bin/activate
python main.py
```

#### 3. Activate Admin Backend (New Terminal)
```bash
# Method 1: Use helper script
./activate-admin.sh
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Method 2: Manual activation
cd admin/backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. Start Frontend (New Terminal)
```bash
cd admin/frontend
npm start
```

### Development URLs
- **Admin Panel**: http://localhost:8000
- **Frontend Dev**: http://localhost:3000  
- **API Docs**: http://localhost:8000/api/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379

---

## 🔄 Switching Between Docker and .venv

### From Docker to .venv
```bash
# Stop Docker services
docker-compose down

# Start with .venv
./dev-venv.sh
# Then follow instructions to start each component
```

### From .venv to Docker
```bash
# Stop .venv services (Ctrl+C in each terminal)
# Stop core services
docker-compose stop postgres redis

# Start full Docker environment
./scripts/deploy.sh development
```

---

## 🐛 Troubleshooting .venv

### Issue: "python3: command not found"
```bash
# Install Python 3.11+
# macOS
brew install python3

# Ubuntu/Debian  
sudo apt update && sudo apt install python3 python3-pip python3-venv

# Check version
python3 --version
```

### Issue: "pip: command not found"
```bash
# Install pip
# macOS (usually included)
python3 -m ensurepip --upgrade

# Ubuntu/Debian
sudo apt install python3-pip
```

### Issue: ".venv activation fails"
```bash
# Recreate virtual environment
rm -rf chat/.venv
cd chat
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Database connection failed"
```bash
# Ensure PostgreSQL is running via Docker
docker-compose up -d postgres redis
sleep 10

# Test connection
docker-compose exec postgres pg_isready -U postgres

# Run migrations
cd chat
source .venv/bin/activate
python ../scripts/migrate.py
```

### Issue: "Module not found errors"
```bash
# Check if you're in the right virtual environment
which python
# Should show: /path/to/project/chat/.venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt

# Check installed packages
pip list
```

### Issue: "Admin panel not loading"
```bash
# Check if backend is running
curl http://localhost:8000/api/status

# Check backend logs
# Look for errors in the terminal where you started the backend

# Restart backend
cd admin/backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 💡 IDE Configuration

### Visual Studio Code
1. **Open project folder** in VS Code
2. **Select Python interpreter**:
   - Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
   - Type "Python: Select Interpreter"
   - Choose `./chat/.venv/bin/python` for bot development
   - Or `./admin/backend/.venv/bin/python` for admin development

3. **Configure launch.json** for debugging:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Discord Bot",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/chat/main.py",
            "cwd": "${workspaceFolder}/chat",
            "console": "integratedTerminal",
            "python": "${workspaceFolder}/chat/.venv/bin/python"
        },
        {
            "name": "Admin Backend",
            "type": "python", 
            "request": "launch",
            "module": "uvicorn",
            "args": ["main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            "cwd": "${workspaceFolder}/admin/backend",
            "console": "integratedTerminal",
            "python": "${workspaceFolder}/admin/backend/.venv/bin/python"
        }
    ]
}
```

### PyCharm
1. **Open project** in PyCharm
2. **Configure Python interpreter**:
   - Go to Settings → Project → Python Interpreter
   - Click gear icon → Add
   - Choose "Existing environment"
   - Select `chat/.venv/bin/python` or `admin/backend/.venv/bin/python`

---

## 🧹 Cleanup

### Remove All .venv Environments
```bash
# Use cleanup script
./cleanup-venv.sh

# Or manual cleanup
rm -rf chat/.venv
rm -rf admin/backend/.venv
rm -rf admin/frontend/node_modules
rm -f activate-*.sh dev-venv.sh cleanup-venv.sh
```

### Reset to Docker-Only
```bash
# Run cleanup
./cleanup-venv.sh

# Remove generated files
rm -f activate-*.sh dev-venv.sh

# Continue with Docker
./scripts/deploy.sh development
```

---

## 📊 Performance Comparison

| Aspect | .venv | Docker |
|--------|--------|--------|
| **Startup Time** | ~5 seconds | ~30-60 seconds |
| **Memory Usage** | ~100MB | ~500MB+ |
| **Hot Reload** | Instant | 2-5 seconds |
| **Debugging** | Native IDE support | Container debugging |
| **Isolation** | Python only | Complete system |
| **Production Parity** | Good | Excellent |
| **Setup Complexity** | Medium | Low |

---

## ✅ Best Practices

### Development Workflow
1. **Use .venv for daily development** - faster iteration
2. **Test with Docker before committing** - ensure production parity
3. **Keep dependencies in sync** - same versions in requirements.txt
4. **Use IDE debugger with .venv** - better debugging experience

### Environment Management
1. **Don't commit .venv/** to git - already in .gitignore
2. **Update requirements.txt** when adding dependencies
3. **Test both .venv and Docker** before production deployment
4. **Use consistent Python versions** (3.11+)

### Debugging Tips
1. **Set breakpoints in IDE** when using .venv
2. **Use print statements** for quick debugging
3. **Check logs** in terminal for both approaches
4. **Monitor database** with admin panel

---

**🎯 Choose the right tool for the job:**
- **Daily coding**: .venv
- **Testing & deployment**: Docker
- **Production**: Docker always

**Happy coding! 🚀**