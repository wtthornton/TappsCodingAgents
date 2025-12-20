"""
Test rig for prompt enhancement that prints the enhancement after each stage completes.

Usage:
    python scripts/test_enhancer_rig.py "Create a login system"
    python scripts/test_enhancer_rig.py "Add payment processing"
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tapps_agents.agents.enhancer.agent import EnhancerAgent


def print_section(title: str, width: int = 80):
    """Print a formatted section header."""
    print("\n" + "=" * width)
    print(f" {title} ".center(width, "="))
    print("=" * width + "\n")


def format_instruction(inst_dict: dict) -> str:
    """Format an instruction object for display."""
    lines = []
    if isinstance(inst_dict, dict):
        if "agent_name" in inst_dict:
            lines.append(f"- **Agent**: @{inst_dict['agent_name']}")
        if "command" in inst_dict:
            lines.append(f"- **Command**: {inst_dict['command']}")
        if "prompt" in inst_dict:
            prompt_text = inst_dict["prompt"]
            lines.append(f"- **Instruction Prompt**:")
            # Format the prompt nicely, truncating if very long
            if len(prompt_text) > 800:
                lines.append(f"  ```\n  {prompt_text[:800]}\n  ... (truncated)\n  ```")
            else:
                lines.append(f"  ```\n  {prompt_text}\n  ```")
        if "parameters" in inst_dict and inst_dict["parameters"]:
            lines.append(f"- **Parameters**:")
            for key, value in inst_dict["parameters"].items():
                if isinstance(value, str) and len(value) > 200:
                    lines.append(f"  - {key}: {value[:200]}...")
                else:
                    lines.append(f"  - {key}: {value}")
        if "skill_command" in inst_dict:
            lines.append(f"- **Skill Command**: `{inst_dict['skill_command']}`")
    return "\n".join(lines)


def format_stage_output(session: dict, stage_name: str) -> str:
    """Format and return the current enhancement state after a stage."""
    prompt = session["metadata"]["original_prompt"]
    stages = session["stages"]
    
    lines = [f"# Enhanced Prompt (After {stage_name}): {prompt}", ""]
    
    # Add completed stages
    if "analysis" in stages:
        lines.append("## Analysis")
        analysis = stages["analysis"]
        if isinstance(analysis, dict):
            # Extract key info if available
            if "original_prompt" in analysis:
                lines.append(f"- **Original Prompt**: {analysis['original_prompt']}")
            if "instruction" in analysis:
                lines.append("\n### Instruction Prepared:")
                inst_fmt = format_instruction(analysis["instruction"])
                lines.append(inst_fmt)
            if "skill_command" in analysis:
                lines.append(f"\n- **Skill Command**: `{analysis['skill_command']}`")
        lines.append("")
    
    if "requirements" in stages:
        lines.append("## Requirements")
        req = stages["requirements"]
        if isinstance(req, dict):
            # Show requirements analysis if available
            if "requirements_analysis" in req and req["requirements_analysis"]:
                lines.append("### Requirements Analysis")
                analysis_text = req["requirements_analysis"]
                if isinstance(analysis_text, str):
                    lines.append(analysis_text[:600] + ("..." if len(analysis_text) > 600 else ""))
                lines.append("")
            if "functional_requirements" in req and req["functional_requirements"]:
                lines.append("### Functional Requirements")
                for fr in req["functional_requirements"]:
                    lines.append(f"- {fr}")
                lines.append("")
            if "non_functional_requirements" in req and req["non_functional_requirements"]:
                lines.append("### Non-Functional Requirements")
                for nfr in req["non_functional_requirements"]:
                    lines.append(f"- {nfr}")
                lines.append("")
            if "technical_constraints" in req and req["technical_constraints"]:
                lines.append("### Technical Constraints")
                for tc in req["technical_constraints"]:
                    lines.append(f"- {tc}")
                lines.append("")
            if "assumptions" in req and req["assumptions"]:
                lines.append("### Assumptions")
                for ass in req["assumptions"]:
                    lines.append(f"- {ass}")
                lines.append("")
            if "expert_consultations" in req and req["expert_consultations"]:
                lines.append("### Expert Consultations")
                for domain, consultation in req["expert_consultations"].items():
                    lines.append(f"#### {domain}")
                    if "weighted_answer" in consultation:
                        answer = consultation["weighted_answer"]
                        if isinstance(answer, str):
                            lines.append(f"{answer[:500]}...")
                        else:
                            lines.append(str(answer)[:500] + "...")
                    if "confidence" in consultation:
                        lines.append(f"- Confidence: {consultation['confidence']}")
                    if "agreement_level" in consultation:
                        lines.append(f"- Agreement: {consultation['agreement_level']}")
                    if "primary_expert" in consultation:
                        lines.append(f"- Primary Expert: {consultation['primary_expert']}")
                lines.append("")
        lines.append("")
    
    if "architecture" in stages:
        lines.append("## Architecture")
        arch = stages["architecture"]
        if isinstance(arch, dict):
            if "architecture_guidance" in arch and arch["architecture_guidance"]:
                guidance = arch["architecture_guidance"]
                if isinstance(guidance, str):
                    lines.append("### Architecture Guidance")
                    lines.append(guidance[:800] + ("..." if len(guidance) > 800 else ""))
                else:
                    lines.append(str(guidance)[:800] + "...")
                lines.append("")
            if "system_design" in arch and arch["system_design"]:
                lines.append("### System Design")
                design_dict = arch["system_design"]
                if isinstance(design_dict, dict):
                    # Format as readable structure
                    for key, value in design_dict.items():
                        if isinstance(value, (dict, list)):
                            value_str = json.dumps(value, indent=2)
                            if len(value_str) > 400:
                                value_str = value_str[:400] + "..."
                            lines.append(f"- **{key}**:\n  ```json\n  {value_str}\n  ```")
                        else:
                            lines.append(f"- **{key}**: {value}")
                else:
                    design_str = json.dumps(design_dict, indent=2)
                    lines.append(design_str[:600] + ("..." if len(design_str) > 600 else ""))
                lines.append("")
            if "design_patterns" in arch and arch["design_patterns"]:
                lines.append("### Design Patterns")
                for pattern in arch["design_patterns"]:
                    lines.append(f"- {pattern}")
                lines.append("")
            if "technology_recommendations" in arch and arch["technology_recommendations"]:
                lines.append("### Technology Recommendations")
                for tech in arch["technology_recommendations"]:
                    lines.append(f"- {tech}")
                lines.append("")
        lines.append("")
    
    if "codebase_context" in stages:
        lines.append("## Codebase Context")
        ctx = stages["codebase_context"]
        if isinstance(ctx, dict):
            if "related_files" in ctx and ctx["related_files"]:
                lines.append("### Related Files")
                for file in ctx["related_files"][:10]:
                    lines.append(f"- {file}")
            if "codebase_context" in ctx:
                lines.append(f"\n{ctx['codebase_context']}")
        lines.append("")
    
    if "quality" in stages:
        lines.append("## Quality Standards")
        qual = stages["quality"]
        if isinstance(qual, dict):
            if "security_requirements" in qual and qual["security_requirements"]:
                lines.append("### Security")
                for sec in qual["security_requirements"][:5]:
                    lines.append(f"- {sec}")
            if "testing_requirements" in qual and qual["testing_requirements"]:
                lines.append("\n### Testing")
                for test in qual["testing_requirements"]:
                    lines.append(f"- {test}")
            if "code_quality_thresholds" in qual:
                lines.append("\n### Quality Thresholds")
                thresholds = qual["code_quality_thresholds"]
                if isinstance(thresholds, dict):
                    for key, value in thresholds.items():
                        lines.append(f"- {key}: {value}")
        lines.append("")
    
    if "implementation" in stages:
        lines.append("## Implementation Strategy")
        impl = stages["implementation"]
        if isinstance(impl, dict):
            if "tasks" in impl and impl["tasks"]:
                lines.append("### Tasks")
                for i, task in enumerate(impl["tasks"][:10], 1):
                    if isinstance(task, dict):
                        lines.append(f"{i}. {task.get('description', task.get('title', str(task)))}")
                    else:
                        lines.append(f"{i}. {task}")
            if "implementation_plan" in impl:
                plan = impl["implementation_plan"]
                if isinstance(plan, str):
                    lines.append(plan[:500] + ("..." if len(plan) > 500 else ""))
            if "task_breakdown" in impl and impl["task_breakdown"]:
                lines.append("### Task Breakdown")
                for i, task in enumerate(impl["task_breakdown"][:10], 1):
                    lines.append(f"{i}. {task}")
        lines.append("")
    
    if "synthesis" in stages:
        lines.append("## Final Synthesis")
        synth = stages["synthesis"]
        if isinstance(synth, dict):
            if "enhanced_prompt" in synth and synth["enhanced_prompt"]:
                lines.append(synth["enhanced_prompt"])
            elif "instruction" in synth:
                lines.append("### Synthesis Instruction:")
                inst_fmt = format_instruction(synth["instruction"])
                lines.append(inst_fmt)
                if "skill_command" in synth:
                    lines.append(f"\n- **Skill Command**: `{synth['skill_command']}`")
            if "metadata" in synth:
                meta = synth["metadata"]
                lines.append("\n### Synthesis Metadata:")
                for key, value in meta.items():
                    lines.append(f"- **{key}**: {value}")
        lines.append("")
    
    return "\n".join(lines)


async def run_enhancement_with_progress(prompt: str):
    """Run enhancement and print progress after each stage."""
    enhancer = EnhancerAgent()
    await enhancer.activate()
    
    try:
        # Create a session manually so we can monitor it
        config = enhancer._load_enhancement_config()
        session_id = enhancer._create_session(prompt, config)
        session = enhancer.current_session
        
        print_section(f"Starting Enhancement for: '{prompt}'")
        
        # Stage 1: Analysis
        print("\n[1/7] Running Analysis Stage...")
        session["stages"]["analysis"] = await enhancer._stage_analysis(prompt)
        enhancer._save_session(session_id, session)
        print_section("After Analysis Stage")
        print(format_stage_output(session, "Analysis"))
        
        # Stage 2: Requirements
        print("\n[2/7] Running Requirements Stage...")
        session["stages"]["requirements"] = await enhancer._stage_requirements(
            prompt, session["stages"].get("analysis", {})
        )
        enhancer._save_session(session_id, session)
        print_section("After Requirements Stage")
        print(format_stage_output(session, "Requirements"))
        
        # Stage 3: Architecture
        print("\n[3/7] Running Architecture Stage...")
        session["stages"]["architecture"] = await enhancer._stage_architecture(
            prompt, session["stages"].get("requirements", {})
        )
        enhancer._save_session(session_id, session)
        print_section("After Architecture Stage")
        print(format_stage_output(session, "Architecture"))
        
        # Stage 4: Codebase Context
        print("\n[4/7] Running Codebase Context Stage...")
        session["stages"]["codebase_context"] = await enhancer._stage_codebase_context(
            prompt, session["stages"].get("analysis", {})
        )
        enhancer._save_session(session_id, session)
        print_section("After Codebase Context Stage")
        print(format_stage_output(session, "Codebase Context"))
        
        # Stage 5: Quality
        print("\n[5/7] Running Quality Standards Stage...")
        session["stages"]["quality"] = await enhancer._stage_quality(
            prompt, session["stages"].get("requirements", {})
        )
        enhancer._save_session(session_id, session)
        print_section("After Quality Standards Stage")
        print(format_stage_output(session, "Quality Standards"))
        
        # Stage 6: Implementation
        print("\n[6/7] Running Implementation Strategy Stage...")
        session["stages"]["implementation"] = await enhancer._stage_implementation(
            prompt,
            session["stages"].get("requirements", {}),
            session["stages"].get("architecture", {}),
        )
        enhancer._save_session(session_id, session)
        print_section("After Implementation Strategy Stage")
        print(format_stage_output(session, "Implementation Strategy"))
        
        # Stage 7: Synthesis
        print("\n[7/7] Running Synthesis Stage...")
        session["stages"]["synthesis"] = await enhancer._stage_synthesis(
            prompt, session["stages"], "markdown"
        )
        enhancer._save_session(session_id, session)
        print_section("Final Enhanced Prompt (After Synthesis)")
        
        # Try to get the final enhanced prompt
        final_output = enhancer._format_output(session, "markdown")
        print(final_output)
        
        # Extract and print the actual prompt that would be passed to Cursor LLM
        print_section("ACTUAL PROMPT FOR CURSOR LLM")
        synthesis = session["stages"].get("synthesis", {})
        if "instruction" in synthesis and isinstance(synthesis["instruction"], dict):
            synthesis_prompt = synthesis["instruction"].get("prompt", "")
            if synthesis_prompt:
                print("=" * 80)
                print("This is the actual prompt text that would be sent to the Cursor LLM:")
                print("=" * 80)
                print()
                print(synthesis_prompt)
                print()
                print("=" * 80)
            else:
                print("(Synthesis prompt not found in instruction object)")
        else:
            print("(Synthesis instruction object not found)")
        
        # Explanation about empty results
        print_section("WHY ARE REQUIREMENTS/ARCHITECTURE/IMPLEMENTATION EMPTY?")
        print("""
The Enhancer Agent is designed to work with Cursor Skills. It creates instruction 
objects that are meant to be executed by the Cursor Skills system, not executed 
directly by the agents themselves.

What's happening:
1. The agents (Analyst, Architect, Planner) prepare instruction objects
2. These instructions contain prompts that would be sent to Cursor LLM
3. The instructions are NOT executed in this test rig - they're just prepared
4. To get actual requirements/architecture/etc., you need to execute these 
   instructions through Cursor Skills (e.g., using @analyst, @architect commands)

The empty arrays/objects you see are because:
- The enhancer extracts fields like "functional_requirements" from results
- But the agents return instruction objects, not actual analyzed results
- The actual analysis would happen when Cursor Skills executes the instructions

This is the intended design - the enhancer prepares comprehensive instructions 
that can then be executed through Cursor Skills to get actual enhanced prompts.
        """)
        
        print_section("Enhancement Complete")
        print(f"Session ID: {session_id}")
        session_path = Path.cwd() / ".tapps-agents" / "sessions" / f"{session_id}.json"
        print(f"Session saved to: {session_path}")
        
        return session
        
    finally:
        await enhancer.close()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_enhancer_rig.py '<your prompt>'")
        print("\nExample:")
        print("  python scripts/test_enhancer_rig.py 'Create a login system'")
        print("  python scripts/test_enhancer_rig.py 'Add payment processing'")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    
    try:
        asyncio.run(run_enhancement_with_progress(prompt))
    except KeyboardInterrupt:
        print("\n\nEnhancement interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during enhancement: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

