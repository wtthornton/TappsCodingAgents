"""
PR Orchestrator - Coordinates pull request creation and management workflow.

Coordinates: Reviewer → Documenter → PR Creation → Status Tracking

This orchestrator helps create pull requests with auto-generated descriptions,
quality scores, and links to workflow documentation.
"""

from pathlib import Path
from typing import Any
import subprocess
import json

from tapps_agents.core.config import ProjectConfig
from tapps_agents.core.multi_agent_orchestrator import MultiAgentOrchestrator
from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class PROrchestrator(SimpleModeOrchestrator):
    """Orchestrator for pull request creation."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for PR workflow."""
        return ["reviewer", "documenter"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute PR workflow.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input

        Returns:
            Dictionary with execution results
        """
        parameters = parameters or {}
        title = parameters.get("title") or parameters.get("description") or intent.original_input
        from_branch = parameters.get("from_branch")
        to_branch = parameters.get("to_branch", "main")
        
        # Get current branch if not specified
        if not from_branch:
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )
                from_branch = result.stdout.strip() if result.returncode == 0 else "HEAD"
            except Exception:
                from_branch = "HEAD"

        # Create multi-agent orchestrator
        orchestrator = MultiAgentOrchestrator(
            project_root=self.project_root,
            config=self.config,
            max_parallel=1,  # Sequential for PR workflow
        )

        agent_tasks = []

        # Step 1: Analyze changes and final review
        try:
            # Get changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", to_branch, from_branch],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            changed_files = [f.strip() for f in result.stdout.split("\n") if f.strip()] if result.returncode == 0 else []
        except Exception:
            changed_files = []

        reviewer_args = {
            "files": changed_files[:20],  # Limit to 20 files for review
        }

        agent_tasks.append(
            {
                "agent_id": "reviewer-1",
                "agent": "reviewer",
                "command": "review",
                "args": reviewer_args,
            }
        )

        # Execute review
        result = await orchestrator.execute_parallel(agent_tasks)

        reviewer_result = result.get("results", {}).get("reviewer-1", {})
        review_data = reviewer_result.get("result", {}) if reviewer_result.get("success") else {}
        
        # Extract quality scores
        quality_scores = review_data.get("scores", {})
        overall_score = quality_scores.get("overall", 0)
        security_score = quality_scores.get("security", 0)
        maintainability_score = quality_scores.get("maintainability", 0)

        # Step 2: Generate PR description using documenter
        pr_description_template = f"""## Summary
{title}

## Changes
This PR includes changes to {len(changed_files)} file(s).

## Quality Scores
- **Overall Score**: {overall_score}/100
- **Security Score**: {security_score}/10
- **Maintainability Score**: {maintainability_score}/10

## Files Changed
{chr(10).join(f"- {f}" for f in changed_files[:50])}

## Review Results
{review_data.get('summary', 'See review details for more information')}

## Testing
Please verify all tests pass before merging.

## Checklist
- [ ] Code reviewed
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Quality gates passed
"""

        documenter_args = {
            "content": pr_description_template,
            "format": "markdown",
        }

        agent_tasks.append(
            {
                "agent_id": "documenter-1",
                "agent": "documenter",
                "command": "document",
                "args": documenter_args,
            }
        )

        # Execute documenter
        result = await orchestrator.execute_parallel(agent_tasks[-1:])

        documenter_result = result.get("results", {}).get("documenter-1", {})
        pr_description = documenter_result.get("result", {}).get("content", pr_description_template) if documenter_result.get("success") else pr_description_template

        # Step 3: Create PR via Git API or CLI
        pr_result = None
        pr_url = None

        try:
            # Try to use GitHub CLI if available
            gh_result = subprocess.run(
                [
                    "gh", "pr", "create",
                    "--title", title,
                    "--body", pr_description,
                    "--base", to_branch,
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            
            if gh_result.returncode == 0:
                pr_url = gh_result.stdout.strip()
                pr_result = {
                    "success": True,
                    "method": "gh_cli",
                    "url": pr_url,
                }
            else:
                # Fallback: Create PR metadata file
                pr_metadata = {
                    "title": title,
                    "description": pr_description,
                    "from_branch": from_branch,
                    "to_branch": to_branch,
                    "changed_files": changed_files,
                    "quality_scores": quality_scores,
                    "created_via": "tapps-agents",
                }
                
                pr_metadata_path = self.project_root / ".tapps-agents" / "pr_metadata.json"
                pr_metadata_path.parent.mkdir(parents=True, exist_ok=True)
                pr_metadata_path.write_text(json.dumps(pr_metadata, indent=2), encoding="utf-8")
                
                pr_result = {
                    "success": True,
                    "method": "metadata_file",
                    "metadata_path": str(pr_metadata_path),
                    "instructions": "PR metadata created. Use GitHub web UI or GitLab to create PR manually with the metadata.",
                }
        except FileNotFoundError:
            # GitHub CLI not available, create metadata file
            pr_metadata = {
                "title": title,
                "description": pr_description,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "changed_files": changed_files,
                "quality_scores": quality_scores,
                "created_via": "tapps-agents",
            }
            
            pr_metadata_path = self.project_root / ".tapps-agents" / "pr_metadata.json"
            pr_metadata_path.parent.mkdir(parents=True, exist_ok=True)
            pr_metadata_path.write_text(json.dumps(pr_metadata, indent=2), encoding="utf-8")
            
            pr_result = {
                "success": True,
                "method": "metadata_file",
                "metadata_path": str(pr_metadata_path),
                "instructions": "PR metadata created. Use GitHub web UI or GitLab to create PR manually with the metadata.",
            }

        return {
            "type": "pr",
            "success": pr_result.get("success", False) if pr_result else False,
            "agents_executed": result.get("total_agents", 0),
            "results": result.get("results", {}),
            "summary": {
                "title": title,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "changed_files_count": len(changed_files),
                "quality_scores": quality_scores,
                "pr_result": pr_result,
            },
        }
