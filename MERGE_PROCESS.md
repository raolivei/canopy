# Merge Process Documentation for LedgerLight PRs

This document describes the merge process and conflict resolution for Pull Requests in the LedgerLight project.

## Overview

The LedgerLight project uses a branching strategy where:
- `main` - Production-ready code
- `dev` - Development branch where feature branches are merged
- Feature branches - Created from `dev` for specific features

## PR Conflict Resolution

### PR #6: feat-infra-scaffold

**Status:** ✅ Resolved

**Conflict Details:**
- **File:** `backend/app/server.py`
- **Issue:** The `feat-infra-scaffold` branch uses `backend.api.v1.routes` router, while `dev` branch includes transaction and currency routers in `backend.api.transactions` and `backend.api.currency`.

**Resolution:**
1. Updated `server.py` to include both routing structures:
   - Kept the existing `v1_router` from `backend.api.v1.routes` (health, summary endpoints)
   - Added imports for `transactions` and `currency` routers
   - Used try/except to handle cases where routers may not exist
   - Added CORS middleware configuration

2. Resolved CHANGELOG.md conflict by keeping the dev version which includes all new features.

**Final server.py structure:**
```python
from backend.api.v1.routes import router as v1_router
from backend.api import transactions, currency

app.include_router(v1_router)  # Health, summary endpoints
app.include_router(transactions.router)  # Transaction CRUD
app.include_router(currency.router)  # Currency conversion
```

### PR #7: feature/backend-api-setup

**Status:** ✅ Resolved and Mergeable

**Conflict Details:**
- This PR was already compatible with `dev` branch
- No conflicts after merging `dev` into the feature branch

## Merge Process Steps

### For Feature Branches

1. **Update feature branch with latest dev:**
   ```bash
   git checkout feature/your-branch
   git fetch origin
   git merge origin/dev
   ```

2. **Resolve any conflicts:**
   - Identify conflicting files: `git status`
   - Edit conflicted files to resolve conflicts
   - Stage resolved files: `git add <file>`
   - Complete merge: `git commit`

3. **Push resolved branch:**
   ```bash
   git push origin feature/your-branch
   ```

4. **Verify PR status:**
   ```bash
   gh pr view <PR_NUMBER> --json mergeable,mergeStateStatus
   ```

### For Merging PRs into Dev

1. **Ensure PR is mergeable:**
   ```bash
   gh pr view <PR_NUMBER> --json mergeable,mergeStateStatus
   ```

2. **Review PR changes:**
   ```bash
   gh pr diff <PR_NUMBER>
   ```

3. **Merge PR:**
   ```bash
   gh pr merge <PR_NUMBER> --merge --delete-branch
   ```

   Or use GitHub web interface:
   - Go to PR page
   - Click "Merge pull request"
   - Confirm merge

## Testing After Merge

After merging a PR, always run the test script:

```bash
./test_app.sh
```

This script will:
- Check if services are running
- Test all API endpoints
- Test frontend pages
- Verify integration between frontend and backend

## Common Conflict Scenarios

### 1. Server Structure Conflicts

**Symptom:** Import errors or missing routers after merge

**Solution:**
- Check which routers exist in both branches
- Update `server.py` to include all routers
- Ensure router imports are correct

### 2. CHANGELOG Conflicts

**Symptom:** Merge conflict in CHANGELOG.md

**Solution:**
- Keep the version with most recent entries
- Ensure all features are documented
- Maintain chronological order

### 3. Dependency Conflicts

**Symptom:** requirements.txt or package.json conflicts

**Solution:**
- Merge dependencies, removing duplicates
- Ensure version compatibility
- Test after merge

## Best Practices

1. **Regular Updates:** Keep feature branches updated with `dev`:
   ```bash
   git checkout feature/your-branch
   git merge dev
   ```

2. **Test Before PR:** Always test locally before creating PR:
   ```bash
   # Start services
   # Run test script
   ./test_app.sh
   ```

3. **Small PRs:** Keep PRs focused on single features to reduce conflicts

4. **Clear Commit Messages:** Use conventional commit format:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `chore:` for maintenance

5. **Review Before Merge:** Always review PR changes before merging

## Troubleshooting

### PR Shows as Conflicting After Push

1. **Refresh GitHub Status:**
   ```bash
   gh pr view <PR_NUMBER> --json mergeable,mergeStateStatus
   ```
   Wait a few seconds for GitHub to update

2. **Check Branch Status:**
   ```bash
   git fetch origin
   git log origin/dev..origin/feature/your-branch
   ```

3. **Re-merge if needed:**
   ```bash
   git checkout feature/your-branch
   git merge origin/dev
   git push origin feature/your-branch
   ```

### Merge Fails with "Already Up to Date"

This means the branch already contains all changes from dev. No action needed.

### Import Errors After Merge

1. Check if all files exist
2. Verify import paths
3. Check PYTHONPATH configuration
4. Ensure dependencies are installed

## Post-Merge Checklist

After merging a PR:

- [ ] Verify tests pass: `./test_app.sh`
- [ ] Check application starts correctly
- [ ] Verify all endpoints work
- [ ] Check frontend pages load
- [ ] Update CHANGELOG if needed
- [ ] Tag release if appropriate

## Contact

For merge issues or questions, refer to:
- Main README.md for project overview
- MASTER_PROMPT.md for detailed architecture
- GitHub Issues for bug reports

