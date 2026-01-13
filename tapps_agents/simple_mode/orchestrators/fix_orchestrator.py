"""
Fix Orchestrator - Coordinates bug fixing workflow with review loopback and auto-commit.

Coordinates: Debugger → Implementer → Tester → Reviewer (with loopback) → Security Scan → Git Commit
"""

import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tapps_agents.core.config import ProjectConfig, load_config
from tapps_agents.core.git_operations import (
    commit_changes,
    create_and_checkout_branch,
    create_pull_request,
    get_current_branch,
    push_changes,
)
from tapps_agents.core.multi_agent_orchestrator import MultiAgentOrchestrator
from tapps_agents.quality.quality_gates import QualityGate, QualityThresholds
from ..intent_parser import Intent
from .base import SimpleModeOrchestrator

logger = logging.getLogger(__name__)


class FixOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for fixing bugs and errors with review loopback and auto-commit."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for fix workflow."""
        return ["debugger", "implementer", "tester", "reviewer"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute fix workflow with review loopback and auto-commit.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input:
                - files: List of file paths
                - error_message: Error description
                - max_iterations: Maximum iterations for loopback (default: 3)
                - auto_commit: Whether to commit on success (default: True)
                - commit_message: Optional commit message (auto-generated if not provided)
                - quality_thresholds: Optional quality thresholds dict

        Returns:
            Dictionary with execution results including commit info
        """
        parameters = parameters or {}
        files = parameters.get("files", [])
        error_message = parameters.get("error_message", "")
        
        # Load configuration
        config = self.config or load_config()
        bug_fix_config = config.bug_fix_agent
        
        max_iterations = parameters.get("max_iterations", bug_fix_config.max_iterations)
        auto_commit = parameters.get("auto_commit", bug_fix_config.auto_commit)
        commit_message = parameters.get("commit_message")
        escalation_threshold = bug_fix_config.escalation_threshold
        escalation_enabled = bug_fix_config.escalation_enabled
        pre_commit_security_scan = bug_fix_config.pre_commit_security_scan
        metrics_enabled = bug_fix_config.metrics_enabled
        commit_strategy = bug_fix_config.commit_strategy
        auto_merge_pr = bug_fix_config.auto_merge_pr
        require_pr_review = bug_fix_config.require_pr_review
        
        # Get quality thresholds from config or parameters
        thresholds_dict = parameters.get("quality_thresholds", {})
        if thresholds_dict:
            thresholds = QualityThresholds.from_dict(thresholds_dict)
        else:
            # Use thresholds from config
            quality_thresholds = bug_fix_config.quality_thresholds
            thresholds = QualityThresholds(
                overall_min=quality_thresholds.get("overall_min", 7.0),
                security_min=quality_thresholds.get("security_min", 6.5),
                maintainability_min=quality_thresholds.get("maintainability_min", 7.0),
            )
        
        # Initialize metrics collection
        start_time = time.time()
        metrics = {
            "bug_description": error_message or intent.original_input,
            "target_file": files[0] if files else None,
            "start_time": start_time,
            "iterations": 0,
            "success": False,
        }

        # Create multi-agent orchestrator
        orchestrator = MultiAgentOrchestrator(
            project_root=self.project_root,
            config=self.config,
            max_parallel=1,  # Sequential for fix workflow
        )

        # Prepare agent tasks
        target_file = files[0] if files else None
        bug_description = error_message or intent.original_input

        # Step 1: Execute debugger
        debug_tasks = [
            {
                "agent_id": "debugger-1",
                "agent": "debugger",
                "command": "debug",
                "args": {
                    "error_message": bug_description,
                    "file": target_file,
                },
            },
        ]

        logger.info(f"Step 1/4+: Analyzing bug: {bug_description}")
        # #region agent log
        import json
        from datetime import datetime
        log_path = self.project_root / ".cursor" / "debug.log"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "E",
                    "location": "fix_orchestrator.py:execute:before_debugger",
                    "message": "About to execute debugger",
                    "data": {"bug_description": bug_description[:200], "target_file": target_file},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except Exception:
            pass
        # #endregion
        debug_result = await orchestrator.execute_parallel(debug_tasks)
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "E",
                    "location": "fix_orchestrator.py:execute:after_debugger",
                    "message": "debugger execute_parallel returned",
                    "data": {"has_results": "results" in debug_result, "result_keys": list(debug_result.keys())},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except Exception:
            pass
        # #endregion

        # Check if debugger succeeded
        debugger_result = debug_result.get("results", {}).get("debugger-1", {})
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "F",
                    "location": "fix_orchestrator.py:execute:debugger_result_check",
                    "message": "debugger_result structure",
                    "data": {"success": debugger_result.get("success"), "result_keys": list(debugger_result.keys()), "has_result_key": "result" in debugger_result},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except Exception:
            pass
        # #endregion
        if not debugger_result.get("success"):
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "F",
                        "location": "fix_orchestrator.py:execute:debugger_failed",
                        "message": "Debugger failed",
                        "data": {"debugger_result": str(debugger_result)[:500]},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # #endregion
            return {
                "type": "fix",
                "success": False,
                "error": "Debugger failed to analyze the bug",
                "debugger_result": debugger_result,
                "iterations": 0,
                "committed": False,
            }

        # Extract fix suggestion from debugger analysis
        # debug_command returns: {"type": "debug", "analysis": {...}, "suggestions": [...], "fix_examples": [...]}
        debugger_analysis = debugger_result.get("result", {}).get("analysis", {})
        suggestions = debugger_result.get("result", {}).get("suggestions", [])
        fix_examples = debugger_result.get("result", {}).get("fix_examples", [])
        
        # Build fix suggestion from suggestions and examples
        fix_suggestion_parts = []
        if suggestions:
            fix_suggestion_parts.extend(suggestions[:3])  # Take first 3 suggestions
        if fix_examples:
            fix_suggestion_parts.append("\n".join(fix_examples[:2]))  # Take first 2 examples
        fix_suggestion = "\n\n".join(fix_suggestion_parts) if fix_suggestion_parts else ""
        
        # #region agent log
        try:
            result_inner = debugger_result.get("result", {})
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "G",
                    "location": "fix_orchestrator.py:execute:fix_suggestion_check",
                    "message": "Checking fix_suggestion",
                    "data": {"has_result_key": "result" in debugger_result, "result_keys": list(result_inner.keys()) if isinstance(result_inner, dict) else "not_dict", "has_analysis": "analysis" in result_inner, "has_suggestions": "suggestions" in result_inner, "suggestions_count": len(suggestions), "fix_examples_count": len(fix_examples), "fix_suggestion_length": len(fix_suggestion)},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except Exception:
            pass
        # #endregion
        if not fix_suggestion:
            return {
                "type": "fix",
                "success": False,
                "error": "Debugger did not provide a fix suggestion",
                "debugger_result": debugger_result,
                "iterations": 0,
                "committed": False,
            }

        # Step 2-4: Loop: Fix → Test → Review (until quality passes or max iterations)
        quality_passed = False
        iteration = 0
        review_results = []
        
        while iteration < max_iterations and not quality_passed:
            iteration += 1
            logger.info(f"Iteration {iteration}/{max_iterations}: Fix → Test → Review")

            # Step 2: Implement fix
            implement_tasks = [
                {
                    "agent_id": f"implementer-{iteration}",
                    "agent": "implementer",
                    "command": "refactor",
                    "args": {
                        "file": target_file,
                        "instructions": fix_suggestion,
                    },
                },
            ]

            implement_result = await orchestrator.execute_parallel(implement_tasks)
            implementer_result = implement_result.get("results", {}).get(
                f"implementer-{iteration}", {}
            )

            if not implementer_result.get("success"):
                return {
                    "type": "fix",
                    "success": False,
                    "error": f"Implementer failed on iteration {iteration}",
                    "implementer_result": implementer_result,
                    "iterations": iteration,
                    "committed": False,
                }

            # Step 3: Test the fix
            test_tasks = [
                {
                    "agent_id": f"tester-{iteration}",
                    "agent": "tester",
                    "command": "test",
                    "args": {"file": target_file},
                },
            ]

            test_result = await orchestrator.execute_parallel(test_tasks)
            tester_result = test_result.get("results", {}).get(
                f"tester-{iteration}", {}
            )

            if not tester_result.get("success"):
                logger.warning(
                    f"Tester reported issues on iteration {iteration}, continuing to review"
                )

            # Step 4: Review quality
            review_tasks = [
                {
                    "agent_id": f"reviewer-{iteration}",
                    "agent": "reviewer",
                    "command": "review",
                    "args": {"file": target_file},
                },
            ]

            review_result_exec = await orchestrator.execute_parallel(review_tasks)
            reviewer_result = review_result_exec.get("results", {}).get(
                f"reviewer-{iteration}", {}
            )

            if not reviewer_result.get("success"):
                logger.warning(
                    f"Reviewer failed on iteration {iteration}, assuming quality passed"
                )
                quality_passed = True
                review_results.append({
                    "iteration": iteration,
                    "result": reviewer_result,
                    "quality_passed": True,
                })
                break

            # Extract review result
            review_result_data = reviewer_result.get("result", {})
            review_results.append({
                "iteration": iteration,
                "result": review_result_data,
            })

            # Evaluate quality gate
            quality_gate = QualityGate(thresholds=thresholds)
            gate_result = quality_gate.evaluate_from_review_result(
                review_result_data, thresholds
            )

            quality_passed = gate_result.passed

            logger.info(
                f"Iteration {iteration}: Quality gate {'PASSED' if quality_passed else 'FAILED'}"
            )
            logger.info(
                f"  Overall: {gate_result.scores.get('overall_score', 0):.2f}/10 "
                f"(threshold: {thresholds.overall_min})"
            )
            logger.info(
                f"  Security: {gate_result.scores.get('security_score', 0):.2f}/10 "
                f"(threshold: {thresholds.security_min})"
            )

            if not quality_passed:
                failed_iterations = iteration
                # Human-in-the-Loop Escalation (2025 Enhancement)
                if escalation_enabled and failed_iterations >= escalation_threshold:
                    logger.warning(
                        f"🔔 ESCALATION: {failed_iterations} failed iterations reached escalation threshold ({escalation_threshold})"
                    )
                    logger.warning(
                        f"Human intervention recommended. Bug fix agent has attempted {failed_iterations} fixes without meeting quality thresholds."
                    )
                    logger.warning(
                        f"Current scores: Overall={gate_result.scores.get('overall_score', 0):.2f}/10, "
                        f"Security={gate_result.scores.get('security_score', 0):.2f}/10, "
                        f"Maintainability={gate_result.scores.get('maintainability_score', 0):.2f}/10"
                    )
                    # Continue to max_iterations but log escalation
                
                if iteration < max_iterations:
                    # Get improvement suggestions from review
                    improvements = review_result_data.get("improvements", [])
                    if improvements:
                        # Combine with previous fix suggestion
                        fix_suggestion = (
                            f"{fix_suggestion}\n\nAdditional improvements needed:\n"
                            + "\n".join(f"- {imp}" for imp in improvements[:5])
                        )
                    logger.info(
                        f"Quality threshold not met, attempting improvement (iteration {iteration + 1})"
                    )
                else:
                    logger.error(
                        f"Maximum iterations ({max_iterations}) reached, quality threshold not met"
                    )
                    # Record escalation in metrics
                    if metrics_enabled and failed_iterations >= escalation_threshold:
                        metrics["escalated"] = True
                        metrics["escalation_iteration"] = escalation_threshold

        # Check if quality passed
        if not quality_passed:
            execution_time = time.time() - start_time
            if metrics_enabled:
                metrics.update({
                    "iterations": iteration,
                    "success": False,
                    "execution_time": execution_time,
                    "final_quality_scores": review_results[-1]["result"].get("scores", {}) if review_results else {},
                })
                logger.info(f"Metrics: {metrics}")
            
            return {
                "type": "fix",
                "success": False,
                "error": f"Quality threshold not met after {max_iterations} iterations",
                "review_results": review_results,
                "iterations": iteration,
                "committed": False,
                "escalated": escalation_enabled and iteration >= escalation_threshold,
                "metrics": metrics if metrics_enabled else None,
            }

        # Step 5: Pre-Commit Security Scan (2025 Enhancement)
        security_scan_passed = True
        security_scan_result = None
        if pre_commit_security_scan and auto_commit:
            logger.info("Running pre-commit security scan...")
            try:
                security_scan_tasks = [
                    {
                        "agent_id": "ops-security-1",
                        "agent": "ops",
                        "command": "security-scan",
                        "args": {
                            "target": target_file,
                            "scan_type": "code",
                        },
                    },
                ]
                security_result = await orchestrator.execute_parallel(security_scan_tasks)
                security_scan_result = security_result.get("results", {}).get("ops-security-1", {})
                
                if security_scan_result.get("success"):
                    security_score = security_scan_result.get("result", {}).get("security_score", 10.0)
                    vulnerabilities = security_scan_result.get("result", {}).get("vulnerabilities", [])
                    critical_vulns = [v for v in vulnerabilities if v.get("severity") in ["CRITICAL", "HIGH"]]
                    
                    if critical_vulns:
                        logger.error(f"Pre-commit security scan FAILED: {len(critical_vulns)} CRITICAL/HIGH vulnerabilities found")
                        security_scan_passed = False
                        logger.error("Blocking commit due to security vulnerabilities")
                    elif security_score < thresholds.security_min:
                        logger.warning(f"Pre-commit security scan: score {security_score:.2f} below threshold {thresholds.security_min}")
                        # Warn but don't block for non-critical issues
                    else:
                        logger.info(f"Pre-commit security scan PASSED: score {security_score:.2f}/10")
                else:
                    logger.warning("Security scan failed, but continuing with commit")
            except Exception as e:
                logger.warning(f"Error during security scan: {e}, continuing with commit")
        
        if not security_scan_passed:
            execution_time = time.time() - start_time
            if metrics_enabled:
                metrics.update({
                    "iterations": iteration,
                    "success": False,
                    "execution_time": execution_time,
                    "security_scan_blocked": True,
                })
            return {
                "type": "fix",
                "success": False,
                "error": "Pre-commit security scan failed: CRITICAL/HIGH vulnerabilities detected",
                "review_results": review_results,
                "iterations": iteration,
                "committed": False,
                "security_scan_result": security_scan_result,
                "metrics": metrics if metrics_enabled else None,
            }

        # Step 6: Commit changes (direct or PR workflow)
        commit_info = None
        pr_info = None
        if auto_commit:
            try:
                # Generate commit message if not provided
                if not commit_message:
                    final_scores = review_results[-1]["result"].get("scores", {})
                    overall_score = final_scores.get("overall_score", 0)
                    commit_message = (
                        f"Fix: {bug_description}\n\n"
                        f"Quality scores: Overall {overall_score:.1f}/10\n"
                        f"Iterations: {iteration}\n"
                        f"Auto-fixed by TappsCodingAgents Bug Fix Agent"
                    )

                # Branch Protection & PR Workflow (2025 Enhancement)
                if commit_strategy == "pull_request":
                    # Create feature branch for PR
                    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
                    file_stem = Path(target_file).stem if target_file else "fix"
                    feature_branch = f"bugfix/{file_stem}-{timestamp}"
                    
                    logger.info(f"Creating feature branch: {feature_branch}")
                    branch_result = create_and_checkout_branch(feature_branch, self.project_root)
                    
                    if not branch_result["success"]:
                        raise RuntimeError(f"Failed to create branch: {branch_result.get('error')}")
                    
                    # Commit to feature branch
                    commit_result = commit_changes(
                        message=commit_message,
                        files=[target_file] if target_file else None,
                        branch=feature_branch,
                        path=self.project_root,
                    )
                    
                    if commit_result["success"]:
                        # Push feature branch
                        push_result = push_changes(feature_branch, self.project_root)
                        
                        if push_result["success"]:
                            # Create PR
                            pr_title = f"Fix: {bug_description[:100]}"
                            pr_body = (
                                f"## Automated Bug Fix\n\n"
                                f"**Bug Description:** {bug_description}\n\n"
                                f"**Target File:** {target_file}\n\n"
                                f"**Quality Scores:**\n"
                                f"- Overall: {final_scores.get('overall_score', 0):.1f}/10\n"
                                f"- Security: {final_scores.get('security_score', 0):.1f}/10\n"
                                f"- Maintainability: {final_scores.get('maintainability_score', 0):.1f}/10\n\n"
                                f"**Iterations:** {iteration}\n\n"
                                f"**Auto-fixed by:** TappsCodingAgents Bug Fix Agent\n\n"
                                f"---\n\n"
                                f"*This PR was created automatically after passing quality gates.*"
                            )
                            
                            pr_result = create_pull_request(
                                title=pr_title,
                                body=pr_body,
                                head_branch=feature_branch,
                                base_branch="main",
                                path=self.project_root,
                            )
                            
                            if pr_result["success"]:
                                pr_info = {
                                    "pr_url": pr_result.get("pr_url"),
                                    "pr_number": pr_result.get("pr_number"),
                                    "branch": feature_branch,
                                }
                                logger.info(f"Created pull request: {pr_result.get('pr_url', 'N/A')}")
                                
                                if auto_merge_pr and not require_pr_review:
                                    logger.info("Auto-merge enabled, but manual merge required (GitHub CLI limitation)")
                            else:
                                logger.warning(f"Failed to create PR: {pr_result.get('error')}")
                                # Fall back to commit info even if PR creation failed
                                commit_info = {
                                    "commit_hash": commit_result["commit_hash"],
                                    "branch": feature_branch,
                                    "message": commit_message,
                                    "pr_error": pr_result.get("error"),
                                }
                        else:
                            logger.warning(f"Failed to push branch: {push_result.get('error')}")
                            commit_info = {"error": f"Push failed: {push_result.get('error')}"}
                    else:
                        logger.warning(f"Failed to commit to branch: {commit_result.get('error')}")
                        commit_info = {"error": commit_result.get("error")}
                        
                else:
                    # Direct commit to main (original behavior)
                    commit_result = commit_changes(
                        message=commit_message,
                        files=[target_file] if target_file else None,
                        branch="main",
                        path=self.project_root,
                    )

                    if commit_result["success"]:
                        commit_info = {
                            "commit_hash": commit_result["commit_hash"],
                            "branch": commit_result["branch"],
                            "message": commit_message,
                        }
                        logger.info(
                            f"Committed changes to {commit_result['branch']}: "
                            f"{commit_result['commit_hash'][:8]}"
                        )
                    else:
                        logger.warning(
                            f"Failed to commit changes: {commit_result.get('error')}"
                        )
                        commit_info = {
                            "error": commit_result.get("error"),
                        }

            except Exception as e:
                logger.error(f"Error during commit: {e}", exc_info=True)
                commit_info = {"error": str(e)}

        # Update metrics for successful execution
        execution_time = time.time() - start_time
        if metrics_enabled:
            final_scores = review_results[-1]["result"].get("scores", {}) if review_results else {}
            metrics.update({
                "iterations": iteration,
                "success": True,
                "execution_time": execution_time,
                "final_quality_scores": final_scores,
                "committed": commit_info is not None and "error" not in commit_info,
                "security_scan_performed": pre_commit_security_scan and auto_commit,
            })
            logger.info(f"Execution metrics: {metrics}")

        return {
            "type": "fix",
            "success": True,
            "agents_executed": ["debugger", "implementer", "tester", "reviewer"] + (["ops"] if pre_commit_security_scan and auto_commit else []),
            "iterations": iteration,
            "review_results": review_results,
            "quality_passed": True,
            "committed": commit_info is not None and "error" not in commit_info,
            "commit_info": commit_info,
            "pr_info": pr_info,
            "commit_strategy": commit_strategy,
            "security_scan_result": security_scan_result if pre_commit_security_scan and auto_commit else None,
            "metrics": metrics if metrics_enabled else None,
            "summary": {
                "bug_description": bug_description,
                "target_file": target_file,
                "iterations": iteration,
                "final_quality": review_results[-1]["result"].get("scores", {}) if review_results else {},
                "execution_time": execution_time,
            },
        }
