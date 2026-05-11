"""Tests for secret scanning."""

import tempfile
from pathlib import Path

from r0b0tlabbra1n.security.secret_scan import is_safe, scan_for_secrets, scan_file


def test_scan_clean_content():
    assert scan_for_secrets("This is clean content.") == []
    assert is_safe("Regular text about machine learning.")


def test_scan_hf_token():
    issues = scan_for_secrets("My HF token is hf_abc123def456ghi789jkl012")
    assert len(issues) >= 1
    assert "hf_..." in issues[0]
    assert not is_safe("hf_abc123def456ghi789jkl012")


def test_scan_openai_key():
    issues = scan_for_secrets("API key: sk-proj-abc123def456ghi789jkl012mno345pqr678")
    assert len(issues) >= 1
    assert "sk-..." in issues[0]


def test_scan_private_key():
    issues = scan_for_secrets("-----BEGIN RSA PRIVATE KEY-----\nsomething\n-----END RSA PRIVATE KEY-----")
    assert len(issues) >= 1
    assert "Private key" in issues[0]


def test_scan_jwt():
    issues = scan_for_secrets(
        "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    )
    assert len(issues) >= 1
    # Either JWT or Bearer token pattern may match first
    assert any("JWT" in i or "Bearer" in i for i in issues)


def test_scan_env_secret_variable():
    issues = scan_for_secrets('OPENAI_API_KEY="sk-abc123def456ghi789jkl012mno345"')
    assert len(issues) >= 1
    # Either OpenAI key or env variable pattern may match first
    assert any("OPENAI_API_KEY" in i or "OpenAI" in i for i in issues)


def test_scan_env_safe_variables():
    # Safe env vars should not trigger
    content = 'PATH="/usr/bin"\nHOME="/home/user"\nUSER="bob"'
    issues = scan_for_secrets(content)
    assert len(issues) == 0


def test_scan_file_clean():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("This is a clean file.\nNo secrets here.\n")
        f.flush()
        path = Path(f.name)

    try:
        issues = scan_file(path)
        assert issues == []
    finally:
        path.unlink(missing_ok=True)
