# MAAPS API Deployment Guide

## Quick Start

### 1. Install Dependencies

```bash
# Install API dependencies
pip install -r requirements-api.txt

# Or install all MAAPS requirements
pip install -r requirements.txt
pip install -r requirements-api.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
SECRET_KEY=your-secret-key-change-in-production-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Message Bus
MESSAGE_BUS_HOST=localhost
MESSAGE_BUS_PORT=5672

# Database (Optional)
DATABASE_URL=postgresql://user:password@localhost:5432/maaps

# Logging
LOG_LEVEL=INFO
```

### 3. Run Development Server

```bash
# Run with auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or use the Python script
python api/main.py
```

### 4. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Production Deployment

### Option 1: Systemd Service (Linux)

Create `/etc/systemd/system/maaps-api.service`:

```ini
[Unit]
Description=MAAPS API Service
After=network.target

[Service]
Type=simple
User=maaps
WorkingDirectory=/opt/maaps
Environment="PATH=/opt/maaps/venv/bin"
ExecStart=/opt/maaps/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable maaps-api
sudo systemctl start maaps-api
sudo systemctl status maaps-api
```

### Option 2: Docker

**Dockerfile**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-api.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**docker-compose.yml**:

```yaml
version: '3.8'

services:
  maaps-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://maaps:password@db:5432/maaps
    depends_on:
      - db
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=maaps
      - POSTGRES_USER=maaps
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - maaps-api
    restart: unless-stopped

volumes:
  postgres_data:
```

Run with Docker Compose:

```bash
docker-compose up -d
docker-compose logs -f maaps-api
```

### Option 3: Kubernetes

**deployment.yaml**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maaps-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: maaps-api
  template:
    metadata:
      labels:
        app: maaps-api
    spec:
      containers:
      - name: maaps-api
        image: maaps-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: maaps-secrets
              key: secret-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: maaps-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: maaps-api-service
spec:
  selector:
    app: maaps-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy to Kubernetes:

```bash
kubectl apply -f deployment.yaml
kubectl get pods
kubectl logs -f maaps-api-xxxxx
```

---

## Nginx Configuration

**nginx.conf** (reverse proxy with SSL):

```nginx
upstream maaps_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.maaps.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.maaps.example.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Logging
    access_log /var/log/nginx/maaps_api_access.log;
    error_log /var/log/nginx/maaps_api_error.log;

    # Proxy settings
    location / {
        proxy_pass http://maaps_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket endpoint
    location /ws {
        proxy_pass http://maaps_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
```

---

## Performance Tuning

### Uvicorn Workers

```bash
# Production: Use multiple workers (CPU count * 2 + 1)
uvicorn api.main:app --workers 9 --host 0.0.0.0 --port 8000

# With Gunicorn (alternative)
gunicorn api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Variables

```bash
# Worker configuration
WORKERS=4
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
TIMEOUT=60

# Connection limits
BACKLOG=2048
LIMIT_CONCURRENCY=1000
LIMIT_MAX_REQUESTS=10000
```

---

## Monitoring

### Health Check Endpoint

```bash
# Basic health check
curl http://localhost:8000/health

# System metrics
curl http://localhost:8000/api/v1/system/metrics

# Agent statistics
curl http://localhost:8000/api/v1/system/agents/live_effects_chain/stats
```

### Prometheus Metrics (Optional)

Add to `api/main.py`:

```python
from prometheus_client import make_asgi_app

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

Access metrics: `http://localhost:8000/metrics`

---

## Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure CORS for allowed origins only
- [ ] Implement rate limiting
- [ ] Use environment variables for secrets
- [ ] Enable request size limits
- [ ] Implement proper authentication
- [ ] Regular security updates
- [ ] Firewall configuration
- [ ] Database connection encryption

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### WebSocket Connection Issues

1. Check CORS configuration
2. Verify Nginx WebSocket headers
3. Check firewall rules
4. Test with `wscat`:

```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws
```

### High CPU Usage

1. Check number of workers
2. Monitor agent performance
3. Review message bus queue depth
4. Check for memory leaks

### Database Connection Errors

1. Verify DATABASE_URL
2. Check PostgreSQL status
3. Test connection manually:

```bash
psql $DATABASE_URL
```

---

## Testing

### Run API Tests

```bash
# Run all tests
pytest tests/test_api/

# Run with coverage
pytest --cov=api tests/test_api/

# Test specific endpoint
pytest tests/test_api/test_effects.py -v
```

### Manual API Testing

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/effects/chains \
  -H "Content-Type: application/json" \
  -d '{"chain_name": "Test", "effects": []}'

# Using httpie
http POST localhost:8000/api/v1/effects/chains \
  chain_name="Test" effects:=[]
```

---

## Backup & Recovery

### Database Backup

```bash
# Backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore
psql $DATABASE_URL < backup_20251117.sql
```

### Configuration Backup

```bash
# Backup configuration
tar -czf maaps_config_$(date +%Y%m%d).tar.gz \
  config.json .env api/
```

---

## Scaling

### Horizontal Scaling

1. Deploy multiple API instances
2. Use load balancer (Nginx, HAProxy, AWS ALB)
3. Shared database for session storage
4. Redis for caching

### Vertical Scaling

1. Increase worker count
2. Allocate more CPU/memory
3. Optimize database queries
4. Use connection pooling

---

## Support

- **Documentation**: http://localhost:8000/docs
- **GitHub**: https://github.com/yourusername/maaps
- **Issues**: https://github.com/yourusername/maaps/issues

---

**Last Updated**: 2025-11-17
**API Version**: 1.0.0
