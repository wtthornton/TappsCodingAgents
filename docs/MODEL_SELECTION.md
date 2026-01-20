# Model Selection

How `model_profile` in skills is resolved and how to override per-skill or globally.

---

## How It Works

Each skill declares a `model_profile` in its SKILL.md frontmatter (e.g. `reviewer_profile`, `implementer_profile`, `ops_profile`). At runtime:

1. The framework looks up that profile name in `requirements/model_profiles.yaml` or in project config (e.g. `.tapps-agents/config.yaml` or a `model_profiles` section).
2. If found, the `primary` (and optional `fallback`) model is used for that skill.
3. If the profile is **missing**, Cursor uses the **project or user default model** (the one configured in Cursor Settings or the active model in the chat).

So skills keep working even when `model_profiles.yaml` does not define every profile; missing profiles fall back to the IDE default.

---

## Overriding a Profile

### In `requirements/model_profiles.yaml`

Add or edit an entry under `model_profiles`:

```yaml
model_profiles:
  implementer_default:
    primary: local:qwen2.5-coder-14b
    fallback: cursor:gpt-5.1

  # Optional overrides (uncomment and set as needed):
  # reviewer_profile:
  #   primary: cursor:gpt-5.1
  # ops_profile:
  #   primary: cursor:gpt-5.1
  # security_review_profile:
  #   primary: cursor:gpt-5.1
```

Use `primary` and, if desired, `fallback`. The exact values (`cursor:...`, `cloud:...`, `local:...`) depend on your Cursor and runtime setup.

### In Project Config

If your project uses a `model_profiles` (or equivalent) section in `.tapps-agents/config.yaml`, you can override there. The format should match the `model_profiles` schema (e.g. `primary`, `fallback`).

---

## Recommendations

- **Reviewer and security-review:** Use a higher-accuracy model (e.g. `opus` or a stronger `cursor:`/`cloud:` model) when you want the best feedback.
- **Lint, score, and simple steps:** A lighter or local model is often enough.
- **Cost vs. quality:** Prefer stronger models for security and review; lighter ones for generate-tests or refactor when appropriate.

---

## Profiles Referenced by Skills

Common profile names in framework skills: `reviewer_profile`, `implementer_profile`, `architect_profile`, `designer_profile`, `ops_profile`, `planner_profile`, `tester_profile`, `enhancer_profile`, `documenter_profile`, `debugger_profile`, `analyst_profile`, `improver_profile`, `orchestrator_profile`, `evaluator_profile`. Domain skills: `coding-standards` and `security-review` use `reviewer_profile`; `backend-patterns` uses `architect_profile`; `frontend-patterns` uses `designer_profile`.

Add any of these to `model_profiles` to override; otherwise the IDE default is used.

---

## See Also

- [requirements/model_profiles.yaml](../requirements/model_profiles.yaml) – Example and placeholders
- [requirements/PROJECT_REQUIREMENTS.md](../requirements/PROJECT_REQUIREMENTS.md) – Model profile schema (section 8.4)
- [.cursor/rules/performance.mdc](../.cursor/rules/performance.mdc) – Context and MCP usage (model/resource selection)
