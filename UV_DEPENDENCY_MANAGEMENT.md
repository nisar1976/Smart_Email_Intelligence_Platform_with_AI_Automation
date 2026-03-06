# Dependency Management with `uv`

**IMPORTANT: Always use `uv` for ALL dependency management. Never use `pip` directly.**

---

## Installation & Setup

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

---

## Core uv Commands

### Initial Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Verify venv is active (should see (venv) in prompt)
which python  # macOS/Linux
where python  # Windows
```

### Installing Dependencies

```bash
# Install a single package
uv pip install openai

# Install multiple packages
uv pip install openai pydantic python-dotenv pyyaml requests fastapi uvicorn

# Install with version pinning
uv pip install "openai==1.3.0" "pydantic>=2.0,<3.0"

# Install from requirements file
uv pip install -r requirements.txt

# Install optional dependencies
uv pip install hubspot-api-client  # For HubSpot integration
uv pip install pytest pytest-cov   # For testing
```

### Listing & Inspecting

```bash
# List all installed packages
uv pip list

# Show specific package info
uv pip show openai

# Check for outdated packages
uv pip list --outdated

# List packages in requirements format
uv pip freeze
```

### Updating Dependencies

```bash
# Update a specific package
uv pip install --upgrade openai

# Update all packages
uv pip install --upgrade -r requirements.txt

# Update all installed packages (dangerous - use with caution)
uv pip install --upgrade $(uv pip list --format=flat | awk '{print $1}')
```

### Removing Dependencies

```bash
# Remove a package
uv pip uninstall openai

# Remove multiple packages
uv pip uninstall openai pydantic

# Remove all packages (careful!)
uv pip uninstall -r requirements.txt
```

### Creating Requirements Files

```bash
# Export current environment to requirements.txt
uv pip freeze > requirements.txt

# Export in more readable format
uv pip list --format=markdown > requirements.md

# Export only project dependencies (no dev/test packages)
uv pip freeze | grep -E "openai|pydantic|python-dotenv|pyyaml|requests|fastapi|uvicorn" > requirements-prod.txt
```

---

## Project Dependencies Structure

### requirements.txt
```
# Core dependencies (ALWAYS use uv pip install -r requirements.txt)
openai>=1.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0.0
requests>=2.31.0
fastapi>=0.104.0
uvicorn>=0.24.0

# CRM integrations
hubspot-api-client>=8.0.0
convertkit>=0.0.1

# Database
sqlalchemy>=2.0.0

# Analytics
numpy>=1.24.0
```

### Create requirements file

```bash
# Step 1: Create requirements.txt in project root
cat > requirements.txt << 'EOF'
openai>=1.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0.0
requests>=2.31.0
fastapi>=0.104.0
uvicorn>=0.24.0
hubspot-api-client>=8.0.0
pytest>=7.0.0
pytest-cov>=4.0.0
EOF

# Step 2: Install all dependencies with uv
uv pip install -r requirements.txt

# Step 3: Verify installation
uv pip list
```

---

## Development Workflow

### Adding New Dependencies

```bash
# 1. Install with uv
uv pip install new-package

# 2. Update requirements.txt
uv pip freeze > requirements.txt

# 3. Commit to git
git add requirements.txt
git commit -m "Add new-package dependency"
```

### Team Collaboration

```bash
# Teammate receives requirements.txt
# They install same versions with:
uv pip install -r requirements.txt

# This ensures everyone has identical dependency versions
```

### Updating All Dependencies

```bash
# 1. Create backup
cp requirements.txt requirements.txt.bak

# 2. Update all packages
uv pip install --upgrade -r requirements.txt

# 3. Regenerate requirements.txt with new versions
uv pip freeze > requirements.txt

# 4. Test everything
pytest

# 5. Commit if successful
git add requirements.txt
git commit -m "Update all dependencies to latest compatible versions"

# Or revert if something breaks
git checkout requirements.txt
uv pip install -r requirements.txt
```

---

## Virtual Environment Management with uv

### Creating Separate Virtual Environments

```bash
# Create venv for this project
python -m venv venv

# Create venv for testing (optional)
python -m venv venv-test

# Activate different venvs
source venv/bin/activate        # Main development
source venv-test/bin/activate   # Testing only
```

### Switching Between Environments

```bash
# Check which venv is active
which python

# Deactivate current
deactivate

# Activate different one
source venv-test/bin/activate
```

---

## Dependency Troubleshooting

### Issue: "Incompatible dependency versions"

```bash
# Show dependency tree to find conflicts
uv pip list --format=freeze

# Try installing with specific version constraints
uv pip install "package1>=1.0,<2.0" "package2>=2.0,<3.0"
```

### Issue: "Package not found or version too old"

```bash
# Update package index
uv pip index-refresh

# Try again
uv pip install package-name --upgrade
```

### Issue: "Circular dependency or conflict"

```bash
# Use uv's dependency resolver to check compatibility
uv pip install package1 package2 --dry-run

# If --dry-run shows it would work, install without --dry-run
uv pip install package1 package2
```

### Issue: "Need specific Python version"

```bash
# Check Python version in venv
python --version

# If wrong version, create new venv with specific Python
/usr/bin/python3.11 -m venv venv  # Use specific Python path
source venv/bin/activate
uv pip install -r requirements.txt
```

---

## CI/CD & Automated Dependency Management

### GitHub Actions Example

```yaml
name: Test with uv

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install uv
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          export PATH="$HOME/.cargo/bin:$PATH"

      - name: Create venv and install dependencies with uv
        run: |
          python -m venv venv
          source venv/bin/activate
          uv pip install -r requirements.txt

      - name: Run tests
        run: |
          source venv/bin/activate
          pytest --cov=src tests/
```

---

## Best Practices

### ✅ DO

```bash
# ✓ Use uv for all package operations
uv pip install package

# ✓ Keep requirements.txt updated
uv pip freeze > requirements.txt

# ✓ Pin major versions in requirements.txt
openai>=1.0.0,<2.0.0

# ✓ Use uv for team consistency
# Everyone runs: uv pip install -r requirements.txt

# ✓ Create separate dev requirements file
cat > requirements-dev.txt << 'EOF'
-r requirements.txt
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
EOF

# Then install with:
uv pip install -r requirements-dev.txt
```

### ❌ DON'T

```bash
# ✗ Never use pip directly
pip install package  # WRONG - don't do this

# ✗ Don't mix pip and uv
pip install something && uv pip install something-else  # WRONG

# ✗ Don't commit venv folder
git add venv/  # WRONG

# ✗ Don't use ancient package versions without reason
openai==0.9.0  # Outdated, use newer

# ✗ Don't forget to update requirements.txt
# Always run: uv pip freeze > requirements.txt after installing
```

---

## Production Deployment

### Preparing for Production

```bash
# 1. Create production-only requirements
uv pip freeze | grep -v pytest | grep -v black | grep -v flake8 > requirements-prod.txt

# 2. Test with production requirements
python -m venv venv-prod
source venv-prod/bin/activate
uv pip install -r requirements-prod.txt

# 3. Verify application runs
python -m src.main

# 4. Deactivate and deploy
deactivate
# ... deploy venv-prod or requirements-prod.txt
```

### Building Docker Image (using uv)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install uv and use it to install dependencies
RUN pip install uv && \
    uv pip install -r requirements.txt

# Copy application
COPY . .

# Run agent
CMD ["python", "-m", "src.main"]
```

---

## Command Cheat Sheet

| Task | Command |
|------|---------|
| Install package | `uv pip install package` |
| Install from file | `uv pip install -r requirements.txt` |
| List packages | `uv pip list` |
| Show package info | `uv pip show package` |
| Update package | `uv pip install --upgrade package` |
| Uninstall package | `uv pip uninstall package` |
| Export environment | `uv pip freeze > requirements.txt` |
| Check outdated | `uv pip list --outdated` |
| Check compatibility | `uv pip install pkg1 pkg2 --dry-run` |
| Remove all packages | `uv pip uninstall -r requirements.txt -y` |

---

## FAQ

### Q: Why use uv instead of pip?
**A:** `uv` is 10-100x faster, uses less memory, has better dependency resolution, and is the modern standard for Python package management.

### Q: What if a package doesn't work with uv?
**A:** Almost all packages work with uv. If there's an issue, it's usually with the package itself, not uv. Report to package maintainer.

### Q: Do I need to update requirements.txt every time?
**A:** Yes, after installing any new package, run `uv pip freeze > requirements.txt` to keep it in sync.

### Q: Can I use uv with Poetry/Pipenv?
**A:** `uv` is meant to replace those tools. For this project, use only `uv`.

### Q: How do I upgrade Python version?
**A:** Create new venv with new Python: `python3.12 -m venv venv` then reinstall: `uv pip install -r requirements.txt`

---

## Summary

**All dependency management for this project uses `uv`:**
- ✅ Install: `uv pip install package`
- ✅ Update: `uv pip install --upgrade package`
- ✅ List: `uv pip list`
- ✅ Freeze: `uv pip freeze > requirements.txt`
- ✅ Remove: `uv pip uninstall package`

**Never use `pip` directly. Always use `uv pip` instead.**
