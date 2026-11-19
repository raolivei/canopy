# Canopy Deployment Guide

Quick reference for deploying Canopy to your Pi cluster.

## Prerequisites

- k3s cluster (eldertree + fleet-worker nodes)
- kubectl configured with ~/.kube/config-eldertree
- Self-hosted GitHub Actions runner (optional, for CI/CD)
- Docker images built and pushed to GHCR

## How production deploys (GitOps)

Production runs on Eldertree from `pi-fleet/clusters/eldertree/canopy/`, applied
by Flux. Do not `kubectl apply` the files in `k8s/`; they are a local reference.

1. A merge to `main` builds `ghcr.io/raolivei/canopy-api` and `canopy-frontend`
   (`latest` plus the `VERSION` tag).
2. The `canopy` HelmRelease pulls `latest` (`pullPolicy: Always`) on rollout.
   Drift detection is on, so a manual `kubectl scale` is reverted to Git.
3. Each API pod runs a `migrate` init container (`alembic upgrade head`) before
   it serves. Alembic takes a PostgreSQL advisory lock (`backend/alembic/env.py`),
   so pods starting together migrate one at a time; later ones find the schema
   at head. A failed migration keeps the pod in `Init` with the error in
   `kubectl logs <pod> -c migrate -n canopy`; the old pods keep serving.
4. CI proves migrations on a real PostgreSQL database
   (`backend/scripts/check_postgres_migrations.sh`): two concurrent upgrades of
   an empty database, single head, no-op repeat and `alembic check`.

Backups before irreversible migrations and restore drills are tracked in #136;
upgrade tests from older production schemas remain under #48.

### Secrets (Vault + External Secrets)

All secrets come from Vault through External Secrets; none live in Git.

| Kubernetes secret | Keys | Vault path (KV v2 `secret/`) | Defined in |
|---|---|---|---|
| `canopy-secrets` | `postgres-password`, `database-url`, `secret-key`, optional `questrade-refresh-token`, `wise-api-token` | `canopy/postgres`, `canopy/database`, `canopy/app`, `canopy/questrade`, `canopy/wise` | `pi-fleet/clusters/eldertree/secrets-management/external-secrets/externalsecrets/canopy-secrets.yaml` |
| `canopy-basic-auth` | `users` (htpasswd) | `canopy/basic-auth` | `pi-fleet/clusters/eldertree/canopy/basic-auth-external.yaml` |
| `ghcr-secret` | registry token | `canopy/ghcr-token` | `pi-fleet/clusters/eldertree/canopy/ghcr-secret-external.yaml` |

Rotate a secret by writing the new value to Vault. External Secrets refreshes
every 24 hours; to apply sooner, annotate the ExternalSecret
(`kubectl annotate externalsecret canopy-secrets -n canopy force-sync=$(date +%s) --overwrite`)
and restart the pods that read it. Redis runs inside the namespace without a
password. See `pi-fleet/docs/VAULT.md`.

### Verify

```bash
export KUBECONFIG=~/.kube/config-eldertree
kubectl get externalsecret,pods -n canopy
kubectl logs deploy/canopy-api -c migrate -n canopy
curl -fsS https://canopy.eldertree.local/v1/health
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

### GitHub Container Registry (when `ghcr.io/…/canopy-api` looks “missing”)

1. **Use a full image reference** — Docker needs a tag or digest. `ghcr.io/raolivei/canopy-api` alone is not a valid pull spec. Examples: `ghcr.io/raolivei/canopy-api:v0.10.3`, `ghcr.io/raolivei/canopy-api:latest` (only if CI published `latest` on `main`), or `ghcr.io/raolivei/canopy-api@sha256:…`.

2. **Packages appear after the first green push** — The GHCR package is created when [Build and Push Docker Images](https://github.com/raolivei/canopy/actions/workflows/build-and-push.yml) completes successfully and pushes. In the repo: **Packages** (right sidebar) or `https://github.com/raolivei/canopy/pkgs/container/canopy-api` (name may match the image component).

3. **Private repositories → private packages** — Anonymous `docker pull` fails. Log in before pull/push:
   ```bash
   echo YOUR_GH_PAT | docker login ghcr.io -u raolivei --password-stdin
   ```
   Use a classic PAT with **read:packages** (pull) or **write:packages** (push). For Kubernetes, create an `imagePullSecret` with the same credentials.

4. **Tag must exist** — Flux / Helm in `pi-fleet` may pin `v0.6.0`. If that tag was never built for `linux/arm64` or was garbage-collected, bump the chart to a tag that Actions actually published (check the workflow run “Docker Build Summary” or GHCR tags).

5. **Workflow did not run** — Pushes only run when changed paths match `.github/workflows/build-and-push.yml`. Opening a PR that only touches docs will not rebuild images.

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
