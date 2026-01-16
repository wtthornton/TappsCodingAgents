# Git Workflows

## Overview

Git workflows define how teams collaborate on code, manage branches, and release software. Choosing the right workflow improves collaboration and reduces conflicts.

## Common Git Workflows

### Git Flow

**Branches:**
- **main**: Production-ready code
- **develop**: Integration branch
- **feature/**: Feature development
- **release/**: Release preparation
- **hotfix/**: Production fixes

**Flow:**
```
main → develop → feature/ → develop → release/ → main
                                        ↓
                                      hotfix/ → main
```

**Best For:**
- Release-based projects
- Multiple versions in production
- Strict release management

### GitHub Flow

**Branches:**
- **main**: Production-ready code
- **feature/**: Feature development

**Flow:**
```
main → feature/ → Pull Request → main
```

**Best For:**
- Continuous deployment
- Web applications
- Fast iteration cycles

### GitLab Flow

**Branches:**
- **main**: Production-ready code
- **pre-production**: Pre-production testing
- **production**: Production deployment
- **feature/**: Feature development

**Flow:**
```
main → pre-production → production
  ↑         ↑              ↑
feature/ → feature/ → feature/
```

**Best For:**
- Environment-based deployments
- Staging environments
- GitLab projects

## Branch Naming Conventions

### Standard Patterns
- `feature/description`: New features
- `bugfix/description`: Bug fixes
- `hotfix/description`: Urgent production fixes
- `release/version`: Release preparation
- `docs/description`: Documentation updates
- `refactor/description`: Code refactoring

### Examples
```
feature/user-authentication
bugfix/login-error-handling
hotfix/security-patch
release/v1.2.0
docs/api-documentation
refactor/database-access-layer
```

## Commit Message Standards

### Conventional Commits

Format: `type(scope): subject`

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/tooling changes

**Examples:**
```
feat(auth): add JWT token support
fix(api): handle null response in user endpoint
docs(readme): update installation instructions
refactor(db): extract query builder logic
test(auth): add integration tests for login
```

### Commit Message Best Practices

1. **Use Imperative Mood**: "Add feature" not "Added feature"
2. **Keep Under 50 Characters**: Subject line
3. **Explain Why**: Body explains motivation
4. **Reference Issues**: Link to tickets/issues
5. **One Logical Change**: One commit per logical change

## Pull Request Guidelines

### PR Requirements
- All tests passing
- Code review approval
- No merge conflicts
- Up to date with base branch
- Description with context

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests passing
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
```

## Best Practices

### Branch Management
- Keep branches short-lived
- Delete merged branches
- Rebase before merging
- Keep main branch clean

### Commit Strategy
- Commit often, push regularly
- Atomic commits
- Meaningful messages
- Don't commit secrets

### Collaboration
- Review before merging
- Use pull requests
- Discuss major changes
- Share knowledge

## Merge Strategies

### Merge Commit
- Preserves history
- Shows merge point
- Creates merge commits
- Good for feature branches

### Squash and Merge
- Clean linear history
- Single commit per PR
- Easier to rollback
- Good for feature branches

### Rebase and Merge
- Linear history
- No merge commits
- Cleaner log
- Use with caution on shared branches

## Tools

### CLI Tools
- **Git**: Version control
- **GitHub CLI**: GitHub integration
- **GitLab CLI**: GitLab integration

### GUI Tools
- **GitKraken**: Cross-platform GUI
- **SourceTree**: Free Git GUI
- **GitHub Desktop**: Simple Git client

### IDE Integration
- VS Code: Built-in Git support
- IntelliJ: Git integration
- Eclipse: EGit plugin
