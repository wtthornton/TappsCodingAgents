"""
Feedback analyzer for prompt optimization.

Analyzes collected feedback and correlates with prompt versions.
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from .feedback_collector import FeedbackCollector

logger = logging.getLogger(__name__)


class FeedbackAnalyzer:
    """
    Analyzes feedback to identify patterns for prompt optimization.
    
    Correlates feedback with prompt versions and identifies successful patterns.
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize feedback analyzer.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.feedback_collector = FeedbackCollector(self.project_root)

    def analyze_feedback(
        self, prompt_version_id: str | None = None, agent_name: str | None = None
    ) -> dict[str, Any]:
        """
        Analyze feedback for patterns.
        
        Args:
            prompt_version_id: Optional filter by prompt version
            agent_name: Optional filter by agent
            
        Returns:
            Analysis results dictionary
        """
        feedback_records = self.feedback_collector.list_recent_feedback(
            agent_name=agent_name, limit=1000
        )
        
        if prompt_version_id:
            feedback_records = [
                f for f in feedback_records if f.prompt_version_id == prompt_version_id
            ]
        
        # Calculate acceptance rate
        total = len(feedback_records)
        accepted = sum(1 for f in feedback_records if f.accepted)
        acceptance_rate = accepted / total if total > 0 else 0.0
        
        # Analyze by agent
        by_agent: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "accepted": 0})
        for record in feedback_records:
            by_agent[record.agent_name]["total"] += 1
            if record.accepted:
                by_agent[record.agent_name]["accepted"] += 1
        
        # Analyze by command
        by_command: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "accepted": 0})
        for record in feedback_records:
            by_command[record.command]["total"] += 1
            if record.accepted:
                by_command[record.command]["accepted"] += 1
        
        return {
            "total_feedback": total,
            "accepted_count": accepted,
            "rejected_count": total - accepted,
            "acceptance_rate": acceptance_rate,
            "by_agent": {
                agent: {
                    "acceptance_rate": stats["accepted"] / stats["total"] if stats["total"] > 0 else 0.0,
                    **stats,
                }
                for agent, stats in by_agent.items()
            },
            "by_command": {
                command: {
                    "acceptance_rate": stats["accepted"] / stats["total"] if stats["total"] > 0 else 0.0,
                    **stats,
                }
                for command, stats in by_command.items()
            },
        }

    def correlate_with_prompts(
        self, prompt_versions: list[str]
    ) -> dict[str, Any]:
        """
        Correlate feedback with prompt versions.
        
        Args:
            prompt_versions: List of prompt version IDs
            
        Returns:
            Correlation results
        """
        correlations: dict[str, dict[str, Any]] = {}
        
        for version_id in prompt_versions:
            analysis = self.analyze_feedback(prompt_version_id=version_id)
            correlations[version_id] = {
                "acceptance_rate": analysis["acceptance_rate"],
                "total_feedback": analysis["total_feedback"],
            }
        
        return correlations

    def identify_successful_patterns(self) -> list[dict[str, Any]]:
        """
        Identify patterns in successful vs. failed interactions.
        
        Returns:
            List of identified patterns
        """
        feedback_records = self.feedback_collector.list_recent_feedback(limit=1000)
        
        # Group by acceptance
        successful = [f for f in feedback_records if f.accepted]
        failed = [f for f in feedback_records if not f.accepted]
        
        patterns = []
        
        # Pattern: Successful commands
        successful_commands = defaultdict(int)
        for record in successful:
            successful_commands[record.command] += 1
        
        failed_commands = defaultdict(int)
        for record in failed:
            failed_commands[record.command] += 1
        
        # Identify commands with high success rate
        all_commands = set(successful_commands.keys()) | set(failed_commands.keys())
        for command in all_commands:
            success_count = successful_commands.get(command, 0)
            fail_count = failed_commands.get(command, 0)
            total = success_count + fail_count
            
            if total >= 10:  # Minimum samples
                success_rate = success_count / total
                if success_rate > 0.7:
                    patterns.append({
                        "type": "successful_command",
                        "command": command,
                        "success_rate": success_rate,
                        "sample_size": total,
                    })
        
        return patterns

