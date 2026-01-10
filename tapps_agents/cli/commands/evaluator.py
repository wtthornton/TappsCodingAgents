"""
Evaluator agent command handlers
"""
import asyncio

from ...agents.evaluator.agent import EvaluatorAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


def handle_evaluator_command(args: object) -> None:
    """Handle evaluator agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("evaluator")
        feedback.output_result(help_text)
        return
    
    # Evaluator is offline-only (no network required)
    evaluator = EvaluatorAgent()
    try:
        asyncio.run(evaluator.activate(offline_mode=True))
        
        if command == "evaluate":
            workflow_id = getattr(args, "workflow_id", None)
            feedback.start_operation("Evaluate Framework", "Evaluating TappsCodingAgents effectiveness")
            feedback.running("Collecting usage data...", step=1, total_steps=4)
            result = asyncio.run(
                evaluator.run(
                    "evaluate",
                    workflow_id=workflow_id,
                )
            )
            feedback.running("Analyzing usage patterns...", step=2, total_steps=4)
            feedback.running("Analyzing workflow adherence...", step=3, total_steps=4)
            feedback.running("Generating report...", step=4, total_steps=4)
            feedback.clear_progress()
            
        elif command == "evaluate-workflow":
            workflow_id = getattr(args, "workflow_id", None)
            if not workflow_id:
                feedback.output_error("workflow_id is required for evaluate-workflow command")
                return
            
            feedback.start_operation("Evaluate Workflow", f"Evaluating workflow: {workflow_id}")
            feedback.running("Loading workflow state...", step=1, total_steps=4)
            result = asyncio.run(
                evaluator.run(
                    "evaluate-workflow",
                    workflow_id=workflow_id,
                )
            )
            feedback.running("Analyzing workflow execution...", step=2, total_steps=4)
            feedback.running("Analyzing quality metrics...", step=3, total_steps=4)
            feedback.running("Generating report...", step=4, total_steps=4)
            feedback.clear_progress()
        
        elif command == "submit-feedback":
            feedback.start_operation("Submit Feedback", "Submitting external feedback")
            
            # Parse feedback data from args or file
            import json as json_lib
            from pathlib import Path
            
            file_path = getattr(args, "file", None)
            if file_path:
                # Load from file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_data = json_lib.load(f)
                    
                    performance_ratings = file_data.get("performance_ratings", {})
                    suggestions = file_data.get("suggestions", [])
                    context = file_data.get("context", {})
                    metrics = file_data.get("metrics", {})
                    project_id = file_data.get("project_id")
                except Exception as e:
                    feedback.output_error(f"Failed to load feedback file: {e}")
                    return
            else:
                # Parse from command-line arguments
                ratings = getattr(args, "ratings", []) or []
                suggestions = getattr(args, "suggestions", []) or []
                
                if not ratings or not suggestions:
                    feedback.output_error("At least one --rating and one --suggestion is required")
                    return
                
                # Parse ratings
                performance_ratings = {}
                for rating_str in ratings:
                    try:
                        metric, value = rating_str.split("=", 1)
                        performance_ratings[metric.strip()] = float(value.strip())
                    except ValueError:
                        feedback.output_error(f"Invalid rating format: {rating_str}. Use METRIC=VALUE")
                        return
                
                # Parse metrics
                metrics = {}
                metric_args = getattr(args, "metrics", []) or []
                for metric_str in metric_args:
                    try:
                        key, value = metric_str.split("=", 1)
                        # Try to parse as number, otherwise keep as string
                        try:
                            metrics[key.strip()] = float(value.strip())
                        except ValueError:
                            metrics[key.strip()] = value.strip()
                    except ValueError:
                        feedback.output_error(f"Invalid metric format: {metric_str}. Use KEY=VALUE")
                        return
                
                # Build context
                context = {}
                if getattr(args, "workflow_id", None):
                    context["workflow_id"] = args.workflow_id
                if getattr(args, "agent_id", None):
                    context["agent_id"] = args.agent_id
                if getattr(args, "task_type", None):
                    context["task_type"] = args.task_type
                
                project_id = getattr(args, "project_id", None)
            
            result = asyncio.run(
                evaluator.run(
                    "submit-feedback",
                    performance_ratings=performance_ratings,
                    suggestions=suggestions,
                    context=context if context else None,
                    metrics=metrics if metrics else None,
                    project_id=project_id,
                )
            )
            feedback.clear_progress()
        
        elif command == "get-feedback":
            feedback_id = getattr(args, "feedback_id", None)
            if not feedback_id:
                feedback.output_error("feedback_id is required for get-feedback command")
                return
            
            output_format = getattr(args, "format", "text")
            result = asyncio.run(
                evaluator.run(
                    "get-feedback",
                    feedback_id=feedback_id,
                )
            )
        
        elif command == "list-feedback":
            workflow_id = getattr(args, "workflow_id", None)
            agent_id = getattr(args, "agent_id", None)
            start_date = getattr(args, "start_date", None)
            end_date = getattr(args, "end_date", None)
            limit = getattr(args, "limit", None)
            
            result = asyncio.run(
                evaluator.run(
                    "list-feedback",
                    workflow_id=workflow_id,
                    agent_id=agent_id,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                )
            )
            
        else:
            feedback.output_error(f"Unknown command: {command}")
            return
        
        # Check for errors
        if check_result_error(result):
            return
        
        # Format output based on command type
        if command == "submit-feedback":
            if result.get("success"):
                feedback.output_result(f"Feedback submitted successfully")
                feedback.output_result(f"Feedback ID: {result.get('feedback_id', 'N/A')}")
                if result.get("file_path"):
                    feedback.output_result(f"Saved to: {result['file_path']}")
            else:
                feedback.output_error(result.get("error", "Feedback submission failed"))
        elif command == "get-feedback":
            cmd_output_format = getattr(args, "format", "text")
            if result.get("success"):
                if cmd_output_format == "json":
                    format_json_output(result, feedback)
                else:
                    # Text format
                    fb_data = result.get("feedback", {})
                    feedback.output_result(f"Feedback ID: {fb_data.get('feedback_id', 'N/A')}")
                    feedback.output_result(f"Timestamp: {fb_data.get('timestamp', 'N/A')}")
                    feedback.output_result("\nPerformance Ratings:")
                    for metric, rating in fb_data.get("performance_ratings", {}).items():
                        feedback.output_result(f"  {metric}: {rating}")
                    feedback.output_result("\nSuggestions:")
                    for suggestion in fb_data.get("suggestions", []):
                        feedback.output_result(f"  - {suggestion}")
                    if fb_data.get("context"):
                        feedback.output_result("\nContext:")
                        for key, value in fb_data["context"].items():
                            feedback.output_result(f"  {key}: {value}")
            else:
                feedback.output_error(result.get("error", "Failed to retrieve feedback"))
        elif command == "list-feedback":
            cmd_output_format = getattr(args, "format", "text")
            if result.get("success"):
                if cmd_output_format == "json":
                    format_json_output(result, feedback)
                else:
                    # Text format
                    count = result.get("count", 0)
                    feedback.output_result(f"Found {count} feedback entries\n")
                    for idx, fb in enumerate(result.get("feedback", [])[:10], 1):  # Show first 10
                        feedback.output_result(f"{idx}. Feedback ID: {fb.get('feedback_id', 'N/A')}")
                        feedback.output_result(f"   Timestamp: {fb.get('timestamp', 'N/A')}")
                        ratings = fb.get("performance_ratings", {})
                        if "overall" in ratings:
                            feedback.output_result(f"   Overall Rating: {ratings['overall']}")
                        feedback.output_result(f"   Suggestions: {len(fb.get('suggestions', []))}")
                        feedback.output_result("")
            else:
                feedback.output_error(result.get("error", "Failed to list feedback"))
        elif output_format == "json":
            format_json_output(result, feedback)
        elif output_format == "text":
            if result.get("success"):
                output_file = result.get("output_file", "N/A")
                feedback.output_result(f"Evaluation complete. Report saved to: {output_file}")
                if result.get("report"):
                    feedback.output_result("\n" + result["report"][:500] + "..." if len(result["report"]) > 500 else result["report"])
            else:
                feedback.output_error(result.get("error", "Evaluation failed"))
        else:
            # Default to showing report
            if result.get("report"):
                feedback.output_result(result["report"])
            else:
                format_json_output(result, feedback)
                
    except Exception as e:
        feedback.output_error(f"Evaluation failed: {str(e)}")
    finally:
        safe_close_agent_sync(evaluator)
