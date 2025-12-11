"""
Script to analyze TappsCodingAgents project, create a plan, and execute fixes.
Uses the framework's own agents to improve itself.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any

from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tapps_agents.agents.analyst.agent import AnalystAgent
from tapps_agents.agents.planner.agent import PlannerAgent
from tapps_agents.agents.implementer.agent import ImplementerAgent
from tapps_agents.agents.ops.agent import OpsAgent
from tapps_agents.core.config import load_config


async def analyze_project() -> Dict[str, Any]:
    """Analyze the entire project for issues."""
    print("🔍 Analyzing TappsCodingAgents project...")
    
    reviewer = ReviewerAgent()
    try:
        await reviewer.activate()
        
        # Analyze project (command is "analyze-project" not "*analyze-project")
        result = await reviewer.run(
            "analyze-project",
            project_root=".",
            include_comparison=True
        )
        
        return result
    finally:
        await reviewer.close()


async def check_dependencies() -> Dict[str, Any]:
    """Check for dependency vulnerabilities."""
    print("🔒 Checking dependencies for security issues...")
    
    ops = OpsAgent()
    try:
        await ops.activate()
        
        result = await ops.run("*audit-dependencies")
        
        return result
    except Exception as e:
        print(f"Warning: Dependency check failed: {e}")
        return {"error": str(e)}


async def create_improvement_plan(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Create a plan to fix identified issues."""
    print("📋 Creating improvement plan...")
    
    analyst = AnalystAgent()
    planner = PlannerAgent()
    
    try:
        await analyst.activate()
        await planner.activate()
        
        # Gather requirements for improvements
        requirements = await analyst.run(
            "*gather-requirements",
            description=f"Fix issues found in project analysis: {json.dumps(analysis_results, indent=2)}"
        )
        
        # Create stories for each major issue category
        stories = []
        
        if "services" in analysis_results:
            for service_name, service_data in analysis_results["services"].items():
                if service_data.get("overall_score", 100) < 70:
                    story = await planner.run(
                        "*create-story",
                        description=f"Improve code quality in {service_name} (current score: {service_data.get('overall_score', 0):.1f})",
                        epic="code-quality",
                        priority="high"
                    )
                    stories.append(story)
        
        if "vulnerabilities" in analysis_results or "issues" in analysis_results:
            story = await planner.run(
                "*create-story",
                description="Fix security vulnerabilities and code issues",
                epic="security",
                priority="high"
            )
            stories.append(story)
        
        return {
            "requirements": requirements,
            "stories": stories,
            "analysis": analysis_results
        }
    finally:
        await analyst.close()
        await planner.close()


async def execute_fixes(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute fixes based on the plan."""
    print("🔧 Executing fixes...")
    
    implementer = ImplementerAgent()
    improver = ImplementerAgent()  # Can also use ImproverAgent
    
    results = []
    
    try:
        await implementer.activate()
        
        # Execute fixes for each story
        for story in plan.get("stories", []):
            print(f"\n📝 Working on: {story.get('title', 'Unknown story')}")
            
            # Use implementer to fix issues
            fix_result = await implementer.run(
                "*refactor",
                file=story.get("affected_files", ["."])[0] if story.get("affected_files") else ".",
                instruction=f"Fix issues identified: {story.get('description', '')}"
            )
            
            results.append({
                "story": story,
                "fix_result": fix_result
            })
        
        return results
    finally:
        await implementer.close()


async def main():
    """Main workflow: Analyze → Plan → Execute."""
    print("=" * 60)
    print("TappsCodingAgents Self-Improvement Workflow")
    print("=" * 60)
    print()
    
    # Step 1: Analyze project
    analysis = await analyze_project()
    
    print("\n" + "=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)
    print(json.dumps(analysis, indent=2))
    
    # Step 2: Check dependencies
    deps = await check_dependencies()
    if deps:
        analysis["dependencies"] = deps
        print("\n" + "=" * 60)
        print("DEPENDENCY AUDIT RESULTS")
        print("=" * 60)
        print(json.dumps(deps, indent=2))
    
    # Step 3: Create plan
    plan = await create_improvement_plan(analysis)
    
    print("\n" + "=" * 60)
    print("IMPROVEMENT PLAN")
    print("=" * 60)
    print(json.dumps(plan, indent=2))
    
    # Save plan to file
    plan_file = Path("implementation/IMPROVEMENT_PLAN.json")
    plan_file.parent.mkdir(exist_ok=True)
    with open(plan_file, "w") as f:
        json.dump(plan, f, indent=2)
    print(f"\n💾 Plan saved to: {plan_file}")
    
    # Step 4: Ask for confirmation before executing
    print("\n" + "=" * 60)
    print("READY TO EXECUTE FIXES")
    print("=" * 60)
    print(f"Found {len(plan.get('stories', []))} improvement stories")
    print("\nReview the plan above, then run:")
    print("  python analyze_and_fix.py --execute")
    print("\nOr review the plan file:")
    print(f"  {plan_file}")


if __name__ == "__main__":
    import sys
    
    if "--execute" in sys.argv:
        # Run full workflow including execution
        async def full_workflow():
            analysis = await analyze_project()
            deps = await check_dependencies()
            if deps:
                analysis["dependencies"] = deps
            plan = await create_improvement_plan(analysis)
            results = await execute_fixes(plan)
            
            print("\n" + "=" * 60)
            print("EXECUTION RESULTS")
            print("=" * 60)
            print(json.dumps(results, indent=2))
        
        asyncio.run(full_workflow())
    else:
        # Just analyze and plan
        asyncio.run(main())

