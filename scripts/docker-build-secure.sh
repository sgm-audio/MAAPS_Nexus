#!/bin/bash
# Secure Docker Build and Deployment Script
# Builds MAAPS API with security hardening and vulnerability reduction

set -e  # Exit on error

echo "========================================"
echo "MAAPS API - Secure Docker Build"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Warning: docker-compose not found, will use docker compose${NC}"
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo -e "${GREEN}✓ Docker found${NC}"
echo ""

# Backup old Dockerfile if exists
if [ -f "Dockerfile" ] && [ ! -f "Dockerfile.backup" ]; then
    echo -e "${BLUE}Backing up original Dockerfile...${NC}"
    cp Dockerfile Dockerfile.backup
    echo -e "${GREEN}✓ Backup created: Dockerfile.backup${NC}"
fi

# Use fixed Dockerfile
if [ -f "Dockerfile.fixed" ]; then
    echo -e "${BLUE}Using security-hardened Dockerfile...${NC}"
    cp Dockerfile.fixed Dockerfile
    echo -e "${GREEN}✓ Dockerfile updated${NC}"
fi
echo ""

# Check .dockerignore
if [ ! -f ".dockerignore" ]; then
    echo -e "${YELLOW}Warning: .dockerignore not found${NC}"
    echo -e "${YELLOW}Creating .dockerignore to exclude secrets...${NC}"
    # Create basic .dockerignore
    cat > .dockerignore << 'EOF'
.env
.env.*
*.db
__pycache__
.git
node_modules/
.vscode/
.idea/
*.log
EOF
    echo -e "${GREEN}✓ .dockerignore created${NC}"
fi
echo ""

# Check environment file
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo -e "${YELLOW}Please create .env file with required variables:${NC}"
    echo ""
    echo "JWT_SECRET=your-secret-here"
    echo "DB_PASSWORD=your-db-password"
    echo "REDIS_PASSWORD=your-redis-password"
    echo "GRAFANA_PASSWORD=your-grafana-password"
    echo "ALLOWED_ORIGINS=https://yourdomain.com"
    echo ""
    exit 1
fi

# Build image
echo -e "${BLUE}Building Docker image...${NC}"
echo -e "${YELLOW}This may take 5-10 minutes...${NC}"
echo ""

docker build \
    --no-cache \
    --pull \
    -t maaps-api:latest \
    -f Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Build successful!${NC}"
else
    echo ""
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
echo ""

# Get image size
IMAGE_SIZE=$(docker images maaps-api:latest --format "{{.Size}}")
echo -e "${BLUE}Image size: ${GREEN}${IMAGE_SIZE}${NC}"
echo ""

# Scan for vulnerabilities if Docker Scout is available
if docker scout version &> /dev/null; then
    echo -e "${BLUE}Scanning for vulnerabilities...${NC}"
    docker scout cves maaps-api:latest || true
    echo ""

    echo -e "${BLUE}Getting recommendations...${NC}"
    docker scout recommendations maaps-api:latest || true
    echo ""
else
    echo -e "${YELLOW}Docker Scout not available, skipping vulnerability scan${NC}"
    echo -e "${YELLOW}To install: https://docs.docker.com/scout/install/${NC}"
    echo ""
fi

# Ask if user wants to run
echo ""
read -p "Do you want to run the container now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Starting container...${NC}"

    docker run -d \
        --name maaps-api \
        -p 8000:8000 \
        --env-file .env \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/logs:/app/logs" \
        maaps-api:latest

    echo ""
    echo -e "${GREEN}✓ Container started${NC}"
    echo ""
    echo "Container ID: $(docker ps -aqf "name=maaps-api")"
    echo ""
    echo "View logs: docker logs -f maaps-api"
    echo "Stop: docker stop maaps-api"
    echo "Remove: docker rm maaps-api"
    echo ""

    # Wait for health check
    echo -e "${BLUE}Waiting for health check...${NC}"
    sleep 5

    # Test health endpoint
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo -e "${GREEN}✓ Health check passed${NC}"
        echo ""
        echo "API available at: http://localhost:8000"
        echo "API docs: http://localhost:8000/docs"
    else
        echo -e "${YELLOW}Health check pending... check logs${NC}"
        echo "docker logs maaps-api"
    fi
fi

echo ""
echo "========================================"
echo -e "${GREEN}Build complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Run: docker run -p 8000:8000 --env-file .env maaps-api:latest"
echo "2. Test: curl http://localhost:8000/health"
echo "3. View docs: http://localhost:8000/docs"
echo ""
echo "For production deployment:"
echo "docker-compose -f docker-compose.secure.yml up -d"
echo ""
