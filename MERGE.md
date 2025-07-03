# Merge Instructions for RAG Chat Application

## Overview
This document provides instructions for merging feature branches into the main branch for the RAG Chat Application project.

## Branch Strategy
- **Main Branch**: `main` - Production-ready code
- **Feature Branches**: `feature/*` - Individual features or phases
- **Hotfix Branches**: `hotfix/*` - Critical bug fixes

## Pre-Merge Checklist

### Code Quality
- [ ] Code follows project conventions and style guide
- [ ] All linting passes (`uv run ruff check` for Python, `npm run lint` for TypeScript)
- [ ] Type checking passes (`uv run mypy` for Python, `npm run type-check` for TypeScript)
- [ ] No hardcoded secrets or API keys
- [ ] No console.log or print statements (except for debugging)

### Testing
- [ ] All existing tests pass
- [ ] New features have corresponding tests
- [ ] Manual testing completed
- [ ] Edge cases tested

### Documentation
- [ ] Code is properly commented
- [ ] API endpoints documented
- [ ] README updated if needed
- [ ] CHANGELOG updated

### Deployment
- [ ] Environment variables documented in `.env.example`
- [ ] Vercel deployment successful on preview branch
- [ ] No breaking changes to API contracts

## Merge Process

### 1. Update Your Branch
```bash
git checkout feature/your-branch
git fetch origin
git rebase origin/main
```

### 2. Run Tests Locally
```bash
# Backend tests
cd backend
uv run pytest

# Frontend tests
cd frontend
npm test
```

### 3. Create Pull Request
1. Push your branch: `git push origin feature/your-branch`
2. Go to GitHub and create a new Pull Request
3. Use the PR template below

### 4. PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- List key changes
- Include screenshots for UI changes

## Testing
- Describe testing performed
- Include test commands

## Deployment Notes
- Any special deployment considerations
- Environment variable changes
- Migration requirements

## Checklist
- [ ] My code follows the project style guidelines
- [ ] I have performed a self-review
- [ ] I have added tests that prove my fix/feature works
- [ ] All new and existing tests pass locally
- [ ] I have updated the documentation
```

### 5. Review Process
1. Request review from at least one team member
2. Address all review comments
3. Ensure all CI checks pass
4. Get approval before merging

### 6. Merge Strategy
- Use **Squash and Merge** for feature branches
- Keep commit message descriptive
- Delete branch after merge

## Post-Merge Actions

1. **Verify Deployment**
   - Check Vercel deployment status
   - Test production endpoints
   - Monitor error logs

2. **Update Documentation**
   - Update CHANGELOG.md
   - Close related issues
   - Update project board

3. **Communication**
   - Notify team of significant changes
   - Update deployment notes

## Rollback Procedure

If issues are discovered after merge:

1. **Immediate Rollback**
   ```bash
   git revert <merge-commit-hash>
   git push origin main
   ```

2. **Vercel Rollback**
   - Go to Vercel dashboard
   - Select previous deployment
   - Promote to production

3. **Investigation**
   - Create hotfix branch
   - Fix issues
   - Follow expedited merge process

## Special Considerations

### Database Migrations
- Always test migrations on staging first
- Include rollback scripts
- Document schema changes

### API Changes
- Version APIs appropriately
- Maintain backward compatibility
- Document breaking changes

### Security Updates
- Review security implications
- Update dependencies carefully
- Test authentication flows

## Contact
For questions about the merge process, contact the project maintainers.