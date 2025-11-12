#!/bin/bash

# Global Chat System - Complete Run Script
# This script builds the frontend, starts the backend and bot

set -e  # Exit on any error

echo "🚀 Starting Global Chat System..."
echo "================================="

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
    echo "✅ Docker is running"
}

# Function to build frontend
build_frontend() {
    echo ""
    echo "🔨 Building React frontend..."
    cd admin/frontend
    
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    
    echo "🏗️ Building optimized production build..."
    npm run build
    
    echo "✅ Frontend built successfully"
    cd ../..
}

# Function to start services with Docker Compose
start_services() {
    echo ""
    echo "🐳 Starting Docker services..."
    
    # Stop any existing containers
    echo "🛑 Stopping existing containers..."
    docker-compose down --remove-orphans
    
    # Build and start all services
    echo "🔨 Building and starting services..."
    docker-compose up --build -d
    
    echo "✅ All services started"
}

# Function to fix static file structure
fix_static_files() {
    echo ""
    echo "🔧 Fixing static file structure..."
    
    # Wait for admin container to be ready
    sleep 5
    
    # Check if nested static directory exists and flatten it
    if docker exec globalchat_admin test -d /app/admin/backend/static/static; then
        echo "📁 Flattening nested static directory structure..."
        docker exec globalchat_admin bash -c "cd /app/admin/backend/static && mv static/* . && rmdir static" 2>/dev/null || true
        echo "✅ Static file structure fixed"
    else
        echo "ℹ️ Static file structure already correct"
    fi
}

# Function to show service status
show_status() {
    echo ""
    echo "📊 Service Status:"
    echo "=================="
    docker-compose ps
    
    echo ""
    echo "🔍 Checking service health..."
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    # Check admin panel
    if curl -s -f http://localhost:8000/api/status > /dev/null; then
        echo "✅ Admin Panel: http://localhost:8000"
    else
        echo "❌ Admin Panel: Not responding"
    fi
    
    # Check database
    if docker exec globalchat_postgres pg_isready -U postgres -d balu > /dev/null 2>&1; then
        echo "✅ Database: Connected"
    else
        echo "❌ Database: Connection failed"
    fi
    
    # Check Redis
    if docker exec globalchat_redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis: Connected"
    else
        echo "❌ Redis: Connection failed"
    fi
    
    # Check Discord bot
    BOT_LOGS=$(docker logs globalchat_bot --tail 5 2>&1)
    if echo "$BOT_LOGS" | grep -q "is online\|connected"; then
        echo "✅ Discord Bot: Online"
    else
        echo "⚠️ Discord Bot: Check logs - docker logs globalchat_bot"
    fi
}

# Function to show logs
show_logs() {
    echo ""
    echo "📋 Recent Logs:"
    echo "==============="
    echo ""
    echo "🤖 Discord Bot Logs:"
    docker logs globalchat_bot --tail 10 2>&1 | head -10
    
    echo ""
    echo "🖥️ Admin Panel Logs:"
    docker logs globalchat_admin --tail 5 2>&1 | head -5
}

# Main execution
main() {
    echo "🎯 Global Chat System Startup"
    echo "Current directory: $(pwd)"
    
    # Check prerequisites
    check_docker
    
    # Build frontend
    build_frontend
    
    # Start all services
    start_services
    
    # Fix static file structure 
    fix_static_files
    
    # Show status
    show_status
    
    # Show logs
    show_logs
    
    echo ""
    echo "🎉 Startup Complete!"
    echo "===================="
    echo ""
    echo "📱 Access Points:"
    echo "  • Admin Panel: http://localhost:8000"
    echo "  • Login: admin / admin123"
    echo "  • API Docs: http://localhost:8000/api/docs"
    echo ""
    echo "📋 Useful Commands:"
    echo "  • View logs: docker-compose logs -f [service_name]"
    echo "  • Stop all: docker-compose down"
    echo "  • Restart: docker-compose restart [service_name]"
    echo ""
    echo "🤖 Discord Bot:"
    echo "  • Check status: docker logs globalchat_bot"
    echo "  • Restart: docker-compose restart discord_bot"
}

# Handle script arguments
case "${1:-}" in
    "logs")
        echo "📋 Showing all logs..."
        docker-compose logs -f
        ;;
    "stop")
        echo "🛑 Stopping all services..."
        docker-compose down
        ;;
    "restart")
        echo "🔄 Restarting services..."
        docker-compose restart
        ;;
    "status")
        show_status
        ;;
    *)
        main
        ;;
esac