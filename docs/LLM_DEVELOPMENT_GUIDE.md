# LlumDocs Development Guide

Quick reference guide for making commits and maintaining code quality.

---

## 1. How to Make Commits

### Step by step

```bash
# 1. Stage your changes
git add .

# 2. Commit (pre-commit will run automatically)
git commit -m "[component] Description of change"
```

### Before committing (optional)

If you want to check everything is correct before committing:

```bash
# Run all pre-commit hooks
pre-commit run --all-files
```

---

## 2. Commit Message Format

### Required format

Commit messages must follow this format:

```
[component] Brief description in infinitive
```

### Accepted components

- `[core]` - Core system changes
- `[ui]` - User interface changes
- `[api]` - API changes
- `[docs]` - Documentation changes
- `[test]` - Test-related changes
- `[fix]` - Bug fixes
- `[refactor]` - Code refactoring

### Valid examples

```bash
git commit -m "[core] Add summarization service"
git commit -m "[ui] Improve translation interface"
git commit -m "[api] Add semantic search endpoint"
git commit -m "[docs] Update LlumDocs README"
git commit -m "[fix] Fix error in image processing"
git commit -m "[refactor] Simplify validation logic"
```

### Rules

- ✅ Message must start with `[` and contain `]`
- ✅ There must be text after the label
- ✅ Description should be in infinitive (add, improve, fix, etc.)
- ❌ Messages without component are not allowed: `"Add feature"` (incorrect)
- ❌ Messages without description are not allowed: `"[core]"` (incorrect)

---

## 3. Ruff Commands

### Basic commands

```bash
# Check for errors and warnings (without modifying files)
ruff check .

# Check and automatically fix fixable errors
ruff check --fix .

# Check a specific directory
ruff check llumdocs/

# Check a specific file
ruff check llumdocs/app/main.py
```

### Format code

```bash
# Format all files
ruff format .

# Format a specific directory
ruff format llumdocs/

# Format a specific file
ruff format llumdocs/app/main.py
```

### Combined commands

```bash
# Check and format everything
ruff check --fix . && ruff format .

# Check and format a directory
ruff check --fix llumdocs/ && ruff format llumdocs/
```

### Other useful options

```bash
# Show only errors (no warnings)
ruff check --select E,F .

# Show all issues (including suggestions)
ruff check --select ALL .

# Temporarily ignore a specific rule
ruff check --ignore E501 .
```

---

## 4. Pre-commit (Info)

Pre-commit hooks run automatically when you do `git commit` and check:

- Code formatting (ruff format, black)
- Linting (ruff check)
- Trailing whitespace and newlines
- Commit message format

If any hook fails, the commit is rejected and you must fix the errors before trying again.

---

## 5. Ruff Configuration

Ruff configuration is in `pyproject.toml`:

- Line length: 100 characters
- Python version: 3.11
- Active rules: E (pycodestyle), F (pyflakes), I (imports), B (bugbear)
