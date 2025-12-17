# Epic 5: Workflow Recommendation Engine Enhancement

## Epic Goal

Enhance the existing workflow recommendation system with an interactive CLI command that guides users through workflow selection, reducing cognitive load and preventing wrong workflow choices. This builds on the existing `WorkflowRecommender` class.

## Epic Description

### Existing System Context

- **Current relevant functionality**: TappsCodingAgents has `WorkflowRecommender` class (`tapps_agents/workflow/recommender.py`) that programmatically recommends workflows based on project detection. Workflow detection exists but lacks interactive CLI command
- **Technology stack**: Python 3.13+, Click CLI, existing workflow recommender, project detection
- **Integration points**: 
  - Existing `WorkflowRecommender` class
  - Project detection system (`tapps_agents/core/project_profile.py`)
  - CLI command system
  - Workflow executor

### Enhancement Details

- **What's being added/changed**: 
  - Create interactive CLI command `tapps-agents workflow-recommend`
  - Add interactive Q&A for ambiguous cases
  - Show time estimates and alternatives
  - Enhance recommendation message with comparisons
  - Add workflow selection confirmation
  - Integrate with existing `WorkflowRecommender`

- **How it integrates**: 
  - New CLI command uses existing `WorkflowRecommender` class
  - Interactive mode enhances programmatic recommendations
  - Works with existing project detection
  - Integrates with workflow executor for auto-loading
  - Aligns with BMAD's `*workflow-init` pattern

- **Success criteria**: 
  - Interactive CLI command guides users through workflow selection
  - Q&A handles ambiguous cases
  - Time estimates and alternatives shown
  - Recommendation includes comparison of options
  - Users can confirm or override recommendations

## Stories

1. **Story 5.1: Interactive CLI Command Implementation**
   - Create `workflow-recommend` CLI command
   - Implement interactive mode with prompts
   - Add non-interactive mode (programmatic)
   - Integrate with existing `WorkflowRecommender`
   - Acceptance criteria: CLI command created, interactive mode works, integrates with recommender

2. **Story 5.2: Interactive Q&A for Ambiguous Cases**
   - Detect ambiguous workflow selection scenarios
   - Implement Q&A prompts to clarify user intent
   - Add logic to refine recommendations based on answers
   - Handle edge cases (multiple valid workflows)
   - Acceptance criteria: Q&A detects ambiguity, prompts clarify intent, recommendations refined

3. **Story 5.3: Time Estimates & Alternatives Display**
   - Calculate time estimates for recommended workflows
   - Show alternative workflow options
   - Display comparison of workflows (time, complexity, use cases)
   - Format output for readability
   - Acceptance criteria: Time estimates shown, alternatives displayed, comparison clear

4. **Story 5.4: Recommendation Enhancement & Confirmation**
   - Enhance recommendation message with detailed reasoning
   - Add workflow selection confirmation prompt
   - Support workflow auto-loading after confirmation
   - Add option to override recommendation
   - Acceptance criteria: Recommendations detailed, confirmation works, auto-loading works, override supported

5. **Story 5.5: Testing & Documentation**
   - Add unit tests for interactive command
   - Test Q&A flow and recommendation logic
   - Document command usage and examples
   - Create workflow selection guide
   - Acceptance criteria: Comprehensive test coverage, documentation complete, examples provided

## Compatibility Requirements

- [x] Existing `WorkflowRecommender` API remains unchanged
- [x] Programmatic workflow recommendation continues to work
- [x] CLI command is additive (doesn't break existing functionality)
- [x] Workflow executor integration maintained
- [x] No breaking changes to workflow system

## Risk Mitigation

- **Primary Risk**: Interactive prompts may be too verbose
  - **Mitigation**: Configurable verbosity, non-interactive mode, clear defaults
- **Primary Risk**: Q&A may not handle all edge cases
  - **Mitigation**: Fallback to programmatic recommendation, extensible Q&A system
- **Primary Risk**: Time estimates may be inaccurate
  - **Mitigation**: Estimates are approximate, clearly labeled, based on historical data
- **Rollback Plan**: 
  - Remove CLI command to revert to programmatic only
  - Feature flag to disable interactive mode
  - Non-interactive mode always available

## Definition of Done

- [x] All stories completed with acceptance criteria met
- [x] Interactive CLI command implemented
- [x] Q&A handles ambiguous cases
- [x] Time estimates and alternatives displayed
- [x] Recommendation confirmation works
- [x] Comprehensive test coverage
- [x] Documentation complete (command guide, examples, workflow selection guide)
- [x] No regression in existing workflow recommendation
- [x] User experience improved (measured)

## Implementation Status

**Last Updated:** 2025-01-27

**Overall Status:** ✅ Completed

**Story Status:**
- Story 33.1 (CLI Command): ✅ Ready for Review - Implemented `workflow recommend` command
- Story 33.2 (Interactive Q&A): ✅ Ready for Review - Ambiguity detection and Q&A prompts implemented
- Story 33.3 (Time Estimates): ✅ Ready for Review - Time estimation and alternatives display implemented
- Story 33.4 (Confirmation): ✅ Ready for Review - Enhanced recommendations and confirmation/override implemented
- Story 33.5 (Testing & Docs): ✅ Ready for Review - Comprehensive tests and documentation created

**Implementation Summary:**
- ✅ CLI command `tapps-agents workflow recommend` created as subcommand
- ✅ Interactive and non-interactive modes supported
- ✅ Ambiguity detection (low confidence < 0.7 or many alternatives)
- ✅ Q&A prompts for clarifying questions (scope, time, documentation)
- ✅ Time estimates based on workflow track (5-15, 15-30, 30-60 minutes)
- ✅ Alternative workflows displayed
- ✅ Enhanced recommendation messages with confidence and reasoning
- ✅ Confirmation prompt with override option
- ✅ Auto-loading integration with WorkflowExecutor
- ✅ Comprehensive unit tests created
- ✅ User documentation guide created

**Files Created/Modified:**
- `tapps_agents/cli/parsers/top_level.py` - Added recommend subcommand parser
- `tapps_agents/cli/commands/top_level.py` - Implemented command handler with all features
- `tests/unit/cli/test_workflow_recommend.py` - Comprehensive unit tests
- `docs/WORKFLOW_RECOMMENDATION_GUIDE.md` - User documentation

**Notes:**
- Existing `WorkflowRecommender` class provides foundation (API unchanged)
- Interactive command enhances existing functionality (additive, no breaking changes)
- Aligns with BMAD's `*workflow-init` pattern for consistency
- Command uses `workflow recommend` (subcommand) rather than `workflow-recommend` (top-level) to match existing CLI structure

