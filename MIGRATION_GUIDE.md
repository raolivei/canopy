# Migration Guide: ledger-light → canopy

**Migration Complete** ✅ - This guide documents the completed migration from `ledger-light` to `canopy`.

## Pre-Migration Checklist

- [x] Update all code references to Canopy
- [x] Update package.json and pyproject.toml
- [x] Update backend config
- [x] Update frontend meta tags
- [ ] Replace brand assets with Canopy logo (see Brand Assets section)
- [ ] Test locally to ensure everything works
- [ ] Commit all changes to current branch

## GitHub Repository Migration

### Option 1: Rename Existing Repository (Recommended)

GitHub preserves redirects from the old name, so links won't break.

```bash
# 1. Go to GitHub repository settings
# https://github.com/raolivei/canopy/settings (migration complete)

# 2. Scroll to "Repository name" section

# 3. Repository name is now "canopy" (migration complete)

# 4. Migration already completed

# 5. Update your local remote:
cd ~/WORKSPACE/raolivei/canopy
git remote set-url origin git@github.com:raolivei/canopy.git

# 6. Verify:
git remote -v

# 7. Local directory already renamed to canopy:
cd ~/WORKSPACE/raolivei/canopy
```

### Option 2: Create New Repository

If you want a clean slate:

```bash
# 1. Create new repo on GitHub: https://github.com/new
# Name: canopy
# Description: Self-hosted personal finance, investment, and budgeting dashboard

# 2. Update remote in your local repo:
cd ~/WORKSPACE/raolivei/canopy
git remote set-url origin git@github.com:raolivei/canopy.git

# 3. Push all branches:
git push -u origin main
git push -u origin --all

# 4. Push tags (if any):
git push -u origin --tags

# 5. Archive old repository (optional):
# Repository is now at https://github.com/raolivei/canopy/settings
# Scroll down to "Archive this repository"
```

## Post-Migration Steps

### 1. Update GitHub Settings

- **Description**: Self-hosted personal finance, investment, and budgeting dashboard
- **Website**: (if applicable)
- **Topics**: Add tags: `personal-finance`, `self-hosted`, `raspberry-pi`, `k3s`, `fastapi`, `nextjs`, `budgeting`, `investment-tracking`
- **Features**: Enable Issues, disable Wikis (if not used)

### 2. Update GitHub Actions Secrets

If using self-hosted runner, ensure these secrets are set:

```
K3S_CONFIG          # Kubeconfig for eldertree cluster
DOCKER_USERNAME     # For GHCR
DOCKER_PASSWORD     # GitHub token with packages:write
SSH_PRIVATE_KEY     # For Pi cluster access (if needed)
```

### 3. Update Branch Protection Rules

```bash
# Protect main branch
# Settings → Branches → Add rule
# Branch name pattern: main
# ✓ Require pull request reviews before merging
# ✓ Require status checks to pass (if CI is set up)
```

### 4. Create Release v1.0.0

```bash
# Tag the migration as v1.0.0
git tag -a v1.0.0 -m "Canopy v1.0.0 - Migration from LedgerLight"
git push origin v1.0.0

# Create GitHub release:
# Go to https://github.com/raolivei/canopy/releases/new
# Tag: v1.0.0
# Title: Canopy v1.0.0 🌳
# Description: See CHANGELOG.md
```

## Brand Assets Migration

The Canopy logo (image.png) needs to be converted to various formats:

### Required Assets

1. **Icon (SVG)** → `frontend/public/brand/canopy-icon.svg`
2. **PNG Icons**: 32, 64, 180, 192, 256, 512, 1024px
3. **Logo Dark** → `canopy-logo-dark.svg`
4. **Logo Light** → `canopy-logo-light.svg`
5. **Banners**: 1600×900 (dark/light)
6. **OG Images**: 1200×630 (dark/light)

### Asset Generation

```bash
# Using ImageMagick or similar tool:
cd ~/WORKSPACE/raolivei/canopy/frontend/public/brand

# Generate PNGs from SVG (once you have canopy-icon.svg):
convert canopy-icon.svg -resize 32x32 canopy-icon-32.png
convert canopy-icon.svg -resize 64x64 canopy-icon-64.png
convert canopy-icon.svg -resize 180x180 canopy-icon-180.png
convert canopy-icon.svg -resize 192x192 canopy-icon-192.png
convert canopy-icon.svg -resize 256x256 canopy-icon-256.png
convert canopy-icon.svg -resize 512x512 canopy-icon-512.png
convert canopy-icon.svg -resize 1024x1024 canopy-icon-1024.png
```

## Documentation Updates

### Files Already Updated:
- [x] README.md (project name, structure)
- [x] backend/pyproject.toml
- [x] frontend/package.json
- [x] backend/app/config.py
- [x] backend/app/server.py
- [x] All frontend page titles
- [x] frontend/public/brand/README.md

### Files To Update:
- [ ] ARCHITECTURE.md (references to project name)
- [ ] MASTER_PROMPT.md (full rewrite for Canopy vision)
- [ ] CHANGELOG.md (add v1.0.0 entry)
- [ ] CSV_IMPORT_GUIDE.md (references)
- [ ] IMPORT_FEATURE_SUMMARY.md (references)

## Testing After Migration

```bash
# 1. Clean install backend
cd ~/WORKSPACE/raolivei/canopy/backend
rm -rf venv __pycache__
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Start backend
PYTHONPATH=~/WORKSPACE/raolivei/canopy python3 -m uvicorn app.server:app --reload

# 3. Clean install frontend
cd ~/WORKSPACE/raolivei/canopy/frontend
rm -rf node_modules .next
npm install
npm run dev

# 4. Verify:
# - http://localhost:3000 (frontend loads)
# - http://localhost:8000/docs (API docs show "Canopy API")
# - Check browser console for errors
# - Verify favicon shows (once brand assets are updated)
```

## Pi Cluster Deployment

Once migration is complete and tested locally:

```bash
# 1. Update kubeconfig context
export KUBECONFIG=~/.kube/config-eldertree

# 2. Apply k8s manifests (after updating them)
kubectl apply -f ~/WORKSPACE/raolivei/canopy/k8s/

# 3. Verify deployment
kubectl get pods -n canopy
kubectl logs -f deployment/canopy-api -n canopy
```

## Rollback Plan

If something goes wrong:

```bash
# GitHub will keep the redirect, but you can rename back:
# Migration complete - repository is now "canopy"

# Revert local changes:
git reset --hard HEAD~1  # If you've committed
git checkout main        # If on a branch

# Revert remote:
git remote set-url origin git@github.com:raolivei/canopy.git
```

## Migration Completion Checklist

- [ ] GitHub repository renamed
- [ ] Local directory renamed
- [ ] Remote URL updated
- [ ] All code references updated
- [ ] Brand assets replaced
- [ ] Documentation updated
- [ ] Local testing passed
- [ ] Changes committed and pushed
- [ ] v1.0.0 release created
- [ ] GitHub settings updated
- [ ] Pi cluster deployment updated (optional)

---

**Migration Date**: 2025-11-13  
**Version**: 1.0.0  
**Status**: Ready for execution

