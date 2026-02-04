"""
Architecture pattern detection from project layout. MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS §3.7.

Heuristics over directory layout and key files. 8 patterns: Layered, MVC,
Service+Repository, Clean/Hexagonal, CQRS, Microservices, Event Sourcing.
"""

from pathlib import Path
from typing import Any

# (pattern_name, list of dir/file signatures; any match adds evidence)
_PATTERN_SIGS: list[tuple[str, list[list[str]]]] = [
    ("Layered", [["handlers", "middleware"], ["api", "services", "models"], ["controllers", "services", "repositories"]]),
    ("MVC", [["models", "views", "controllers"], ["model", "view", "controller"]]),
    ("Service Layer + Repository", [["services", "repositories"], ["service", "repository"]]),
    ("Clean/Hexagonal", [["domain", "adapters", "application"], ["domain", "ports", "adapters"], ["src", "domain", "infrastructure"]]),
    ("CQRS", [["commands", "queries"], ["read_models", "write_models"], ["command", "query"]]),
    ("Microservices", [["services", "packages"], ["kubernetes"], ["k8s"], ["deployments", "docker-compose"]]),
    ("Event Sourcing", [["event_store"], ["events", "aggregates"], ["events", "projections"]]),
]


def detect_architecture_patterns(project_root: Path) -> list[dict[str, Any]]:
    """
    Detect architecture patterns from project layout. §3.7.

    Returns:
        [ {"pattern": str, "confidence": float, "evidence": list[str]}, ... ]
    """
    root = Path(project_root).resolve()
    if not root.is_dir():
        return []

    # Collect all directory names (one level) and two-level paths for matching
    dirs_1: set[str] = set()
    dirs_2: set[str] = set()
    for p in root.iterdir():
        if p.is_dir() and not p.name.startswith("."):
            dirs_1.add(p.name.lower())
            for q in p.iterdir():
                if q.is_dir() and not q.name.startswith("."):
                    dirs_2.add(f"{p.name}/{q.name}".lower())

    # k8s / kubernetes
    if (root / "k8s").is_dir():
        dirs_1.add("k8s")
    if (root / "kubernetes").is_dir():
        dirs_1.add("kubernetes")

    found: list[dict[str, Any]] = []

    def _has(s: str) -> bool:
        s = s.lower()
        if s in dirs_1:
            return True
        return any(s in d or d.endswith("/" + s) for d in dirs_2)

    for pattern_name, or_groups in _PATTERN_SIGS:
        evidence: list[str] = []
        for and_sigs in or_groups:
            if all(_has(s) for s in and_sigs):
                evidence.append(f"Layout: {', '.join(and_sigs)}")
                break

        if evidence:
            # Confidence from 0.5–0.9 by number of signals
            confidence = min(0.9, 0.5 + 0.1 * len(evidence))
            found.append({
                "pattern": pattern_name,
                "confidence": round(confidence, 2),
                "evidence": list(dict.fromkeys(evidence))[:5],
            })

    return found
