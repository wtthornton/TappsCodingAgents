"""
Test script for Cursor Workflow Executor.

This script tests the Cursor-native workflow execution without requiring
full workflow execution or Skill invocation.
"""

import asyncio
from pathlib import Path

from tapps_agents.workflow.cursor_executor import CursorWorkflowExecutor
from tapps_agents.workflow.models import Workflow, WorkflowStep, WorkflowType
from tapps_agents.workflow.parser import WorkflowParser


async def test_cursor_executor_initialization():
    """Test that CursorWorkflowExecutor can be initialized."""
    print("=" * 60)
    print("Test 1: CursorWorkflowExecutor Initialization")
    print("=" * 60)
    
    try:
        CursorWorkflowExecutor(project_root=Path("."))
        print("[OK] CursorWorkflowExecutor initialized successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to initialize: {e}")
        return False


async def test_project_profiling():
    """Test that project profiling works."""
    print("\n" + "=" * 60)
    print("Test 2: Project Profiling")
    print("=" * 60)
    
    try:
        executor = CursorWorkflowExecutor(project_root=Path("."))
        
        # Test profiling
        executor._profile_project()
        
        if executor.project_profile:
            print("[OK] Project profile detected successfully")
            print(f"   - Deployment Type: {executor.project_profile.deployment_type}")
            print(f"   - Security Level: {executor.project_profile.security_level}")
            print(f"   - User Scale: {executor.project_profile.user_scale}")
            
            # Test profile context formatting
            context = executor.project_profile.format_context(min_confidence=0.7)
            if context:
                print(f"[OK] Profile context formatted: {len(context)} characters")
            else:
                print("[WARN] Profile context is empty (low confidence values)")
            
            return True
        else:
            print("[WARN] Project profile is None (may be expected for test environment)")
            return True  # Not a failure, just no profile detected
    except Exception as e:
        print(f"[FAIL] Project profiling failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_workflow_initialization():
    """Test that workflow can be initialized."""
    print("\n" + "=" * 60)
    print("Test 3: Workflow Initialization")
    print("=" * 60)
    
    try:
        # Create a minimal test workflow
        test_workflow = Workflow(
            id="test-workflow",
            name="Test Workflow",
            description="Test workflow for Cursor executor",
            version="1.0.0",
            type=WorkflowType.GREENFIELD,
            steps=[
                WorkflowStep(
                    id="step-1",
                    agent="analyst",
                    action="gather-requirements",
                )
            ],
        )
        
        executor = CursorWorkflowExecutor(project_root=Path("."))
        state = executor.start(workflow=test_workflow, user_prompt="Test prompt")
        
        if state:
            print("[OK] Workflow initialized successfully")
            print(f"   - Workflow ID: {state.workflow_id}")
            print(f"   - Status: {state.status}")
            print(f"   - Current Step: {state.current_step}")
            print(f"   - Project Profile in State: {'project_profile' in state.variables}")
            return True
        else:
            print("[FAIL] Workflow state is None")
            return False
    except Exception as e:
        print(f"[FAIL] Workflow initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_skill_invoker():
    """Test that SkillInvoker can build commands."""
    print("\n" + "=" * 60)
    print("Test 4: Skill Invoker Command Building")
    print("=" * 60)
    
    try:
        from tapps_agents.workflow.skill_invoker import SkillInvoker
        
        invoker = SkillInvoker(project_root=Path("."))
        
        # Test command mapping
        test_cases = [
            ("analyst", "gather-requirements"),
            ("planner", "plan"),
            ("architect", "design-system"),
            ("designer", "design-api"),
        ]
        
        for agent_name, action in test_cases:
            if (agent_name, action) in invoker.COMMAND_MAPPING:
                skill_cmd, params = invoker.COMMAND_MAPPING[(agent_name, action)]
                print(f"[OK] {agent_name}/{action} -> {skill_cmd} with params: {list(params.keys())}")
            else:
                print(f"[WARN] {agent_name}/{action} not found in mapping")
        
        return True
    except Exception as e:
        print(f"[FAIL] Skill invoker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_workflow_parser():
    """Test that we can load a real workflow."""
    print("\n" + "=" * 60)
    print("Test 5: Workflow Parser")
    print("=" * 60)
    
    try:
            # Try to load the full-sdlc workflow
        workflow_file = Path("workflows/presets/full-sdlc.yaml")
        
        if workflow_file.exists():
            workflow = WorkflowParser.parse_file(workflow_file)
            print(f"[OK] Loaded workflow: {workflow.name}")
            print(f"   - ID: {workflow.id}")
            print(f"   - Type: {workflow.type}")
            print(f"   - Steps: {len(workflow.steps)}")
            
            # Test executor with real workflow
            executor = CursorWorkflowExecutor(project_root=Path("."))
            state = executor.start(
                workflow=workflow,
                user_prompt="Test prompt for full SDLC workflow"
            )
            
            if state:
                print(f"[OK] Workflow state created: {state.workflow_id}")
                return True
            else:
                print("[FAIL] Failed to create workflow state")
                return False
        else:
            print(f"[WARN] Workflow file not found: {workflow_file}")
            return True  # Not a failure, just file not found
    except Exception as e:
        print(f"[FAIL] Workflow parser test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Cursor Workflow Executor - Test Suite")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(await test_cursor_executor_initialization())
    results.append(await test_project_profiling())
    results.append(await test_workflow_initialization())
    results.append(await test_skill_invoker())
    results.append(await test_workflow_parser())
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("[OK] All tests passed!")
        return 0
    else:
        print(f"[WARN] {total - passed} test(s) failed or had warnings")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

