#!/bin/bash

# Global Chat System Deployment Script
# This script handles deployment of the entire system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="globalchat"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_DIR="backups"

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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning ".env file not found. Creating from .env.example..."
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_warning "Please edit .env file with your configuration before proceeding."
            log_warning "Required: DISCORD_BOT_TOKEN, POSTGRES_PASSWORD, SECRET_KEY"
            exit 1
        else
            log_error ".env.example file not found. Please create environment configuration."
            exit 1
        fi
    fi
    
    log_success "Prerequisites check completed."
}

backup_data() {
    if [[ "$1" == "true" ]]; then
        log_info "Creating backup..."
        mkdir -p "$BACKUP_DIR"
        
        # Backup database if running
        if docker-compose ps postgres | grep -q "Up"; then
            backup_file="$BACKUP_DIR/postgres_$(date +%Y%m%d_%H%M%S).sql"
            docker-compose exec -T postgres pg_dump -U postgres balu > "$backup_file"
            log_success "Database backup created: $backup_file"
        fi
        
        # Backup volumes
        docker run --rm -v "${PROJECT_NAME}_postgres_data:/data" -v "$(pwd)/$BACKUP_DIR:/backup" busybox tar czf /backup/postgres_data_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
        docker run --rm -v "${PROJECT_NAME}_redis_data:/data" -v "$(pwd)/$BACKUP_DIR:/backup" busybox tar czf /backup/redis_data_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
        
        log_success "Data backup completed."
    fi
}

build_images() {
    log_info "Building Docker images..."
    
    # Build with no cache for clean build
    docker-compose build --no-cache
    
    log_success "Docker images built successfully."
}

deploy_services() {
    local mode="$1"
    
    log_info "Deploying services in $mode mode..."
    
    # Stop existing services
    docker-compose down
    
    # Start core services (database and cache)
    log_info "Starting core services..."
    docker-compose up -d postgres redis
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    timeout 60 bash -c 'until docker-compose exec postgres pg_isready -U postgres -d balu; do sleep 2; done'
    
    # Run database migrations
    log_info "Running database migrations..."
    docker-compose run --rm discord_bot python scripts/migrate.py
    
    # Start application services
    if [[ "$mode" == "production" ]]; then
        log_info "Starting application services with Nginx..."
        docker-compose --profile production up -d
    else
        log_info "Starting application services..."
        docker-compose up -d discord_bot admin_panel
    fi
    
    log_success "Services deployed successfully."
}

check_health() {
    log_info "Checking service health..."
    
    # Wait for services to be ready
    sleep 10
    
    # Check each service
    services=("postgres" "redis" "discord_bot" "admin_panel")
    
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            log_success "$service is running"
        else
            log_error "$service failed to start"
            docker-compose logs "$service"
            exit 1
        fi
    done
    
    # Test admin panel endpoint
    if curl -f http://localhost:8000/api/status &> /dev/null; then
        log_success "Admin panel is responding"
    else
        log_warning "Admin panel may not be ready yet"
    fi
}

show_status() {
    log_info "Current system status:"
    docker-compose ps
    
    echo
    log_info "Service URLs:"
    echo "  Admin Panel: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/api/docs"
    echo "  Database: localhost:5432"
    echo "  Redis: localhost:6379"
    
    echo
    log_info "To view logs:"
    echo "  All services: docker-compose logs -f"
    echo "  Specific service: docker-compose logs -f <service_name>"
    
    echo
    log_info "To stop all services:"
    echo "  docker-compose down"
}

# Main deployment function
main() {
    local mode="${1:-development}"
    local backup="${2:-false}"
    
    log_info "Starting deployment in $mode mode..."
    
    # Check prerequisites
    check_prerequisites
    
    # Create backup if requested
    backup_data "$backup"
    
    # Build images
    build_images
    
    # Deploy services
    deploy_services "$mode"
    
    # Check health
    check_health
    
    # Show status
    show_status
    
    log_success "Deployment completed successfully!"
}

# Script usage
usage() {
    echo "Usage: $0 [mode] [backup]"
    echo "  mode: development|production (default: development)"
    echo "  backup: true|false (default: false)"
    echo
    echo "Examples:"
    echo "  $0                           # Deploy in development mode"
    echo "  $0 production                # Deploy in production mode"
    echo "  $0 development true          # Deploy with backup"
    echo "  $0 production true           # Production deploy with backup"
}

# Handle script arguments
case "$1" in
    -h|--help)
        usage
        exit 0
        ;;
    "")
        main "development" "false"
        ;;
    production|development)
        main "$1" "${2:-false}"
        ;;
    *)
        log_error "Invalid mode: $1"
        usage
        exit 1
        ;;
esac