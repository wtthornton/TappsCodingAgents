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
            
        else:
            feedback.output_error(f"Unknown command: {command}")
            return
        
        # Check for errors
        if check_result_error(result):
            return
        
        # Format output
        if output_format == "json":
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
