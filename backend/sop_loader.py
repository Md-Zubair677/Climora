"""
Loads SOPs from sops/sops.yaml.

This is intentionally the ONLY place that reads the policy file. Nothing else
in the codebase hardcodes an SOP id, condition, or threshold — so editing
sops.yaml (including adding an 11th, 12th, Nth SOP live) requires touching
zero lines of Python.
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

SOPS_PATH = Path(__file__).resolve().parent.parent / "sops" / "sops.yaml"

_VALID_SEVERITIES = {"low", "medium", "high", "critical"}
_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _validate(sop: dict[str, Any]) -> None:
    required = {"id", "category", "severity", "title", "condition", "guidance"}
    missing = required - sop.keys()
    if missing:
        raise ValueError(f"SOP {sop.get('id', '<unknown>')} missing fields: {missing}")
    if sop["severity"] not in _VALID_SEVERITIES:
        raise ValueError(
            f"SOP {sop['id']} has invalid severity '{sop['severity']}'. "
            f"Must be one of {_VALID_SEVERITIES}."
        )


@functools.lru_cache(maxsize=1)
def load_sops(path: Path = SOPS_PATH) -> list[dict[str, Any]]:
    """Load, validate, and cache the SOP list. Cache is per-process; restart
    (or call load_sops.cache_clear()) to pick up edits to the YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        sops = yaml.safe_load(f)

    if not sops:
        raise ValueError("sops.yaml is empty or invalid.")

    seen_ids = set()
    for sop in sops:
        _validate(sop)
        if sop["id"] in seen_ids:
            raise ValueError(f"Duplicate SOP id: {sop['id']}")
        seen_ids.add(sop["id"])

    return sops


def sop_by_id(sop_id: str) -> dict[str, Any] | None:
    for sop in load_sops():
        if sop["id"] == sop_id:
            return sop
    return None


def severity_rank(severity: str) -> int:
    return _SEVERITY_RANK.get(severity, -1)


def format_sops_for_prompt() -> str:
    """Render all SOPs into a compact, LLM-readable block for the matcher node."""
    lines = []
    for sop in load_sops():
        lines.append(
            f"[{sop['id']}] (category={sop['category']}, severity={sop['severity']}) "
            f"{sop['title']}\n"
            f"  CONDITION: {sop['condition'].strip()}\n"
            f"  GUIDANCE: {sop['guidance'].strip()}"
        )
    return "\n\n".join(lines)
