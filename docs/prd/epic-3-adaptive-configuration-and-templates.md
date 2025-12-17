# Epic 3: Adaptive Configuration & Templates (BMAD-Inspired Improvements)

## Epic Goal

Make TappsCodingAgents “zero-config by default” across diverse codebases by automatically detecting project context (tech stack + project type), applying safe and explainable templates, and enabling layered, update-safe customization of agent behavior and workflow selection.

## Epic Description

### Existing System Context

- **Current relevant functionality**:
  - Project initialization supports installing Cursor Rules/Skills and framework presets.
  - A customization system exists (update-safe overrides) and user role templates exist.
  - Tech stack detection and expert prioritization exist and can persist stack hints.
  - Workflows exist with a recommender component, but UX is not fully “guided” end-to-end.
- **Technology stack**: Python 3.13+, YAML templates/config, agent runtime + CLI, project profiling, expert registry, workflow engine.
- **Integration points**:
  - `tapps_agents/core/init_project.py` (project initialization)
  - Template selection/merging (`tapps_agents/core/template_selector.py`, `tapps_agents/core/template_merger.py`)
  - Customizations (`tapps_agents/core/customization_loader.py`, `tapps_agents/core/customization_schema.py`)
  - User role templates (`tapps_agents/core/role_template_loader.py`)
  - Workflow recommender (`tapps_agents/workflow/recommender.py`)
  - Docs/UX surfaces: Cursor Rules/Skills, installed templates under `templates/`

### Enhancement Details

- **What’s being added/changed**:
  - Dynamic tech stack templates that are selected and merged automatically during init.
  - Project-type templates (api-service, web-app, cli-tool, library, microservice) that shape defaults (validators, workflow recommendations, docs skeleton).
  - Context-aware template variables/conditional logic so templates can adapt to detected signals (without hardcoding).
  - Agent role markdown files (human-readable personas) with a loader and a consistent inheritance/override strategy.
  - A guided workflow recommendation UX (CLI + agent-facing docs) that reduces user cognitive load and prevents wrong workflow choices.
  - Scale-adaptive tech stack detection refresh (detect drift as dependencies change; propose updates rather than silently changing behavior).
- **How it integrates**:
  - During `tapps-agents init`, detect stack + project type → select templates → merge into generated config files → apply customizations and role templates last.
  - Template rendering uses a limited, safe variable engine; output includes a “generated from” trace for transparency.
  - Workflow recommendation uses the project profile + repo signals and surfaces a recommended track/workflow with rationale and a fallback option.
- **Success criteria**:
  - A new repo can be initialized with minimal manual edits and still get relevant defaults.
  - Generated config is explainable and reproducible (traceable inputs, deterministic merges).
  - Customizations remain update-safe and override behavior predictably.
  - Workflow recommendation reduces mis-selection and improves onboarding.

## Stories

1. **Story 3.1: Dynamic Tech Stack Template Library**
   - Create a curated set of stack templates (Python/FastAPI/Django; Node/React/Next.js; mixed stacks).
   - Ensure templates can be applied safely and incrementally (merge strategy, conflict rules, trace output).
   - Acceptance criteria: Running init selects and applies at least 3 common stack templates correctly and produces stable output artifacts.

2. **Story 3.2: Project Type Templates**
   - Define project archetypes and create templates per type (api-service, web-app, cli-tool, library, microservice).
   - Include default workflow suggestions, quality thresholds, and documentation skeleton recommendations.
   - Acceptance criteria: Project type templates are selectable (auto or explicit) and measurably reduce manual setup steps.

3. **Story 3.3: Context-Aware Template Variables & Conditions**
   - Implement a safe, minimal variable expansion and conditional blocks (e.g., `{{project.type}}`, `{{tech_stack.frameworks}}`).
   - Add “explain” metadata so users can see why a block rendered.
   - Acceptance criteria: Templates can express conditional defaults without code changes; rendering is deterministic and documented.

4. **Story 3.4: Agent Role Markdown Files + Loader**
   - Create `templates/agent_roles/` markdown role files (identity, principles, comms style, expertise emphasis).
   - Load roles during agent activation and allow override via the customization layer.
   - Acceptance criteria: Role files are applied consistently and are user-editable without modifying agent code/skills.

5. **Story 3.5: Persona/Configuration Inheritance Model**
   - Standardize inheritance order (Base → Role → Project → Customization → User role template where applicable).
   - Define conflict rules (override vs merge) per field type.
   - Acceptance criteria: Inheritance behavior is predictable, documented, and verified via tests across representative agents.

6. **Story 3.6: Workflow Recommendation Engine UX**
   - Provide a “workflow-recommend” experience (CLI + docs) that analyzes repo signals and suggests workflow/track with rationale.
   - Include time estimates and a small set of alternatives.
   - Acceptance criteria: Users can reliably choose an appropriate workflow with minimal back-and-forth; recommendations are explainable and consistent.

7. **Story 3.7: Scale-Adaptive Tech Stack Detection Refresh**
   - Persist tech stack signals and support refresh when dependencies change.
   - Generate non-destructive suggestions (PR-like diff or “apply” step) rather than silently changing behavior.
   - Acceptance criteria: Detection drift is caught, users can accept/reject updates, and system remains stable under change.

## Execution (Reuse of Existing Sharded Stories)

This repo already contains sharded story documents that implement most of this epic. Execute Epic 3 by completing/reviewing the linked stories below (and only create new stories where coverage is missing).

### Story Map (links)

- **Customization layer (Epic 3 foundation)**:
  - `docs/stories/29.1.customization-directory-structure.md`
  - `docs/stories/29.2.customization-loader-implementation.md`
  - `docs/stories/29.3.agent-initialization-integration.md`
  - `docs/stories/29.4.customization-template-generator.md`
  - `docs/stories/29.5.gitignore-documentation.md`
- **Tech stack expert prioritization (input signal for templates)**:
  - `docs/stories/30.1.tech-stack-expert-priority-mapping.md`
  - `docs/stories/30.2.tech-stack-config-persistence.md`
  - `docs/stories/30.3.expert-registry-priority-integration.md`
  - `docs/stories/30.4.priority-configuration-during-init.md`
  - `docs/stories/30.5.priority-testing-documentation.md`
- **Dynamic tech stack templates (auto-select + merge + init)**:
  - `docs/stories/31.1.tech-stack-template-structure.md`
  - `docs/stories/31.2.template-selection-logic.md`
  - `docs/stories/31.3.template-merging-system.md` (includes variable expansion)
  - `docs/stories/31.4.init-integration.md`
  - `docs/stories/31.5.additional-templates-documentation.md`
  - **Gap story (added by this epic)**: `docs/stories/31.6.template-conditional-blocks.md` (conditional rendering + “explain why” metadata)
- **Agent role markdown files (human-editable roles)**:
  - `docs/stories/32.1.agent-role-file-format.md`
  - `docs/stories/32.2.role-file-directory-organization.md`
  - `docs/stories/32.3.role-file-loader-implementation.md`
  - `docs/stories/32.4.agent-initialization-role-integration.md`
  - `docs/stories/32.5.additional-role-files-documentation.md`
- **Workflow recommendation UX**:
  - `docs/stories/33.1.interactive-cli-command.md`
  - `docs/stories/33.2.interactive-qa-ambiguous-cases.md`
  - `docs/stories/33.3.time-estimates-alternatives-display.md`
  - `docs/stories/33.4.recommendation-enhancement-confirmation.md`
  - `docs/stories/33.5.workflow-recommendation-testing-documentation.md`
- **Project type templates (missing coverage in repo; added by this epic)**:
  - `docs/stories/35.1.project-type-template-library.md`
  - `docs/stories/35.2.project-type-detection-and-init-application.md`

### Recommended execution order

1. `29.*` (customization layer foundations)
2. `30.*` + `31.*` (signals → template selection/merge → init)
3. `31.6` (conditional blocks + explain/trace)
4. `35.*` (project-type templates + detection + init application)
5. `32.*` (role files) + `33.*` (workflow recommendation UX)

> Note: Many of these stories are already marked “Ready for Review” in this repo. Execution can mean QA + finalization (marking Done) rather than new implementation.

## Compatibility Requirements

- [ ] Existing `tapps-agents init` behavior remains valid without templates (defaults still work).
- [ ] All new templates are additive and optional; no breaking changes to config schema.
- [ ] Existing customization and role template systems continue to function and remain highest-precedence.
- [ ] Template rendering must be deterministic and safe (no arbitrary code execution).

## Risk Mitigation

- **Primary Risk:** Incorrect detection applies wrong defaults and harms UX/quality.
  - **Mitigation:** Provide “explain why” + preview diffs; require explicit user confirmation for impactful changes; allow easy rollback.
- **Primary Risk:** Template complexity becomes unmaintainable.
  - **Mitigation:** Keep variable engine minimal; prefer composition over deep conditionals; add template tests.
- **Primary Risk:** Conflicting precedence rules lead to unpredictable behavior.
  - **Mitigation:** Formalize inheritance order; enforce via tests; document with examples.
- **Rollback Plan:**
  - Disable auto-selection and fall back to static defaults.
  - Keep generated artifacts and allow re-init without templates.

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] Template library and project type templates shipped with docs
- [ ] Context-aware template engine implemented and tested
- [ ] Agent role markdown roles implemented and integrated
- [ ] Inheritance/precedence model documented and validated
- [ ] Workflow recommendation experience available and documented
- [ ] Scale-adaptive detection refresh flow implemented with safe suggestions
- [ ] No regression in init, customization, or agent activation behavior

## Implementation Status

**Last Updated:** 2025-12-17

**Overall Status:** Draft

**Notes:**
- Some foundations already exist (customization layer, role templates, tech stack detection/priorities). This epic focuses on completing the “adaptive, template-driven” layer and improving the end-to-end initialization and workflow-selection UX.

## Dependencies & Related Work

- **Customization Layer (already present)**: This epic assumes the update-safe customization system remains the highest-precedence override mechanism.
- **User Role Templates (already present)**: Aligns with `implementation/EPIC_06_User_Role_Templates.md` (completed) and should reuse its loader/merge patterns.
- **Tech Stack Expert Priorities (already present)**: Builds on the existing priority mapping and `.tapps-agents/tech-stack.yaml` persistence (see `docs/TECH_STACK_EXPERT_PRIORITIES_GUIDE.md`).
- **Workflow System**: Leverages the existing workflow recommender and state persistence; this epic focuses on making the recommendation UX explicit and reliable.

## References

- `BMAD_INSPIRED_IMPROVEMENTS_RANKED.md` (source ranking + scope for “highest improvements”)
- `BMAD_INSPIRED_IMPROVEMENTS.md` (detailed improvement descriptions)
- `.bmad-core/core-config.yaml` (BMAD doc locations and conventions)


