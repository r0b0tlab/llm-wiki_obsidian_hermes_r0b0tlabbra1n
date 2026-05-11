# Release Checklist

Before publishing a release:

- [ ] `bash scripts/quality_gate.sh` passes.
- [ ] `ruff check .` passes.
- [ ] `pytest -q` passes.
- [ ] Retrieval eval metrics are recorded.
- [ ] README feature status table matches implementation.
- [ ] `docs/architecture.md` matches implementation.
- [ ] Version bumped in `pyproject.toml` and `r0b0tlabbra1n/__init__.py`.
- [ ] No secrets in repo or generated vault fixtures.
- [ ] Fresh venv install succeeds.
- [ ] GitHub Actions CI passes.
