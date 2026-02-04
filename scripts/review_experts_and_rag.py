"""
Expert and RAG Review Script

Reviews all experts and RAG knowledge bases to ensure correctness and completeness.
"""

import os
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tapps_agents.experts.builtin_registry import BuiltinExpertRegistry
from tapps_agents.experts.domain_utils import sanitize_domain_for_path


def review_experts_and_rag():
    """Review all experts and RAG knowledge bases."""
    print("=" * 80)
    print("Expert and RAG Review")
    print("=" * 80)
    print()

    # Get all built-in experts
    experts = BuiltinExpertRegistry.get_builtin_experts()
    kb_path = BuiltinExpertRegistry.get_builtin_knowledge_path()

    print(f"Total Built-in Experts: {len(experts)}")
    print(f"Knowledge Base Path: {kb_path}")
    print()

    # Check each expert
    issues = []
    warnings = []
    successes = []

    print("Expert-to-Knowledge Mapping:")
    print("-" * 80)

    for expert in experts:
        domain = expert.primary_domain
        expert_id = expert.expert_id
        # Use sanitize_domain_for_path to get correct directory name
        sanitized_domain = sanitize_domain_for_path(domain)
        kb_dir = kb_path / sanitized_domain

        # Check if knowledge directory exists
        kb_exists = kb_dir.exists() and kb_dir.is_dir()

        # Count knowledge files
        kb_files = []
        if kb_exists:
            kb_files = list(kb_dir.glob("*.md"))
            kb_file_count = len(kb_files)
        else:
            kb_file_count = 0

        # Check RAG enabled
        rag_enabled = expert.rag_enabled

        # Verify expert ID pattern
        f"expert-{domain.replace('-', '-')}"
        id_matches = expert_id.startswith("expert-")

        status = "[OK]" if kb_exists and kb_file_count > 0 and rag_enabled else "[WARN]"
        print(
            f"{status} {expert_id:30} | Domain: {domain:30} | KB: {str(kb_exists):5} | Files: {kb_file_count:3} | RAG: {str(rag_enabled):5}"
        )

        # Collect issues
        if not kb_exists:
            issues.append(
                f"[ERROR] {expert_id}: Knowledge directory missing: {domain}/"
            )
        elif kb_file_count == 0:
            warnings.append(
                f"[WARN] {expert_id}: Knowledge directory empty: {domain}/"
            )
        elif kb_file_count < 3:
            warnings.append(
                f"[WARN] {expert_id}: Knowledge directory has few files ({kb_file_count}): {domain}/"
            )
        else:
            successes.append(f"[OK] {expert_id}: {kb_file_count} knowledge files")

        if not rag_enabled:
            warnings.append(f"[WARN] {expert_id}: RAG disabled but knowledge exists")

        if not id_matches:
            issues.append(f"[ERROR] {expert_id}: Expert ID doesn't match pattern 'expert-*'")

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()

    if issues:
        print("[ERROR] Issues Found:")
        for issue in issues:
            print(f"  {issue}")
        print()

    if warnings:
        print("[WARN] Warnings:")
        for warning in warnings:
            print(f"  {warning}")
        print()

    if successes:
        print(f"[OK] Successes: {len(successes)} experts with knowledge bases")
        print()

    # Check for orphaned knowledge directories
    print("Checking for orphaned knowledge directories...")
    print("-" * 80)
    if kb_path.exists():
        kb_dirs = [d for d in kb_path.iterdir() if d.is_dir() and not d.name.startswith(".")]
        expert_domains = {e.primary_domain for e in experts}
        
        # Map expert domains to directory names using sanitize_domain_for_path
        expert_dir_names = {sanitize_domain_for_path(d) for d in expert_domains}

        orphaned = []
        for kb_dir in kb_dirs:
            if kb_dir.name not in expert_dir_names:
                orphaned.append(kb_dir.name)

        if orphaned:
            print("[WARN] Orphaned knowledge directories (no matching expert):")
            for orphan in orphaned:
                print(f"  - {orphan}/")
            print("  Note: These may be legacy directories or need expert configuration")
        else:
            print("[OK] No orphaned knowledge directories")
    print()

    # Check domain coverage
    print("Domain Coverage:")
    print("-" * 80)
    technical_domains = BuiltinExpertRegistry.TECHNICAL_DOMAINS
    expert_domains = {e.primary_domain for e in experts}

    missing_domains = technical_domains - expert_domains
    extra_domains = expert_domains - technical_domains

    if missing_domains:
        print("[ERROR] Domains in TECHNICAL_DOMAINS but no expert:")
        for domain in missing_domains:
            print(f"  - {domain}")
    else:
        print("[OK] All TECHNICAL_DOMAINS have experts")

    if extra_domains:
        print("[WARN] Experts with domains not in TECHNICAL_DOMAINS:")
        for domain in extra_domains:
            expert = next(e for e in experts if e.primary_domain == domain)
            print(f"  - {domain} ({expert.expert_id})")
    else:
        print("[OK] All expert domains are in TECHNICAL_DOMAINS")
    print()

    # Final status
    print("=" * 80)
    if issues:
        print("[ERROR] REVIEW FAILED: Issues found that need to be fixed")
        return 1
    elif warnings:
        print("[WARN] REVIEW PASSED WITH WARNINGS: Some improvements recommended")
        return 0
    else:
        print("[OK] REVIEW PASSED: All experts and knowledge bases are correct")
        return 0


if __name__ == "__main__":
    exit_code = review_experts_and_rag()
    sys.exit(exit_code)
