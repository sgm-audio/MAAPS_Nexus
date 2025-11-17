# Deployment Guide: Multi-Agent Audio Processing System

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the System](#running-the-system)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Scaling & Performance](#scaling--performance)
7. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

- **OS**: Windows 10+, Linux (Ubuntu 20.04+), macOS 10.15+
- **Python**: 3.8 or higher
- **RAM**: 8 GB minimum, 16 GB recommended
- **CPU**: 4 cores minimum, 8 cores recommended
- **Storage**: 10 GB free space for system and cache

### Recommended for Production

- **RAM**: 32 GB+
- **CPU**: 16+ cores (for parallel processing)
- **GPU**: NVIDIA GPU with CUDA support (for ML models)
- **Storage**: SSD with 50+ GB free space

## Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd agents
```

### Step 2: Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Optional: Install ML dependencies for advanced features
pip install torch torchaudio transformers

# Optional: Install additional audio processing libraries
pip install noisereduce essentia
```

### Step 4: Verify Installation

```bash
# Test imports
python -c "from src.system import create_system; print('Installation successful')"
```

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# System Configuration
AGENT_LOG_LEVEL=INFO
AGENT_HEARTBEAT_INTERVAL=1.0

# Message Bus
MESSAGE_BUS_MAX_QUEUE_SIZE=10000
MESSAGE_BUS_DISPATCHER_THREADS=4

# Resource Limits
MAX_CPU_USAGE_PERCENT=85.0
MAX_MEMORY_USAGE_PERCENT=90.0
MAX_GPU_USAGE_PERCENT=90.0

# Cache Configuration
CACHE_MAX_SIZE_MB=500
CACHE_EVICTION_POLICY=lru

# Database
METADATA_DB_PATH=./data/metadata.db
PROJECT_DB_PATH=./data/projects.db

# Performance
ENABLE_GPU=true
GPU_DEVICE_ID=0
MAX_WORKER_THREADS=8

# Monitoring
ENABLE_HEALTH_MONITORING=true
HEALTH_CHECK_INTERVAL=5.0
METRICS_COLLECTION_INTERVAL=1.0
```

### Agent Configuration File

Create `config.json`:

```json
{
  "system": {
    "name": "AudioProcessingSystem",
    "version": "1.0.0",
    "monitoring": {
      "enabled": true,
      "interval_seconds": 5.0,
      "auto_restart_failed_agents": true
    }
  },
  "message_bus": {
    "max_queue_size": 10000,
    "priority_enabled": true,
    "dead_letter_queue_enabled": true
  },
  "agents": {
    "audio_enhancement": {
      "enabled": true,
      "processing_threads": 4,
      "default_params": {
        "noise_reduction_amount": 0.8,
        "preserve_transients": true,
        "declicking_sensitivity": 0.5
      },
      "limits": {
        "max_processing_time_seconds": 300,
        "max_audio_length_seconds": 600
      }
    },
    "content_generation": {
      "enabled": true,
      "models": {
        "melody": "default",
        "harmony": "default",
        "drums": "default"
      },
      "limits": {
        "max_generation_bars": 32,
        "max_processing_time_seconds": 60
      }
    },
    "performance_optimization": {
      "enabled": true,
      "monitoring_interval": 1.0,
      "cache": {
        "enabled": true,
        "max_size_mb": 500,
        "eviction_policy": "lru"
      },
      "scheduler": {
        "algorithm": "resource_aware",
        "max_concurrent_tasks": 10
      }
    },
    "metadata_management": {
      "enabled": true,
      "database_path": "./data/metadata.db",
      "deep_analysis_default": true,
      "search_index_size": 10000
    }
  },
  "workflows": {
    "default_timeout_seconds": 300,
    "max_retries": 3,
    "retry_delay_seconds": 1.0
  }
}
```

## Running the System

### Development Mode

```python
# Create and start system
from src.system import create_system

system = create_system()
system.start()

# Use the system
health = system.get_health()
print(f"System Health: {health['health_score']}%")

# When done
system.stop()
```

### Production Mode with Context Manager

```python
from src.system import create_system

# System automatically starts and stops
with create_system() as system:
    # Check health
    health = system.get_health()
    print(f"Health Score: {health['health_score']}%")

    # Process audio
    result = system.enhance_audio(audio_data, sample_rate=44100)

    # Generate music
    melody = system.generate_music('melody', musical_context)
```

### As a Service (Linux)

Create `/etc/systemd/system/audio-agents.service`:

```ini
[Unit]
Description=Multi-Agent Audio Processing System
After=network.target

[Service]
Type=simple
User=audiouser
WorkingDirectory=/opt/audio-agents
Environment="PATH=/opt/audio-agents/venv/bin"
ExecStart=/opt/audio-agents/venv/bin/python -m src.system
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable audio-agents
sudo systemctl start audio-agents
sudo systemctl status audio-agents
```

## Monitoring & Maintenance

### Health Monitoring

```python
# Get system health
health = system.get_health()

print(f"Health Score: {health['health_score']}%")
print(f"Healthy Agents: {health['agents_healthy']}/{health['agents_total']}")
print(f"System Uptime: {health['system_uptime_seconds']}s")

# Get message bus metrics
bus_metrics = health['message_bus_metrics']
print(f"Messages Delivered: {bus_metrics['messages_delivered']}")
print(f"Avg Latency: {bus_metrics['avg_latency_ms']}ms")
```

### Resource Monitoring

```python
# Get current resource usage
metrics = system.get_resource_metrics()

print(f"CPU: {metrics['metrics']['cpu_usage_percent']}%")
print(f"Memory: {metrics['metrics']['memory_usage_percent']}%")
print(f"GPU: {metrics['metrics']['gpu_usage_percent']}%")
```

### Agent Status

```python
# Check all agents
agents = system.get_all_agents()
for agent in agents:
    print(f"{agent['agent_name']}: {agent['state']}")
    print(f"  Messages Received: {agent['metrics']['messages_received']}")
    print(f"  Messages Sent: {agent['metrics']['messages_sent']}")
    print(f"  Uptime: {agent['metrics']['uptime_seconds']}s")
```

### Logging

Configure logging in your application:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audio_system.log'),
        logging.StreamHandler()
    ]
)
```

## Scaling & Performance

### Horizontal Scaling

Deploy multiple instances with load balancing:

```
                  ┌─── Agent Instance 1
Load Balancer ────┼─── Agent Instance 2
                  └─── Agent Instance 3
                           │
                     Shared Database
```

### Vertical Scaling

Increase resources per instance:

```json
{
  "agents": {
    "audio_enhancement": {
      "processing_threads": 16  // Increase threads
    }
  },
  "performance_optimization": {
    "cache": {
      "max_size_mb": 2000  // Increase cache
    },
    "scheduler": {
      "max_concurrent_tasks": 50  // More concurrent tasks
    }
  }
}
```

### Performance Tuning

1. **Enable GPU Processing**: Set `ENABLE_GPU=true`
2. **Increase Worker Threads**: Adjust `MAX_WORKER_THREADS`
3. **Optimize Cache Size**: Balance between memory and performance
4. **Tune Task Scheduler**: Use `resource_aware` algorithm
5. **Batch Processing**: Process multiple files together

### Production Checklist

- [ ] Set `AGENT_LOG_LEVEL=WARNING` or `ERROR`
- [ ] Enable health monitoring
- [ ] Configure automatic agent restarts
- [ ] Set up log rotation
- [ ] Configure resource limits
- [ ] Enable caching
- [ ] Set up database backups
- [ ] Configure alerting for failures
- [ ] Test disaster recovery procedures

## Troubleshooting

### Common Issues

#### 1. Agents Fail to Start

**Symptom**: Agents show as "stopped" or "error" state

**Solutions**:
```python
# Check agent status
status = system.get_agent_status('audio_enhancement_agent')
print(status)

# Restart agent
from src.orchestration import get_coordinator
coordinator = get_coordinator()
coordinator.restart_agent('audio_enhancement_agent')
```

#### 2. High Memory Usage

**Symptom**: Memory usage exceeds 90%

**Solutions**:
```python
# Clear cache
system.message_bus.request(
    Message(
        topic="system.cache.clear",
        sender="admin",
        payload={"clear_all": True}
    )
)

# Reduce cache size in config
# cache.max_size_mb: 500 -> 250
```

#### 3. Slow Processing

**Symptom**: Audio processing takes too long

**Solutions**:
- Enable GPU processing
- Increase worker threads
- Optimize task scheduling
- Check resource bottlenecks

```python
# Analyze performance
health = system.get_health()
bus_metrics = health['message_bus_metrics']

if bus_metrics['avg_latency_ms'] > 100:
    print("High message latency detected")

# Check resource usage
metrics = system.get_resource_metrics()
if metrics['metrics']['cpu_usage_percent'] > 80:
    print("CPU bottleneck")
```

#### 4. Workflow Timeout

**Symptom**: Workflows fail with timeout error

**Solutions**:
```python
# Increase workflow timeout
workflow_def['steps'][0]['timeout'] = 180.0  # 3 minutes

# Or use longer default timeout in config
{
  "workflows": {
    "default_timeout_seconds": 600
  }
}
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Start system with debug
system = create_system()
system.start()
```

### Getting Help

1. Check logs: `tail -f audio_system.log`
2. Review system health: `system.get_health()`
3. Check agent statuses: `system.get_all_agents()`
4. Monitor resources: `system.get_resource_metrics()`

## Backup & Recovery

### Database Backup

```bash
# Backup metadata database
cp data/metadata.db backups/metadata_$(date +%Y%m%d).db

# Automated backup script
#!/bin/bash
BACKUP_DIR="/opt/backups/audio-agents"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp data/metadata.db $BACKUP_DIR/metadata_$DATE.db
```

### System State Backup

```python
# Export system configuration
import json

config = {
    'agents': system.get_all_agents(),
    'health': system.get_health(),
    'timestamp': time.time()
}

with open('system_state.json', 'w') as f:
    json.dump(config, f, indent=2)
```

## Security

### Best Practices

1. **Authentication**: Implement authentication for API access
2. **Encryption**: Encrypt sensitive data in databases
3. **Input Validation**: Validate all input data
4. **Resource Limits**: Set limits to prevent DoS
5. **Logging**: Log all security-relevant events

### Network Security

```python
# Configure firewall rules
# Allow only necessary ports
# Use HTTPS for external access
# Implement rate limiting
```

---

**Deployment Guide Version 1.0** - Multi-Agent Audio Processing System

For additional support, consult the README.md and inline code documentation.
