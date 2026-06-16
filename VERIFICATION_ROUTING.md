# Canopy Eldertree Routing Verification

This document describes the routing configuration for Canopy on the Eldertree cluster and how to verify it works.

## Overview

Canopy is now configured with dual routing:
- **Internal**: `canopy.eldertree.local` (LAN access, self-signed cert)
- **Public**: `canopy.eldertree.xyz` (Cloudflare tunnel, Cloudflare origin cert)

## Changes Made

### 1. Canopy Repo (k8s manifests)

#### `k8s/ingress.yaml` (internal)
- **Changed**: `host: canopy.local` → `host: canopy.eldertree.local`
- **Added**: `external-dns.alpha.kubernetes.io/hostname: canopy.eldertree.local` annotation
- **TLS**: Uses `selfsigned-cluster-issuer` for internal cert

#### `k8s/ingress-public.yaml` (NEW - public)
- **Host**: `canopy.eldertree.xyz`
- **TLS**: Uses `canopy-cloudflare-origin-tls` secret
- **Annotation**: `external-dns.alpha.kubernetes.io/exclude: "true"` (Cloudflare handles DNS)
- **Entry points**: `websecure` only (HTTPS)

### 2. Pi-Fleet Registry (already configured)

The following files in `pi-fleet` already include `canopy.eldertree.local`:
- ✅ `docs/eldertree-local-services.yaml` (line 50-51)
- ✅ `docs/eldertree-local-hosts-block.txt` (line 11)
- ✅ `scripts/add-services-to-hosts.sh` (line 66, 92)
- ✅ `scripts/Caddyfile` (lines 181-189)

The HelmRelease in `pi-fleet/clusters/eldertree/canopy/helmrelease.yaml` already configures both domains with CORS.

### 3. Mac Hosts Setup

If you haven't already, add the Eldertree services to your Mac's `/etc/hosts`:

```bash
cd ~/WORKSPACE/raolivei/pi-fleet
sudo ./scripts/add-services-to-hosts.sh
```

Or manually add to `/etc/hosts`:
```
192.168.2.101  canopy.eldertree.local
```

### 4. Caddy (Optional - for local HTTPS proxy)

If using Caddy for local HTTPS without BIND9 DNS:

```bash
cd ~/WORKSPACE/raolivei/pi-fleet
sudo caddy run --config scripts/Caddyfile
```

Caddy entry for canopy already exists (lines 181-189).

## Verification Steps

### Phase 1: Pre-Deployment (Repo Files)

From `pi-fleet` repo:

```bash
cd ~/WORKSPACE/raolivei/pi-fleet
./scripts/check-local-routing-registry.sh
```

Expected output: `OK` for all sync targets

### Phase 2: Deploy

#### Option A: Direct kubectl apply (from canopy repo)

```bash
export KUBECONFIG=~/.kube/config-eldertree
cd ~/WORKSPACE/raolivei/canopy

kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/ingress-public.yaml
```

#### Option B: FluxCD GitOps (from pi-fleet)

Commit changes to both repos, then:

```bash
export KUBECONFIG=~/.kube/config-eldertree
cd ~/WORKSPACE/raolivei/pi-fleet

flux reconcile source git flux-system -n flux-system
flux reconcile kustomization flux-system -n flux-system --timeout=5m
```

Wait for reconciliation to complete.

### Phase 3: Post-Deployment Verification

From `pi-fleet` repo:

```bash
export KUBECONFIG=~/.kube/config-eldertree
cd ~/WORKSPACE/raolivei/pi-fleet

./scripts/verify-service-routing.sh --host canopy.eldertree.local
```

This script checks:
1. ✅ Ingress exists with correct host and backend service
2. ✅ Service has endpoints (pods are running)
3. ✅ TLS certificate is Ready
4. ✅ external-dns annotation present
5. ✅ LAN DNS (BIND9) resolves hostname
6. ✅ Traefik NodePort responds (cluster-level routing)
7. ✅ Mac can curl the service (end-to-end)
8. ✅ Registry files in sync

### Manual Verification

#### Internal Access (canopy.eldertree.local)

```bash
# Test DNS resolution
nslookup canopy.eldertree.local 192.168.2.201

# Test HTTPS (via Traefik NodePort)
curl -k https://192.168.2.101:32474 -H 'Host: canopy.eldertree.local'

# Test via hostname (requires /etc/hosts or Caddy)
curl -k https://canopy.eldertree.local
```

#### Public Access (canopy.eldertree.xyz)

```bash
# Test public endpoint (requires Cloudflare tunnel configured)
curl https://canopy.eldertree.xyz
```

### Kubernetes Checks

```bash
export KUBECONFIG=~/.kube/config-eldertree

# Check ingress
kubectl get ingress -n canopy

# Check endpoints
kubectl get endpoints -n canopy

# Check certificates
kubectl get certificate -n canopy

# Check pods
kubectl get pods -n canopy

# View ingress details
kubectl describe ingress canopy -n canopy
kubectl describe ingress canopy-public -n canopy
```

## Troubleshooting

### Ingress exists but no endpoints
**Issue**: Pods not running or wrong selector
**Fix**: Check pod status: `kubectl get pods -n canopy -o wide`

### DNS resolution fails
**Issue**: external-dns not syncing or BIND9 issue
**Fix**: 
- Check external-dns logs: `kubectl logs -n kube-system -l app.kubernetes.io/name=external-dns`
- Verify annotation: `kubectl get ingress canopy -n canopy -o yaml | grep external-dns`

### Certificate not Ready
**Issue**: cert-manager can't issue cert
**Fix**: Check cert-manager logs and certificate status:
```bash
kubectl describe certificate canopy-tls -n canopy
kubectl logs -n cert-manager -l app=cert-manager
```

### Mac curl fails but Traefik works
**Issue**: Mac DNS or /etc/hosts not configured
**Fix**: 
- Add to /etc/hosts: `192.168.2.101  canopy.eldertree.local`
- Or restart Caddy if using Caddyfile

### Public domain (eldertree.xyz) not reachable
**Issue**: Cloudflare tunnel not configured or wrong origin cert
**Fix**:
- Verify Cloudflare tunnel is running
- Check origin certificate secret exists: `kubectl get secret canopy-cloudflare-origin-tls -n canopy`

## References

- **Onboarding Guide**: `pi-fleet/docs/ONBOARDING_APP_ROUTING.md`
- **Eldertree Service Routing Playbook**: `ollie/docs/agent-playbooks/eldertree-service-routing.md`
- **Memory**: `ollie/memory/feedback_eldertree_service_routing_e2e.md`
- **Ingress Details**: `pi-fleet/docs/INGRESS.md`
- **Services Reference**: `pi-fleet/docs/SERVICES_REFERENCE.md`

## Summary

**Internal (LAN)**: 
- Host: `canopy.eldertree.local`
- Cert: Self-signed via cert-manager
- DNS: BIND9 LAN DNS (192.168.2.201) via external-dns
- Access: Mac /etc/hosts + optional Caddy proxy

**Public (Internet)**:
- Host: `canopy.eldertree.xyz`
- Cert: Cloudflare Origin Certificate
- DNS: Managed by Cloudflare (external-dns excluded)
- Access: Cloudflare tunnel → Traefik → Canopy pods

Both ingresses route traffic to the same backend services:
- `canopy-frontend:3000` for `/` (Next.js app)
- `canopy-api:8000` for `/api` (FastAPI backend)
