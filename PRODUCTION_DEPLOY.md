# MAAPS Production Deployment Guide

**Complete guide for deploying MAAPS to production environments**

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Docker Deployment](#docker-deployment)
3. [Linux Server Deployment](#linux-server-deployment)
4. [Monitoring Setup](#monitoring-setup)
5. [Backup Strategy](#backup-strategy)
6. [Security Hardening](#security-hardening)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### System Requirements (Production)

- [ ] Linux server (Ubuntu 20.04+ or CentOS 8+)
- [ ] Python 3.11+
- [ ] 16-32 GB RAM
- [ ] 8-16 CPU cores
- [ ] 100+ GB SSD storage
- [ ] Network connectivity
- [ ] Sudo/root access

### Files Ready

- [x] `.env.production` - Production environment variables
- [x] `config.json` - Agent configuration
- [x] `Dockerfile` - Docker image definition
- [x] `docker-compose.yml` - Docker orchestration
- [x] `maaps.service` - systemd service file
- [x] `scripts/backup.sh` - Backup automation
- [x] `scripts/monitor.py` - Health monitoring
- [x] `scripts/healthcheck.sh` - Health check script

### Pre-Flight Tests

```bash
# 1. Run all tests
pytest tests/ -v

# 2. Run demonstrations
python start_using_maaps.py

# 3. Check health
python -c "from src.system import create_system; s=create_system(); s.start(); print(s.get_health()); s.stop()"
```

---

## Docker Deployment

### Option 1: Docker Compose (Recommended)

#### Step 1: Prepare Environment

```bash
# On your server
mkdir -p /opt/maaps
cd /opt/maaps

# Copy files (from your local machine)
scp -r F:\agents/* user@server:/opt/maaps/
```

#### Step 2: Configure Production

```bash
# Copy production environment
cp .env.production .env

# Review and adjust configuration
nano .env
nano config.json
```

#### Step 3: Build and Deploy

```bash
# Build the image
docker-compose build

# Start the service
docker-compose up -d

# Check logs
docker-compose logs -f maaps
```

#### Step 4: Verify Deployment

```bash
# Check container status
docker-compose ps

# Check health
docker exec maaps python -c "from src.system import create_system; s=create_system(); s.start(); print(s.get_health()); s.stop()"

# View logs
docker-compose logs --tail=100 maaps
```

### Option 2: Docker only

```bash
# Build image
docker build -t maaps:production .

# Run container
docker run -d \
  --name maaps \
  --restart unless-stopped \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/backups:/app/backups \
  --env-file .env.production \
  maaps:production

# Check status
docker ps
docker logs -f maaps
```

### Docker Management Commands

```bash
# Stop service
docker-compose down

# Restart service
docker-compose restart

# View resource usage
docker stats maaps

# Execute command in container
docker exec -it maaps bash

# Update deployment
docker-compose pull
docker-compose up -d
```

---

## Linux Server Deployment

### Step 1: Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip \
  build-essential libsndfile1 libsndfile1-dev ffmpeg

# Create MAAPS user
sudo useradd -m -s /bin/bash maaps
sudo usermod -aG sudo maaps
```

### Step 2: Install MAAPS

```bash
# Switch to MAAPS user
sudo su - maaps

# Create installation directory
sudo mkdir -p /opt/maaps
sudo chown maaps:maaps /opt/maaps
cd /opt/maaps

# Copy project files
# (upload via scp, rsync, or git clone)

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy production config
cp .env.production .env

# Edit configuration
nano .env
nano config.json

# Create directories
mkdir -p data logs backups
```

### Step 4: Install systemd Service

```bash
# Copy service file
sudo cp maaps.service /etc/systemd/system/

# Create log directory
sudo mkdir -p /var/log/maaps
sudo chown maaps:maaps /var/log/maaps

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable maaps

# Start service
sudo systemctl start maaps

# Check status
sudo systemctl status maaps
```

### Step 5: Verify Deployment

```bash
# Check service status
sudo systemctl status maaps

# View logs
sudo journalctl -u maaps -f

# Check health
sudo -u maaps /opt/maaps/venv/bin/python -c \
  "from src.system import create_system; s=create_system(); s.start(); print(s.get_health()); s.stop()"
```

### Service Management Commands

```bash
# Start service
sudo systemctl start maaps

# Stop service
sudo systemctl stop maaps

# Restart service
sudo systemctl restart maaps

# View logs
sudo journalctl -u maaps -n 100
sudo journalctl -u maaps -f

# Check status
sudo systemctl status maaps
```

---

## Monitoring Setup

### Continuous Monitoring

```bash
# Run monitoring script
nohup python scripts/monitor.py > /var/log/maaps/monitor.log 2>&1 &

# Or add to systemd (create maaps-monitor.service)
```

### Health Check Cron Job

```bash
# Add to crontab
crontab -e

# Add this line (check every 5 minutes)
*/5 * * * * /opt/maaps/scripts/healthcheck.sh >> /var/log/maaps/healthcheck.log 2>&1
```

### Monitoring Dashboard (Optional)

```bash
# Install Prometheus + Grafana
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Access Grafana at http://server:3000
```

---

## Backup Strategy

### Automated Backups

```bash
# Make backup script executable
chmod +x scripts/backup.sh

# Test backup
./scripts/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /opt/maaps/scripts/backup.sh >> /var/log/maaps/backup.log 2>&1
```

### Manual Backup

```bash
# Database backup
cp data/metadata.db backups/metadata_manual_$(date +%Y%m%d).db

# Full backup
tar -czf maaps_backup_$(date +%Y%m%d).tar.gz \
  data/ logs/ config.json .env.production
```

### Restore from Backup

```bash
# Stop service
sudo systemctl stop maaps  # or docker-compose down

# Restore database
cp backups/metadata_YYYYMMDD.db data/metadata.db

# Restore configuration
cp backups/config_YYYYMMDD.json config.json

# Start service
sudo systemctl start maaps  # or docker-compose up -d
```

---

## Security Hardening

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 8000/tcp  # If exposing API
sudo ufw enable

# Verify
sudo ufw status
```

### File Permissions

```bash
# Set proper ownership
sudo chown -R maaps:maaps /opt/maaps

# Restrict permissions
chmod 700 /opt/maaps/data
chmod 700 /opt/maaps/backups
chmod 600 /opt/maaps/.env.production
chmod 600 /opt/maaps/config.json
```

### SSL/TLS (if exposing API)

```bash
# Generate self-signed certificate (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /opt/maaps/ssl/private.key \
  -out /opt/maaps/ssl/certificate.crt

# Production: Use Let's Encrypt
sudo certbot certonly --standalone -d your-domain.com
```

### Security Checklist

- [ ] Running as non-root user
- [ ] File permissions restricted
- [ ] Firewall configured
- [ ] SSL/TLS enabled (if API exposed)
- [ ] Regular security updates
- [ ] Log monitoring enabled
- [ ] Backup encryption (if needed)

---

## Performance Tuning

### Production Configuration

Edit `.env.production`:

```bash
# Increase resources
MAX_WORKER_THREADS=16
MESSAGE_BUS_DISPATCHER_THREADS=8
CACHE_MAX_SIZE_MB=2000

# Optimize limits
MAX_CPU_USAGE_PERCENT=80.0
MAX_MEMORY_USAGE_PERCENT=85.0
MAX_CONCURRENT_WORKFLOWS=50
```

### System Tuning

```bash
# Increase file descriptors
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize TCP settings (Linux)
sudo sysctl -w net.core.somaxconn=4096
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=4096
```

### Performance Monitoring

```bash
# CPU usage
htop

# Memory usage
free -h

# Disk I/O
iostat -x 1

# MAAPS metrics
python -c "from src.system import create_system; s=create_system(); s.start(); print(s.get_resource_metrics()); s.stop()"
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u maaps -n 100

# Check status
sudo systemctl status maaps

# Test manually
sudo -u maaps /opt/maaps/venv/bin/python /opt/maaps/my_audio_app.py

# Check permissions
ls -la /opt/maaps/
```

### High Resource Usage

```bash
# Check system resources
htop
free -h

# Check MAAPS health
python -c "from src.system import create_system; s=create_system(); s.start(); print(s.get_resource_metrics()); s.stop()"

# Reduce concurrent tasks
# Edit config.json -> agents.performance_optimization.scheduler.max_concurrent_tasks
```

### Database Corruption

```bash
# Stop service
sudo systemctl stop maaps

# Backup current database
cp data/metadata.db data/metadata.db.corrupt

# Restore from backup
cp backups/metadata_LATEST.db data/metadata.db

# Start service
sudo systemctl start maaps
```

### Log Files Too Large

```bash
# Rotate logs manually
sudo logrotate /etc/logrotate.d/maaps

# Check log size
du -sh logs/

# Clean old logs
find logs/ -name "*.log.*" -mtime +30 -delete
```

---

## Production Deployment Verification

### Final Checklist

- [ ] Service starts automatically on boot
- [ ] Health checks passing
- [ ] Logs being written correctly
- [ ] Backups running automatically
- [ ] Monitoring active
- [ ] Resource usage normal
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Team trained on operations
- [ ] Incident response plan ready

### Success Metrics

After deployment, verify:

```bash
# 1. System health
# Should return 100% health
python -c "from src.system import create_system; s=create_system(); s.start(); h=s.get_health(); print(f\"Health: {h['health_score']}%\"); s.stop()"

# 2. Uptime
sudo systemctl status maaps | grep "Active:"

# 3. Resource usage
docker stats maaps  # or htop

# 4. Recent logs
sudo journalctl -u maaps -n 50
```

---

## Support & Maintenance

### Regular Maintenance

- **Daily**: Check health status
- **Weekly**: Review logs for errors
- **Monthly**: Update dependencies
- **Quarterly**: Full system audit

### Getting Help

1. Check logs: `journalctl -u maaps -f`
2. Run health check: `scripts/healthcheck.sh`
3. Review documentation: `DEPLOYMENT.md`
4. Check monitoring: `scripts/monitor.py`

---

**MAAPS Production Deployment Guide v1.0**
System Status: ✅ Production Ready
Last Updated: 2025-11-15
