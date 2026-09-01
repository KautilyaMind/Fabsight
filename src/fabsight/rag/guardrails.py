"""Lightweight post-generation warning checks."""

import re

PATTERNS = {
    "anonymous_feature_physical_meaning": re.compile(r"feature_\d+\s*(?:=|is|represents|means)\s*(?:temperature|pressure|flow|power|speed)", re.I),
    "confirmed_root_cause_claim": re.compile(r"confirmed root cause|definitely caused|proves? (?:that )?.+caused", re.I),
}


def find_guardrail_flags(text: str) -> list[str]:
    return [name for name, pattern in PATTERNS.items() if pattern.search(text)]
