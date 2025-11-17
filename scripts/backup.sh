#!/bin/bash
# MAAPS Backup Script
# Usage: ./backup.sh
# Add to crontab: 0 2 * * * /opt/maaps/scripts/backup.sh

set -e

# Configuration
MAAPS_DIR="/opt/maaps"
BACKUP_DIR="/opt/backups/maaps"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}[MAAPS Backup] Starting backup at $(date)${NC}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
echo -e "${YELLOW}[1/5] Backing up databases...${NC}"
if [ -f "$MAAPS_DIR/data/metadata.db" ]; then
    cp "$MAAPS_DIR/data/metadata.db" "$BACKUP_DIR/metadata_$DATE.db"
    echo "  -> metadata.db backed up"
fi

if [ -f "$MAAPS_DIR/data/projects.db" ]; then
    cp "$MAAPS_DIR/data/projects.db" "$BACKUP_DIR/projects_$DATE.db"
    echo "  -> projects.db backed up"
fi

# Backup configuration
echo -e "${YELLOW}[2/5] Backing up configuration...${NC}"
cp "$MAAPS_DIR/config.json" "$BACKUP_DIR/config_$DATE.json"
cp "$MAAPS_DIR/.env.production" "$BACKUP_DIR/env_production_$DATE.txt"
echo "  -> Configuration backed up"

# Backup logs (compress)
echo -e "${YELLOW}[3/5] Backing up logs...${NC}"
if [ -d "$MAAPS_DIR/logs" ]; then
    tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" -C "$MAAPS_DIR" logs/
    echo "  -> Logs backed up and compressed"
fi

# Create backup manifest
echo -e "${YELLOW}[4/5] Creating backup manifest...${NC}"
cat > "$BACKUP_DIR/manifest_$DATE.txt" <<EOF
MAAPS Backup Manifest
Date: $(date)
Hostname: $(hostname)
User: $(whoami)

Files backed up:
- metadata_$DATE.db
- projects_$DATE.db
- config_$DATE.json
- env_production_$DATE.txt
- logs_$DATE.tar.gz

System Info:
$(python --version)
Disk Usage: $(df -h $MAAPS_DIR | tail -1)
EOF
echo "  -> Manifest created"

# Cleanup old backups
echo -e "${YELLOW}[5/5] Cleaning up old backups (older than $RETENTION_DAYS days)...${NC}"
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete
REMOVED=$(find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS 2>/dev/null | wc -l)
echo "  -> Removed $REMOVED old backup files"

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo -e "${GREEN}[SUCCESS] Backup completed!${NC}"
echo "  -> Total backup size: $BACKUP_SIZE"
echo "  -> Backup location: $BACKUP_DIR"
echo "  -> Backup timestamp: $DATE"

# Optional: Send notification (uncomment to enable)
# echo "MAAPS backup completed successfully at $(date)" | mail -s "MAAPS Backup Report" admin@example.com

exit 0
