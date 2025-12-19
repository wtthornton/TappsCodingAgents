#!/usr/bin/env python3
"""
TappsCodingAgents Framework Validation Script

This script validates that the framework is working correctly by testing:
- CLI availability
- Core agent functionality
- Expert system
- Configuration loading
- Workflow system
- Basic integrations

Run with: python scripts/validate_framework.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Imports after sys.path modification are intentional
from tapps_agents.core.config import get_default_config, load_config  # noqa: E402
from tapps_agents.core.project_profile import load_project_profile  # noqa: E402
from tapps_agents.experts.builtin_registry import BuiltinExpertRegistry  # noqa: E402
from tapps_agents.experts.expert_registry import ExpertRegistry  # noqa: E402
from tapps_agents.workflow.detector import ProjectDetector  # noqa: E402
from tapps_agents.workflow.parser import WorkflowParser  # noqa: E402


class ValidationResult:
    """Track validation results."""
    
    def __init__(self):
        self.passed: list[str] = []
        self.failed: list[tuple[str, str]] = []
        self.warnings: list[str] = []
    
    def add_pass(self, test_name: str):
        self.passed.append(test_name)
        print(f"[PASS] {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        print(f"[FAIL] {test_name}: {error}")
    
    def add_warning(self, test_name: str, message: str):
        self.warnings.append(f"{test_name}: {message}")
        print(f"[WARN] {test_name}: {message}")
    
    def print_summary(self):
        print("\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)
        print(f"[PASS] Passed: {len(self.passed)}")
        print(f"[FAIL] Failed: {len(self.failed)}")
        print(f"[WARN] Warnings: {len(self.warnings)}")
        
        if self.failed:
            print("\nFailed Tests:")
            for test_name, error in self.failed:
                print(f"  - {test_name}: {error}")
        
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        print("\n" + "="*70)
        
        if self.failed:
            print("[FAIL] VALIDATION FAILED - Some tests did not pass")
            return False
        elif self.warnings:
            print("[WARN] VALIDATION PASSED WITH WARNINGS")
            return True
        else:
            print("[PASS] VALIDATION PASSED - All tests successful")
            return True


def test_config_loading(result: ValidationResult):
    """Test configuration loading."""
    try:
        # Test default config
        default_config = get_default_config()
        assert default_config is not None, "Default config should not be None"
        result.add_pass("Config: Default config loads")
        
        # Test config loading from file (if exists)
        config_path = project_root / ".tapps-agents" / "config.yaml"
        if config_path.exists():
            try:
                config = load_config(project_root)
                assert config is not None, "Config file should load"
                result.add_pass("Config: File-based config loads")
            except PermissionError:
                result.add_warning("Config", "Permission denied loading config (may need admin)")
            except Exception as e:
                result.add_warning("Config", f"Config file exists but couldn't load: {str(e)}")
        else:
            result.add_warning("Config", "No .tapps-agents/config.yaml found (optional)")
        
    except Exception as e:
        result.add_fail("Config: Configuration loading", str(e))




def test_builtin_experts(result: ValidationResult):
    """Test built-in expert registry."""
    try:
        # BuiltinExpertRegistry is a class with static methods
        # Check that it has the BUILTIN_EXPERTS list
        experts = BuiltinExpertRegistry.BUILTIN_EXPERTS
        assert len(experts) > 0, "Should have at least one built-in expert"
        result.add_pass(f"Experts: {len(experts)} built-in experts defined")
        
        # Check for key experts
        key_experts = ["expert-security", "expert-performance", "expert-testing"]
        expert_ids = [e.expert_id for e in experts]
        for expert_id in key_experts:
            if expert_id in expert_ids:
                result.add_pass(f"Experts: {expert_id} available")
            else:
                result.add_warning("Experts", f"{expert_id} not found (may be optional)")
        
    except Exception as e:
        result.add_fail("Experts: BuiltinExpertRegistry", str(e))


def test_expert_registry(result: ValidationResult):
    """Test expert registry system."""
    try:
        registry = ExpertRegistry(load_builtin=True)
        assert registry is not None, "ExpertRegistry should initialize"
        result.add_pass("Experts: ExpertRegistry initialization")
        
        # Test expert listing
        experts = registry.list_experts()
        assert len(experts) > 0, "Should have experts available"
        result.add_pass(f"Experts: {len(experts)} total experts available")
        
    except Exception as e:
        result.add_fail("Experts: ExpertRegistry", str(e))


def test_workflow_parser(result: ValidationResult):
    """Test workflow parser."""
    try:
        parser = WorkflowParser()
        assert parser is not None, "WorkflowParser should initialize"
        result.add_pass("Workflow: Parser initialization")
        
        # Try to parse example workflow if it exists
        workflow_dir = project_root / "workflows"
        if workflow_dir.exists():
            workflow_files = list(workflow_dir.glob("*.yaml"))
            if workflow_files:
                test_workflow = workflow_files[0]
                workflow = parser.parse_file(test_workflow)
                assert workflow is not None, "Should parse workflow file"
                result.add_pass(f"Workflow: Can parse {test_workflow.name}")
            else:
                result.add_warning("Workflow", "No workflow files found in workflows/")
        else:
            result.add_warning("Workflow", "workflows/ directory not found")
        
    except Exception as e:
        result.add_fail("Workflow: Parser", str(e))


def test_project_detector(result: ValidationResult):
    """Test project detector."""
    try:
        detector = ProjectDetector(project_root)
        assert detector is not None, "ProjectDetector should initialize"
        result.add_pass("Project: Detector initialization")
        
        # Test project characteristics detection
        characteristics = detector.detect()
        assert characteristics is not None, "Should detect project characteristics"
        result.add_pass(f"Project: Detected type: {characteristics.project_type.value}")
        
    except Exception as e:
        result.add_fail("Project: Detector", str(e))


def test_project_profiling(result: ValidationResult):
    """Test project profiling system."""
    try:
        # Try to load existing profile if it exists
        profile = load_project_profile(project_root)
        if profile:
            result.add_pass("Profile: Project profile loaded")
            if profile.deployment_type:
                result.add_pass(f"Profile: Deployment type: {profile.deployment_type}")
        else:
            result.add_warning("Profile", "No project profile found (optional - can be created)")
        
    except Exception as e:
        result.add_warning("Profile", f"Project profiling - {str(e)}")


def test_imports(result: ValidationResult):
    """Test that key modules can be imported."""
    modules_to_test = [
        ("tapps_agents.core.agent_base", "BaseAgent"),
        ("tapps_agents.agents.reviewer.agent", "ReviewerAgent"),
        ("tapps_agents.agents.implementer.agent", "ImplementerAgent"),
        ("tapps_agents.agents.tester.agent", "TesterAgent"),
        ("tapps_agents.agents.reviewer.scoring", "CodeScorer"),
    ]
    
    for module_path, class_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            assert cls is not None, f"{class_name} should be importable"
            result.add_pass(f"Import: {class_name}")
        except Exception as e:
            result.add_fail(f"Import: {class_name}", str(e))


async def main():
    """Run all validation tests."""
    print("="*70)
    print("TappsCodingAgents Framework Validation")
    print("="*70)
    print(f"Project Root: {project_root}")
    print()
    
    result = ValidationResult()
    
    # Run synchronous tests
    print("Running Configuration Tests...")
    test_config_loading(result)
    print()
    
    print("Running Expert System Tests...")
    test_builtin_experts(result)
    test_expert_registry(result)
    print()
    
    print("Running Workflow Tests...")
    test_workflow_parser(result)
    print()
    
    print("Running Project Detection Tests...")
    test_project_detector(result)
    test_project_profiling(result)
    print()
    
    print("Running Import Tests...")
    test_imports(result)
    print()
    
    # Print summary
    success = result.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

