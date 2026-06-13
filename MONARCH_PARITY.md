# Monarch Money Parity - Parallel Development Environment

## Overview

This document describes the parallel development environment for achieving Monarch Money feature parity in Canopy. The goal is to train Canopy to match Monarch's data quality, personal finance management features, and AI assistant capabilities without impacting the production instance.

## Architecture

### Two Environments

| Environment | Host | Namespace | Purpose |
|-------------|------|-----------|---------|
| **Production** | `canopy.eldertree.local` | `canopy` | Stable production instance |
| **Monarch Dev** | `monarch.eldertree.local` | `canopy-monarch` | Aggressive Monarch parity development |

### Why Parallel Deployment?

1. **Breaking Changes**: Monarch parity work involves significant database schema changes (budgets, cashflow, recurring transactions, categories, rules)
2. **Data Experimentation**: Need to test Monarch API integration and data sync without polluting production data
3. **Feature Isolation**: Can iterate on new features (budgets, cashflow, recurring transactions) independently
4. **Migration Testing**: Validate migration path before touching production
5. **MCP Oracle**: Use Monarch MCP server to query live Monarch data while developing Canopy equivalents

### Key Differences

- **Fresh Database**: `canopy_monarch` database (separate from production `canopy`)
- **Separate Redis**: Independent cache/session store
- **Monarch API Integration**: Environment configured for Monarch API token
- **Single Replica**: Lower resource footprint for dev environment
- **Image Tags**: Uses `monarch-dev` tags (vs `v1.0.0` for production)

## Usage

### Local Development

Development workflow remains the same - use Docker Compose locally:

```bash
# From canopy/ directory
source ../workspace-config/ports/.env.ports
docker-compose up

# Frontend: http://localhost:3001
# API: http://localhost:8001
```

### Deploy to Monarch Dev Environment

```bash
# 1. Build and push monarch-dev images
docker build -t ghcr.io/raolivei/canopy-api:monarch-dev ./backend
docker push ghcr.io/raolivei/canopy-api:monarch-dev

docker build -t ghcr.io/raolivei/canopy-frontend:monarch-dev ./frontend
docker push ghcr.io/raolivei/canopy-frontend:monarch-dev

# 2. Create secrets (first time only)
cd k8s/monarch-parity
cp secrets-template.yaml secrets.yaml
# Edit secrets.yaml with actual values
kubectl apply -f secrets.yaml
rm secrets.yaml  # Never commit secrets!

# 3. Deploy
kubectl apply -f k8s/monarch-parity/

# 4. Verify
kubectl get pods -n canopy-monarch
kubectl logs -n canopy-monarch -l component=api
```

### Access Environments

- **Production**: https://canopy.eldertree.local
- **Monarch Dev**: https://monarch.eldertree.local

### Switching Between Versions

Both environments run simultaneously. Use the appropriate URL to access each version.

## Development Workflow

### Feature Development

1. **Create Feature Branch**: All Monarch parity work happens on `feat/monarch-parity` branch
2. **Develop Locally**: Use Docker Compose for rapid iteration
3. **Deploy to Monarch Dev**: Push `monarch-dev` images and apply k8s manifests
4. **Test with Live Monarch**: Use Monarch MCP server (`uvx monarch-mcp`) to compare live Monarch data
5. **Iterate**: Repeat until feature matches Monarch quality
6. **Document Changes**: Update CHANGELOG.md for all changes

### Testing Strategy

1. **Unit Tests**: Run locally before commit (`pytest`, `npm test`)
2. **Integration Tests**: Test against monarch.eldertree.local
3. **Monarch Comparison**: Use MCP to verify data parity with live Monarch
4. **Migration Testing**: Test production migration path

### Merge Strategy

Features merge back to `main` when:

1. **Feature Complete**: Matches or exceeds Monarch capability
2. **Tests Pass**: 100% test coverage for new code
3. **Migration Safe**: Migration path validated and documented
4. **Production Ready**: No breaking changes or documented upgrade path
5. **Documentation Updated**: CHANGELOG.md, API docs, UI docs updated

## Deployment Considerations

### Resource Footprint

Monarch dev environment uses minimal resources:
- API: 256Mi RAM, 250m CPU (vs 512Mi/500m for production)
- Frontend: 128Mi RAM, 100m CPU
- Redis: 64Mi RAM, 50m CPU
- PostgreSQL: 256Mi RAM, 250m CPU

Total: ~700Mi RAM, ~650m CPU (fits comfortably on Raspberry Pi 5 8GB)

### Data Isolation

- **Separate Database**: `canopy_monarch` database (no shared tables)
- **Separate Secrets**: `canopy-monarch-secrets` (independent credentials)
- **Separate Redis**: No shared cache keys

### Ingress Configuration

Uses Traefik with separate host:
- `monarch.eldertree.local` → `canopy-monarch` namespace
- Self-signed TLS certificate via cert-manager
- Same middleware stack as production

## Monarch Parity Roadmap

See [GitHub Issues](https://github.com/raolivei/canopy/issues) for full roadmap.

### Phase 1: Foundation (P0)
- Database migrations automation
- Vault secrets integration
- Fresh monarch.eldertree.local deployment

### Phase 2: Core Features (P1)
- Monarch API integration
- Budget models and service
- Cashflow analysis
- Recurring transactions
- Category taxonomy alignment
- Transaction rules engine

### Phase 3: Assistant (P2)
- AI assistant tool enhancements (budgets, cashflow, recurring)
- Golden question templates
- Eldertree hosting strategy

### Phase 4: Operations (P3)
- Metrics and dashboards
- MCP integration playbook
- Production cutover runbook

## Monarch MCP Integration

Use Monarch MCP server to query live Monarch data during development:

```bash
# Start Monarch MCP server
uvx monarch-mcp

# In Claude (with MCP configured)
"What are my current budgets in Monarch?"
"Show me recurring transactions"
"Compare my Monarch categories to Canopy"
```

This allows real-time comparison between Canopy implementation and Monarch ground truth.

## Troubleshooting

### Pods Not Starting

```bash
kubectl get pods -n canopy-monarch
kubectl describe pod -n canopy-monarch <pod-name>
kubectl logs -n canopy-monarch <pod-name>
```

### Database Connection Issues

```bash
# Check PostgreSQL pod
kubectl logs -n canopy-monarch canopy-monarch-postgres-0

# Check database connectivity
kubectl exec -n canopy-monarch deployment/canopy-monarch-api -- \
  python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); engine.connect()"
```

### Ingress Not Working

```bash
# Check ingress
kubectl get ingress -n canopy-monarch
kubectl describe ingress -n canopy-monarch canopy-monarch

# Check Traefik logs
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik
```

### Image Pull Failures

```bash
# Verify image exists
docker pull ghcr.io/raolivei/canopy-api:monarch-dev

# Check image pull secrets (if using private registry)
kubectl get secrets -n canopy-monarch
```

## References

- [Canopy CLAUDE.md](./CLAUDE.md) - Main development guide
- [Workspace Conventions](../workspace-config/docs/PROJECT_CONVENTIONS.md) - Shared conventions
- [Eldertree Service Routing](../ollie/docs/agent-playbooks/eldertree-service-routing.md) - Ingress setup
- [Monarch MCP + Claude Playbook](../ollie/docs/agent-playbooks/monarch-mcp-claude.md) - MCP integration guide

---

**Last Updated**: 2026-06-12  
**Branch**: `feat/monarch-parity`  
**Status**: Initial setup complete, ready for development
