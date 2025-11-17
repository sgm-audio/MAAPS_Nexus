# MAAPS Kubernetes Deployment

Deploy MAAPS to Kubernetes cluster with high availability and auto-scaling.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Helm 3.x (optional)
- Docker registry access

## Quick Deploy

```bash
# Create namespace
kubectl create namespace maaps

# Apply configurations
kubectl apply -f k8s/configmap.yaml -n maaps
kubectl apply -f k8s/pvc.yaml -n maaps
kubectl apply -f k8s/deployment.yaml -n maaps
kubectl apply -f k8s/service.yaml -n maaps
kubectl apply -f k8s/hpa.yaml -n maaps
kubectl apply -f k8s/ingress.yaml -n maaps

# Verify deployment
kubectl get all -n maaps
```

## Detailed Steps

### 1. Create Namespace

```bash
kubectl create namespace maaps
kubectl label namespace maaps env=production
```

### 2. Create Secrets

```bash
# Create Docker registry secret
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_TOKEN \
  -n maaps

# Create application secrets
kubectl create secret generic maaps-secrets \
  --from-literal=API_KEY=your-secret-api-key \
  --from-literal=DB_PASSWORD=your-db-password \
  -n maaps
```

### 3. Apply Configuration

```bash
# ConfigMaps (environment and app config)
kubectl apply -f k8s/configmap.yaml -n maaps

# Persistent Volume Claims
kubectl apply -f k8s/pvc.yaml -n maaps

# Deployment
kubectl apply -f k8s/deployment.yaml -n maaps

# Service
kubectl apply -f k8s/service.yaml -n maaps

# Horizontal Pod Autoscaler
kubectl apply -f k8s/hpa.yaml -n maaps

# Ingress (if using)
kubectl apply -f k8s/ingress.yaml -n maaps
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n maaps

# Check services
kubectl get svc -n maaps

# Check HPA
kubectl get hpa -n maaps

# Check logs
kubectl logs -f deployment/maaps -n maaps
```

## Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment maaps --replicas=5 -n maaps
```

### Auto-Scaling

HPA is configured to:
- Min replicas: 2
- Max replicas: 10
- Target CPU: 70%
- Target Memory: 80%

Monitor scaling:
```bash
kubectl get hpa maaps-hpa -n maaps --watch
```

## Updating

### Rolling Update

```bash
# Update image
kubectl set image deployment/maaps maaps=ghcr.io/your-org/maaps:v1.1.0 -n maaps

# Check rollout status
kubectl rollout status deployment/maaps -n maaps

# Rollback if needed
kubectl rollout undo deployment/maaps -n maaps
```

## Monitoring

### Health Check

```bash
# Get service endpoint
kubectl get svc maaps-service -n maaps

# Check health (from within cluster)
kubectl run curl --image=curlimages/curl -it --rm --restart=Never -- \
  curl http://maaps-internal:8000/health
```

### Logs

```bash
# View logs
kubectl logs -f deployment/maaps -n maaps

# View logs from specific pod
kubectl logs -f POD_NAME -n maaps

# View logs from all pods
kubectl logs -f -l app=maaps -n maaps
```

### Metrics

```bash
# Pod metrics (requires metrics-server)
kubectl top pods -n maaps

# Node metrics
kubectl top nodes
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod
kubectl describe pod POD_NAME -n maaps

# Check events
kubectl get events -n maaps --sort-by='.lastTimestamp'

# Check logs
kubectl logs POD_NAME -n maaps
```

### Service Not Accessible

```bash
# Check service
kubectl describe svc maaps-service -n maaps

# Check endpoints
kubectl get endpoints maaps-service -n maaps

# Test from within cluster
kubectl run test-pod --image=curlimages/curl -it --rm --restart=Never -- \
  curl http://maaps-internal:8000/health
```

### Storage Issues

```bash
# Check PVCs
kubectl get pvc -n maaps

# Describe PVC
kubectl describe pvc maaps-data-pvc -n maaps
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace maaps

# Or delete individually
kubectl delete -f k8s/ -n maaps
```

## Production Checklist

- [ ] Image pushed to registry
- [ ] Secrets created
- [ ] ConfigMaps configured
- [ ] PVCs provisioned
- [ ] Deployment applied
- [ ] Service accessible
- [ ] HPA configured
- [ ] Ingress configured (if using)
- [ ] TLS certificates configured
- [ ] Monitoring enabled
- [ ] Backups configured
- [ ] Resource limits set
- [ ] Health checks working
- [ ] Logs accessible

## Architecture

```
Internet
    |
[Ingress/LoadBalancer]
    |
[Service: maaps-service]
    |
[Deployment: maaps (3 replicas)]
    |
[Pods with health checks]
    |
[PVC: data, logs]
```

## Auto-Scaling Behavior

- **Scale Up**: Fast (30s window, up to 100% or +2 pods)
- **Scale Down**: Conservative (5min window, max 50% reduction)
- **Triggers**: CPU >70% or Memory >80%

## Resource Allocation

Per Pod:
- **Requests**: 2 CPU, 4Gi RAM
- **Limits**: 4 CPU, 8Gi RAM

Total (3 replicas):
- **Min**: 6 CPU, 12Gi RAM
- **Max**: 12 CPU, 24Gi RAM

## Cost Optimization

1. **Right-size resources**: Adjust based on actual usage
2. **Use spot instances**: For non-critical workloads
3. **Enable cluster autoscaler**: Scale nodes automatically
4. **Use storage classes**: Choose appropriate storage tier
5. **Monitor costs**: Use cloud provider cost tools

## Support

For issues, check:
1. Pod logs: `kubectl logs -f deployment/maaps -n maaps`
2. Events: `kubectl get events -n maaps`
3. Health endpoint: `/health`
4. Metrics: `kubectl top pods -n maaps`
