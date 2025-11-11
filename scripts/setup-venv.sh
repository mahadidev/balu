#!/bin/bash

# Virtual Environment Setup Script for Global Chat System
# This script sets up .venv for local development

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "docker-compose.yml" ]]; then
    log_error "Please run this script from the project root directory (where docker-compose.yml is located)"
    exit 1
fi

log_info "Setting up Python virtual environments for Global Chat System"
echo "================================================================="

# Check Python version
python_version=$(python3 --version 2>/dev/null || echo "Python 3 not found")
log_info "Detected: $python_version"

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required but not installed"
    log_info "Install Python 3.11+ and try again"
    exit 1
fi

# Check if pip is available
if ! python3 -m pip --version &> /dev/null; then
    log_error "pip is not available"
    log_info "Install pip and try again"
    exit 1
fi

# Create virtual environment for Discord bot
log_info "Creating virtual environment for Discord bot..."
cd chat
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
    log_success "Created .venv for Discord bot"
else
    log_warning ".venv already exists for Discord bot, skipping creation"
fi

# Activate venv and install dependencies
log_info "Installing Discord bot dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
log_success "Discord bot dependencies installed"
cd ..

# Create virtual environment for Admin backend
log_info "Creating virtual environment for Admin backend..."
cd admin/backend
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
    log_success "Created .venv for Admin backend"
else
    log_warning ".venv already exists for Admin backend, skipping creation"
fi

# Activate venv and install dependencies
log_info "Installing Admin backend dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
log_success "Admin backend dependencies installed"
cd ../..

# Install Node.js dependencies for frontend
log_info "Installing Node.js dependencies for Admin frontend..."
cd admin/frontend
if command -v npm &> /dev/null; then
    npm install
    log_success "Frontend dependencies installed"
else
    log_warning "npm not found, skipping frontend dependency installation"
    log_info "Install Node.js and npm, then run: cd admin/frontend && npm install"
fi
cd ../..

# Create activation scripts
log_info "Creating activation scripts..."

# Bot activation script
cat > activate-bot.sh << 'EOF'
#!/bin/bash
echo "🤖 Activating Discord Bot virtual environment..."
cd chat
source .venv/bin/activate
echo "✅ Bot environment activated!"
echo "💡 To run the bot: python main.py"
echo "💡 To deactivate: deactivate"
EOF
chmod +x activate-bot.sh

# Admin backend activation script
cat > activate-admin.sh << 'EOF'
#!/bin/bash
echo "📊 Activating Admin Backend virtual environment..."
cd admin/backend
source .venv/bin/activate
echo "✅ Admin backend environment activated!"
echo "💡 To run the backend: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo "💡 To deactivate: deactivate"
EOF
chmod +x activate-admin.sh

# Combined development script
cat > dev-venv.sh << 'EOF'
#!/bin/bash

# Development script for running with virtual environments
# This script runs the core services (DB, Redis) with Docker and apps with .venv

echo "🚀 Starting development environment with .venv"
echo "============================================="

# Check if .env exists
if [[ ! -f ".env" ]]; then
    echo "❌ .env file not found!"
    echo "💡 Copy .env.example to .env and configure it first"
    exit 1
fi

# Start PostgreSQL and Redis with Docker
echo "🐳 Starting database and cache services..."
docker-compose up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are ready
echo "🔍 Checking service health..."
if ! docker-compose exec postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "❌ PostgreSQL not ready"
    exit 1
fi

if ! docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis not ready"
    exit 1
fi

echo "✅ Core services are ready!"

# Run database migrations
echo "🔄 Running database migrations..."
cd chat
source .venv/bin/activate
python ../scripts/migrate.py
deactivate
cd ..

echo ""
echo "🎉 Development environment ready!"
echo ""
echo "📋 Next steps:"
echo "1. Start Discord Bot:"
echo "   ./activate-bot.sh"
echo "   python main.py"
echo ""
echo "2. Start Admin Backend (new terminal):"
echo "   ./activate-admin.sh"
echo "   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "3. Start Frontend (new terminal):"
echo "   cd admin/frontend"
echo "   npm start"
echo ""
echo "🔗 URLs:"
echo "   Admin Panel: http://localhost:8000"
echo "   Frontend Dev: http://localhost:3000"
echo "   API Docs: http://localhost:8000/api/docs"
echo ""
echo "⏹️  To stop services: docker-compose stop postgres redis"
EOF
chmod +x dev-venv.sh

# Create cleanup script
cat > cleanup-venv.sh << 'EOF'
#!/bin/bash

echo "🧹 Cleaning up virtual environments..."

# Remove bot .venv
if [[ -d "chat/.venv" ]]; then
    rm -rf chat/.venv
    echo "✅ Removed chat/.venv"
fi

# Remove admin .venv
if [[ -d "admin/backend/.venv" ]]; then
    rm -rf admin/backend/.venv
    echo "✅ Removed admin/backend/.venv"
fi

# Remove Node modules (optional)
read -p "🤔 Also remove node_modules? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ -d "admin/frontend/node_modules" ]]; then
        rm -rf admin/frontend/node_modules
        echo "✅ Removed admin/frontend/node_modules"
    fi
fi

# Remove activation scripts
rm -f activate-bot.sh activate-admin.sh dev-venv.sh cleanup-venv.sh

echo "🎉 Cleanup complete!"
EOF
chmod +x cleanup-venv.sh

# Create .gitignore entries for venvs
if [[ -f ".gitignore" ]]; then
    if ! grep -q ".venv" .gitignore; then
        echo "" >> .gitignore
        echo "# Virtual Environments" >> .gitignore
        echo "chat/.venv/" >> .gitignore
        echo "admin/backend/.venv/" >> .gitignore
        echo "*.sh" >> .gitignore
        log_success "Added .venv entries to .gitignore"
    fi
else
    cat > .gitignore << 'EOF'
# Virtual Environments
chat/.venv/
admin/backend/.venv/

# Environment files
.env

# Generated scripts
activate-bot.sh
activate-admin.sh
dev-venv.sh
cleanup-venv.sh

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
EOF
    log_success "Created .gitignore with .venv entries"
fi

echo ""
echo "================================================================="
log_success "Virtual environment setup complete!"
echo ""
echo "📋 What was created:"
echo "   ✅ chat/.venv - Discord bot virtual environment"
echo "   ✅ admin/backend/.venv - Admin backend virtual environment" 
echo "   ✅ activate-bot.sh - Bot environment activation script"
echo "   ✅ activate-admin.sh - Admin environment activation script"
echo "   ✅ dev-venv.sh - Combined development script"
echo "   ✅ cleanup-venv.sh - Environment cleanup script"
echo ""
echo "🚀 Quick start with .venv:"
echo "   ./dev-venv.sh"
echo ""
echo "🐳 Or continue using Docker:"
echo "   ./scripts/deploy.sh development"
echo ""
echo "🧹 To remove all .venv setups:"
echo "   ./cleanup-venv.sh"
echo ""
echo "📖 See guides/local-development.md for detailed instructions"