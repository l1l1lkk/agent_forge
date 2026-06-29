"""Security utilities: command classification and risk assessment.

First version provides basic command risk classification.
Full security manager with approval flows comes in Milestone 7.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Patterns that indicate high-risk operations
HIGH_RISK_PATTERNS: list[str] = [
    r"\brm\s+-rf\b",
    r"\bsudo\b",
    r"\bchmod\s+-R\b",
    r"\bchown\s+-R\b",
    r"\bdocker\s+rm\b",
    r"\bdocker\s+system\s+prune\b",
    r"\bgit\s+push\b",
    r"\bcurl\s+.*\|\s*bash\b",
    r"\bwget\s+.*\|\s*bash\b",
    r"\bscp\b",
    r"\bssh\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bmkfs\b",
    r"\bdd\s+if=\b",
    r"\b>:.*/dev/\w",
]

# Patterns that indicate medium-risk operations
MEDIUM_RISK_PATTERNS: list[str] = [
    r"\bpip\s+install\b",
    r"\bnpm\s+install\b",
    r"\bdocker\s+build\b",
    r"\bgit\s+checkout\b",
    r"\bgit\s+reset\b",
    r"\bgit\s+rebase\b",
]


def classify_command(command: str) -> RiskLevel:
    """Classify a shell command by risk level.

    Args:
        command: The shell command string to classify.

    Returns:
        RiskLevel.LOW, MEDIUM, or HIGH.
    """
    cmd_stripped = command.strip()

    for pattern in HIGH_RISK_PATTERNS:
        if re.search(pattern, cmd_stripped, re.IGNORECASE):
            return RiskLevel.HIGH

    for pattern in MEDIUM_RISK_PATTERNS:
        if re.search(pattern, cmd_stripped, re.IGNORECASE):
            return RiskLevel.MEDIUM

    return RiskLevel.LOW


def is_command_denied(
    command: str,
    deny_patterns: Optional[list[str]] = None,
) -> tuple[bool, Optional[str]]:
    """Check if a command matches any deny-list patterns.

    Args:
        command: The command to check.
        deny_patterns: List of regex patterns to deny. Uses built-in defaults if None.

    Returns:
        Tuple of (denied, matched_pattern).
    """
    if deny_patterns is None:
        deny_patterns = [
            r"\brm\s+-rf\s+/",
            r"\bmkfs\b",
            r"\bshutdown\b",
            r"\breboot\b",
        ]

    for pattern in deny_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True, pattern

    return False, None
