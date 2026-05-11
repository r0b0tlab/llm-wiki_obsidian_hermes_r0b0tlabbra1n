"""Secret scanner — detect and block secrets from entering the vault."""

from __future__ import annotations

import re
from pathlib import Path

# Patterns that indicate secrets
# These are intentionally over-broad — better a false positive than a leak
_SECRET_PATTERNS: list[tuple[str, str]] = [
    # HuggingFace tokens
    (r"hf_[a-zA-Z0-9]{20,}", "HuggingFace token (hf_...)"),
    # OpenAI API keys
    (r"sk-(?:proj-)?[a-zA-Z0-9]{20,}", "OpenAI API key (sk-...)"),
    # Anthropic API keys
    (r"sk-ant-[a-zA-Z0-9]{20,}", "Anthropic API key (sk-ant-...)"),
    # GitHub tokens
    (r"gh[pousr]_[a-zA-Z0-9]{20,}", "GitHub token (ghp_/gho_/ghu_/ghs_/ghr_...)"),
    # Generic bearer tokens
    (r"bearer\s+[a-zA-Z0-9\-_\.]{20,}", "Bearer token"),
    # JWT tokens
    (r"eyJ[a-zA-Z0-9\-_]{20,}\.[a-zA-Z0-9\-_]{20,}\.[a-zA-Z0-9\-_]{20,}", "JWT token"),
    # Private key patterns
    (r"-----BEGIN (?:RSA|EC|DSA|OPENSSH|PGP) PRIVATE KEY-----", "Private key"),
    # AWS keys
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"aws_secret_access_key\s*=\s*[\"']?[a-zA-Z0-9+/]{20,}", "AWS secret key"),
    # Generic API key assignments
    (
        r"(?:api[_-]?key|apikey|secret|token|password)\s*[:=]\s*[\"'][a-zA-Z0-9\-_\.]{16,}[\"']",
        "API key/secret assignment",
    ),
    # AgentMail tokens
    (r"am_[a-zA-Z0-9]{20,}", "AgentMail token (am_...)"),
    # Google API keys
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API key"),
]


def scan_for_secrets(content: str, source: str = "<unknown>") -> list[str]:
    """Scan content for secrets. Returns list of human-readable issue descriptions.

    Args:
        content: The text to scan
        source: Identifier for the content (e.g., filename)

    Returns:
        List of issues found, empty if clean
    """
    issues = []

    for pattern, description in _SECRET_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            # Mask the secret for the message
            value = match.group(0)
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            issues.append(f"Secret detected [{description}]: {masked} in {source}")

    # Also check for .env file values being copied
    env_pattern = re.compile(r'([A-Z_]{3,})=["\']?([^"\'\n]{8,})["\']?')
    for match in env_pattern.finditer(content):
        key = match.group(1)
        value = match.group(2)
        # Skip known non-secret env vars
        if key in (
            "PATH",
            "HOME",
            "USER",
            "SHELL",
            "LANG",
            "PWD",
            "TERM",
            "DISPLAY",
            "EDITOR",
            "PAGER",
            "HOSTNAME",
            "LOGNAME",
        ):
            continue
        # Flag potential secret env values
        if any(
            secret_word in key.upper()
            for secret_word in ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASS", "AUTH", "CREDENTIAL")
        ):
            issues.append(f"Env secret variable: {key} in {source}")

    return issues


def scan_file(path: Path) -> list[str]:
    """Scan a file for secrets."""
    if not path.exists():
        return []
    try:
        content = path.read_text(encoding="utf-8")
        return scan_for_secrets(content, str(path))
    except Exception:
        return [f"Could not read {path} for secret scan"]


def is_safe(content: str) -> bool:
    """Quick check: return True if no secrets detected."""
    return len(scan_for_secrets(content)) == 0
