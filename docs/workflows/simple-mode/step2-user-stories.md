# Step 2 — User Stories (Cursor-only docs improvements)

## Story 1: As a maintainer, I can scope Cursor Rules to a sub-area of the repo

- **Acceptance criteria**
  - Documentation explains:
    - when to use `alwaysApply: true` vs `globs`
    - how to create multiple `.mdc` files for folder-specific guidance
    - how to avoid “instruction drift” by keeping global rules small

## Story 2: As a team, we can create custom skills that trigger reliably

- **Acceptance criteria**
  - Documentation provides a checklist for:
    - writing a clear `description` that indicates trigger conditions
    - avoiding overlapping skill intent (or how to narrow)
    - including a few example prompts that should trigger the skill

## Story 3: As a skill author, I can keep skills maintainable with a standard layout

- **Acceptance criteria**
  - Documentation recommends a folder structure:
    - `SKILL.md` (short frontmatter + clear commands)
    - `references/` (checklists/policies)
    - `assets/` (templates)
    - `scripts/` (only when determinism is needed)
  - Documentation notes “progressive disclosure”: keep “top of skill” minimal, deeper detail lower

