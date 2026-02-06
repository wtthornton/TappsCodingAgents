"""
Expert CLI command handlers (Phase 8.3).

Commands: expert list, consult, info, search, cached
"""

import json
import logging
from pathlib import Path
from typing import Any

from ...core.config import load_config
from ...core.unicode_safe import safe_print

logger = logging.getLogger(__name__)


def handle_expert_command(args: object) -> None:
    """Route expert subcommands."""
    command = getattr(args, "expert_command", None)
    if command == "list":
        handle_expert_list(args)
    elif command == "consult":
        handle_expert_consult(args)
    elif command == "info":
        handle_expert_info(args)
    elif command == "search":
        handle_expert_search(args)
    elif command == "cached":
        handle_expert_cached(args)
    else:
        safe_print("Usage: tapps-agents expert {list|consult|info|search|cached}")
        safe_print("  list    - List all available experts")
        safe_print("  consult - Consult an expert domain")
        safe_print("  info    - Show detailed info about an expert")
        safe_print("  search  - Search across knowledge bases")
        safe_print("  cached  - List cached Context7 libraries")


def _load_experts(project_root: Path) -> list[dict[str, Any]]:
    """Load all experts (built-in + project-defined)."""
    experts: list[dict[str, Any]] = []

    # Load from experts.yaml
    experts_yaml = project_root / ".tapps-agents" / "experts.yaml"
    if experts_yaml.exists():
        import yaml
        try:
            data = yaml.safe_load(experts_yaml.read_text(encoding="utf-8")) or {}
            for name, config in data.items():
                if isinstance(config, dict):
                    experts.append({
                        "id": name,
                        "domain": config.get("domain", "general"),
                        "triggers": config.get("triggers", []),
                        "priority": config.get("priority", 0.7),
                        "knowledge_files": config.get("knowledge_files", []),
                        "description": config.get("description", ""),
                        "source": "project",
                    })
        except Exception as exc:
            logger.warning("Failed to load experts.yaml: %s", exc)

    # Load built-in experts from registry
    try:
        from ...core.generators.expert_generator import ExpertGenerator
        gen = ExpertGenerator(project_root)
        builtin = gen.list_builtin_experts() if hasattr(gen, "list_builtin_experts") else []
        for b in builtin:
            if isinstance(b, dict):
                experts.append({**b, "source": "built-in"})
    except Exception:
        pass

    return experts


def handle_expert_list(args: object) -> None:
    """List all available experts."""
    project_root = Path.cwd()
    output_format = getattr(args, "format", "text")
    domain_filter = getattr(args, "domain", None)

    experts = _load_experts(project_root)
    if domain_filter:
        experts = [e for e in experts if e.get("domain") == domain_filter]

    if output_format == "json":
        safe_print(json.dumps(experts, indent=2))
        return

    if not experts:
        safe_print("No experts configured. Run 'tapps-agents setup-experts init' to generate.")
        return

    safe_print(f"{'ID':<35} {'Domain':<20} {'Priority':<10} {'Source':<10} {'Knowledge':<10}")
    safe_print("-" * 85)
    for e in experts:
        kf_count = len(e.get("knowledge_files", []))
        safe_print(
            f"{e['id'][:33]:<35} {e.get('domain', '')[:18]:<20} "
            f"{e.get('priority', 0.7):<10.2f} {e.get('source', ''):<10} "
            f"{kf_count} files"
        )


def handle_expert_consult(args: object) -> None:
    """Consult an expert domain."""
    project_root = Path.cwd()
    domain = getattr(args, "domain", "")
    question = getattr(args, "question", "")
    output_format = getattr(args, "format", "text")

    if not domain or not question:
        safe_print("Error: domain and question required")
        return

    # Search knowledge base for relevant content
    kb_dir = project_root / ".tapps-agents" / "kb"
    results: list[str] = []

    if kb_dir.exists():
        for md_file in kb_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                # Simple keyword matching for domain relevance
                if domain.lower() in content.lower() or domain.lower() in md_file.stem.lower():
                    # Extract first 500 chars as context
                    results.append(f"[{md_file.name}]: {content[:500]}")
            except Exception:
                continue

    if output_format == "json":
        safe_print(json.dumps({
            "domain": domain,
            "question": question,
            "knowledge_results": len(results),
            "context": results[:5],
        }, indent=2))
        return

    safe_print(f"Expert Consultation: {domain}")
    safe_print(f"Question: {question}")
    safe_print(f"\nKnowledge results: {len(results)} relevant files")
    if results:
        for r in results[:5]:
            safe_print(f"\n{r[:300]}...")
    else:
        safe_print("No knowledge base files found for this domain.")
        safe_print("Tip: Add .md files to .tapps-agents/kb/ and run 'tapps-agents setup-experts init'")


def handle_expert_info(args: object) -> None:
    """Show detailed info about a specific expert."""
    project_root = Path.cwd()
    expert_id = getattr(args, "expert_id", "")
    output_format = getattr(args, "format", "text")

    experts = _load_experts(project_root)
    expert = next((e for e in experts if e.get("id") == expert_id), None)

    if not expert:
        safe_print(f"Expert not found: {expert_id}")
        safe_print("Use 'tapps-agents expert list' to see available experts.")
        return

    if output_format == "json":
        safe_print(json.dumps(expert, indent=2))
        return

    safe_print(f"Expert: {expert['id']}")
    safe_print(f"Domain: {expert.get('domain', 'N/A')}")
    safe_print(f"Priority: {expert.get('priority', 'N/A')}")
    safe_print(f"Source: {expert.get('source', 'N/A')}")
    safe_print(f"Description: {expert.get('description', 'N/A')}")
    triggers = expert.get("triggers", [])
    if triggers:
        safe_print(f"Triggers: {', '.join(triggers)}")
    kf = expert.get("knowledge_files", [])
    if kf:
        safe_print(f"Knowledge files ({len(kf)}):")
        for f in kf[:20]:
            safe_print(f"  - {f}")


def handle_expert_search(args: object) -> None:
    """Search across all expert knowledge bases."""
    project_root = Path.cwd()
    query = getattr(args, "query", "")
    output_format = getattr(args, "format", "text")

    if not query:
        safe_print("Error: query required")
        return

    kb_dir = project_root / ".tapps-agents" / "kb"
    results: list[dict[str, str]] = []

    if kb_dir.exists():
        query_lower = query.lower()
        for md_file in kb_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    # Find matching line
                    for i, line in enumerate(content.split("\n"), 1):
                        if query_lower in line.lower():
                            results.append({
                                "file": str(md_file.relative_to(project_root)),
                                "line": i,
                                "match": line.strip()[:200],
                            })
                            break
            except Exception:
                continue

    if output_format == "json":
        safe_print(json.dumps(results, indent=2))
        return

    if not results:
        safe_print(f"No results for '{query}' in knowledge base.")
        return

    safe_print(f"Search results for '{query}' ({len(results)} matches):")
    for r in results[:20]:
        safe_print(f"  {r['file']}:{r['line']} — {r['match']}")


def handle_expert_cached(args: object) -> None:
    """List cached Context7 libraries."""
    project_root = Path.cwd()
    library = getattr(args, "library", None)
    output_format = getattr(args, "format", "text")

    cache_dir = project_root / ".tapps-agents" / "kb" / "context7-cache"
    if not cache_dir.exists():
        cache_dir = project_root / ".tapps-agents" / "context7-docs"

    if not cache_dir.exists():
        safe_print("No Context7 cache found.")
        safe_print("Run 'tapps-agents init' to populate the cache.")
        return

    cached_files = sorted(cache_dir.glob("*.json"))

    if library:
        cached_files = [f for f in cached_files if library.lower() in f.stem.lower()]

    if output_format == "json":
        items = []
        for f in cached_files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                items.append({"file": f.name, "library": f.stem, "size": f.stat().st_size})
            except Exception:
                items.append({"file": f.name, "error": "parse failed"})
        safe_print(json.dumps(items, indent=2))
        return

    if not cached_files:
        safe_print(f"No cached libraries{f' matching {library}' if library else ''}.")
        return

    safe_print(f"Cached Context7 libraries ({len(cached_files)}):")
    for f in cached_files:
        size_kb = f.stat().st_size / 1024
        safe_print(f"  {f.stem:<40} {size_kb:>8.1f} KB")
