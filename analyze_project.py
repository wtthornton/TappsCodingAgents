"""
Analyze TappsCodingAgents project using its own agents.
This demonstrates self-hosting - using the framework to improve itself.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from tapps_agents.agents.analyst.agent import AnalystAgent
from tapps_agents.agents.ops.agent import OpsAgent
from tapps_agents.agents.planner.agent import PlannerAgent
from tapps_agents.agents.reviewer.agent import ReviewerAgent


async def analyze_code_quality() -> dict[str, Any]:
    """Analyze code quality using Reviewer Agent."""
    print("🔍 Step 1: Analyzing code quality...")

    reviewer = ReviewerAgent()
    try:
        await reviewer.activate()

        # Analyze key files
        key_files = [
            "tapps_agents/core/agent_base.py",
            "tapps_agents/core/mal.py",
            "tapps_agents/agents/reviewer/agent.py",
            "tapps_agents/cli.py",
        ]

        results = {}
        for file_path in key_files:
            path = Path(file_path)
            if path.exists():
                print(f"  Analyzing {file_path}...")
                result = await reviewer.run("score", file=str(path))
                results[file_path] = result

        return {"code_quality": results}
    except Exception as e:
        print(f"  Error: {e}")
        return {"error": str(e)}


async def check_security() -> dict[str, Any]:
    """Check for security issues using Ops Agent."""
    print("\n🔒 Step 2: Checking security and dependencies...")

    ops = OpsAgent()
    try:
        await ops.activate()

        # Check dependencies
        print("  Checking dependencies...")
        deps_result = await ops.run("*audit-dependencies")

        # Security scan on key files
        print("  Scanning for security issues...")
        security_result = await ops.run("*security-scan", target="tapps_agents")

        return {"dependencies": deps_result, "security": security_result}
    except Exception as e:
        print(f"  Error: {e}")
        return {"error": str(e)}


async def create_improvement_plan(analysis: dict[str, Any]) -> dict[str, Any]:
    """Create improvement plan using Analyst and Planner agents."""
    print("\n📋 Step 3: Creating improvement plan...")

    analyst = AnalystAgent()
    planner = PlannerAgent()

    try:
        await analyst.activate()
        await planner.activate()

        # Gather requirements for improvements
        print("  Gathering requirements...")
        requirements = await analyst.run(
            "*gather-requirements",
            description=f"Improve TappsCodingAgents framework based on analysis: {json.dumps(analysis, indent=2)[:500]}",
        )

        # Create stories for improvements
        stories = []

        # Story for code quality improvements
        if "code_quality" in analysis:
            story = await planner.run(
                "*create-story",
                description="Improve code quality scores across framework modules",
                epic="code-quality",
                priority="high",
            )
            stories.append(story)

        # Story for security improvements
        if "security" in analysis or "dependencies" in analysis:
            story = await planner.run(
                "*create-story",
                description="Address security vulnerabilities and dependency issues",
                epic="security",
                priority="high",
            )
            stories.append(story)

        return {"requirements": requirements, "stories": stories}
    except Exception as e:
        print(f"  Error: {e}")
        return {"error": str(e)}


async def main():
    """Main analysis workflow."""
    print("=" * 70)
    print("TappsCodingAgents Self-Analysis & Improvement Plan")
    print("=" * 70)
    print()

    # Collect all analysis
    analysis = {}

    # Step 1: Code quality
    quality = await analyze_code_quality()
    analysis.update(quality)

    # Step 2: Security
    security = await check_security()
    analysis.update(security)

    # Step 3: Create plan
    plan = await create_improvement_plan(analysis)

    # Combine results
    results = {"analysis": analysis, "plan": plan}

    # Save results
    output_file = Path("implementation/PROJECT_ANALYSIS.json")
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\n📊 Results saved to: {output_file}")
    print(f"\n📋 Found {len(plan.get('stories', []))} improvement stories")
    print("\nNext steps:")
    print("  1. Review the analysis in the JSON file")
    print("  2. Prioritize stories from the plan")
    print("  3. Use Implementer agent to fix issues")
    print("  4. Use Reviewer agent to verify improvements")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if "code_quality" in analysis:
        print("\nCode Quality Analysis:")
        for file, result in analysis["code_quality"].items():
            if "scoring" in result:
                score = result["scoring"].get("overall_score", 0)
                print(f"  {file}: {score:.1f}/100")

    if "dependencies" in analysis:
        print("\nDependency Audit:")
        deps = analysis.get("dependencies", {})
        if "vulnerabilities" in deps:
            vulns = deps["vulnerabilities"]
            print(f"  Vulnerabilities found: {len(vulns)}")
        else:
            print(f"  Status: {deps.get('message', 'Unknown')}")

    if "plan" in results and "stories" in results["plan"]:
        print("\nImprovement Stories:")
        for i, story in enumerate(results["plan"]["stories"], 1):
            print(
                f"  {i}. {story.get('title', 'Unknown')} - {story.get('epic', 'N/A')}"
            )


if __name__ == "__main__":
    asyncio.run(main())
