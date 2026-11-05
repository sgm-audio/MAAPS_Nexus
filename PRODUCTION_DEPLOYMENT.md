# MAAPS Production Deployment Guide

Complete guide for deploying MAAPS to production with Docker, monitoring, and best practices.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Production Architecture](#production-architecture)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Configuration](#configuration)
6. [SSL/TLS Setup](#ssltls-setup)
7. [Monitoring & Observability](#monitoring--observability)
8. [Backup & Recovery](#backup--recovery)
9. [Scaling](#scaling)
10. [Troubleshooting](#troubleshooting)
11. [Security Checklist](#security-checklist)

## Prerequisites

### Required Software

- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **Git**: >= 2.30
- **Bash**: 4.0+ (for deployment scripts)

### Server Requirements

**Minimum:**
- 4 CPU cores
- 8 GB RAM
- 50 GB SSD storage
- Ubuntu 20.04+ / Debian 11+ / RHEL 8+

**Recommended:**
- 8 CPU cores
- 16 GB RAM
- 100 GB SSD storage
- GPU for audio processing (NVIDIA with CUDA 11.8+)

### Network Requirements

- Open ports: 80 (HTTP), 443 (HTTPS)
- Domain name configured (for SSL)
- Firewall rules configured

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/maaps.git
cd maaps
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.production.example .env.production

# Edit configuration
nano .env.production
```

**Update these critical values:**

```bash
# Database
DB_PASSWORD=your-secure-database-password

# Redis
REDIS_PASSWORD=your-secure-redis-password

# Security
JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# CORS
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

### 3. Setup SSL Certificates

**Option A: Let's Encrypt (Recommended)**

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone -d api.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/api.yourdomain.com/privkey.pem nginx/ssl/
sudo chown $USER:$USER nginx/ssl/*.pem
```

**Option B: Self-Signed (Development Only)**

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=api.yourdomain.com"
```

### 4. Deploy

```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Start production deployment
./scripts/deploy.sh start
```

### 5. Verify Deployment

```bash
# Check service status
./scripts/deploy.sh status

# Check health
./scripts/deploy.sh health

# View logs
./scripts/deploy.sh logs maaps-api
```

**Test API:**

```bash
curl https://api.yourdomain.com/api/health
```

**Expected response:**

```json
{
  "health_score": 100.0,
  "agents_healthy": 5,
  "agents_total": 5,
  "system_uptime_seconds": 123.45,
  "timestamp": "2025-11-17T15:30:00.000000"
}
```

## Production Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ 80/443
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (Reverse Proxy)                    │
│  • SSL/TLS Termination                                      │
│  • Rate Limiting                                            │
│  • Static File Serving                                      │
│  • Load Balancing                                           │
└──────┬───────────────────────────────────┬──────────────────┘
       │                                   │
       │ /api/*                           │ / (Frontend)
       ▼                                   ▼
┌──────────────────────┐          ┌──────────────────────┐
│   MAAPS API (x4)     │          │  React Frontend      │
│  • FastAPI           │          │  • Static Build      │
│  • Multi-Agent Core  │          │  • SPA Router        │
│  • WebSocket         │          └──────────────────────┘
└──────┬───────────────┘
       │
       ├─────────┬─────────┬──────────┐
       ▼         ▼         ▼          ▼
┌────────┐  ┌────────┐  ┌──────┐  ┌─────────┐
│PostgreSQL Redis    │ Prometheus Grafana  │
│  • Sessions        │  • Metrics │  • Dashboards
│  • Metadata        │  • Alerts  │  • Visualization
└────────┘  └────────┘  └──────┘  └─────────┘
```

## Step-by-Step Deployment

### Phase 1: Server Preparation

#### 1.1 Update System

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y curl git vim htop
```

#### 1.2 Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

#### 1.3 Configure Firewall

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Firewalld (RHEL/CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Phase 2: Application Setup

#### 2.1 Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/maaps.git /opt/maaps
cd /opt/maaps

# Setup environment
cp .env.production.example .env.production
nano .env.production  # Edit configuration

# Create necessary directories
mkdir -p data logs backups nginx/ssl monitoring
```

#### 2.2 Build Frontend

```bash
cd frontend/maaps-ui

# Install dependencies
npm install

# Build for production
npm run build

# Copy to nginx serve directory
# (or configure nginx to serve from dist/)
```

### Phase 3: Deploy Services

#### 3.1 Start Infrastructure

```bash
# Start database and cache first
docker-compose -f docker-compose.production.yml up -d postgres redis

# Wait for services to be ready
sleep 10

# Check database
docker exec maaps-postgres pg_isready -U maaps
```

#### 3.2 Start Application

```bash
# Start API servers
docker-compose -f docker-compose.production.yml up -d maaps-api

# Check health
curl http://localhost:8000/health
```

#### 3.3 Start Reverse Proxy

```bash
# Start Nginx
docker-compose -f docker-compose.production.yml up -d nginx

# Check configuration
docker exec maaps-nginx nginx -t

# View status
docker-compose -f docker-compose.production.yml ps
```

### Phase 4: Monitoring Setup

```bash
# Start monitoring stack
docker-compose -f docker-compose.production.yml up -d prometheus grafana loki

# Access Grafana
# Navigate to http://your-server:3001
# Login with admin / password from .env.production

# Import MAAPS dashboards from monitoring/grafana-dashboards/
```

## Configuration

### Environment Variables

#### Core Application

| Variable | Description | Example |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `production` |
| `LOG_LEVEL` | Logging verbosity | `info` |
| `WORKERS` | Number of API workers | `4` |

#### Database

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_HOST` | Database hostname | `postgres` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `maaps` |
| `DB_USER` | Database user | `maaps` |
| `DB_PASSWORD` | Database password | `secure-password` |

#### Security

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET` | JWT signing key | `random-32-byte-key` |
| `CORS_ORIGINS` | Allowed origins | `https://app.com` |

### Nginx Configuration

Edit `nginx/nginx.conf` to customize:

- **Server name**: Change `api.maaps.io` to your domain
- **Rate limits**: Adjust `limit_req_zone` values
- **SSL settings**: Update certificate paths
- **Upstream servers**: Add/remove API workers

### Database Initialization

Create `scripts/init-db.sql` for database schema:

```sql
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create tables
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions USING hash(token);

-- Add your schema here
```

## SSL/TLS Setup

### Let's Encrypt (Production)

#### Initial Setup

```bash
# Install Certbot
sudo apt-get install certbot

# Stop Nginx temporarily
docker-compose -f docker-compose.production.yml stop nginx

# Obtain certificate
sudo certbot certonly --standalone \
  -d api.yourdomain.com \
  -d www.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos \
  --no-eff-email

# Copy certificates
sudo cp /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/api.yourdomain.com/privkey.pem nginx/ssl/
sudo chown $USER:$USER nginx/ssl/*.pem

# Start Nginx
docker-compose -f docker-compose.production.yml up -d nginx
```

#### Auto-Renewal

Create `/etc/cron.d/certbot-renew`:

```cron
0 3 * * * root certbot renew --quiet --post-hook "cd /opt/maaps && ./scripts/deploy.sh restart nginx"
```

### SSL Testing

```bash
# Test SSL configuration
curl -I https://api.yourdomain.com

# Check SSL rating
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=api.yourdomain.com
```

## Monitoring & Observability

### Prometheus Metrics

**Endpoints:**
- Prometheus: `http://your-server:9090`
- API Metrics: `http://localhost:8000/metrics`

**Key Metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `agent_messages_processed` - Agent message throughput
- `system_cpu_percent` - CPU usage
- `system_memory_percent` - Memory usage

### Grafana Dashboards

**Access:** `http://your-server:3001`

**Default Dashboards:**
1. **System Overview** - Health, resource usage
2. **API Performance** - Request rates, latency
3. **Agent Metrics** - Message processing, errors
4. **Database Metrics** - Connections, queries

### Alerting

Configure alerts in `monitoring/prometheus.yml`:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - "/etc/prometheus/alerts/*.yml"
```

Create alert rules in `monitoring/alerts/api-alerts.yml`:

```yaml
groups:
  - name: maaps-api
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} (threshold: 0.05)"

      - alert: APIDown
        expr: up{job="maaps-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MAAPS API is down"
```

### Log Aggregation

Logs are centralized in Loki and accessible via Grafana:

```bash
# View logs in Grafana
# Navigate to Explore -> Select Loki data source
# Query: {container_name="maaps-api"}

# Or use docker logs
docker-compose -f docker-compose.production.yml logs -f maaps-api
```

## Backup & Recovery

### Automated Backups

#### Create Backup

```bash
./scripts/deploy.sh backup
```

**Backup includes:**
- PostgreSQL database dump
- Application data directory
- Configuration files
- Logs (last 7 days)

**Backup location:** `./backups/maaps_backup_YYYYMMDD_HHMMSS.tar.gz`

#### Schedule Backups

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * cd /opt/maaps && ./scripts/deploy.sh backup

# Weekly backup cleanup (keep last 4 weeks)
0 3 * * 0 cd /opt/maaps/backups && ls -t maaps_backup_*.tar.gz | tail -n +5 | xargs -r rm
```

### Restore from Backup

```bash
./scripts/deploy.sh restore backups/maaps_backup_20250117_020000.tar.gz
```

**Restore process:**
1. Stops all services
2. Extracts backup files
3. Restores database
4. Restarts services
5. Verifies health

### Disaster Recovery

#### Database Backup

```bash
# Manual database backup
docker exec maaps-postgres pg_dump -U maaps maaps > backup.sql

# Restore database
cat backup.sql | docker exec -i maaps-postgres psql -U maaps maaps
```

#### Full System Backup

```bash
# Backup entire Docker volumes
docker run --rm \
  -v maaps_postgres-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres-data.tar.gz -C /data .

# Restore Docker volumes
docker run --rm \
  -v maaps_postgres-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/postgres-data.tar.gz -C /data
```

## Scaling

### Horizontal Scaling

#### Add API Workers

Edit `docker-compose.production.yml`:

```yaml
services:
  maaps-api:
    deploy:
      replicas: 8  # Increase from 4 to 8
```

Or scale manually:

```bash
docker-compose -f docker-compose.production.yml up -d --scale maaps-api=8
```

#### Load Balancer Configuration

Nginx automatically load balances across replicas:

```nginx
upstream maaps_api {
    least_conn;  # Use least connections algorithm
    server maaps-api:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

### Vertical Scaling

#### Resource Limits

```yaml
services:
  maaps-api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Database Scaling

#### Read Replicas

```yaml
postgres-replica:
  image: postgres:15-alpine
  environment:
    POSTGRES_MASTER_HOST: postgres
  command: |
    bash -c "
    until pg_isready -h postgres; do sleep 1; done
    pg_basebackup -h postgres -D /var/lib/postgresql/data -U replicator -Xs -P
    postgres -c hot_standby=on
    "
```

#### Connection Pooling

Use PgBouncer:

```yaml
pgbouncer:
  image: pgbouncer/pgbouncer
  environment:
    DATABASES_HOST: postgres
    DATABASES_PORT: 5432
    DATABASES_DBNAME: maaps
    PGBOUNCER_POOL_MODE: transaction
    PGBOUNCER_MAX_CLIENT_CONN: 1000
```

## Troubleshooting

### Common Issues

#### API Not Responding

```bash
# Check if container is running
docker ps | grep maaps-api

# Check logs
docker logs maaps-api

# Check health endpoint
curl http://localhost:8000/health

# Restart service
docker-compose -f docker-compose.production.yml restart maaps-api
```

#### Database Connection Errors

```bash
# Check database status
docker exec maaps-postgres pg_isready -U maaps

# Check connection from API
docker exec maaps-api nc -zv postgres 5432

# View database logs
docker logs maaps-postgres

# Restart database
docker-compose -f docker-compose.production.yml restart postgres
```

#### High Memory Usage

```bash
# Check resource usage
docker stats

# Reduce worker count in .env.production
WORKERS=2

# Restart with new configuration
./scripts/deploy.sh restart
```

#### SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in nginx/ssl/fullchain.pem -noout -dates

# Verify certificate chain
openssl verify -CAfile nginx/ssl/fullchain.pem nginx/ssl/fullchain.pem

# Renew Let's Encrypt certificate
sudo certbot renew
```

### Performance Tuning

#### Database Optimization

```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM sessions WHERE user_id = 'xyz';

-- Create indexes
CREATE INDEX CONCURRENTLY idx_table_column ON table(column);

-- Update statistics
ANALYZE;
```

#### API Tuning

```python
# In .env.production
WORKERS=4                    # 2 * CPU cores
WORKER_CONNECTIONS=1000
REQUEST_TIMEOUT_SECONDS=60
MAX_UPLOAD_SIZE_MB=100
```

### Debug Mode

Enable debug logging:

```bash
# In .env.production
LOG_LEVEL=debug

# Restart
./scripts/deploy.sh restart
```

## Security Checklist

### Pre-Deployment

- [ ] Change all default passwords
- [ ] Generate strong JWT secret
- [ ] Configure CORS origins
- [ ] Setup SSL certificates
- [ ] Configure firewall rules
- [ ] Disable debug mode
- [ ] Review environment variables

### Access Control

- [ ] Use non-root Docker user
- [ ] Implement API authentication
- [ ] Setup rate limiting
- [ ] Configure IP whitelisting (if needed)
- [ ] Enable audit logging

### Network Security

- [ ] SSL/TLS enabled
- [ ] HSTS headers configured
- [ ] Security headers added
- [ ] Expose only necessary ports
- [ ] Use private Docker networks

### Data Protection

- [ ] Database encrypted at rest
- [ ] Backups encrypted
- [ ] Secrets not in version control
- [ ] PII data anonymized in logs
- [ ] Secure file upload validation

### Monitoring

- [ ] Health checks enabled
- [ ] Alerting configured
- [ ] Log aggregation setup
- [ ] Metrics collection active
- [ ] Uptime monitoring

### Updates

- [ ] Security patches applied
- [ ] Docker images updated
- [ ] Dependencies scanned for vulnerabilities
- [ ] Regular backup testing
- [ ] Disaster recovery plan documented

## Maintenance

### Regular Tasks

**Daily:**
- Check system health
- Review error logs
- Monitor resource usage

**Weekly:**
- Verify backups
- Update dependencies
- Review metrics

**Monthly:**
- SSL certificate renewal
- Security audit
- Performance review
- Capacity planning

### Update Procedure

```bash
# 1. Create backup
./scripts/deploy.sh backup

# 2. Pull latest code
git pull origin main

# 3. Update deployment
./scripts/deploy.sh update

# 4. Verify health
./scripts/deploy.sh health
```

## Support

- **Documentation**: https://docs.maaps.io
- **Issues**: https://github.com/yourusername/maaps/issues
- **Email**: support@maaps.io
- **Discord**: https://discord.gg/maaps

---

**Last Updated**: 2025-11-17
**Version**: 1.0.0
