"""
Cursor integration verification utilities
"""
import json
from pathlib import Path

import yaml


def verify_cursor_integration(project_root: Path = None) -> tuple[bool, dict]:
    """
    Verify Cursor integration components are properly installed.
    
    Args:
        project_root: Root directory of the project (defaults to current directory)
        
    Returns:
        Tuple of (is_valid, results_dict)
    """
    if project_root is None:
        project_root = Path.cwd()
    
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "components": {}
    }
    
    # Check Skills directory
    skills_dir = project_root / ".claude" / "skills"
    skills_result = _verify_skills(skills_dir)
    results["components"]["skills"] = skills_result
    if not skills_result["valid"]:
        results["valid"] = False
        results["errors"].extend(skills_result["errors"])
    if skills_result["warnings"]:
        results["warnings"].extend(skills_result["warnings"])
    
    # Check Rules directory
    rules_dir = project_root / ".cursor" / "rules"
    rules_result = _verify_rules(rules_dir)
    results["components"]["rules"] = rules_result
    if not rules_result["valid"]:
        results["valid"] = False
        results["errors"].extend(rules_result["errors"])
    if rules_result["warnings"]:
        results["warnings"].extend(rules_result["warnings"])
    
    # Check Background Agents config
    bg_agents_file = project_root / ".cursor" / "background-agents.yaml"
    bg_agents_result = _verify_background_agents(bg_agents_file)
    results["components"]["background_agents"] = bg_agents_result
    if not bg_agents_result["valid"]:
        results["valid"] = False
        results["errors"].extend(bg_agents_result["errors"])
    if bg_agents_result["warnings"]:
        results["warnings"].extend(bg_agents_result["warnings"])
    
    # Check .cursorignore
    cursorignore_file = project_root / ".cursorignore"
    cursorignore_result = _verify_cursorignore(cursorignore_file)
    results["components"]["cursorignore"] = cursorignore_result
    if not cursorignore_result["valid"]:
        results["warnings"].extend(cursorignore_result["warnings"])  # Not critical
    
    # Check .cursorrules (legacy support)
    cursorrules_file = project_root / ".cursorrules"
    cursorrules_result = _verify_cursorrules(cursorrules_file)
    results["components"]["cursorrules"] = cursorrules_result
    if not cursorrules_result["valid"]:
        results["warnings"].extend(cursorrules_result["warnings"])  # Optional file
    
    return results["valid"], results


def _verify_skills(skills_dir: Path) -> dict:
    """Verify Skills directory structure"""
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "skills_found": [],
        "expected_skills": [
            "analyst", "architect", "debugger", "designer", "documenter",
            "enhancer", "implementer", "improver", "ops", "orchestrator",
            "planner", "reviewer", "tester"
        ]
    }
    
    if not skills_dir.exists():
        result["valid"] = False
        result["errors"].append(f"Skills directory not found: {skills_dir}")
        return result
    
    # Check for each expected skill
    for skill_name in result["expected_skills"]:
        skill_path = skills_dir / skill_name / "SKILL.md"
        if skill_path.exists():
            result["skills_found"].append(skill_name)
            # Verify YAML frontmatter
            try:
                with open(skill_path, encoding="utf-8") as f:
                    content = f.read()
                    if not content.startswith("---"):
                        result["warnings"].append(
                            f"Skill {skill_name}: Missing YAML frontmatter"
                        )
                    elif "name:" not in content[:500]:
                        result["warnings"].append(
                            f"Skill {skill_name}: Missing 'name' in frontmatter"
                        )
            except Exception as e:
                result["warnings"].append(
                    f"Skill {skill_name}: Error reading file: {e}"
                )
        else:
            result["valid"] = False
            result["errors"].append(f"Missing skill: {skill_name}")
    
    if len(result["skills_found"]) < len(result["expected_skills"]):
        result["warnings"].append(
            f"Found {len(result['skills_found'])}/{len(result['expected_skills'])} skills"
        )
    
    return result


def _verify_rules(rules_dir: Path) -> dict:
    """Verify Rules directory structure"""
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "rules_found": [],
        "expected_rules": [
            "workflow-presets.mdc",
            "quick-reference.mdc",
            "agent-capabilities.mdc",
            "project-context.mdc",
            "project-profiling.mdc",
            "simple-mode.mdc",
            "command-reference.mdc"
        ]
    }
    
    if not rules_dir.exists():
        result["valid"] = False
        result["errors"].append(f"Rules directory not found: {rules_dir}")
        return result
    
    # Check for each expected rule
    for rule_name in result["expected_rules"]:
        rule_path = rules_dir / rule_name
        if rule_path.exists():
            result["rules_found"].append(rule_name)
            # Verify it's a markdown file
            if not rule_name.endswith(".mdc"):
                result["warnings"].append(
                    f"Rule {rule_name}: Should have .mdc extension"
                )
        else:
            result["warnings"].append(f"Missing rule: {rule_name}")
    
    if len(result["rules_found"]) < len(result["expected_rules"]):
        result["warnings"].append(
            f"Found {len(result['rules_found'])}/{len(result['expected_rules'])} rules"
        )
    
    return result


def _verify_background_agents(bg_agents_file: Path) -> dict:
    """Verify Background Agents configuration"""
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "agents_count": 0
    }
    
    if not bg_agents_file.exists():
        result["valid"] = False
        result["errors"].append(f"Background agents config not found: {bg_agents_file}")
        return result
    
    # Verify YAML syntax
    try:
        with open(bg_agents_file, encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if config and "agents" in config:
                result["agents_count"] = len(config["agents"])
                if result["agents_count"] == 0:
                    result["warnings"].append("No agents configured in background-agents.yaml")
            else:
                result["warnings"].append("No 'agents' key found in background-agents.yaml")
    except yaml.YAMLError as e:
        result["valid"] = False
        result["errors"].append(f"Invalid YAML syntax: {e}")
    except Exception as e:
        result["warnings"].append(f"Error reading file: {e}")
    
    return result


def _verify_cursorignore(cursorignore_file: Path) -> dict:
    """Verify .cursorignore file"""
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    if not cursorignore_file.exists():
        result["warnings"].append(".cursorignore not found (optional but recommended)")
        result["valid"] = False
        return result
    
    # Check for common patterns
    try:
        with open(cursorignore_file, encoding="utf-8") as f:
            content = f.read()
            important_patterns = [".venv", "__pycache__", ".pytest_cache"]
            missing_patterns = [
                pattern for pattern in important_patterns
                if pattern not in content
            ]
            if missing_patterns:
                result["warnings"].append(
                    f"Missing recommended patterns: {', '.join(missing_patterns)}"
                )
    except Exception as e:
        result["warnings"].append(f"Error reading .cursorignore: {e}")
    
    return result


def _verify_cursorrules(cursorrules_file: Path) -> dict:
    """Verify .cursorrules file (legacy support)"""
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    if not cursorrules_file.exists():
        result["warnings"].append(".cursorrules not found (optional legacy support file)")
        result["valid"] = False
        return result
    
    return result


def format_verification_results(results: dict, format: str = "text") -> str:
    """Format verification results for display"""
    if format == "json":
        return json.dumps(results, indent=2)
    
    # Use ASCII-safe symbols for Windows compatibility
    check = "[OK]"
    cross = "[X]"
    warning = "[!]"
    folder = "[*]"
    
    # Text format
    lines = []
    lines.append("=" * 60)
    lines.append("Cursor Integration Verification")
    lines.append("=" * 60)
    lines.append("")
    
    if results["valid"]:
        lines.append(f"{check} Status: VALID")
    else:
        lines.append(f"{cross} Status: INVALID")
    
    lines.append("")
    
    # Components
    for component_name, component_result in results["components"].items():
        lines.append(f"{folder} {component_name.upper().replace('_', ' ')}")
        if component_result.get("valid", False):
            lines.append(f"   {check} Valid")
        else:
            lines.append(f"   {cross} Invalid")
        
        # Show details
        if component_name == "skills":
            skills_found = component_result.get("skills_found", [])
            expected = component_result.get("expected_skills", [])
            lines.append(f"   Found: {len(skills_found)}/{len(expected)} skills")
            if len(skills_found) < len(expected):
                missing = set(expected) - set(skills_found)
                lines.append(f"   Missing: {', '.join(missing)}")
        
        elif component_name == "rules":
            rules_found = component_result.get("rules_found", [])
            expected = component_result.get("expected_rules", [])
            lines.append(f"   Found: {len(rules_found)}/{len(expected)} rules")
        
        elif component_name == "background_agents":
            agents_count = component_result.get("agents_count", 0)
            lines.append(f"   Agents configured: {agents_count}")
        
        lines.append("")
    
    # Errors
    if results["errors"]:
        lines.append(f"{cross} ERRORS:")
        for error in results["errors"]:
            lines.append(f"   - {error}")
        lines.append("")
    
    # Warnings
    if results["warnings"]:
        lines.append(f"{warning} WARNINGS:")
        for warning_msg in results["warnings"]:
            lines.append(f"   - {warning_msg}")
        lines.append("")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)

