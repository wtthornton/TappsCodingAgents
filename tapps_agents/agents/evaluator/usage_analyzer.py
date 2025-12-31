"""
Usage Analyzer - Analyzes command usage patterns and statistics.
"""

from typing import Any


class UsageAnalyzer:
    """
    Analyzes command usage patterns and statistics.
    
    Tracks:
    - Total commands executed
    - CLI vs Cursor Skills vs Simple Mode usage
    - Individual agent usage frequency
    - Command success/failure rates
    - Usage gaps (intended vs actual)
    """

    def analyze_usage(
        self,
        workflow_state: dict[str, Any] | None = None,
        cli_logs: list[dict] | None = None,
        runtime_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Analyze command usage patterns.
        
        Args:
            workflow_state: Workflow execution state (if available)
            cli_logs: CLI execution logs (if available)
            runtime_data: Runtime analysis data (if available)
        
        Returns:
            Dictionary with usage statistics and analysis
        """
        # Collect all commands from data sources
        commands = self._collect_commands(workflow_state, cli_logs, runtime_data)
        
        # Calculate statistics
        stats = self.calculate_statistics(commands)
        
        # Identify gaps
        gaps = self.identify_gaps(stats)
        
        return {
            "statistics": stats,
            "gaps": gaps,
            "recommendations": self._generate_recommendations(stats, gaps)
        }

    def _collect_commands(
        self,
        workflow_state: dict[str, Any] | None,
        cli_logs: list[dict] | None,
        runtime_data: dict[str, Any] | None
    ) -> list[dict]:
        """Collect commands from all data sources."""
        commands = []
        
        # Extract from workflow state
        if workflow_state:
            steps = workflow_state.get("step_executions", [])
            for step in steps:
                commands.append({
                    "command": step.get("action", ""),
                    "agent": step.get("agent", ""),
                    "invocation_method": "workflow",
                    "success": step.get("success", True),
                    "workflow_id": workflow_state.get("workflow_id"),
                })
        
        # Add CLI logs if available
        if cli_logs:
            commands.extend(cli_logs)
        
        # Add runtime data if available
        if runtime_data:
            runtime_commands = runtime_data.get("commands", [])
            commands.extend(runtime_commands)
        
        return commands

    def calculate_statistics(self, commands: list[dict]) -> dict[str, Any]:
        """
        Calculate usage statistics from command list.
        
        Returns:
            Dictionary with usage statistics
        """
        if not commands:
            return {
                "total_commands": 0,
                "cli_commands": 0,
                "cursor_skills": 0,
                "simple_mode": 0,
                "agent_usage": {},
                "command_success_rate": 0.0,
                "most_used_agents": [],
                "least_used_agents": [],
            }
        
        total = len(commands)
        cli_count = sum(1 for c in commands if c.get("invocation_method") == "cli")
        skills_count = sum(1 for c in commands if c.get("invocation_method") == "cursor_skill")
        simple_mode_count = sum(1 for c in commands if c.get("invocation_method") == "simple_mode")
        
        # Agent usage frequency
        agent_usage: dict[str, int] = {}
        for cmd in commands:
            agent = cmd.get("agent", "unknown")
            agent_usage[agent] = agent_usage.get(agent, 0) + 1
        
        # Success rate
        successful = sum(1 for c in commands if c.get("success", True))
        success_rate = (successful / total) if total > 0 else 0.0
        
        # Most/least used agents
        sorted_agents = sorted(agent_usage.items(), key=lambda x: x[1], reverse=True)
        most_used = [agent for agent, _ in sorted_agents[:5]]
        least_used = [agent for agent, _ in sorted_agents[-5:]] if len(sorted_agents) > 5 else []
        
        return {
            "total_commands": total,
            "cli_commands": cli_count,
            "cursor_skills": skills_count,
            "simple_mode": simple_mode_count,
            "agent_usage": agent_usage,
            "command_success_rate": success_rate,
            "most_used_agents": most_used,
            "least_used_agents": least_used,
        }

    def identify_gaps(
        self,
        actual_stats: dict[str, Any],
        intended_usage: dict[str, Any] | None = None
    ) -> list[dict]:
        """
        Identify gaps between intended and actual usage.
        
        Returns:
            List of gap dictionaries
        """
        gaps = []
        
        # Check Simple Mode usage
        total = actual_stats.get("total_commands", 0)
        simple_mode = actual_stats.get("simple_mode", 0)
        if total > 0 and simple_mode == 0:
            gaps.append({
                "type": "usage_pattern",
                "description": "Simple Mode not used despite being recommended",
                "impact": "high",
                "recommendation": "Consider using @simple-mode commands for better workflow orchestration",
            })
        
        # Check if CLI is overused vs Skills
        cli = actual_stats.get("cli_commands", 0)
        skills = actual_stats.get("cursor_skills", 0)
        if cli > skills * 2 and total > 0:
            gaps.append({
                "type": "usage_pattern",
                "description": "CLI commands used more than Cursor Skills",
                "impact": "medium",
                "recommendation": "Consider using Cursor Skills (@agent-name) for better IDE integration",
            })
        
        return gaps

    def _generate_recommendations(
        self,
        stats: dict[str, Any],
        gaps: list[dict]
    ) -> list[dict]:
        """Generate recommendations based on usage analysis."""
        recommendations = []
        
        # Add gap-based recommendations
        recommendations.extend(gaps)
        
        # Add statistics-based recommendations
        success_rate = stats.get("command_success_rate", 0.0)
        if success_rate < 0.8:
            recommendations.append({
                "type": "quality",
                "description": f"Command success rate is {success_rate:.1%} (below 80% threshold)",
                "impact": "high",
                "recommendation": "Investigate command failures and improve error handling",
            })
        
        return recommendations
