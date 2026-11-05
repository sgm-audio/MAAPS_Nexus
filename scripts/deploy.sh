#!/bin/bash

# MAAPS Production Deployment Script
# Usage: ./scripts/deploy.sh [start|stop|restart|status|logs|backup]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.production.yml"
ENV_FILE="$PROJECT_ROOT/.env.production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_env() {
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file not found: $ENV_FILE"
        log_info "Copy .env.production.example to .env.production and configure it"
        exit 1
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
}

pre_deploy_checks() {
    log_info "Running pre-deployment checks..."

    check_docker
    check_env

    # Check disk space
    available_space=$(df -BG "$PROJECT_ROOT" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 10 ]; then
        log_warn "Low disk space: ${available_space}GB available (recommended: 10GB+)"
    fi

    # Check SSL certificates
    if [ ! -f "$PROJECT_ROOT/nginx/ssl/fullchain.pem" ]; then
        log_warn "SSL certificates not found in nginx/ssl/"
        log_warn "Run './scripts/setup-ssl.sh' to generate certificates"
    fi

    log_info "Pre-deployment checks completed"
}

build_images() {
    log_info "Building Docker images..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache
    log_info "Images built successfully"
}

start_services() {
    log_info "Starting MAAPS services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    log_info "Services started successfully"

    log_info "Waiting for services to be healthy..."
    sleep 10

    check_health
}

stop_services() {
    log_info "Stopping MAAPS services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    log_info "Services stopped successfully"
}

restart_services() {
    log_info "Restarting MAAPS services..."
    stop_services
    sleep 5
    start_services
}

check_health() {
    log_info "Checking service health..."

    # Check API health
    max_retries=30
    retry=0
    while [ $retry -lt $max_retries ]; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            log_info "✓ API is healthy"
            break
        fi
        retry=$((retry + 1))
        sleep 2
    done

    if [ $retry -eq $max_retries ]; then
        log_error "✗ API health check failed"
        show_logs maaps-api
        exit 1
    fi

    # Check database
    if docker exec maaps-postgres pg_isready -U maaps > /dev/null 2>&1; then
        log_info "✓ Database is healthy"
    else
        log_error "✗ Database health check failed"
    fi

    # Check Redis
    if docker exec maaps-redis redis-cli ping > /dev/null 2>&1; then
        log_info "✓ Redis is healthy"
    else
        log_error "✗ Redis health check failed"
    fi
}

show_status() {
    log_info "Service Status:"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

    echo ""
    log_info "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
        maaps-api maaps-postgres maaps-redis maaps-nginx 2>/dev/null || true
}

show_logs() {
    service=${1:-maaps-api}
    log_info "Showing logs for $service (Ctrl+C to exit)..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f "$service"
}

backup_data() {
    log_info "Creating backup..."

    backup_dir="$PROJECT_ROOT/backups"
    mkdir -p "$backup_dir"

    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="$backup_dir/maaps_backup_$timestamp.tar.gz"

    # Backup database
    log_info "Backing up database..."
    docker exec maaps-postgres pg_dump -U maaps maaps > "$backup_dir/db_$timestamp.sql"

    # Backup data directory
    log_info "Backing up data directory..."
    tar -czf "$backup_file" -C "$PROJECT_ROOT" data logs backups/db_$timestamp.sql

    # Cleanup SQL dump
    rm "$backup_dir/db_$timestamp.sql"

    log_info "Backup created: $backup_file"

    # Keep only last 7 backups
    cd "$backup_dir"
    ls -t maaps_backup_*.tar.gz | tail -n +8 | xargs -r rm
    log_info "Cleaned up old backups (keeping last 7)"
}

restore_backup() {
    backup_file="$1"

    if [ -z "$backup_file" ]; then
        log_error "Usage: $0 restore <backup_file>"
        exit 1
    fi

    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi

    log_warn "This will restore from backup and may overwrite current data"
    read -p "Are you sure you want to continue? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Restore cancelled"
        exit 0
    fi

    log_info "Restoring from backup: $backup_file"

    # Stop services
    stop_services

    # Extract backup
    tar -xzf "$backup_file" -C "$PROJECT_ROOT"

    # Start services
    start_services

    log_info "Restore completed successfully"
}

update_deployment() {
    log_info "Updating deployment..."

    # Create backup before update
    backup_data

    # Pull latest code
    log_info "Pulling latest code..."
    git pull origin main || log_warn "Git pull failed (not a git repository?)"

    # Rebuild images
    build_images

    # Restart services
    restart_services

    log_info "Deployment updated successfully"
}

show_help() {
    cat << EOF
MAAPS Production Deployment Script

Usage: $0 [command]

Commands:
    start       Start all services
    stop        Stop all services
    restart     Restart all services
    status      Show service status
    logs        Show service logs (default: maaps-api)
    build       Build Docker images
    health      Check service health
    backup      Create backup of data and database
    restore     Restore from backup
    update      Update deployment (pull, build, restart)
    help        Show this help message

Examples:
    $0 start
    $0 logs maaps-api
    $0 restore backups/maaps_backup_20250117_120000.tar.gz

EOF
}

# Main
case "${1:-}" in
    start)
        pre_deploy_checks
        build_images
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    build)
        build_images
        ;;
    health)
        check_health
        ;;
    backup)
        backup_data
        ;;
    restore)
        restore_backup "$2"
        ;;
    update)
        update_deployment
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: ${1:-}"
        echo ""
        show_help
        exit 1
        ;;
esac
