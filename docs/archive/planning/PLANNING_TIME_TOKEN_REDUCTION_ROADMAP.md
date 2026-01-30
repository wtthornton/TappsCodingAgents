# Planning Time & Token Reduction Optimization Roadmap

**Epic:** Performance Optimization - Planning Time & Token Efficiency
**Status:** Planning → Implementation
**Priority:** High
**Created:** 2026-01-29
**Owner:** TappsCodingAgents Team

---

## Executive Summary

This roadmap addresses critical performance bottlenecks in TappsCodingAgents' planning phase:
- **Planning time**: 8-10 minutes for Full SDLC (Steps 1-4)
- **Token consumption**: ~40K tokens (44% of 200K limit) before implementation
- **Documentation verbosity**: ~40 pages generated before code is written

**Goals:**
- **50-60% reduction** in planning time for simple tasks
- **30-50% reduction** in token consumption through optimization
- **6x speedup** in code review execution (60s → 10s)
- **Better user experience** with smart preset recommendations

---

## Impact Analysis

### Current State (Baseline)

| Metric | Full SDLC | Impact Area |
|--------|-----------|-------------|
| Planning Time (Steps 1-4) | 8-10 minutes | User wait time |
| Token Consumption | 40K tokens (44%) | Budget exhaustion |
| Documentation Pages | ~40 pages | Verbosity, duplication |
| mypy Execution | 60 seconds | Review step slowdown |
| Enhancement Phase | 2-3 minutes | All workflows |
| Expert Queries | No caching | Redundant API calls |

### Target State (Post-Optimization)

| Metric | Simple Tasks | Medium Tasks | Complex Tasks | Improvement |
|--------|--------------|--------------|---------------|-------------|
| Planning Time | 2-4 min | 5-7 min | 8-10 min | **-30-60%** |
| Token Consumption | 15-20K | 25-30K | 35-40K | **-30-50%** |
| Documentation | 15-20 pages | 25-30 pages | 35-40 pages | **-30-50%** |
| mypy Execution | 10 sec | 10 sec | 10 sec | **-83% (6x)** |
| Enhancement | 1-1.5 min | 2-2.5 min | 2-3 min | **-30-50%** |
| Expert Cache Hits | 40-60% | 40-60% | 40-60% | **New capability** |

---

## Implementation Phases

### **Phase 1: Quick Wins (Week 1-2)** ⚡

**Goal:** Immediate impact with minimal effort

#### 1.1 Token Budget Warnings System
**Priority:** High | **Effort:** 4-6 hours | **Impact:** Critical visibility

**Description:**
Add real-time token budget monitoring with threshold warnings.

**Implementation:**
```python
# tapps_agents/core/token_monitor.py

from dataclasses import dataclass
from typing import Literal

@dataclass
class TokenBudget:
    """Token budget tracking for workflows."""
    total: int = 200000  # Claude Sonnet 4.5 limit
    consumed: int = 0
    remaining: int = 200000

    @property
    def usage_percentage(self) -> float:
        """Calculate usage as percentage."""
        return (self.consumed / self.total) * 100

    def check_threshold(self) -> Literal["green", "yellow", "orange", "red"]:
        """Check current threshold level."""
        pct = self.usage_percentage
        if pct >= 90:
            return "red"      # Critical
        elif pct >= 75:
            return "orange"   # High
        elif pct >= 50:
            return "yellow"   # Warning
        else:
            return "green"    # OK

class TokenMonitor:
    """Monitor token usage and emit warnings."""

    def __init__(self, budget: TokenBudget):
        self.budget = budget
        self._last_threshold = "green"

    def update(self, tokens_consumed: int) -> dict:
        """Update token count and check thresholds."""
        self.budget.consumed += tokens_consumed
        self.budget.remaining = self.budget.total - self.budget.consumed

        current_threshold = self.budget.check_threshold()
        threshold_changed = current_threshold != self._last_threshold

        result = {
            "consumed": self.budget.consumed,
            "remaining": self.budget.remaining,
            "percentage": self.budget.usage_percentage,
            "threshold": current_threshold,
            "threshold_changed": threshold_changed,
            "message": self._get_threshold_message(current_threshold, threshold_changed)
        }

        self._last_threshold = current_threshold
        return result

    def _get_threshold_message(self, threshold: str, changed: bool) -> str | None:
        """Get warning message for threshold."""
        if not changed:
            return None

        messages = {
            "yellow": "⚠️  Token Budget: 50% consumed (100K remaining)",
            "orange": "🟠 Token Budget Warning: 75% consumed (50K remaining)",
            "red": "🔴 Token Budget Critical: 90% consumed (20K remaining)\n"
                   "   Consider saving checkpoint and resuming in new session."
        }
        return messages.get(threshold)
```

**Integration Points:**
- Workflow orchestrator (after each step)
- Simple Mode handler
- CLI command execution

**Testing:**
- Unit tests for threshold calculations
- Integration tests with workflow execution
- Mock token consumption scenarios

**Deliverables:**
- [ ] TokenMonitor class implementation
- [ ] Integration with workflow engine
- [ ] CLI output formatting
- [ ] Unit tests (≥85% coverage)
- [ ] Documentation update

**Success Criteria:**
- Warnings display at 50%, 75%, 90% thresholds
- Checkpoint suggestion at 90% threshold
- No false positives/negatives

---

#### 1.2 ENH-002: Scope mypy to Target File
**Priority:** High | **Effort:** 30 minutes | **Impact:** 6x speedup (60s → 10s)

**Description:**
Optimize mypy execution by scoping to target file only, eliminating unrelated project errors.

**Implementation:**
```python
# tapps_agents/agents/reviewer/tools/mypy_runner.py

class MypyRunner:
    """Execute mypy type checking with optimized scoping."""

    def run(self, file_path: str, show_errors_only: bool = True) -> MypyResult:
        """
        Run mypy on specific file.

        Args:
            file_path: Target file for type checking
            show_errors_only: Only show errors (no summary)

        Returns:
            MypyResult with errors and timing
        """
        cmd = ["mypy", file_path]

        if show_errors_only:
            cmd.append("--no-error-summary")

        # Performance optimization: skip cache check for single file
        cmd.append("--no-incremental")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # Fail fast
        )

        return MypyResult(
            file_path=file_path,
            errors=self._parse_errors(result.stdout),
            exit_code=result.returncode,
            execution_time=result.execution_time
        )
```

**Changes:**
1. Add `--no-error-summary` flag (remove unrelated output)
2. Scope to single file (not entire project)
3. Add `--no-incremental` for speed
4. Add 30-second timeout

**Deliverables:**
- [ ] Update MypyRunner implementation
- [ ] Update ReviewerAgent integration
- [ ] Performance benchmarks (before/after)
- [ ] Unit tests
- [ ] Documentation update

**Success Criteria:**
- mypy execution time ≤10 seconds (from 60s)
- Only target file errors shown
- No project-wide errors

---

#### 1.3 Document Workflow Presets Prominently
**Priority:** High | **Effort:** 2-3 hours | **Impact:** Immediate user guidance

**Description:**
Add prominent workflow preset documentation to CLAUDE.md and create selection guide.

**Updates:**

**CLAUDE.md Changes:**
```markdown
## Workflow Presets - Choose the Right Level

TappsCodingAgents provides **4 workflow presets** to match task complexity:

### ⚡ Minimal (2 steps, ~5 min, ~15K tokens)
**Best for:** Simple fixes, typos, documentation updates
```bash
@simple-mode *fix "description" --preset minimal
```
**Steps:** Implement → Test
**Use when:** Clear requirements, low risk, quick change

### ⚙️ Standard (4 steps, ~15 min, ~30K tokens) **[DEFAULT]**
**Best for:** Regular features, bug fixes, refactoring
```bash
@simple-mode *build "description" --preset standard
```
**Steps:** Plan → Implement → Review → Test
**Use when:** Most development tasks

### 🎯 Comprehensive (7 steps, ~45 min, ~60K tokens)
**Best for:** Complex features, API changes, security-sensitive code
```bash
@simple-mode *build "description" --preset comprehensive
```
**Steps:** Enhance → Analyze → Plan → Design → Implement → Review → Test
**Use when:** High complexity, multiple stakeholders, critical functionality

### 🏗️ Full SDLC (9 steps, ~2 hours, ~80K tokens)
**Best for:** Framework development, major architectural changes
```bash
@simple-mode *full "description"
```
**Steps:** Full → Comprehensive + Architecture + Security + Documentation
**Use when:** Modifying tapps_agents/ package, breaking changes

## Preset Selection Guide

| Task Type | Preset | Why |
|-----------|--------|-----|
| Fix typo | minimal | No planning needed |
| Add logging | minimal | Simple, low risk |
| Add validation | standard | Needs review & tests |
| New API endpoint | comprehensive | Design decisions needed |
| Refactor auth system | full-sdlc | Security-critical, architecture |
| Framework changes | full-sdlc | **MANDATORY** for tapps_agents/ |
```

**New File:** `docs/guides/workflow-preset-selection.md`

**Deliverables:**
- [ ] Update CLAUDE.md with preset guide
- [ ] Create workflow-preset-selection.md
- [ ] Update .cursor/rules/workflow-presets.mdc
- [ ] Add examples for each preset
- [ ] Update CLI help text

**Success Criteria:**
- Clear guidance on when to use each preset
- Examples for common scenarios
- Default behavior documented

---

### **Phase 2: Smart Optimization (Week 3-4)** 🧠

**Goal:** Intelligent task-based optimization

#### 2.1 Quick Enhancement Mode
**Priority:** High | **Effort:** 6-8 hours | **Impact:** 50% token reduction for simple tasks

**Description:**
Add fast-track enhancement mode that runs only stages 1-3 (skip deep analysis stages).

**Implementation:**
```python
# tapps_agents/agents/enhancer/agent.py

class EnhancerAgent:
    """Enhanced prompt generation with quick mode support."""

    def enhance(
        self,
        prompt: str,
        mode: Literal["full", "quick"] = "full",
        context: dict | None = None
    ) -> EnhancedPrompt:
        """
        Enhance prompt with configurable depth.

        Args:
            prompt: User's original prompt
            mode: "full" (all 7 stages) or "quick" (stages 1-3)
            context: Optional context

        Returns:
            Enhanced prompt result
        """
        if mode == "quick":
            stages = ["clarify", "enrich", "structure"]  # Stages 1-3
        else:
            stages = ["clarify", "enrich", "structure", "validate",
                     "optimize", "domain_enhance", "finalize"]  # All 7

        result = {"original": prompt, "stages": {}}

        for stage in stages:
            stage_result = self._run_stage(stage, prompt, context)
            result["stages"][stage] = stage_result
            prompt = stage_result["output"]  # Chain to next stage

        return EnhancedPrompt(
            original=result["original"],
            enhanced=prompt,
            stages=result["stages"],
            mode=mode,
            token_savings=self._calculate_savings(mode)
        )

    def _calculate_savings(self, mode: str) -> dict:
        """Calculate token savings for quick mode."""
        if mode == "quick":
            return {
                "stages_skipped": 4,
                "estimated_tokens_saved": 8000,  # ~2K per stage
                "time_saved_minutes": 1.5
            }
        return {"stages_skipped": 0, "estimated_tokens_saved": 0}
```

**CLI Integration:**
```bash
@simple-mode *build "description" --quick-enhance
tapps-agents simple-mode build --prompt "desc" --quick-enhance
```

**Deliverables:**
- [ ] Quick enhancement mode implementation
- [ ] CLI flag support (--quick-enhance)
- [ ] Token savings tracking
- [ ] Documentation update
- [ ] Unit tests (≥85% coverage)

**Success Criteria:**
- Quick mode 50% faster than full mode
- ~8K token savings for simple tasks
- Quality still meets minimum thresholds

---

#### 2.2 Smart Preset Recommendation
**Priority:** High | **Effort:** 4-6 hours | **Impact:** Prevents over-planning

**Description:**
Automatically suggest appropriate preset based on task analysis.

**Implementation:**
```python
# tapps_agents/workflow/preset_recommender.py

from dataclasses import dataclass
from typing import Literal

PresetType = Literal["minimal", "standard", "comprehensive", "full-sdlc"]

@dataclass
class PresetRecommendation:
    """Recommendation for workflow preset."""
    preset: PresetType
    confidence: float  # 0-1
    reasoning: list[str]
    complexity_score: float  # 1-10
    risk_score: float  # 1-10

class PresetRecommender:
    """Recommend workflow preset based on task analysis."""

    def recommend(self, prompt: str, file_context: dict | None = None) -> PresetRecommendation:
        """
        Analyze task and recommend preset.

        Args:
            prompt: User's task description
            file_context: Optional file/project context

        Returns:
            Preset recommendation with reasoning
        """
        complexity = self._analyze_complexity(prompt, file_context)
        risk = self._analyze_risk(prompt, file_context)

        # Decision logic
        if self._is_framework_change(file_context):
            return PresetRecommendation(
                preset="full-sdlc",
                confidence=1.0,
                reasoning=["Framework change detected (tapps_agents/)",
                          "Full SDLC mandatory for framework development"],
                complexity_score=complexity,
                risk_score=risk
            )

        if complexity >= 8 or risk >= 8:
            return PresetRecommendation(
                preset="comprehensive",
                confidence=0.9,
                reasoning=[f"High complexity ({complexity}/10)",
                          f"High risk ({risk}/10)",
                          "Design phase recommended"],
                complexity_score=complexity,
                risk_score=risk
            )

        if complexity <= 3 and risk <= 3:
            return PresetRecommendation(
                preset="minimal",
                confidence=0.85,
                reasoning=[f"Low complexity ({complexity}/10)",
                          f"Low risk ({risk}/10)",
                          "Simple change, minimal overhead"],
                complexity_score=complexity,
                risk_score=risk
            )

        # Default: standard
        return PresetRecommendation(
            preset="standard",
            confidence=0.8,
            reasoning=["Moderate complexity/risk",
                      "Standard workflow appropriate"],
            complexity_score=complexity,
            risk_score=risk
        )

    def _analyze_complexity(self, prompt: str, context: dict | None) -> float:
        """Score task complexity 1-10."""
        score = 5.0  # Baseline

        prompt_lower = prompt.lower()

        # Complexity indicators (increase score)
        if any(kw in prompt_lower for kw in ["architecture", "design", "refactor", "rewrite"]):
            score += 2
        if any(kw in prompt_lower for kw in ["multiple", "several", "integrate", "coordinate"]):
            score += 1
        if any(kw in prompt_lower for kw in ["new", "create", "build", "implement"]):
            score += 1

        # Simplicity indicators (decrease score)
        if any(kw in prompt_lower for kw in ["typo", "fix comment", "update doc", "add log"]):
            score -= 3
        if any(kw in prompt_lower for kw in ["simple", "quick", "small"]):
            score -= 1

        # File context
        if context:
            files_affected = context.get("files_affected", 1)
            if files_affected > 5:
                score += 2
            elif files_affected == 1:
                score -= 1

        return max(1.0, min(10.0, score))

    def _analyze_risk(self, prompt: str, context: dict | None) -> float:
        """Score task risk 1-10."""
        score = 5.0  # Baseline

        prompt_lower = prompt.lower()

        # Risk indicators
        if any(kw in prompt_lower for kw in ["security", "auth", "validation", "crypto"]):
            score += 3
        if any(kw in prompt_lower for kw in ["breaking", "migration", "deprecate"]):
            score += 2
        if any(kw in prompt_lower for kw in ["database", "api", "production"]):
            score += 1

        # Low risk indicators
        if any(kw in prompt_lower for kw in ["test", "doc", "comment", "log"]):
            score -= 2
        if any(kw in prompt_lower for kw in ["internal", "dev", "debug"]):
            score -= 1

        # File context
        if context and context.get("is_test_file"):
            score -= 2

        return max(1.0, min(10.0, score))

    def _is_framework_change(self, context: dict | None) -> bool:
        """Check if change affects framework (tapps_agents/)."""
        if not context:
            return False

        file_path = context.get("file_path", "")
        return "tapps_agents/" in file_path and not "/tests/" in file_path
```

**CLI Integration:**
```bash
# Auto-suggest preset
@simple-mode *build "description"  # Auto-detects and suggests
# Output: "Detected low complexity task. Suggesting --preset minimal"
```

**Deliverables:**
- [ ] PresetRecommender implementation
- [ ] Complexity & risk analysis
- [ ] CLI integration with suggestions
- [ ] Override capability (user can ignore)
- [ ] Unit tests (≥85% coverage)
- [ ] Documentation

**Success Criteria:**
- 80%+ accuracy in preset recommendations
- Clear reasoning provided for each suggestion
- User can override easily

---

#### 2.3 Lightweight SDLC Preset
**Priority:** High | **Effort:** 8-10 hours | **Impact:** 50% token reduction for medium tasks

**Description:**
Create new preset that combines requirements + design and skips architecture for medium-complexity tasks.

**Preset Definition:**
```yaml
# .tapps-agents/workflow-presets.yaml

lightweight:
  name: "Lightweight SDLC"
  description: "Streamlined SDLC for medium-complexity tasks"
  steps:
    - enhance:
        mode: "quick"  # Use quick enhancement
    - requirements:
        depth: "standard"
    - design:
        combine_with: "requirements"  # Combined step
        skip_architecture: true
    - implement:
        auto_validate: true
    - review:
        quick_mode: true
    - test:
        min_coverage: 75

  estimated_time: "30-45 minutes"
  estimated_tokens: "35-45K"

  use_when:
    - "Medium complexity (5-7/10)"
    - "Clear requirements"
    - "No major architecture changes"
    - "Single component changes"
```

**Implementation:**
```python
# tapps_agents/workflow/presets/lightweight.py

class LightweightSDLCPreset(WorkflowPreset):
    """Lightweight SDLC preset for medium-complexity tasks."""

    def get_steps(self) -> list[WorkflowStep]:
        """Get workflow steps for lightweight preset."""
        return [
            WorkflowStep(
                name="enhance",
                agent="enhancer",
                config={"mode": "quick"}  # Quick enhancement
            ),
            WorkflowStep(
                name="requirements",
                agent="analyst",
                config={"depth": "standard"}
            ),
            WorkflowStep(
                name="combined_design",  # Combined step
                agent="designer",
                config={
                    "include_requirements_summary": True,
                    "skip_architecture_deep_dive": True,
                    "focus": "api_design"
                }
            ),
            WorkflowStep(
                name="implement",
                agent="implementer",
                config={"auto_validate": True}
            ),
            WorkflowStep(
                name="review",
                agent="reviewer",
                config={"quick_mode": True}
            ),
            WorkflowStep(
                name="test",
                agent="tester",
                config={"min_coverage": 75}
            )
        ]

    def estimate_resources(self) -> dict:
        """Estimate time and token usage."""
        return {
            "time_minutes": 35,
            "tokens": 40000,
            "steps": 6
        }
```

**Deliverables:**
- [ ] Lightweight preset implementation
- [ ] Combined requirements+design step
- [ ] Quick review mode
- [ ] CLI integration
- [ ] Documentation
- [ ] Unit tests

**Success Criteria:**
- 50% faster than full SDLC
- 50% fewer tokens than full SDLC
- Quality meets minimum thresholds (≥70 overall)

---

### **Phase 3: Advanced Optimization (Week 5-8)** 🚀

**Goal:** Deep optimizations for token efficiency

#### 3.1 Delta Mode for Documentation
**Priority:** Medium | **Effort:** 8-10 hours | **Impact:** 20-30% token reduction

**Description:**
Reduce duplication by having later steps reference earlier documents instead of repeating content.

**Implementation:**
```python
# tapps_agents/workflow/delta_mode.py

from dataclasses import dataclass

@dataclass
class DeltaDocument:
    """Document in delta mode - references previous content."""
    step_name: str
    previous_steps: list[str]  # Steps this references
    new_content: dict  # Only new information
    references: dict  # References to previous steps

    def render(self, full_mode: bool = False) -> str:
        """
        Render document in delta or full mode.

        Args:
            full_mode: If True, expand all references

        Returns:
            Rendered markdown document
        """
        if full_mode:
            return self._render_full()
        else:
            return self._render_delta()

    def _render_delta(self) -> str:
        """Render in delta mode (references only)."""
        output = f"# {self.step_name}\n\n"

        # Show references
        if self.references:
            output += "## Previous Context\n\n"
            for step, ref in self.references.items():
                output += f"- See [{step}]({ref['path']}) for: {ref['summary']}\n"
            output += "\n"

        # Show only new content
        output += "## New Findings\n\n"
        output += self._format_new_content()

        return output

    def _render_full(self) -> str:
        """Render full document (all content)."""
        # Expand references and include all content
        pass

class DeltaModeManager:
    """Manage delta mode for workflow documentation."""

    def __init__(self):
        self.documents = {}  # step_name -> DeltaDocument

    def create_delta_document(
        self,
        step_name: str,
        content: dict,
        previous_steps: list[str]
    ) -> DeltaDocument:
        """
        Create delta document that references previous steps.

        Args:
            step_name: Current step name
            content: New content for this step
            previous_steps: Previous steps to reference

        Returns:
            Delta document
        """
        # Extract what's already in previous docs
        existing_content = self._extract_existing_content(previous_steps)

        # Calculate delta (what's new)
        new_content = self._calculate_delta(content, existing_content)

        # Create references
        references = self._create_references(previous_steps, content)

        doc = DeltaDocument(
            step_name=step_name,
            previous_steps=previous_steps,
            new_content=new_content,
            references=references
        )

        self.documents[step_name] = doc
        return doc

    def _calculate_delta(
        self,
        new: dict,
        existing: dict
    ) -> dict:
        """Calculate what content is actually new."""
        delta = {}

        for key, value in new.items():
            if key not in existing:
                delta[key] = value  # Completely new
            elif value != existing[key]:
                delta[key] = {
                    "changed_from": existing[key],
                    "changed_to": value,
                    "reason": "updated_based_on_analysis"
                }

        return delta

    def calculate_token_savings(self) -> dict:
        """Calculate token savings from delta mode."""
        total_tokens_full = sum(
            self._estimate_tokens(doc, full=True)
            for doc in self.documents.values()
        )

        total_tokens_delta = sum(
            self._estimate_tokens(doc, full=False)
            for doc in self.documents.values()
        )

        return {
            "full_mode_tokens": total_tokens_full,
            "delta_mode_tokens": total_tokens_delta,
            "tokens_saved": total_tokens_full - total_tokens_delta,
            "percentage_saved": ((total_tokens_full - total_tokens_delta) / total_tokens_full) * 100
        }
```

**Example Delta Document:**
```markdown
# Step 3: Architecture Design

## Previous Context
- See [Enhanced Prompt](docs/workflows/step1-enhancement.md) for: Requirements, constraints, technical stack
- See [Requirements Analysis](docs/workflows/step2-requirements.md) for: 7 functional requirements, 7 non-functional requirements, risk assessment

## New Findings

### Architecture Pattern Selected
**Decision:** Async Pipeline with Graceful Degradation

**Rationale:**
- Requirement FR-1 (parallel execution) → Async pipeline
- Requirement NFR-4 (reliability) → Graceful degradation
- Risk R-3 (Windows async issues) → Sequential fallback

**New Information:**
- Component diagram (see below)
- Sequence diagrams for success/timeout scenarios
- 5 Architecture Decision Records (ADRs)

### ADR-001: Two-Phase Execution
**Context:** Need to balance speed with reliability
**Decision:** Parallel first, sequential fallback
**Consequences:**
- (+) 2-3x speedup in normal case
- (+) 100% reliability through fallback
- (-) Slight complexity in error handling

[... only new content, no duplication ...]
```

**Deliverables:**
- [ ] DeltaModeManager implementation
- [ ] Delta document rendering
- [ ] Token savings calculator
- [ ] Integration with workflow engine
- [ ] CLI flag (--delta-mode)
- [ ] Documentation
- [ ] Unit tests (≥85% coverage)

**Success Criteria:**
- 20-30% token reduction in planning phase
- No loss of information
- Full mode still available on demand

---

#### 3.2 Checkpoint & Resume System
**Priority:** Medium | **Effort:** 2-3 weeks | **Impact:** Prevents token exhaustion

**Description:**
Save workflow state at each step, enabling pause/resume when token budget low.

**Implementation:**
```python
# tapps_agents/workflow/checkpoint.py

from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime

@dataclass
class WorkflowCheckpoint:
    """Workflow checkpoint for pause/resume."""
    checkpoint_id: str
    workflow_id: str
    workflow_type: str  # "full-sdlc", "standard", etc.

    # Progress tracking
    completed_steps: list[str]
    current_step: str
    pending_steps: list[str]

    # State
    workflow_context: dict
    step_results: dict  # step_name -> result

    # Resources
    tokens_consumed: int
    tokens_remaining: int
    time_elapsed_minutes: float

    # Metadata
    created_at: datetime
    checkpoint_reason: str  # "token_limit", "user_request", "error"

    def save(self, checkpoint_dir: Path) -> Path:
        """Save checkpoint to disk."""
        checkpoint_path = checkpoint_dir / f"{self.checkpoint_id}.json"

        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()

        checkpoint_path.write_text(json.dumps(data, indent=2))
        return checkpoint_path

    @classmethod
    def load(cls, checkpoint_path: Path) -> "WorkflowCheckpoint":
        """Load checkpoint from disk."""
        data = json.loads(checkpoint_path.read_text())
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

class CheckpointManager:
    """Manage workflow checkpoints."""

    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def create_checkpoint(
        self,
        workflow_state: dict,
        reason: str = "user_request"
    ) -> WorkflowCheckpoint:
        """
        Create checkpoint from current workflow state.

        Args:
            workflow_state: Current workflow state
            reason: Reason for checkpoint

        Returns:
            Checkpoint object
        """
        checkpoint_id = f"checkpoint-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        checkpoint = WorkflowCheckpoint(
            checkpoint_id=checkpoint_id,
            workflow_id=workflow_state["workflow_id"],
            workflow_type=workflow_state["workflow_type"],
            completed_steps=workflow_state["completed_steps"],
            current_step=workflow_state["current_step"],
            pending_steps=workflow_state["pending_steps"],
            workflow_context=workflow_state["context"],
            step_results=workflow_state["results"],
            tokens_consumed=workflow_state["tokens_consumed"],
            tokens_remaining=workflow_state["tokens_remaining"],
            time_elapsed_minutes=workflow_state["time_elapsed"],
            created_at=datetime.now(),
            checkpoint_reason=reason
        )

        path = checkpoint.save(self.checkpoint_dir)
        print(f"✅ Checkpoint saved: {path}")
        print(f"   Resume with: tapps-agents resume {checkpoint_id}")

        return checkpoint

    def resume_from_checkpoint(
        self,
        checkpoint_id: str
    ) -> dict:
        """
        Resume workflow from checkpoint.

        Args:
            checkpoint_id: Checkpoint to resume from

        Returns:
            Restored workflow state
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_path.exists():
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        checkpoint = WorkflowCheckpoint.load(checkpoint_path)

        print(f"📂 Resuming workflow from checkpoint")
        print(f"   Workflow: {checkpoint.workflow_type}")
        print(f"   Completed: {len(checkpoint.completed_steps)} steps")
        print(f"   Remaining: {len(checkpoint.pending_steps)} steps")
        print(f"   Tokens consumed: {checkpoint.tokens_consumed:,}")
        print(f"   Tokens remaining: {checkpoint.tokens_remaining:,}")

        return {
            "workflow_id": checkpoint.workflow_id,
            "workflow_type": checkpoint.workflow_type,
            "completed_steps": checkpoint.completed_steps,
            "current_step": checkpoint.current_step,
            "pending_steps": checkpoint.pending_steps,
            "context": checkpoint.workflow_context,
            "results": checkpoint.step_results,
            "tokens_consumed": checkpoint.tokens_consumed,
            "tokens_remaining": checkpoint.tokens_remaining,
            "time_elapsed": checkpoint.time_elapsed_minutes,
            "resumed_from_checkpoint": True,
            "checkpoint_id": checkpoint.checkpoint_id
        }

    def list_checkpoints(self) -> list[WorkflowCheckpoint]:
        """List all available checkpoints."""
        checkpoints = []
        for path in self.checkpoint_dir.glob("*.json"):
            checkpoint = WorkflowCheckpoint.load(path)
            checkpoints.append(checkpoint)

        return sorted(checkpoints, key=lambda c: c.created_at, reverse=True)
```

**CLI Integration:**
```bash
# Auto-checkpoint when token budget low
@simple-mode *full "description"
# Output at 90% tokens:
# 🔴 Token Budget Critical: 90% consumed (20K remaining)
# 🔖 Creating checkpoint... (checkpoint-20260129-143022)
# ✅ Checkpoint saved. Resume with: tapps-agents resume checkpoint-20260129-143022

# Resume from checkpoint
tapps-agents resume checkpoint-20260129-143022
# Output:
# 📂 Resuming workflow from checkpoint
#    Workflow: full-sdlc
#    Completed: 4/9 steps (enhance, requirements, architecture, design)
#    Remaining: 5 steps (implement, review, test, security, documentation)
#    Tokens consumed: 180,000
#    Starting fresh session with 200,000 tokens...
```

**Deliverables:**
- [ ] WorkflowCheckpoint dataclass
- [ ] CheckpointManager implementation
- [ ] Auto-checkpoint at 90% tokens
- [ ] Resume command (`tapps-agents resume`)
- [ ] List checkpoints command
- [ ] Documentation
- [ ] Unit tests (≥85% coverage)

**Success Criteria:**
- Checkpoints save all workflow state
- Resume continues exactly where left off
- No data loss during checkpoint/resume
- Works across different sessions

---

### **Phase 4: Long-Term Optimizations (Week 9-12)** 🔮

**Goal:** Advanced performance enhancements

#### 4.1 Cache Hit Detection for Expert Consultations
**Priority:** Medium | **Effort:** 1-2 weeks | **Impact:** 40-60% reduction in expert queries

**Description:**
Implement caching for expert consultations to avoid redundant queries within workflow.

**Implementation:**
```python
# tapps_agents/experts/cache.py

from dataclasses import dataclass
from typing import Any
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta

@dataclass
class CachedExpertResponse:
    """Cached expert consultation response."""
    query_hash: str
    domain: str
    query: str
    response: Any
    experts_consulted: list[str]
    timestamp: datetime
    ttl_hours: int = 24

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        expiry = self.timestamp + timedelta(hours=self.ttl_hours)
        return datetime.now() > expiry

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "query_hash": self.query_hash,
            "domain": self.domain,
            "query": self.query,
            "response": self.response,
            "experts_consulted": self.experts_consulted,
            "timestamp": self.timestamp.isoformat(),
            "ttl_hours": self.ttl_hours
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CachedExpertResponse":
        """Create from dict."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

class ExpertCache:
    """Cache for expert consultations."""

    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_hours = ttl_hours
        self._memory_cache = {}  # In-memory cache for current session

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "expirations": 0
        }

    def get(self, query: str, domain: str) -> CachedExpertResponse | None:
        """
        Get cached response for query.

        Args:
            query: Expert query
            domain: Domain name

        Returns:
            Cached response or None if not found/expired
        """
        query_hash = self._hash_query(query, domain)

        # Check memory cache first
        if query_hash in self._memory_cache:
            cached = self._memory_cache[query_hash]
            if not cached.is_expired:
                self.stats["hits"] += 1
                return cached
            else:
                self.stats["expirations"] += 1
                del self._memory_cache[query_hash]

        # Check disk cache
        cache_file = self.cache_dir / f"{query_hash}.json"
        if cache_file.exists():
            data = json.loads(cache_file.read_text())
            cached = CachedExpertResponse.from_dict(data)

            if not cached.is_expired:
                self._memory_cache[query_hash] = cached
                self.stats["hits"] += 1
                return cached
            else:
                self.stats["expirations"] += 1
                cache_file.unlink()  # Delete expired cache

        self.stats["misses"] += 1
        return None

    def put(
        self,
        query: str,
        domain: str,
        response: Any,
        experts_consulted: list[str]
    ) -> CachedExpertResponse:
        """
        Cache expert response.

        Args:
            query: Expert query
            domain: Domain name
            response: Expert response
            experts_consulted: List of experts consulted

        Returns:
            Cached response object
        """
        query_hash = self._hash_query(query, domain)

        cached = CachedExpertResponse(
            query_hash=query_hash,
            domain=domain,
            query=query,
            response=response,
            experts_consulted=experts_consulted,
            timestamp=datetime.now(),
            ttl_hours=self.ttl_hours
        )

        # Save to memory cache
        self._memory_cache[query_hash] = cached

        # Save to disk cache
        cache_file = self.cache_dir / f"{query_hash}.json"
        cache_file.write_text(json.dumps(cached.to_dict(), indent=2))

        return cached

    def _hash_query(self, query: str, domain: str) -> str:
        """Generate hash for query + domain."""
        content = f"{domain}:{query}".lower().strip()
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_queries = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_queries * 100) if total_queries > 0 else 0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "expirations": self.stats["expirations"],
            "total_queries": total_queries,
            "hit_rate_percentage": hit_rate,
            "memory_cache_size": len(self._memory_cache),
            "disk_cache_size": len(list(self.cache_dir.glob("*.json")))
        }

    def clear_expired(self) -> int:
        """Clear expired cache entries."""
        cleared = 0
        for cache_file in self.cache_dir.glob("*.json"):
            data = json.loads(cache_file.read_text())
            cached = CachedExpertResponse.from_dict(data)
            if cached.is_expired:
                cache_file.unlink()
                cleared += 1
        return cleared
```

**Integration with Expert System:**
```python
# tapps_agents/experts/base_expert.py

class BaseExpert:
    def __init__(self, cache: ExpertCache | None = None):
        self.cache = cache

    async def consult(self, query: str, domain: str, **kwargs) -> ExpertResponse:
        """Consult expert with caching."""
        # Check cache first
        if self.cache:
            cached = self.cache.get(query, domain)
            if cached:
                return ExpertResponse(
                    response=cached.response,
                    experts_consulted=cached.experts_consulted,
                    cache_hit=True,
                    timestamp=cached.timestamp
                )

        # Cache miss - consult experts
        response = await self._consult_experts(query, domain, **kwargs)

        # Cache the response
        if self.cache:
            self.cache.put(query, domain, response.data, response.experts_consulted)

        return response
```

**Deliverables:**
- [ ] ExpertCache implementation
- [ ] Integration with BaseExpert
- [ ] Cache statistics tracking
- [ ] Cache cleanup (expired entries)
- [ ] Configuration (TTL, cache dir)
- [ ] Documentation
- [ ] Unit tests (≥85% coverage)

**Success Criteria:**
- 40-60% cache hit rate after warmup
- No stale responses (TTL working)
- Performance improvement measurable

---

#### 4.2 Parallel Agent Execution
**Priority:** Low | **Effort:** 2-3 weeks | **Impact:** 20-30% time reduction

**Description:**
Execute independent workflow steps in parallel (e.g., security scan + documentation).

**Implementation:**
```python
# tapps_agents/workflow/parallel_executor.py

import asyncio
from dataclasses import dataclass
from typing import Any

@dataclass
class ParallelGroup:
    """Group of workflow steps that can run in parallel."""
    group_id: str
    steps: list[str]
    dependencies: list[str]  # Steps that must complete first

class ParallelWorkflowExecutor:
    """Execute workflow steps in parallel where possible."""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.parallel_groups = self._define_parallel_groups()

    def _define_parallel_groups(self) -> list[ParallelGroup]:
        """Define which steps can run in parallel."""
        return [
            # Group 1: Sequential planning steps
            ParallelGroup(
                group_id="planning",
                steps=["enhance", "requirements", "architecture", "design"],
                dependencies=[]
            ),

            # Group 2: Implementation (sequential)
            ParallelGroup(
                group_id="implementation",
                steps=["implement"],
                dependencies=["planning"]
            ),

            # Group 3: Validation (PARALLEL - independent!)
            ParallelGroup(
                group_id="validation",
                steps=["review", "test"],  # Can run in parallel
                dependencies=["implementation"]
            ),

            # Group 4: Final steps (PARALLEL - independent!)
            ParallelGroup(
                group_id="final",
                steps=["security", "documentation"],  # Can run in parallel
                dependencies=["validation"]
            )
        ]

    async def execute_workflow(
        self,
        workflow_steps: list[WorkflowStep],
        context: dict
    ) -> dict:
        """
        Execute workflow with parallelization.

        Args:
            workflow_steps: List of workflow steps
            context: Workflow context

        Returns:
            Workflow results
        """
        results = {}

        for group in self.parallel_groups:
            # Wait for dependencies
            await self._wait_for_dependencies(group.dependencies, results)

            # Get steps in this group
            group_steps = [s for s in workflow_steps if s.name in group.steps]

            if len(group_steps) > 1:
                # Execute in parallel
                print(f"⚡ Parallel execution: {', '.join(group.steps)}")
                group_results = await self._execute_parallel(group_steps, context)
            else:
                # Execute sequentially
                group_results = await self._execute_sequential(group_steps, context)

            results.update(group_results)

        return results

    async def _execute_parallel(
        self,
        steps: list[WorkflowStep],
        context: dict
    ) -> dict:
        """Execute steps in parallel."""
        tasks = [
            asyncio.create_task(self._execute_step(step, context))
            for step in steps
        ]

        step_results = await asyncio.gather(*tasks)

        return {
            step.name: result
            for step, result in zip(steps, step_results)
        }

    async def _execute_step(
        self,
        step: WorkflowStep,
        context: dict
    ) -> Any:
        """Execute single workflow step."""
        agent = self._get_agent(step.agent)
        return await agent.execute(step.config, context)
```

**Parallelization Opportunities:**

| Sequential Execution | Parallel Execution | Time Saved |
|---------------------|-------------------|------------|
| review (15 min) → test (8 min) | review ‖ test (15 min) | **8 min (35%)** |
| security (5 min) → docs (20 min) | security ‖ docs (20 min) | **5 min (20%)** |

**Total Estimated Savings:** 13 minutes (~20-30% of post-implementation time)

**Deliverables:**
- [ ] ParallelWorkflowExecutor implementation
- [ ] Parallel group definitions
- [ ] Dependency tracking
- [ ] Error handling for parallel failures
- [ ] Configuration (max_concurrent)
- [ ] Documentation
- [ ] Unit tests (≥85% coverage)

**Success Criteria:**
- Independent steps run in parallel
- Dependencies respected (no premature execution)
- 20-30% time reduction for validation phase

---

## Timeline & Resource Allocation

### Resource Requirements

| Phase | Duration | Team Size | Effort (hours) |
|-------|----------|-----------|----------------|
| Phase 1: Quick Wins | 2 weeks | 1 dev | 10-15 hours |
| Phase 2: Smart Optimization | 2 weeks | 1 dev | 20-25 hours |
| Phase 3: Advanced Optimization | 4 weeks | 1 dev | 40-50 hours |
| Phase 4: Long-Term | 4 weeks | 1-2 devs | 60-80 hours |
| **Total** | **12 weeks** | **1-2 devs** | **130-170 hours** |

### Gantt Chart (Simplified)

```
Week 1-2:  [Phase 1: Quick Wins         ]
Week 3-4:                                 [Phase 2: Smart Optimization]
Week 5-8:                                                              [Phase 3: Advanced      ]
Week 9-12:                                                                                      [Phase 4: Long-Term  ]
```

### Milestone Schedule

| Milestone | Date | Deliverables |
|-----------|------|--------------|
| M1: Quick Wins Complete | Week 2 | Token warnings, mypy optimization, preset docs |
| M2: Smart Optimization Complete | Week 4 | Quick enhance, smart recommender, lightweight preset |
| M3: Advanced Optimization Complete | Week 8 | Delta mode, checkpoint/resume |
| M4: Long-Term Complete | Week 12 | Expert cache, parallel execution |

---

## Testing Strategy

### Unit Tests
- **Coverage Target:** ≥85% for all new code
- **Test Files:** One test file per implementation file
- **Framework:** pytest with pytest-asyncio

### Integration Tests
- **Scenarios:**
  - End-to-end workflow with token monitoring
  - Checkpoint creation and resume
  - Cache hit/miss scenarios
  - Parallel execution with dependencies
  - Delta mode document generation

### Performance Tests
- **Benchmarks:**
  - Token consumption before/after (target: -30-50%)
  - Planning time before/after (target: -30-60%)
  - mypy execution time (target: 10s vs 60s)
  - Cache hit rate (target: 40-60%)
  - Parallel execution speedup (target: 20-30%)

### Acceptance Tests
- **User Stories:**
  - As a user, I see token warnings before running out
  - As a user, I can resume workflows from checkpoints
  - As a user, quick tasks complete 50% faster
  - As a user, I get smart preset recommendations

---

## Risk Assessment

### High Risks

#### Risk 1: Token Savings Less Than Expected
**Probability:** Medium | **Impact:** High

**Mitigation:**
- Measure baseline token usage before optimization
- A/B test delta mode vs full mode
- Conservative estimates (target 30%, expect 20%)
- Fallback to full mode if quality degrades

#### Risk 2: Cache Invalidation Issues
**Probability:** Medium | **Impact:** Medium

**Mitigation:**
- Short TTL (24 hours)
- Cache versioning (invalidate on expert KB updates)
- Manual cache clear command
- Disable cache flag for critical workflows

### Medium Risks

#### Risk 3: Parallel Execution Bugs
**Probability:** Medium | **Impact:** Medium

**Mitigation:**
- Extensive dependency testing
- Fallback to sequential on errors
- Gradual rollout (opt-in first)
- Monitoring and telemetry

#### Risk 4: User Confusion with Checkpoints
**Probability:** Low | **Impact:** Medium

**Mitigation:**
- Clear documentation
- Auto-checkpoint messaging
- Easy resume commands
- Checkpoint management UI

---

## Success Metrics & KPIs

### Primary KPIs

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Planning Time (Simple)** | 8-10 min | 2-4 min | **-60-75%** |
| **Planning Time (Medium)** | 8-10 min | 5-7 min | **-30-50%** |
| **Token Consumption (Simple)** | 40K | 15-20K | **-50-63%** |
| **Token Consumption (Medium)** | 40K | 25-30K | **-25-38%** |
| **mypy Execution** | 60s | 10s | **-83% (6x)** |
| **Cache Hit Rate** | 0% | 40-60% | **+40-60%** |

### Secondary KPIs

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| User Adoption (preset usage) | 80%+ | Analytics tracking |
| Quality Score (unchanged) | ≥75 | Automated quality tools |
| User Satisfaction | ≥4.5/5 | User surveys |
| Token Exhaustion Rate | <5% | Checkpoint usage tracking |

---

## Documentation Plan

### User Documentation

1. **Workflow Preset Guide** (docs/guides/workflow-presets.md)
   - When to use each preset
   - Examples for common scenarios
   - Effort/token estimates

2. **Token Budget Guide** (docs/guides/token-budget-management.md)
   - How token monitoring works
   - Checkpoint/resume workflow
   - Best practices

3. **Performance Tips** (docs/guides/performance-optimization.md)
   - Quick enhancement mode
   - Delta mode benefits
   - Cache usage

### Developer Documentation

1. **Architecture: Optimization Systems** (docs/architecture/performance-optimization.md)
   - Token monitoring design
   - Checkpoint system architecture
   - Cache implementation
   - Parallel execution design

2. **API Reference** (docs/api/performance-apis.md)
   - TokenMonitor API
   - CheckpointManager API
   - ExpertCache API
   - ParallelWorkflowExecutor API

---

## Rollout Plan

### Phase 1 Rollout (Week 2)
- **Features:** Token warnings, mypy optimization, preset docs
- **Rollout:** Full release (low risk)
- **Communication:** Release notes, blog post

### Phase 2 Rollout (Week 4)
- **Features:** Quick enhance, smart recommender, lightweight preset
- **Rollout:** Beta flag (opt-in), then full release
- **Communication:** User guide updates, examples

### Phase 3 Rollout (Week 8)
- **Features:** Delta mode, checkpoint/resume
- **Rollout:** Feature flags (configurable), gradual rollout
- **Communication:** Documentation, video tutorial

### Phase 4 Rollout (Week 12)
- **Features:** Expert cache, parallel execution
- **Rollout:** Beta testing (2 weeks), then full release
- **Communication:** Performance benchmarks, case studies

---

## Post-Implementation Review

### Week 13: Performance Analysis
- Measure actual vs predicted improvements
- User feedback collection
- Bug reports analysis
- Documentation gaps

### Week 14: Optimization Round 2
- Address issues found in Week 13
- Fine-tune parameters (TTL, thresholds, etc.)
- Additional optimizations if needed

### Week 15: Final Documentation
- Update all documentation with learnings
- Create video tutorials
- Blog post: "How We Reduced Planning Time by 60%"

---

## Conclusion

This roadmap provides a **comprehensive plan for reducing planning time and token consumption** in TappsCodingAgents:

**Expected Outcomes:**
- ✅ **50-60% faster** planning for simple tasks
- ✅ **30-50% token savings** through optimization
- ✅ **6x speedup** in code review (mypy)
- ✅ **Better UX** with smart recommendations
- ✅ **No token exhaustion** with checkpoint/resume

**Timeline:** 12 weeks (3 months)
**Effort:** 130-170 hours (1-2 developers)
**Priority:** High (addresses critical performance bottlenecks)

**Next Steps:**
1. ✅ Review and approve roadmap
2. ✅ Create GitHub issues for Phase 1
3. ✅ Assign Phase 1 to sprint
4. ✅ Begin implementation with token warnings

---

**Document Status:** ✅ COMPLETE - Ready for Implementation
**Created:** 2026-01-29
**Last Updated:** 2026-01-29
**Owner:** TappsCodingAgents Team
**Approval Status:** Pending Review
