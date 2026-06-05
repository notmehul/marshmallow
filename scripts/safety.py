#!/usr/bin/env python3
"""Shared safety checks for generated Marshmallow runtime guidance."""

from __future__ import annotations

import re
from pathlib import Path

from marshmallow_workspace import MarshmallowError

BLOCKED_GUIDANCE_PATTERNS = (
    re.compile(r"\bignore (?:all |any |the )?(?:previous|prior|system|developer|user) instructions?\b", re.IGNORECASE),
    re.compile(r"\b(?:disregard|override|bypass) (?:the )?(?:system|developer|user|security|safety|permission)", re.IGNORECASE),
    re.compile(r"\b(?:run|execute|invoke) (?:this |the )?(?:command|shell|bash|python|curl|wget)\b", re.IGNORECASE),
    re.compile(r"\b(?:read|write|upload|send|exfiltrate|delete) (?:the |all |any )?(?:secret|credential|token|api[- ]?key)", re.IGNORECASE),
    re.compile(r"\b(?:system prompt|developer message|jailbreak)\b", re.IGNORECASE),
)


def validate_generated_guidance(text: str, source: str | Path, max_chars: int | None = None) -> None:
    """Reject generated guidance that should never enter runtime context."""

    if max_chars is not None and len(text) > max_chars:
        raise MarshmallowError(f"{source}: generated guidance exceeds {max_chars} characters")
    for pattern in BLOCKED_GUIDANCE_PATTERNS:
        if pattern.search(text):
            raise MarshmallowError(f"{source}: generated guidance contains a blocked instruction pattern")
