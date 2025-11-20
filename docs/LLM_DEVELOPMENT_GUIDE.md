# LlumDocs Development Guide

Short checklist for contributing code without breaking conventions.

---

## 1. Daily Workflow

1. Pull the latest changes and create a feature branch.
2. Run `uv sync` if dependencies changed (check `uv.lock` in commits).
3. Keep business logic inside `llumdocs/services`, surface it via API/UI layers, and avoid direct OpenAI SDK calls—always go through `llumdocs.llm` helpers.
4. Write or update tests next to the component you touch (unit first, integration as needed).
5. Run linters + tests locally before opening a PR.

---

## 2. Commit Style

- Format: `[component] Do something` (imperative, ≤70 chars).
- Components: `[core]`, `[api]`, `[ui]`, `[services]`, `[docs]`, `[test]`, `[fix]`, `[refactor]`.
- Example:
  ```bash
  git commit -m "[services] Add keyword extraction throttle"
  ```
- Pre-commit enforces the format; failing hooks block the commit until fixed.

---

## 3. Quality Gates

- **Pre-commit** runs automatically on `git commit`. Run manually with `pre-commit run --all-files` when iterating on large changes.
- **Ruff** handles lint + format:
  ```bash
  ruff check .            # lint only
  ruff check --fix .      # auto-fix
  ruff format .           # formatting
  ```
- Config lives in `pyproject.toml` (line length 100, Python 3.12, rules E/F/I/B).

---

## 4. Testing Expectations

- Unit tests should pass without network access; mock LiteLLM calls.
- Integration tests require real providers—see `docs/TESTING.md` for env vars, commands, and troubleshooting.
- Prefer `uv run pytest ...` so the virtualenv from `uv sync` is reused.

---

## 5. Handy Commands

```bash
# Install dev extras in the current environment
uv sync --all-extras && source .venv/bin/activate

# Lint + format everything
ruff check --fix . && ruff format .

# Run fast unit suite
uv run pytest -m "not integration"
```

---

Stick to this guide, keep logic modular, and every PR stays small and easy to review. For architecture expectations, read `docs/LLM_GUIDE_GLOBAL.md`; for capability blueprints, see `docs/LLM_FEATURE_SPECS.md`.
