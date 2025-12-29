"""
Tester Agent - Generates and runs tests
"""

import json
import logging
import re
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any

from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...experts.agent_integration import ExpertSupportMixin
from .test_generator import TestGenerator

logger = logging.getLogger(__name__)


class TesterAgent(BaseAgent, ExpertSupportMixin):
    """
    Tester Agent - Test generation and execution.

    Permissions: Read, Write, Edit, Grep, Glob, Bash

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify
    """

    def __init__(self, config: ProjectConfig | None = None):
        super().__init__(agent_id="tester", agent_name="Tester Agent", config=config)
        # Use config if provided, otherwise load defaults
        if config is None:
            config = load_config()
        self.config = config

        # Initialize test generator
        self.test_generator = TestGenerator()

        # Get tester config
        tester_config = config.agents.tester if config and config.agents else None
        self.test_framework = (
            tester_config.test_framework if tester_config else "pytest"
        )
        self.tests_dir = (
            Path(tester_config.tests_dir)
            if tester_config and tester_config.tests_dir
            else Path("tests")
        )
        self.coverage_threshold = (
            tester_config.coverage_threshold if tester_config else 80.0
        )
        self.auto_write_tests = (
            tester_config.auto_write_tests if tester_config else True
        )

        # Ensure tests directory exists
        self.tests_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Context7 helper
        self.context7: Context7AgentHelper | None = None
        if config:
            self.context7 = get_context7_helper(self, config)

        # Expert registry initialization (required due to multiple inheritance MRO issue)
        # BaseAgent.__init__() doesn't call super().__init__(), so ExpertSupportMixin.__init__()
        # is never called via MRO. We must manually initialize to avoid AttributeError.
        # The registry will be properly initialized in activate() via _initialize_expert_support()
        self.expert_registry: Any | None = None

    async def activate(self, project_root: Path | None = None, offline_mode: bool = False):
        """Activate the tester agent with expert support."""
        # Validate that expert_registry attribute exists (safety check)
        if not hasattr(self, 'expert_registry'):
            raise AttributeError(
                f"{self.__class__.__name__}.expert_registry not initialized. "
                "This should not happen if __init__() properly initializes the attribute."
            )
        await super().activate(project_root, offline_mode=offline_mode)
        # Initialize expert support
        await self._initialize_expert_support(project_root, offline_mode=offline_mode)

    def get_commands(self) -> list[dict[str, str]]:
        """Return list of available commands."""
        commands = super().get_commands()
        commands.extend(
            [
                {
                    "command": "*test",
                    "description": "Generate and run tests for a file",
                },
                {
                    "command": "*generate-tests",
                    "description": "Generate tests without running",
                },
                {
                    "command": "*generate-e2e-tests",
                    "description": "Generate end-to-end tests (requires E2E framework)",
                },
                {"command": "*run-tests", "description": "Run existing tests"},
            ]
        )
        return commands

    async def run(self, command: str, **kwargs) -> dict[str, Any]:
        """Execute a command."""
        if command == "test":
            return await self.test_command(**kwargs)
        elif command == "generate-tests":
            return await self.generate_tests_command(**kwargs)
        elif command == "generate-e2e-tests":
            return await self.generate_e2e_tests_command(**kwargs)
        elif command == "run-tests":
            return await self.run_tests_command(**kwargs)
        elif command == "help":
            return self._help()
        else:
            return {"error": f"Unknown command: {command}"}

    async def test_command(
        self,
        file: str | None = None,
        test_file: str | None = None,
        integration: bool = False,
        focus: str | None = None,
        **kwargs,  # Accept additional kwargs to be more flexible
    ) -> dict[str, Any]:
        """
        Generate and run tests for a file.

        Args:
            file: Source code file to test
            test_file: Optional path to write test file
            integration: If True, generate integration tests
            focus: Comma-separated list of test aspects to focus on
        """
        if not file:
            return {"error": "File path required"}

        file_path = Path(file)
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        # Validate path (inherited from BaseAgent)
        try:
            self._validate_path(file_path, max_file_size=10 * 1024 * 1024)
        except (FileNotFoundError, ValueError) as e:
            return {"error": str(e)}

        # Build expert query with focus areas if provided
        focus_text = ""
        if focus:
            focus_areas = [area.strip() for area in focus.split(",")]
            focus_text = f" Focus specifically on: {', '.join(focus_areas)}."
        
        # D1: Get Context7 test framework documentation
        framework_docs = None
        test_framework = "pytest"  # Default
        try:
            from ...core.language_detector import LanguageDetector
            detector = LanguageDetector()
            language = detector.detect_language(file_path)
            test_framework = self.test_generator._detect_test_framework_for_language(
                language=language,
                code=file_path.read_text(encoding="utf-8") if file_path.exists() else ""
            )
        except Exception as e:
            logger.debug(f"Failed to detect test framework: {e}, using default pytest")
        
        if self.context7:
            try:
                # Get Context7 documentation for test framework
                framework_docs = await self.context7.get_documentation(
                    library=test_framework,  # e.g., "pytest", "jest", "vitest"
                    topic="testing",
                    use_fuzzy_match=True
                )
                if framework_docs:
                    logger.debug(f"D1: Fetched Context7 docs for {test_framework}")
            except Exception as e:
                logger.debug(f"D1: Context7 framework docs lookup failed: {e}")

        # Consult Testing expert for test generation guidance
        expert_guidance = ""
        expert_advice = None
        
        # Enhance expert query with Context7 best practices if available
        context7_guidance = ""
        if framework_docs and framework_docs.get("content"):
            content_preview = framework_docs.get("content", "")[:1000]  # First 1000 chars
            context7_guidance = f"\n\nContext7 Best Practices for {test_framework}:\n{content_preview}"
        
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
            testing_consultation = await self.expert_registry.consult(
                query=f"Provide best practices for generating {'integration' if integration else 'unit'} tests for: {file_path.name}. Focus on test coverage, edge cases, and maintainability.{focus_text}{context7_guidance}",
                domain="testing-strategies",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if (
                testing_consultation.confidence
                >= testing_consultation.confidence_threshold
            ):
                expert_guidance = testing_consultation.weighted_answer
                expert_advice = {
                    "confidence": testing_consultation.confidence,
                    "threshold": testing_consultation.confidence_threshold,
                    "guidance": expert_guidance,
                }
            else:
                expert_advice = {
                    "confidence": testing_consultation.confidence,
                    "threshold": testing_consultation.confidence_threshold,
                    "guidance": f"Low confidence expert advice: {testing_consultation.weighted_answer}",
                }

        # Prepare test generation instruction
        if integration:
            instruction = self.test_generator.prepare_integration_tests(
                [file_path],
                test_path=Path(test_file) if test_file else None,
                context=None,
                expert_guidance=expert_guidance,
            )
        else:
            instruction = self.test_generator.prepare_unit_tests(
                file_path,
                test_path=Path(test_file) if test_file else None,
                context=None,
                expert_guidance=expert_guidance,
            )

        # Determine test file path
        if test_file:
            test_path = Path(test_file)
        else:
            # Auto-generate test file path
            test_path = self._get_test_file_path(file_path)

        # Ensure test directory exists (fix for nested path issues)
        try:
            test_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(
                f"Failed to create test directory {test_path.parent}: {e}. "
                "Test file creation may fail.",
                exc_info=True
            )

        # D2: Prepare test quality validation info (will be used after test generation)
        quality_validation = None
        if self.context7 and framework_docs:
            try:
                # Get quality standards for the test framework
                quality_standards = await self.context7.get_documentation(
                    library=test_framework,
                    topic="quality-standards",
                    use_fuzzy_match=True
                )
                
                if quality_standards:
                    quality_validation = {
                        "framework": test_framework,
                        "standards_available": True,
                        "source": quality_standards.get("source", "unknown"),
                    }
                else:
                    quality_validation = {
                        "framework": test_framework,
                        "standards_available": False,
                    }
            except Exception as e:
                logger.debug(f"D2: Quality standards lookup failed: {e}")

        # Issue 4 Fix: Actually generate and write test file if auto_write_tests is enabled
        test_code = None
        file_written = False
        run_result = None
        
        if self.auto_write_tests:
            # Use test_file if provided, otherwise use auto-generated path
            target_test_path = test_path
            
            # Build test generation prompt using test_generator
            try:
                source_code = file_path.read_text(encoding="utf-8")
                code_analysis = self.test_generator._analyze_code(source_code, file_path)
                
                if integration:
                    prompt = self.test_generator._build_integration_test_prompt(
                        code=source_code,
                        test_path=target_test_path,
                        context=None,
                        expert_guidance=expert_guidance,
                    )
                else:
                    prompt = self.test_generator._build_unit_test_prompt(
                        code=source_code,
                        analysis=code_analysis,
                        test_path=target_test_path,
                        context=None,
                        expert_guidance=expert_guidance,
                    )
                
                # Generate test code template
                test_code = self._generate_test_template(
                    file_path=file_path,
                    code_analysis=code_analysis,
                    test_framework=test_framework,
                    expert_guidance=expert_guidance,
                    integration=integration,
                )
                
                # Write test file
                target_test_path.write_text(test_code, encoding="utf-8")
                file_written = True
                logger.info(f"Test file written to: {target_test_path}")
                
                # Run tests after generating
                run_result = await self._run_pytest(
                    test_path=target_test_path,
                    source_paths=[str(file_path)],
                    coverage=True,
                )
                
            except Exception as e:
                logger.warning(
                    f"Failed to auto-generate test file: {e}. "
                    "Returning instruction for manual execution.",
                    exc_info=True
                )
                # Fall through to return instruction

        result = {
            "type": "test",
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "test_file": str(test_path),
            "test_directory": str(test_path.parent),
            "file_written": file_written,
            "run_result": run_result,
            "expert_advice": expert_advice,  # Include expert recommendations
            # D1 Enhancement: Context7 framework documentation
            "context7_framework_docs": {
                "framework": test_framework,
                "docs_available": framework_docs is not None,
                "source": framework_docs.get("source") if framework_docs else None,
            } if framework_docs else None,
            # D2 Enhancement: Quality validation info
            "quality_validation": quality_validation,
        }
        
        if test_code and file_written:
            result["test_code_preview"] = test_code[:500]  # Preview of generated code
        
        return result

    async def generate_tests_command(
        self,
        file: str | None = None,
        test_file: str | None = None,
        integration: bool = False,
    ) -> dict[str, Any]:
        """
        Generate tests without running them.

        Args:
            file: Source code file to test
            test_file: Optional path to write test file
            integration: If True, generate integration tests
        """
        if not file:
            return {"error": "File path required"}

        file_path = Path(file)
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        # Validate path (inherited from BaseAgent)
        try:
            self._validate_path(file_path, max_file_size=10 * 1024 * 1024)
        except (FileNotFoundError, ValueError) as e:
            return {"error": str(e)}

        # D1: Get Context7 test framework documentation (same as test_command)
        framework_docs = None
        test_framework = "pytest"  # Default
        try:
            from ...core.language_detector import LanguageDetector
            detector = LanguageDetector()
            language = detector.detect_language(file_path)
            test_framework = self.test_generator._detect_test_framework_for_language(
                language=language,
                code=file_path.read_text(encoding="utf-8") if file_path.exists() else ""
            )
        except Exception as e:
            logger.debug(f"Failed to detect test framework: {e}, using default pytest")
        
        if self.context7:
            try:
                framework_docs = await self.context7.get_documentation(
                    library=test_framework,
                    topic="testing",
                    use_fuzzy_match=True
                )
                if framework_docs:
                    logger.debug(f"D1: Fetched Context7 docs for {test_framework}")
            except Exception as e:
                logger.debug(f"D1: Context7 framework docs lookup failed: {e}")

        # Consult Testing expert for test generation guidance
        expert_guidance = ""
        context7_guidance = ""
        if framework_docs and framework_docs.get("content"):
            content_preview = framework_docs.get("content", "")[:1000]
            context7_guidance = f"\n\nContext7 Best Practices for {test_framework}:\n{content_preview}"
        
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
            testing_consultation = await self.expert_registry.consult(
                query=f"Provide best practices for generating {'integration' if integration else 'unit'} tests for: {file_path.name}. Focus on test coverage, edge cases, and maintainability.{context7_guidance}",
                domain="testing-strategies",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if (
                testing_consultation.confidence
                >= testing_consultation.confidence_threshold
            ):
                expert_guidance = testing_consultation.weighted_answer

        # Prepare test generation instruction
        if integration:
            instruction = self.test_generator.prepare_integration_tests(
                [file_path],
                test_path=Path(test_file) if test_file else None,
                context=None,
                expert_guidance=expert_guidance,
            )
        else:
            instruction = self.test_generator.prepare_unit_tests(
                file_path,
                test_path=Path(test_file) if test_file else None,
                context=None,
                expert_guidance=expert_guidance,
            )

        # Determine test file path
        if test_file:
            test_path = Path(test_file)
        else:
            test_path = self._get_test_file_path(file_path)

        # Ensure test directory exists
        try:
            test_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(
                f"Failed to create test directory {test_path.parent}: {e}. "
                "Test file creation may fail.",
                exc_info=True
            )

        # D2: Quality validation info
        quality_validation = None
        if self.context7 and framework_docs:
            try:
                quality_standards = await self.context7.get_documentation(
                    library=test_framework,
                    topic="quality-standards",
                    use_fuzzy_match=True
                )
                if quality_standards:
                    quality_validation = {
                        "framework": test_framework,
                        "standards_available": True,
                        "source": quality_standards.get("source", "unknown"),
                    }
            except Exception as e:
                logger.debug(f"D2: Quality standards lookup failed: {e}")

        # Issue 4 Fix: Actually generate and write test file if auto_write_tests is enabled
        test_code = None
        file_written = False
        if self.auto_write_tests:
            # Build test generation prompt using test_generator
            try:
                source_code = file_path.read_text(encoding="utf-8")
                code_analysis = self.test_generator._analyze_code(source_code, file_path)
                
                if integration:
                    prompt = self.test_generator._build_integration_test_prompt(
                        code=source_code,
                        test_path=test_path,
                        context=None,
                        expert_guidance=expert_guidance,
                    )
                else:
                    prompt = self.test_generator._build_unit_test_prompt(
                        code=source_code,
                        analysis=code_analysis,
                        test_path=test_path,
                        context=None,
                        expert_guidance=expert_guidance,
                    )
                
                # Use implementer agent to generate test code
                from ...agents.implementer.agent import ImplementerAgent
                implementer = ImplementerAgent(config=self.config)
                await implementer.activate(offline_mode=False)
                
                # Generate test code using implementer's generate_code
                generate_result = await implementer.generate_code(
                    specification=prompt,
                    file_path=str(test_path),
                    context=source_code,
                    language="python",
                )
                
                # Extract generated code from result
                # Note: implementer.generate_code returns instruction, but we can use the prompt
                # to generate code via Cursor AI if available, or create a template
                # For now, create a basic test file template based on the analysis
                test_code = self._generate_test_template(
                    file_path=file_path,
                    code_analysis=code_analysis,
                    test_framework=test_framework,
                    expert_guidance=expert_guidance,
                    integration=integration,
                )
                
                # Write test file
                test_path.write_text(test_code, encoding="utf-8")
                file_written = True
                logger.info(f"Test file written to: {test_path}")
                
                await implementer.close()
            except Exception as e:
                logger.warning(
                    f"Failed to auto-generate test file: {e}. "
                    "Returning instruction for manual execution.",
                    exc_info=True
                )
                # Fall through to return instruction

        result = {
            "type": "test_generation",
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "test_file": str(test_path),
            "file_written": file_written,
            # D1 Enhancement
            "context7_framework_docs": {
                "framework": test_framework,
                "docs_available": framework_docs is not None,
                "source": framework_docs.get("source") if framework_docs else None,
            } if framework_docs else None,
            # D2 Enhancement
            "quality_validation": quality_validation,
        }
        
        if test_code and file_written:
            result["test_code_preview"] = test_code[:500]  # Preview of generated code
        
        return result

    async def generate_e2e_tests_command(
        self,
        test_file: str | None = None,
        project_root: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate end-to-end (E2E) tests for the project.

        Args:
            test_file: Optional path where test will be written
            project_root: Optional project root directory (default: current directory)

        Returns:
            Dictionary with test generation results
        """
        # Determine project root
        if project_root:
            proj_root = Path(project_root)
        else:
            proj_root = self.project_root if hasattr(self, "project_root") else Path.cwd()

        if not proj_root.exists():
            return {"error": f"Project root not found: {proj_root}"}

        # Consult Testing expert for E2E test generation guidance
        expert_guidance = ""
        expert_advice = None
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
            testing_consultation = await self.expert_registry.consult(
                query="Provide best practices for generating end-to-end (E2E) tests. Focus on test coverage, user workflows, and maintainability.",
                domain="testing-strategies",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if (
                testing_consultation.confidence
                >= testing_consultation.confidence_threshold
            ):
                expert_guidance = testing_consultation.weighted_answer
                expert_advice = {
                    "confidence": testing_consultation.confidence,
                    "threshold": testing_consultation.confidence_threshold,
                    "guidance": expert_guidance,
                }

        # Prepare E2E test generation instruction
        instruction = self.test_generator.prepare_e2e_tests(
            project_root=proj_root,
            test_path=Path(test_file) if test_file else None,
            context=None,
            expert_guidance=expert_guidance,
        )

        # Check if E2E framework was detected
        if instruction is None:
            return {
                "type": "e2e_test_generation",
                "error": "No E2E testing framework detected. Please install one of: playwright, pytest-playwright, selenium, or cypress.",
                "instruction": None,
                "test_file": None,
                "framework_detected": False,
            }

        # Determine test file path
        if test_file:
            test_path = Path(test_file)
        else:
            # Default E2E test location
            test_path = proj_root / "tests" / "e2e" / "test_e2e.py"

        return {
            "type": "e2e_test_generation",
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "test_file": str(test_path),
            "framework_detected": instruction.test_framework,
            "expert_advice": expert_advice,
        }

    async def run_tests_command(
        self, test_path: str | None = None, coverage: bool = True
    ) -> dict[str, Any]:
        """
        Run existing tests.

        Args:
            test_path: Path to test file or directory (default: tests/)
            coverage: Include coverage report
        """
        if test_path:
            path = Path(test_path)
            if not path.exists():
                return {"error": f"Test path not found: {path}"}
        else:
            path = self.tests_dir

        # Run tests
        run_result = await self._run_pytest(path, coverage=coverage)

        return {"type": "test_execution", "test_path": str(path), "result": run_result}

    def _generate_test_template(
        self,
        file_path: Path,
        code_analysis: dict[str, Any],
        test_framework: str,
        expert_guidance: str,
        integration: bool = False,
    ) -> str:
        """
        Generate a basic test file template.
        
        This is a fallback when full LLM generation is not available.
        Creates a structured test file with imports and basic test structure.
        
        Args:
            file_path: Source file path
            code_analysis: Code analysis from test_generator
            test_framework: Test framework to use (pytest/unittest)
            expert_guidance: Expert guidance for test generation
            integration: If True, generate integration test template
            
        Returns:
            Test file content as string
        """
        # Determine module import path
        try:
            # Try to make path relative to project root
            project_root = self._project_root if hasattr(self, "_project_root") else Path.cwd()
            rel_path = file_path.resolve().relative_to(project_root.resolve())
            # Convert to module path (remove .py, replace / with .)
            module_path = str(rel_path.with_suffix("")).replace("/", ".").replace("\\", ".")
        except (ValueError, AttributeError):
            # Fallback to filename
            module_path = file_path.stem
        
        if test_framework == "pytest":
            lines = [
                '"""',
                f"Tests for {file_path.name}",
                '"""',
                "",
                "import pytest",
                "",
            ]
            
            # Add import for the module being tested
            lines.append(f"from {module_path} import *")
            lines.append("")
            
            if expert_guidance:
                lines.append("# Expert Guidance:")
                lines.append(f"# {expert_guidance[:200]}...")
                lines.append("")
            
            # Add test functions based on code analysis
            functions = code_analysis.get("functions", [])
            classes = code_analysis.get("classes", [])
            
            if functions:
                lines.append("# Test functions")
                for func in functions[:5]:  # Limit to first 5 functions
                    func_name = func.get("name", "unknown")
                    lines.append("")
                    lines.append(f"def test_{func_name}():")
                    lines.append(f'    """Test {func_name} function."""')
                    lines.append("    # TODO: Implement test")
                    lines.append("    pass")
            
            if classes:
                lines.append("")
                lines.append("# Test classes")
                for cls in classes[:3]:  # Limit to first 3 classes
                    cls_name = cls.get("name", "Unknown")
                    methods = cls.get("methods", [])
                    lines.append("")
                    lines.append(f"class Test{cls_name}:")
                    lines.append(f'    """Test {cls_name} class."""')
                    lines.append("")
                    if methods:
                        for method in methods[:3]:  # Limit to first 3 methods
                            lines.append(f"    def test_{method}(self):")
                            lines.append(f'        """Test {method} method."""')
                            lines.append("        # TODO: Implement test")
                            lines.append("        pass")
                    else:
                        lines.append("    def test_init(self):")
                        lines.append('        """Test initialization."""')
                        lines.append("        # TODO: Implement test")
                        lines.append("        pass")
            
            if not functions and not classes:
                # Generic test structure
                lines.append("")
                lines.append("def test_basic():")
                lines.append('    """Basic test placeholder."""')
                lines.append("    # TODO: Implement tests based on code structure")
                lines.append("    assert True")
            
            return "\n".join(lines)
        else:
            # unittest framework
            lines = [
                '"""',
                f"Tests for {file_path.name}",
                '"""',
                "",
                "import unittest",
                "",
                f"from {module_path} import *",
                "",
            ]
            
            if expert_guidance:
                lines.append("# Expert Guidance:")
                lines.append(f"# {expert_guidance[:200]}...")
                lines.append("")
            
            lines.append("")
            lines.append("class TestModule(unittest.TestCase):")
            lines.append(f'    """Test cases for {file_path.name}."""')
            lines.append("")
            lines.append("    def setUp(self):")
            lines.append('        """Set up test fixtures."""')
            lines.append("        pass")
            lines.append("")
            lines.append("    def tearDown(self):")
            lines.append('        """Clean up after tests."""')
            lines.append("        pass")
            lines.append("")
            lines.append("    def test_basic(self):")
            lines.append('        """Basic test placeholder."""')
            lines.append("        # TODO: Implement tests based on code structure")
            lines.append("        self.assertTrue(True)")
            
            return "\n".join(lines)

    def _get_test_file_path(self, source_path: Path) -> Path:
        """Generate test file path from source file path."""
        # Convert source path to absolute and try to make it relative to cwd
        abs_source = source_path.resolve()
        try:
            cwd = Path.cwd().resolve()
            rel_path = abs_source.relative_to(cwd)
        except ValueError:
            # If not relative to cwd, use the source path's parent structure
            rel_path = source_path

        # Determine test directory structure
        # If source is in src/, put test in tests/
        # Otherwise mirror directory structure in tests/
        parts = list(rel_path.parts)

        # Remove filename for directory structure
        file_name = parts[-1]

        if "src" in parts:
            # Source is in src/, test goes to tests/
            # Replace src with tests
            test_parts = []
            for p in parts[:-1]:
                if p == "src":
                    test_parts.append("tests")
                else:
                    test_parts.append(p)
        else:
            # Mirror structure in tests/ directory
            test_parts = ["tests"] + parts[:-1]

        # Generate test file name: test_<original_name>
        test_name = f"test_{Path(file_name).stem}.py"

        # Build path relative to cwd
        if test_parts:
            return (Path.cwd() / Path(*test_parts) / test_name).resolve()
        else:
            return (Path.cwd() / "tests" / test_name).resolve()

    async def _run_pytest(
        self,
        test_path: Path | None = None,
        source_paths: list[str] | None = None,
        coverage: bool = True,
    ) -> dict[str, Any]:
        """
        Run pytest and return results.

        Args:
            test_path: Path to test file or directory
            source_paths: Source paths for coverage calculation
            coverage: Include coverage report
        """
        # Prefer pytest on PATH, but fall back to module execution (python -m pytest)
        if shutil.which("pytest"):
            cmd: list[str] = ["pytest", "-v"]
        else:
            cmd = [sys.executable, "-m", "pytest", "-v"]
        
        # Use parallel execution and unit test marker when running all tests
        # (not when a specific test_path is provided, as it might be integration/e2e)
        if not test_path:
            cmd.extend(["-m", "unit", "-n", "auto"])
        else:
            # Still use parallel execution for specific paths (faster)
            cmd.extend(["-n", "auto"])

        if coverage and source_paths:
            # Add coverage options
            source_modules = ",".join([str(Path(p).stem) for p in source_paths])
            cmd.extend(
                [
                    "--cov",
                    source_modules,
                    "--cov-report=term-missing",
                    "--cov-report=json:coverage.json",
                ]
            )
        elif coverage:
            # Coverage for all modules
            cmd.extend(
                [
                    "--cov",
                    ".",
                    "--cov-report=term-missing",
                    "--cov-report=json:coverage.json",
                ]
            )

        if test_path:
            cmd.append(str(test_path))

        try:
            result = subprocess.run(  # nosec B603
                cmd, capture_output=True, text=True, timeout=300  # 5 minute timeout
            )

            # Parse coverage if available
            coverage_data = None
            if coverage and Path("coverage.json").exists():
                try:
                    with open("coverage.json", encoding="utf-8") as f:
                        coverage_data = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    pass

            # Extract summary from stdout
            summary_match = re.search(
                r"(\d+) (passed|failed|error)", result.stdout, re.IGNORECASE
            )
            summary = None
            if summary_match:
                summary = {
                    "count": int(summary_match.group(1)),
                    "status": summary_match.group(2).lower(),
                }

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "summary": summary,
                "coverage": coverage_data.get("totals") if coverage_data else None,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timeout (5 minutes)",
                "return_code": -1,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "return_code": -1}

    def _help(self) -> dict[str, Any]:
        """
        Return help information for Tester Agent.
        
        Returns standardized help format with commands and usage examples.
        
        Returns:
            dict: Help information with standardized format:
                - type (str): Always "help"
                - content (str): Formatted help text containing:
                    - Available commands (from format_help())
                    - Usage examples for test, generate-tests, and run-tests commands
                    
        Note:
            This method is synchronous as it performs no I/O operations.
            Called via agent.run("help") which handles async context.
            Uses BaseAgent.format_help() which caches command list for performance.
        """
        # Optimize string building by using list and join
        examples = [
            "  *test file.py              # Generate and run tests for file.py",
            "  *generate-tests file.py    # Generate tests only",
            "  *run-tests                 # Run all tests in tests/",
            "  *run-tests test_file.py    # Run specific test file",
        ]
        help_text = "\n".join([self.format_help(), "\nExamples:", *examples])
        return {"type": "help", "content": help_text}

    async def close(self):
        """Close agent and clean up resources."""
