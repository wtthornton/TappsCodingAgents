"""
Clawdbot Integration for TappsCodingAgents

Provides a simplified interface for AI assistants (like Clawdbot/Claude) to use
TappsCodingAgents tools directly without going through Cursor IDE.

Features:
- Code scoring with objective metrics
- Domain detection from code/prompts
- Expert consultation
- Outcome tracking for learning across sessions

Usage:
    from tapps_agents.integrations.clawdbot import ClawdbotIntegration
    
    bot = ClawdbotIntegration(project_root="/path/to/project")
    
    # Score code
    result = await bot.score_file("src/auth.py")
    
    # Detect domains
    domains = await bot.detect_domains("Implement OAuth2 refresh token flow")
    
    # Consult an expert
    advice = await bot.consult_expert("security", "Best practices for token storage?")
    
    # Track outcome
    await bot.track_outcome(
        task_id="task-123",
        task_type="implement",
        success=True,
        iterations=1,
        notes="First-pass success"
    )
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ScoreResult:
    """Result of code scoring."""
    file_path: str
    overall_score: float
    complexity: float
    security: float
    maintainability: float
    linting: float
    type_checking: float
    passed: bool
    threshold: float
    issues: list[str]
    timestamp: str


@dataclass
class DomainResult:
    """Result of domain detection."""
    domains: list[str]
    primary_language: str | None
    confidence: float
    signals: list[str]


@dataclass
class OutcomeRecord:
    """Record of a task outcome for learning."""
    task_id: str
    task_type: str  # implement, review, fix, test, etc.
    timestamp: str
    success: bool
    iterations: int
    experts_consulted: list[str]
    scores_before: dict[str, float] | None
    scores_after: dict[str, float] | None
    notes: str


class ClawdbotIntegration:
    """
    Integration layer for Clawdbot to use TappsCodingAgents.
    
    Designed for AI assistants that want to:
    - Verify their code with objective metrics
    - Detect relevant domains for a task
    - Consult domain experts
    - Track and learn from outcomes
    """
    
    def __init__(self, project_root: Path | str | None = None):
        """
        Initialize Clawdbot integration.
        
        Args:
            project_root: Root directory of the project (defaults to cwd)
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config_dir = self.project_root / ".tapps-agents"
        self.outcomes_dir = self.config_dir / "outcomes"
        self.outcomes_dir.mkdir(parents=True, exist_ok=True)
        
        # Track session state
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_task: str | None = None
        self._scores_before: dict[str, float] | None = None
    
    async def score_file(self, file_path: str | Path) -> ScoreResult:
        """
        Score a file using the TappsCodingAgents reviewer.
        
        Args:
            file_path: Path to the file to score (relative to project_root)
            
        Returns:
            ScoreResult with metrics and pass/fail status
        """
        from ..agents.reviewer import ReviewerAgent
        
        full_path = self.project_root / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")
        
        reviewer = ReviewerAgent(project_root=self.project_root)
        
        try:
            # Run the scoring
            result = await reviewer.score_file(str(full_path))
            
            # Extract scores
            scores = result.get("scores", {})
            threshold = result.get("threshold", 70.0)
            overall = result.get("overall_score", 0.0)
            
            # Collect issues
            issues = []
            for issue in result.get("linting_issues", []):
                issues.append(f"[LINT] {issue}")
            for issue in result.get("type_issues", []):
                issues.append(f"[TYPE] {issue}")
            for issue in result.get("security_issues", []):
                issues.append(f"[SEC] {issue}")
            
            return ScoreResult(
                file_path=str(file_path),
                overall_score=overall,
                complexity=scores.get("complexity_score", 0.0),
                security=scores.get("security_score", 0.0),
                maintainability=scores.get("maintainability_score", 0.0),
                linting=scores.get("linting_score", 0.0),
                type_checking=scores.get("type_checking_score", 0.0),
                passed=overall >= threshold,
                threshold=threshold,
                issues=issues[:20],  # Limit to first 20 issues
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            raise
    
    async def detect_domains(
        self, 
        prompt: str | None = None,
        scan_project: bool = True
    ) -> DomainResult:
        """
        Detect relevant domains from a prompt and/or project structure.
        
        Args:
            prompt: Optional prompt/task description to analyze
            scan_project: Whether to scan project structure for domains
            
        Returns:
            DomainResult with detected domains and confidence
        """
        from ..experts.domain_detector import DomainStackDetector
        from ..experts.adaptive_domain_detector import AdaptiveDomainDetector
        
        domains = []
        signals = []
        confidence = 0.0
        primary_language = None
        
        # Scan project structure
        if scan_project:
            detector = DomainStackDetector(project_root=self.project_root)
            result = detector.detect()
            
            primary_language = result.primary_language
            
            for domain_mapping in result.detected_domains:
                domains.append(domain_mapping.domain)
                signals.append(f"[PROJECT] {domain_mapping.reasoning}")
                confidence = max(confidence, domain_mapping.confidence)
        
        # Analyze prompt for additional domains
        if prompt:
            adaptive = AdaptiveDomainDetector()
            suggestions = await adaptive.detect_domains(prompt=prompt)
            
            for suggestion in suggestions:
                if suggestion.domain not in domains:
                    domains.append(suggestion.domain)
                evidence_str = ", ".join(suggestion.evidence[:3]) if suggestion.evidence else suggestion.source
                signals.append(f"[PROMPT] {suggestion.domain}: {evidence_str}")
                confidence = max(confidence, suggestion.confidence)
        
        return DomainResult(
            domains=domains,
            primary_language=primary_language,
            confidence=confidence,
            signals=signals
        )
    
    async def consult_expert(
        self, 
        domain: str, 
        question: str,
        context: str | None = None
    ) -> dict[str, Any]:
        """
        Consult a domain expert for guidance.
        
        Args:
            domain: Domain to consult (e.g., "security", "performance", "testing")
            question: The question to ask
            context: Optional code or context for the question
            
        Returns:
            Dictionary with expert advice, confidence, and sources
        """
        from ..experts import ExpertRegistry, SimpleKnowledgeBase
        
        registry = ExpertRegistry(project_root=self.project_root)
        
        # Get relevant experts for this domain
        experts = registry.get_experts_for_domain(domain)
        
        if not experts:
            return {
                "advice": f"No experts configured for domain: {domain}",
                "confidence": 0.0,
                "sources": [],
                "experts_consulted": []
            }
        
        # Query knowledge base
        kb_dir = self.config_dir / "knowledge" / domain
        advice_parts = []
        sources = []
        
        if kb_dir.exists():
            kb = SimpleKnowledgeBase(kb_dir)
            chunks = kb.search(question, top_k=3)
            
            for chunk in chunks:
                advice_parts.append(chunk.content)
                sources.append(chunk.source)
        
        # Also check built-in knowledge
        from ..experts.knowledge import KNOWLEDGE_BASE_DIR
        builtin_kb_dir = KNOWLEDGE_BASE_DIR / domain
        
        if builtin_kb_dir.exists():
            kb = SimpleKnowledgeBase(builtin_kb_dir)
            chunks = kb.search(question, top_k=3)
            
            for chunk in chunks:
                advice_parts.append(chunk.content)
                sources.append(f"[builtin] {chunk.source}")
        
        return {
            "advice": "\n\n---\n\n".join(advice_parts) if advice_parts else "No specific guidance found.",
            "confidence": 0.7 if advice_parts else 0.3,
            "sources": sources,
            "experts_consulted": [e.expert_id for e in experts],
            "domain": domain,
            "question": question
        }
    
    def start_task(self, task_id: str, task_type: str) -> None:
        """
        Start tracking a new task.
        
        Call this before starting work, then call complete_task() when done.
        
        Args:
            task_id: Unique identifier for this task
            task_type: Type of task (implement, review, fix, test, etc.)
        """
        self._current_task = task_id
        self._task_type = task_type
        self._task_start = datetime.now()
        self._experts_consulted: list[str] = []
        self._scores_before = None
        logger.info(f"Started task: {task_id} ({task_type})")
    
    async def complete_task(
        self,
        success: bool,
        iterations: int = 1,
        notes: str = "",
        scores_after: dict[str, float] | None = None
    ) -> OutcomeRecord:
        """
        Complete the current task and record the outcome.
        
        Args:
            success: Whether the task was successful
            iterations: Number of iterations/attempts
            notes: Any notes about the outcome
            scores_after: Optional final scores
            
        Returns:
            OutcomeRecord that was saved
        """
        if not self._current_task:
            raise ValueError("No task started. Call start_task() first.")
        
        record = OutcomeRecord(
            task_id=self._current_task,
            task_type=self._task_type,
            timestamp=datetime.now().isoformat(),
            success=success,
            iterations=iterations,
            experts_consulted=self._experts_consulted,
            scores_before=self._scores_before,
            scores_after=scores_after,
            notes=notes
        )
        
        # Save to disk
        await self._save_outcome(record)
        
        # Reset state
        self._current_task = None
        self._scores_before = None
        self._experts_consulted = []
        
        return record
    
    async def track_outcome(
        self,
        task_id: str,
        task_type: str,
        success: bool,
        iterations: int = 1,
        experts_consulted: list[str] | None = None,
        scores_before: dict[str, float] | None = None,
        scores_after: dict[str, float] | None = None,
        notes: str = ""
    ) -> OutcomeRecord:
        """
        Track a task outcome directly (without start_task/complete_task).
        
        Args:
            task_id: Unique identifier for this task
            task_type: Type of task (implement, review, fix, test, etc.)
            success: Whether the task was successful
            iterations: Number of iterations/attempts
            experts_consulted: List of expert IDs consulted
            scores_before: Optional initial scores
            scores_after: Optional final scores
            notes: Any notes about the outcome
            
        Returns:
            OutcomeRecord that was saved
        """
        record = OutcomeRecord(
            task_id=task_id,
            task_type=task_type,
            timestamp=datetime.now().isoformat(),
            success=success,
            iterations=iterations,
            experts_consulted=experts_consulted or [],
            scores_before=scores_before,
            scores_after=scores_after,
            notes=notes
        )
        
        await self._save_outcome(record)
        return record
    
    async def _save_outcome(self, record: OutcomeRecord) -> None:
        """Save an outcome record to disk."""
        # Use date-based files for easy querying
        date_str = datetime.now().strftime("%Y-%m-%d")
        outcomes_file = self.outcomes_dir / f"outcomes_{date_str}.jsonl"
        
        with open(outcomes_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record)) + "\n")
        
        logger.info(f"Saved outcome: {record.task_id} (success={record.success})")
    
    def get_outcomes(
        self, 
        days: int = 30,
        task_type: str | None = None
    ) -> list[OutcomeRecord]:
        """
        Get historical outcomes for analysis.
        
        Args:
            days: Number of days to look back
            task_type: Optional filter by task type
            
        Returns:
            List of OutcomeRecords
        """
        outcomes = []
        
        for outcome_file in self.outcomes_dir.glob("outcomes_*.jsonl"):
            try:
                with open(outcome_file, encoding="utf-8") as f:
                    for line in f:
                        data = json.loads(line)
                        record = OutcomeRecord(**data)
                        
                        if task_type and record.task_type != task_type:
                            continue
                        
                        outcomes.append(record)
            except Exception as e:
                logger.warning(f"Error reading {outcome_file}: {e}")
        
        return outcomes
    
    def get_success_rate(self, task_type: str | None = None, days: int = 30) -> float:
        """
        Calculate first-pass success rate.
        
        Args:
            task_type: Optional filter by task type
            days: Number of days to look back
            
        Returns:
            Success rate as a float (0.0 to 1.0)
        """
        outcomes = self.get_outcomes(days=days, task_type=task_type)
        
        if not outcomes:
            return 0.0
        
        first_pass_successes = sum(
            1 for o in outcomes 
            if o.success and o.iterations == 1
        )
        
        return first_pass_successes / len(outcomes)
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get overall statistics.
        
        Returns:
            Dictionary with stats about outcomes, success rates, etc.
        """
        outcomes = self.get_outcomes(days=30)
        
        if not outcomes:
            return {
                "total_tasks": 0,
                "success_rate": 0.0,
                "first_pass_rate": 0.0,
                "avg_iterations": 0.0,
                "by_type": {}
            }
        
        successes = sum(1 for o in outcomes if o.success)
        first_pass = sum(1 for o in outcomes if o.success and o.iterations == 1)
        total_iterations = sum(o.iterations for o in outcomes)
        
        # Group by type
        by_type: dict[str, dict[str, Any]] = {}
        for o in outcomes:
            if o.task_type not in by_type:
                by_type[o.task_type] = {"total": 0, "success": 0, "first_pass": 0}
            by_type[o.task_type]["total"] += 1
            if o.success:
                by_type[o.task_type]["success"] += 1
            if o.success and o.iterations == 1:
                by_type[o.task_type]["first_pass"] += 1
        
        return {
            "total_tasks": len(outcomes),
            "success_rate": successes / len(outcomes),
            "first_pass_rate": first_pass / len(outcomes),
            "avg_iterations": total_iterations / len(outcomes),
            "by_type": by_type
        }
