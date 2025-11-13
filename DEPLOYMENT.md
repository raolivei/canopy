# Canopy Deployment Guide

Quick reference for deploying Canopy to your Pi cluster [[memory:10892785]].

## Prerequisites

- k3s cluster (eldertree + fleet-worker nodes)
- kubectl configured with ~/.kube/config-eldertree
- Self-hosted GitHub Actions runner (optional, for CI/CD)
- Docker images built and pushed to GHCR

## Quick Deploy

```bash
# Set kubeconfig
export KUBECONFIG=~/.kube/config-eldertree

# Create secrets (first time only)
cp k8s/secrets-template.yaml k8s/secrets.yaml
# Edit secrets.yaml with real values
kubectl apply -f k8s/secrets.yaml
rm k8s/secrets.yaml  # Don't commit!

# Deploy all components
kubectl apply -f k8s/deploy.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Verify deployment
kubectl get pods -n canopy
kubectl get svc -n canopy
kubectl logs -f deployment/canopy-api -n canopy
```

## Manual Build & Deploy

### Build Images Locally

```bash
# Build API image
cd backend
docker build -t ghcr.io/raolivei/canopy-api:latest .
docker push ghcr.io/raolivei/canopy-api:latest

# Build Frontend image
cd ../frontend
docker build -t ghcr.io/raolivei/canopy-frontend:latest .
docker push ghcr.io/raolivei/canopy-frontend:latest
```

### Deploy to Cluster

```bash
export KUBECONFIG=~/.kube/config-eldertree

# Apply manifests
kubectl apply -f k8s/

# Watch rollout
kubectl rollout status deployment/canopy-api -n canopy
kubectl rollout status deployment/canopy-frontend -n canopy
```

## CI/CD with GitHub Actions

### Setup Self-Hosted Runner

```bash
# On one of your Pi workers
cd ~/actions-runner
./config.sh --url https://github.com/raolivei/canopy --token YOUR_TOKEN
./run.sh

# Or run as service
sudo ./svc.sh install
sudo ./svc.sh start
```

### Required GitHub Secrets

Add these secrets in GitHub Settings → Secrets:

```
KUBECONFIG_ELDERTREE
```

Content: Your ~/.kube/config-eldertree file content

### Automatic Deployment

Push to `main` branch triggers:

1. Build Docker images
2. Push to GHCR
3. Deploy to Pi cluster (via self-hosted runner)
4. Restart deployments

## Accessing Canopy

### Local Access

```bash
# Port forward for testing
kubectl port-forward svc/canopy-frontend 3000:3000 -n canopy
kubectl port-forward svc/canopy-api 8000:8000 -n canopy

# Open in browser
open http://localhost:3000
```

### Ingress Access

Update `/etc/hosts` or DNS:

```
<INGRESS_IP> canopy.local
```

Access: http://canopy.local

## Scaling

```bash
# Scale API replicas
kubectl scale deployment/canopy-api --replicas=3 -n canopy

# Scale frontend replicas
kubectl scale deployment/canopy-frontend --replicas=2 -n canopy
```

## Monitoring

```bash
# Get pod status
kubectl get pods -n canopy

# View logs
kubectl logs -f deployment/canopy-api -n canopy
kubectl logs -f deployment/canopy-frontend -n canopy
kubectl logs -f deployment/canopy-redis -n canopy

# Describe pod for issues
kubectl describe pod <pod-name> -n canopy

# Events
kubectl get events -n canopy --sort-by='.lastTimestamp'
```

## Database Management

```bash
# Connect to PostgreSQL
kubectl exec -it statefulset/canopy-postgres -n canopy -- psql -U canopy

# Backup database
kubectl exec statefulset/canopy-postgres -n canopy -- \
  pg_dump -U canopy canopy > backup-$(date +%Y%m%d).sql

# Restore database
kubectl exec -i statefulset/canopy-postgres -n canopy -- \
  psql -U canopy canopy < backup-20251113.sql
```

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod <pod-name> -n canopy
kubectl logs <pod-name> -n canopy
```

Common issues:

- ImagePullBackOff: Check GHCR credentials
- CrashLoopBackOff: Check logs for application errors
- Pending: Check resource constraints

### Database connection issues

```bash
# Check postgres is running
kubectl get pods -n canopy | grep postgres

# Test connection from API pod
kubectl exec -it deployment/canopy-api -n canopy -- \
  python -c "from backend.app.config import get_settings; print(get_settings().database_url)"
```

### Ingress not working

```bash
# Check ingress status
kubectl describe ingress canopy -n canopy

# Check nginx ingress controller
kubectl get pods -n ingress-nginx
```

## Updating Deployment

```bash
# Update image
kubectl set image deployment/canopy-api api=ghcr.io/raolivei/canopy-api:v1.1.0 -n canopy

# Or edit deployment
kubectl edit deployment canopy-api -n canopy

# Rollback if needed
kubectl rollout undo deployment/canopy-api -n canopy
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace canopy

# Or delete specific components
kubectl delete -f k8s/deploy.yaml
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/ingress.yaml
```

## Resource Requirements

**Minimum (per replica)**:

- API: 256Mi RAM, 250m CPU
- Frontend: 128Mi RAM, 100m CPU
- Redis: 64Mi RAM, 50m CPU
- Postgres: 256Mi RAM, 250m CPU

**Total for default setup (2 API, 2 Frontend)**:

- ~1.2Gi RAM
- ~1 CPU

Fits comfortably on Pi 5 8GB (eldertree) + workers.

## Backup Strategy

1. **Database**: Daily pg_dump via CronJob
2. **Config**: Version-controlled in Git
3. **Volumes**: Snapshot PVCs if using Longhorn

## Maintenance

- **Updates**: Run CI/CD on main branch
- **Database migrations**: Apply before deployment
- **Secrets rotation**: Update secrets.yaml and reapply
- **Certificate renewal**: Handled by cert-manager (if configured)

---

**Deployed to**: eldertree (control) + fleet-worker-01, fleet-worker-02  
**Namespace**: canopy  
**Ingress**: canopy.local
