# Beads Mandatory: Documentation and Init Updates

## Documentation Updated

1. **docs/BEADS_INTEGRATION.md**
   - Doctor and Init section: added `beads.required` to reported config; doctor fails when required-but-missing
   - Init: REQUIRED message when beads.required and .beads missing or bd not found
   - Init --reset: clarified that user config (including beads) is preserved

2. **docs/CONFIGURATION.md**
   - Doctor section: beads.required in status; fail when required-but-missing
   - Beads integration reference: added required option

3. **README.md**
   - Beads bullet: beads.required option to make Beads mandatory
   - Optional dependencies: beads required vs optional

4. **.cursor/rules/command-reference.mdc**
   - Init Beads support: beads.required and REQUIRED message
   - Doctor: beads.required in status; fail when required-but-missing

## Init Process Updates

**_print_next_steps** (after init completes):

- Loads config from project_root/.tapps-agents/config.yaml
- When beads.required is true:
  - bd not found: "REQUIRED: Beads (bd) is configured as required but bd was not found..."
  - .beads missing: "REQUIRED: Beads (bd) is configured as required. Run `bd init`..."
- When beads.required is false: existing optional/hint messages unchanged

## Init --reset

- No code changes: config.yaml is user data, not framework-managed
- Init --reset preserves .tapps-agents/config.yaml (and beads settings)
- Documentation updated to state this explicitly
