"""Tests for vault linting."""

import tempfile
from pathlib import Path

from r0b0tlabbra1n.vault.initialize import init_vault
from r0b0tlabbra1n.vault.lint import lint_vault


def test_lint_clean_vault():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "test-brain"
        init_vault(vault)

        issues = lint_vault(vault)
        # New vault should have minimal issues (only orphans for default pages without incoming links)
        errors = [i for i in issues if i["level"] == "ERROR"]
        assert len(errors) == 0


def test_lint_broken_wikilink():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "test-brain"
        init_vault(vault)

        # Create a page with a broken link
        page = vault / "broken-link.md"
        page.write_text("""---
title: Broken Link
type: concept
status: active
provenance: test
---

See [[nonexistent-page]] for more info.
""")

        issues = lint_vault(vault)
        warnings = [i for i in issues if "Broken wikilink" in i.get("message", "")]
        assert len(warnings) >= 1
        # Check that nonexistent-page is in at least one of the warnings
        assert any("nonexistent-page" in w["message"] for w in warnings)


def test_lint_missing_title():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "test-brain"
        init_vault(vault)

        page = vault / "no-title.md"
        page.write_text("""---
type: concept
status: active
---

No title here.
""")

        issues = lint_vault(vault)
        errors = [i for i in issues if "title" in i.get("message", "").lower()]
        assert len(errors) >= 1


def test_lint_invalid_type():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "test-brain"
        init_vault(vault)

        page = vault / "bad-type.md"
        page.write_text("""---
title: Bad Type
type: not_a_real_type
status: active
---

Invalid page type.
""")

        issues = lint_vault(vault)
        errors = [i for i in issues if "Invalid page type" in i.get("message", "")]
        assert len(errors) >= 1
