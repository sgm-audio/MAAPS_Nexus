#!/bin/bash
# MAAPS Health Check Script
# Returns 0 if healthy, 1 if unhealthy
# Usage: ./healthcheck.sh

set -e

MAAPS_DIR="/opt/maaps"
HEALTH_THRESHOLD=70

# Change to MAAPS directory
cd "$MAAPS_DIR"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run health check
HEALTH_OUTPUT=$(python -c "
from src.system import create_system
import sys

try:
    system = create_system()
    system.start()
    health = system.get_health()
    system.stop()

    health_score = health.get('health_score', 0)
    agents_healthy = health.get('agents_healthy', 0)
    agents_total = health.get('agents_total', 0)

    print(f'Health: {health_score}%')
    print(f'Agents: {agents_healthy}/{agents_total}')

    if health_score >= $HEALTH_THRESHOLD and agents_healthy == agents_total:
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
" 2>&1)

EXIT_CODE=$?

# Output result
echo "$HEALTH_OUTPUT"

# Return appropriate exit code
if [ $EXIT_CODE -eq 0 ]; then
    echo "Status: HEALTHY"
    exit 0
else
    echo "Status: UNHEALTHY"
    exit 1
fi
