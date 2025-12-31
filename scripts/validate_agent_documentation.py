"""
Agent Documentation Validation Script

Validates that all agents are properly documented in:
- .cursor/rules/command-reference.mdc
- .cursor/rules/agent-capabilities.mdc
- CLI command parsers
- Agent directories

Usage:
    python scripts/validate_agent_documentation.py
    python scripts/validate_agent_documentation.py --verbose
    python scripts/validate_agent_documentation.py --output report.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def discover_agents_from_directory() -> list[str]:
    """Discover all agents from tapps_agents/agents/ directory."""
    agents_dir = project_root / "tapps_agents" / "agents"
    agents = []
    
    if not agents_dir.exists():
        return agents
    
    for item in agents_dir.iterdir():
        if item.is_dir() and not item.name.startswith("__") and not item.name.startswith("."):
            # Check if it has an agent.py file (indicates it's an agent)
            agent_file = item / "agent.py"
            if agent_file.exists():
                agents.append(item.name)
    
    return sorted(agents)


def discover_agents_from_cli() -> list[str]:
    """Discover all agents from CLI main.py imports."""
    cli_main = project_root / "tapps_agents" / "cli" / "main.py"
    agents = []
    
    if not cli_main.exists():
        return agents
    
    content = cli_main.read_text(encoding="utf-8")
    
    # Look for agent imports in the commands section
    expected_agents = [
        "analyst", "architect", "debugger", "designer", "documenter",
        "enhancer", "evaluator", "implementer", "improver", "ops",
        "orchestrator", "planner", "reviewer", "tester"
    ]
    
    for agent in expected_agents:
        if f"from .commands import {agent}" in content or f"import {agent}" in content:
            agents.append(agent)
    
    return sorted(agents)


def check_command_reference(agents: list[str]) -> dict[str, Any]:
    """Check if agents are documented in command-reference.mdc."""
    cmd_ref = project_root / ".cursor" / "rules" / "command-reference.mdc"
    results = {
        "file_exists": cmd_ref.exists(),
        "agents_found": [],
        "agents_missing": [],
        "content": ""
    }
    
    if not cmd_ref.exists():
        results["agents_missing"] = agents
        return results
    
    content = cmd_ref.read_text(encoding="utf-8")
    results["content"] = content[:1000]  # First 1000 chars for context
    
    for agent in agents:
        # Check for agent section or command documentation
        if f"### {agent.capitalize()}" in content or f"**{agent}**" in content or f"`{agent}`" in content:
            results["agents_found"].append(agent)
        else:
            results["agents_missing"].append(agent)
    
    return results


def check_agent_capabilities(agents: list[str]) -> dict[str, Any]:
    """Check if agents are documented in agent-capabilities.mdc."""
    agent_cap = project_root / ".cursor" / "rules" / "agent-capabilities.mdc"
    results = {
        "file_exists": agent_cap.exists(),
        "agents_found": [],
        "agents_missing": [],
        "content": ""
    }
    
    if not agent_cap.exists():
        results["agents_missing"] = agents
        return results
    
    content = agent_cap.read_text(encoding="utf-8")
    results["content"] = content[:1000]  # First 1000 chars for context
    
    for agent in agents:
        # Check for agent section
        if f"### {agent.capitalize()}" in content or f"**{agent}**" in content:
            results["agents_found"].append(agent)
        else:
            results["agents_missing"].append(agent)
    
    return results


def check_cli_commands(agents: list[str]) -> dict[str, Any]:
    """Check if agents have CLI command parsers."""
    parsers_dir = project_root / "tapps_agents" / "cli" / "parsers"
    commands_dir = project_root / "tapps_agents" / "cli" / "commands"
    
    results = {
        "agents_with_parsers": [],
        "agents_without_parsers": [],
        "agents_with_commands": [],
        "agents_without_commands": [],
    }
    
    for agent in agents:
        # Check for parser file
        parser_file = parsers_dir / f"{agent}.py"
        if parser_file.exists():
            results["agents_with_parsers"].append(agent)
        else:
            results["agents_without_parsers"].append(agent)
        
        # Check for command file
        command_file = commands_dir / f"{agent}.py"
        if command_file.exists():
            results["agents_with_commands"].append(agent)
        else:
            results["agents_without_commands"].append(agent)
    
    return results


def validate_all() -> dict[str, Any]:
    """Run all validation checks."""
    # Discover agents
    agents_from_dir = discover_agents_from_directory()
    agents_from_cli = discover_agents_from_cli()
    
    # Combine and deduplicate
    all_agents = sorted(list(set(agents_from_dir + agents_from_cli)))
    
    # Run checks
    cmd_ref_check = check_command_reference(all_agents)
    agent_cap_check = check_agent_capabilities(all_agents)
    cli_check = check_cli_commands(all_agents)
    
    # Determine overall status
    all_documented = (
        len(cmd_ref_check["agents_missing"]) == 0 and
        len(agent_cap_check["agents_missing"]) == 0 and
        len(cli_check["agents_without_parsers"]) == 0 and
        len(cli_check["agents_without_commands"]) == 0
    )
    
    return {
        "status": "PASS" if all_documented else "FAIL",
        "agents_discovered": {
            "from_directory": agents_from_dir,
            "from_cli": agents_from_cli,
            "total_unique": all_agents,
            "count": len(all_agents)
        },
        "command_reference": cmd_ref_check,
        "agent_capabilities": agent_cap_check,
        "cli_integration": cli_check,
        "summary": {
            "total_agents": len(all_agents),
            "documented_in_command_reference": len(cmd_ref_check["agents_found"]),
            "documented_in_agent_capabilities": len(agent_cap_check["agents_found"]),
            "have_cli_parsers": len(cli_check["agents_with_parsers"]),
            "have_cli_commands": len(cli_check["agents_with_commands"]),
        }
    }


def print_report(results: dict[str, Any], verbose: bool = False) -> None:
    """Print validation report."""
    print("=" * 80)
    print("Agent Documentation Validation Report")
    print("=" * 80)
    print()
    
    # Summary
    summary = results["summary"]
    print(f"Total Agents Discovered: {summary['total_agents']}")
    print(f"Status: {results['status']}")
    print()
    
    # Agents list
    agents = results["agents_discovered"]["total_unique"]
    print(f"Agents ({len(agents)}):")
    for agent in agents:
        print(f"  - {agent}")
    print()
    
    # Command Reference Check
    cmd_ref = results["command_reference"]
    print(f"Command Reference (.cursor/rules/command-reference.mdc):")
    print(f"  File exists: {cmd_ref['file_exists']}")
    print(f"  Agents documented: {len(cmd_ref['agents_found'])}/{summary['total_agents']}")
    if cmd_ref["agents_missing"]:
        print(f"  Missing: {', '.join(cmd_ref['agents_missing'])}")
    print()
    
    # Agent Capabilities Check
    agent_cap = results["agent_capabilities"]
    print(f"Agent Capabilities (.cursor/rules/agent-capabilities.mdc):")
    print(f"  File exists: {agent_cap['file_exists']}")
    print(f"  Agents documented: {len(agent_cap['agents_found'])}/{summary['total_agents']}")
    if agent_cap["agents_missing"]:
        print(f"  Missing: {', '.join(agent_cap['agents_missing'])}")
    print()
    
    # CLI Integration Check
    cli = results["cli_integration"]
    print(f"CLI Integration:")
    print(f"  Agents with parsers: {len(cli['agents_with_parsers'])}/{summary['total_agents']}")
    if cli["agents_without_parsers"]:
        print(f"  Missing parsers: {', '.join(cli['agents_without_parsers'])}")
    print(f"  Agents with commands: {len(cli['agents_with_commands'])}/{summary['total_agents']}")
    if cli["agents_without_commands"]:
        print(f"  Missing commands: {', '.join(cli['agents_without_commands'])}")
    print()
    
    if verbose:
        print("Detailed Information:")
        print(json.dumps(results, indent=2, default=str))
        print()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate agent documentation completeness"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output JSON report to file"
    )
    
    args = parser.parse_args()
    
    # Run validation
    results = validate_all()
    
    # Print report
    print_report(results, verbose=args.verbose)
    
    # Save JSON if requested
    if args.output:
        args.output.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
        print(f"Report saved to: {args.output}")
    
    # Return exit code
    return 0 if results["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
