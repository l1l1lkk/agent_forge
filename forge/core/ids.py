"""ID generation for forge-agent entities.

Generates short, human-readable prefixed IDs like:
  proj_a1b2c3d4
  agent_e5f6g7h8
  ses_i9j0k1l2
  msg_m3n4o5p6
  task_q7r8s9t0
  evt_u1v2w3x4
"""

from __future__ import annotations

import secrets
import time

# Prefix mapping by entity type
PREFIXES: dict[str, str] = {
    "project": "proj",
    "agent": "agent",
    "session": "ses",
    "message": "msg",
    "task": "task",
    "event": "evt",
    "schedule": "sched",
    "audit": "audit",
}

# Character set for the random portion (no ambiguous chars: 0/O, 1/I/l)
_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"


def _random_suffix(length: int = 8) -> str:
    """Generate a random string of the given length."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def _timestamp_suffix(length: int = 8) -> str:
    """Generate a time-based suffix using base36 encoding of microseconds."""
    now = int(time.time() * 1_000_000)
    chars = []
    for _ in range(length):
        now, rem = divmod(now, len(_ALPHABET))
        chars.append(_ALPHABET[rem])
    return "".join(reversed(chars))


def gen_id(prefix: str) -> str:
    """Generate a prefixed unique ID.

    Args:
        prefix: Entity type key (e.g. "project", "agent") or a raw prefix string.

    Returns:
        A string like "proj_a1b2c3d4".

    Raises:
        ValueError: If the prefix is unknown and doesn't look like a valid custom prefix.
    """
    pfx = PREFIXES.get(prefix, prefix)
    if len(pfx) < 2 or len(pfx) > 10:
        raise ValueError(f"Invalid prefix: {prefix!r}")
    suffix = _random_suffix()
    return f"{pfx}_{suffix}"
