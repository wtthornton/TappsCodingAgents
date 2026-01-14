"""
Output Aggregation for Simple Mode.

Aggregates outputs from multiple agents and steps in Simple Mode workflows.
"""

from typing import Any

from tapps_agents.core.instructions import GenericInstruction
from tapps_agents.core.output_formatter import AgentOutput, OutputFormat, OutputFormatter


class SimpleModeOutputAggregator:
    """
    Aggregates outputs from multiple Simple Mode workflow steps.
    
    Collects outputs, formats them consistently, and provides
    a unified view of workflow execution results.
    """

    def __init__(self, workflow_id: str, workflow_type: str = "build"):
        """
        Initialize output aggregator.
        
        Args:
            workflow_id: Unique workflow identifier
            workflow_type: Type of workflow (build, review, fix, etc.)
        """
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.formatter = OutputFormatter()
        self.step_outputs: list[dict[str, Any]] = []
        self.aggregated_output: dict[str, Any] = {}

    def add_step_output(
        self,
        step_number: int,
        step_name: str,
        agent_name: str,
        output: dict[str, Any],
        success: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add output from a workflow step.
        
        Args:
            step_number: Step number in workflow
            step_name: Human-readable step name
            agent_name: Agent that executed the step
            output: Agent output dictionary
            success: Whether step succeeded
            metadata: Optional metadata (artifacts, file paths, etc.)
        """
        step_data = {
            "step_number": step_number,
            "step_name": step_name,
            "agent": agent_name,
            "output": output,
            "success": success,
            "metadata": metadata or {},
        }

        # Check if output contains instruction object
        if "instruction" in output:
            instruction_data = output["instruction"]
            if isinstance(instruction_data, dict):
                # Convert to GenericInstruction if needed
                instruction = GenericInstruction.from_dict(instruction_data)
                step_data["instruction"] = {
                    "type": instruction.__class__.__name__,
                    "description": instruction.get_description() if hasattr(instruction, 'get_description') else str(instruction),
                    "skill_command": instruction.to_skill_command() if hasattr(instruction, 'to_skill_command') else None,
                    "cli_command": instruction.to_cli_command() if hasattr(instruction, 'to_cli_command') else None,
                    "visual_indicator": instruction.get_visual_indicator() if hasattr(instruction, 'get_visual_indicator') else "⚙️",
                }
                step_data["auto_executable"] = True

        self.step_outputs.append(step_data)

    def aggregate(self) -> dict[str, Any]:
        """
        Aggregate all step outputs into a unified result.
        
        Returns:
            Aggregated output dictionary
        """
        # Build summary
        total_steps = len(self.step_outputs)
        successful_steps = sum(1 for step in self.step_outputs if step["success"])
        failed_steps = total_steps - successful_steps

        # Extract key information from each step
        step_summaries = []
        for step in self.step_outputs:
            summary = {
                "step_number": step["step_number"],
                "step_name": step["step_name"],
                "agent": step["agent"],
                "success": step["success"],
            }

            # Extract artifacts
            if "metadata" in step and step["metadata"]:
                if "artifacts" in step["metadata"]:
                    summary["artifacts"] = step["metadata"]["artifacts"]
                if "file_paths" in step["metadata"]:
                    summary["file_paths"] = step["metadata"]["file_paths"]

            # Extract instructions for auto-execution
            if "instruction" in step:
                summary["instruction"] = step["instruction"]
                summary["auto_executable"] = step.get("auto_executable", False)

            step_summaries.append(summary)

        # Extract key outputs by agent type
        agent_outputs = {}
        for step in self.step_outputs:
            agent_name = step["agent"]
            if agent_name not in agent_outputs:
                agent_outputs[agent_name] = []
            agent_outputs[agent_name].append({
                "step_number": step["step_number"],
                "output": step["output"],
                "metadata": step["metadata"],
            })

        # Build aggregated output
        self.aggregated_output = {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "summary": {
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "failed_steps": failed_steps,
                "success_rate": (successful_steps / total_steps * 100) if total_steps > 0 else 0,
            },
            "steps": step_summaries,
            "agent_outputs": agent_outputs,
            "raw_outputs": self.step_outputs,
        }

        return self.aggregated_output

    def format_summary(self, format: OutputFormat = OutputFormat.MARKDOWN) -> str:
        """
        Format aggregated output as a summary.
        
        Args:
            format: Output format
            
        Returns:
            Formatted summary string
        """
        aggregated = self.aggregate()

        if format == OutputFormat.MARKDOWN:
            return self._format_markdown_summary(aggregated)
        elif format == OutputFormat.JSON:
            from json import dumps
            return dumps(aggregated, indent=2)
        else:
            return str(aggregated)

    def _format_markdown_summary(self, aggregated: dict[str, Any]) -> str:
        """Format summary as Markdown."""
        lines = [
            f"# Workflow Summary: {aggregated['workflow_type'].title()}",
            "",
            f"**Workflow ID:** `{aggregated['workflow_id']}`",
            "",
            "## Execution Summary",
            "",
            f"- **Total Steps:** {aggregated['summary']['total_steps']}",
            f"- **Successful Steps:** {aggregated['summary']['successful_steps']}",
            f"- **Failed Steps:** {aggregated['summary']['failed_steps']}",
            f"- **Success Rate:** {aggregated['summary']['success_rate']:.1f}%",
            "",
            "## Step Details",
            "",
        ]

        for step in aggregated["steps"]:
            status_icon = "✅" if step["success"] else "❌"
            lines.append(f"### {status_icon} Step {step['step_number']}: {step['step_name']}")
            lines.append(f"- **Agent:** {step['agent']}")
            if "artifacts" in step:
                lines.append(f"- **Artifacts:** {len(step['artifacts'])} created")
            if "file_paths" in step:
                lines.append(f"- **Files:** {len(step['file_paths'])} created")
            if "instruction" in step and step.get("auto_executable"):
                lines.append(f"- **Auto-Executable:** Yes")
                if "skill_command" in step["instruction"]:
                    lines.append(f"  - Skill Command: `{step['instruction']['skill_command']}`")
            lines.append("")

        return "\n".join(lines)

    def get_executable_instructions(self) -> list[dict[str, Any]]:
        """
        Get all executable instructions from workflow steps.
        
        Returns:
            List of instruction dictionaries ready for execution
        """
        instructions = []

        for step in self.step_outputs:
            if "instruction" in step and step.get("auto_executable"):
                instruction_info = step["instruction"].copy()
                instruction_info["step_number"] = step["step_number"]
                instruction_info["step_name"] = step["step_name"]
                instruction_info["agent"] = step["agent"]
                instructions.append(instruction_info)

        return instructions

    def get_failed_steps(self) -> list[dict[str, Any]]:
        """
        Get all failed steps with error information.
        
        Returns:
            List of failed step dictionaries
        """
        return [
            {
                "step_number": step["step_number"],
                "step_name": step["step_name"],
                "agent": step["agent"],
                "error": step["output"].get("error") if isinstance(step["output"], dict) else None,
                "metadata": step["metadata"],
            }
            for step in self.step_outputs
            if not step["success"]
        ]
