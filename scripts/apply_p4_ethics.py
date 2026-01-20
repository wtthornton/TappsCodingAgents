#!/usr/bin/env python3
"""Apply p4-ethics a11y/inclusion edits to SKILLs and agent-capabilities.mdc. Run from repo root."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EDITS = [
    # implementer: after "7. ... (quality threshold)" before ## Commands
    (
        ROOT / ".claude/skills/implementer/SKILL.md",
        "(quality threshold)\n\n## Commands",
        "(quality threshold)\n\n**Accessibility and inclusion (plan 4.3):** For UI and docs: use semantic HTML, ARIA when needed, sufficient color contrast, keyboard navigation, and screen-reader-friendly text (WCAG 2.1 AA where applicable). Use inclusive, neutral language; avoid assumptions about identity or ability; in examples use diverse persona names where relevant.\n\n## Commands",
    ),
    # designer: after "Ensure consistency across designs" before ## Commands
    (
        ROOT / ".claude/skills/designer/SKILL.md",
        "   - Ensure consistency across designs\n\n## Commands",
        "-   Ensure consistency across designs\n\n**Accessibility and inclusion (plan 4.3):** In UI/UX and API specs: semantic structure, ARIA when needed, color contrast, keyboard and screen-reader support (WCAG 2.1 AA where applicable). Use inclusive, neutral language; avoid assumptions about identity or ability; use diverse persona names in examples where relevant.\n\n## Commands",
    ),
    # reviewer: after "6. **Be constructive, not critical**" before ## Commands
    (
        ROOT / ".claude/skills/reviewer/SKILL.md",
        "6. **Be constructive, not critical**\n\n## Commands",
        "6. **Be constructive, not critical**\n\n**Accessibility and inclusion (plan 4.3):** When reviewing UI or docs: check semantic structure, ARIA, color contrast, keyboard and screen-reader support (flag WCAG 2.1 AA gaps where applicable). Note inclusive language; call out non-inclusive or non-diverse examples when relevant.\n\n## Commands",
    ),
    # ops: after infrastructure patterns before ## Commands
    (
        ROOT / ".claude/skills/ops/SKILL.md",
        "   - Use Context7 KB cache for infrastructure patterns\n\n## Commands",
        "-   Use Context7 KB cache for infrastructure patterns\n\n**Accessibility and inclusion (plan 4.3):** In runbooks, UIs, and user-facing messages: clear structure, sufficient contrast, screen-reader-friendly text (WCAG 2.1 AA for operator tools where applicable). Use inclusive, neutral language; use diverse examples in docs and runbooks where relevant.\n\n## Commands",
    ),
]

AGENT_CAPABILITIES = (
    ROOT / ".cursor/rules/agent-capabilities.mdc",
    "7. **Consult Experts**: Agents automatically consult experts, but you can also use `enhancer` for explicit expert consultation\n\n---\n\n## Related Documentation",
    "7. **Consult Experts**: Agents automatically consult experts, but you can also use `enhancer` for explicit expert consultation\n\n---\n\n## Ethics and Inclusion\n\nImplementer, designer, reviewer, and ops follow a11y and inclusion guidance (WCAG 2.1 AA where applicable, inclusive language, diverse examples). Details are in each agent's SKILL.md.\n\n## Related Documentation",
)


def main() -> None:
    ok = 0
    for path, search, replace in EDITS:
        p = Path(path)
        if not p.exists():
            print(f"SKIP (missing): {p}")
            continue
        raw = p.read_text(encoding="utf-8")
        if "plan 4.3" in raw or "Accessibility and inclusion" in raw:
            print(f"SKIP (already has a11y): {p}")
            ok += 1
            continue
        if search not in raw:
            print(f"FAIL (anchor not found): {p}")
            continue
        out = raw.replace(search, replace, 1)
        p.write_text(out, encoding="utf-8")
        print(f"OK: {p}")
        ok += 1

    # agent-capabilities.mdc
    path, search, replace = AGENT_CAPABILITIES
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    if "Ethics and Inclusion" in raw:
        print(f"SKIP (already has Ethics): {p}")
        ok += 1
    elif search not in raw:
        print(f"FAIL (anchor not found): {p}")
    else:
        out = raw.replace(search, replace, 1)
        p.write_text(out, encoding="utf-8")
        print(f"OK: {p}")
        ok += 1

    print(f"Done. {ok}/6 edits applied.")


if __name__ == "__main__":
    main()
