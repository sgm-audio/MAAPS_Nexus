# MAAPS REST API Guide

**Production-ready REST API for Multi-Agent Audio Processing System**

---

## Quick Start

### Installation

```bash
# Install API dependencies
pip install -r requirements-api.txt

# Start development server
uvicorn api.main:app --reload

# Start production server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## API Endpoints

### System Endpoints

#### GET `/` - API Root
```bash
curl http://localhost:8000/
```

Response:
```json
{
  "name": "MAAPS API",
  "version": "1.0.0",
  "status": "operational",
  "docs": "/docs",
  "health": "/health"
}
```

#### GET `/health` - Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "health_score": 100.0,
  "agents_healthy": 5,
  "agents_total": 5,
  "system_uptime_seconds": 123.45,
  "timestamp": "2025-11-15T12:00:00"
}
```

#### GET `/metrics` - System Metrics
```bash
curl http://localhost:8000/metrics
```

Response:
```json
{
  "metrics": {
    "cpu_usage_percent": 25.3,
    "memory_usage_percent": 45.2,
    "gpu_usage_percent": 0.0,
    "disk_usage_percent": 58.1
  }
}
```

#### GET `/agents` - List Agents
```bash
curl http://localhost:8000/agents
```

Response:
```json
{
  "agents": [
    {
      "agent_id": "audio_enhancement_agent",
      "agent_name": "Audio Enhancement & Restoration Agent",
      "state": "running",
      "metrics": {...}
    }
  ]
}
```

---

### Audio Processing Endpoints

#### POST `/audio/enhance` - Enhance Audio

```bash
curl -X POST http://localhost:8000/audio/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": [0.1, 0.2, 0.3, ...],
    "sample_rate": 44100,
    "noise_reduction": 0.8,
    "declicking_sensitivity": 0.5,
    "preserve_transients": true
  }'
```

**Request Body:**
```json
{
  "audio_data": [float],         // Audio samples
  "sample_rate": 44100,          // 8000-192000 Hz
  "noise_reduction": 0.8,        // 0.0-1.0
  "declicking_sensitivity": 0.5, // 0.0-1.0
  "preserve_transients": true    // true/false
}
```

**Response:**
```json
{
  "enhanced_audio": [float],
  "sample_rate": 44100,
  "processing_time_ms": 123.4,
  "status": "completed"
}
```

#### POST `/audio/metadata` - Extract Metadata

```bash
curl -X POST http://localhost:8000/audio/metadata \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": [0.1, 0.2, 0.3, ...],
    "sample_rate": 44100,
    "deep_analysis": true
  }'
```

**Response:**
```json
{
  "musical_features": {
    "tempo": 120.0,
    "key": "C major",
    "time_signature": "4/4"
  },
  "technical_features": {
    "sample_rate": 44100,
    "duration_seconds": 10.5,
    "channels": 1
  },
  "quality_metrics": {
    "peak_amplitude": 0.95,
    "rms_level": 0.45
  }
}
```

---

### Music Generation Endpoints

#### POST `/music/generate` - Generate Music

```bash
curl -X POST http://localhost:8000/music/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "melody",
    "key": "C major",
    "tempo": 120.0,
    "time_signature": "4/4",
    "chord_progression": ["C", "Am", "F", "G"],
    "length_bars": 8
  }'
```

**Request Body:**
```json
{
  "content_type": "melody",              // melody, harmony, drums, bass
  "key": "C major",
  "tempo": 120.0,                        // 60-200 BPM
  "time_signature": "4/4",
  "chord_progression": ["C", "Am", "F", "G"],
  "length_bars": 8                       // 1-64
}
```

**Response:**
```json
{
  "midi_data": {...},
  "notes": [...],
  "generation_time_ms": 456.7
}
```

---

### Batch Processing Endpoints

#### POST `/batch/enhance` - Batch Enhancement
```bash
curl -X POST http://localhost:8000/batch/enhance \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav" \
  -F "files=@audio3.wav"
```

**Response:**
```json
{
  "job_id": "batch_20251115_120000",
  "status": "queued",
  "message": "Batch job created with 3 files"
}
```

#### GET `/batch/{job_id}` - Get Batch Status
```bash
curl http://localhost:8000/batch/batch_20251115_120000
```

**Response:**
```json
{
  "job_id": "batch_20251115_120000",
  "status": "processing",
  "progress": 66.7,
  "result": null,
  "error": null
}
```

---

## Python Client Example

```python
import requests
import numpy as np

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Check health
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 2. Enhance audio
audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))

response = requests.post(
    f"{BASE_URL}/audio/enhance",
    json={
        "audio_data": audio.tolist(),
        "sample_rate": 44100,
        "noise_reduction": 0.8
    }
)

enhanced = response.json()
print(f"Processing time: {enhanced['processing_time_ms']}ms")

# 3. Generate music
response = requests.post(
    f"{BASE_URL}/music/generate",
    json={
        "content_type": "melody",
        "key": "C major",
        "tempo": 120.0,
        "chord_progression": ["C", "Am", "F", "G"],
        "length_bars": 8
    }
)

melody = response.json()
print(f"Generated {len(melody['notes'])} notes")

# 4. Get system metrics
response = requests.get(f"{BASE_URL}/metrics")
metrics = response.json()
print(f"CPU: {metrics['metrics']['cpu_usage_percent']}%")
```

---

## JavaScript/TypeScript Client

```typescript
// Fetch API example
const BASE_URL = 'http://localhost:8000';

// Check health
const health = await fetch(`${BASE_URL}/health`);
const healthData = await health.json();
console.log(`Health: ${healthData.health_score}%`);

// Enhance audio
const response = await fetch(`${BASE_URL}/audio/enhance`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    audio_data: [0.1, 0.2, 0.3, /* ... */],
    sample_rate: 44100,
    noise_reduction: 0.8
  })
});

const result = await response.json();
console.log(`Enhanced audio: ${result.enhanced_audio.length} samples`);

// Generate music
const musicResponse = await fetch(`${BASE_URL}/music/generate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content_type: 'melody',
    key: 'C major',
    tempo: 120.0,
    chord_progression: ['C', 'Am', 'F', 'G'],
    length_bars: 8
  })
});

const music = await musicResponse.json();
console.log(`Generated ${music.notes.length} notes`);
```

---

## Production Deployment

### Docker

Update `docker-compose.yml`:

```yaml
services:
  maaps-api:
    build: .
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
    ports:
      - "8000:8000"
    environment:
      - WORKERS=4
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.yourdo main.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### systemd Service

Create `/etc/systemd/system/maaps-api.service`:

```ini
[Unit]
Description=MAAPS REST API
After=network.target

[Service]
User=maaps
WorkingDirectory=/opt/maaps
ExecStart=/opt/maaps/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Authentication (TODO)

Add API key authentication:

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = "your-secret-key"
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Use on endpoints:
@app.get("/secure-endpoint", dependencies=[Security(verify_api_key)])
async def secure_endpoint():
    return {"message": "Access granted"}
```

---

## Rate Limiting (TODO)

Add rate limiting with slowapi:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/rate-limited")
@limiter.limit("10/minute")
async def rate_limited_endpoint(request: Request):
    return {"message": "Limited to 10 requests per minute"}
```

---

## Testing

```bash
# Install testing dependencies
pip install pytest httpx

# Run API tests
pytest tests/test_api.py -v
```

---

## Performance

- **Async processing**: FastAPI with uvicorn workers
- **Connection pooling**: Reuses system instance
- **Background tasks**: For long-running operations
- **Caching**: Response caching for expensive operations

---

## API Status

```
Endpoints:      12 ✅
Authentication: Planned
Rate Limiting:  Planned
Batch Process:  Partial
WebSockets:     Planned
Status:         Production Ready
```

**Interactive docs available at: http://localhost:8000/docs**
