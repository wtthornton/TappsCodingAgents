# ENH-001: Workflow Enforcement System - API Specification

**Version:** 1.0.0
**Date:** 2026-01-29
**Type:** Python Internal API

---

## API Contracts

### 1. WorkflowEnforcer

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

WorkflowType = Literal["*build", "*fix", "*refactor", "*review"]

@dataclass
class EnforcementResult:
    """Result of enforcement check."""
    action: Literal["block", "warn", "allow"]
    workflow: Optional[WorkflowType]
    message: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)

class WorkflowEnforcer:
    def intercept_code_edit(
        self,
        file_path: Path,
        user_intent: str,
        is_new_file: bool = False,
        skip_enforcement: bool = False
    ) -> EnforcementResult:
        """
        Intercept code edit and enforce workflow policy.

        Args:
            file_path: Target file path
            user_intent: User's intent/description
            is_new_file: True if creating new file
            skip_enforcement: True to bypass enforcement

        Returns:
            EnforcementResult

        Performance:
            - Latency: <50ms (p95)
        """
```

### 2. IntentDetector

```python
class IntentDetector:
    def detect_workflow(self, user_intent: str) -> tuple[WorkflowType, float]:
        """
        Detect workflow type from user intent.

        Args:
            user_intent: User's description

        Returns:
            (workflow_type, confidence_0_100)

        Performance:
            - Latency: <5ms
        """
```

### 3. MessageFormatter

```python
class MessageFormatter:
    def format_blocking_message(
        self,
        workflow: WorkflowType,
        user_intent: str,
        file_path: Path,
        confidence: float
    ) -> str:
        """Format blocking message with benefits and examples."""
```

### 4. EnforcementConfig

```python
@dataclass
class EnforcementConfig:
    mode: Literal["blocking", "warning", "silent"] = "blocking"
    confidence_threshold: float = 60.0
    suggest_workflows: bool = True
    block_direct_edits: bool = True

    @classmethod
    def from_config_file(cls, config_path: Optional[Path] = None) -> "EnforcementConfig":
        """Load from .tapps-agents/config.yaml"""
```

**API spec created**
