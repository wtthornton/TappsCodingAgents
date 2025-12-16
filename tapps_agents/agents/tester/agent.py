"""
Tester Agent - Generates and runs tests
"""

import json
import re
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any

from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.mal import MAL
from ...experts.agent_integration import ExpertSupportMixin
from .test_generator import TestGenerator


class TesterAgent(BaseAgent, ExpertSupportMixin):
    """
    Tester Agent - Test generation and execution.

    Permissions: Read, Write, Edit, Grep, Glob, Bash
    """

    def __init__(self, mal: MAL | None = None, config: ProjectConfig | None = None):
        super().__init__(agent_id="tester", agent_name="Tester Agent", config=config)
        # Use config if provided, otherwise load defaults
        if config is None:
            config = load_config()
        self.config = config

        # Initialize MAL with config
        mal_config = config.mal if config else None
        self.mal = mal or MAL(
            ollama_url=mal_config.ollama_url if mal_config else "http://localhost:11434"
        )

        # Initialize test generator
        self.test_generator = TestGenerator(self.mal)

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

    async def activate(self, project_root: Path | None = None):
        """Activate the tester agent with expert support."""
        await super().activate(project_root)
        # Initialize expert support
        await self._initialize_expert_support(project_root)

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
            return await self._help()
        else:
            return {"error": f"Unknown command: {command}"}

    async def test_command(
        self,
        file: str | None = None,
        test_file: str | None = None,
        integration: bool = False,
        **kwargs,  # Accept additional kwargs to be more flexible
    ) -> dict[str, Any]:
        """
        Generate and run tests for a file.

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

        # Consult Testing expert for test generation guidance
        expert_guidance = ""
        expert_advice = None
        if self.expert_registry:
            testing_consultation = await self.expert_registry.consult(
                query=f"Provide best practices for generating {'integration' if integration else 'unit'} tests for: {file_path.name}. Focus on test coverage, edge cases, and maintainability.",
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

        # Generate tests
        if integration:
            # For integration tests, use the file itself (could be extended to accept multiple files)
            test_code = await self.test_generator.generate_integration_tests(
                [file_path],
                test_path=Path(test_file) if test_file else None,
                expert_guidance=expert_guidance,
            )
        else:
            test_code = await self.test_generator.generate_unit_tests(
                file_path,
                test_path=Path(test_file) if test_file else None,
                expert_guidance=expert_guidance,
            )

        # Determine test file path
        if test_file:
            test_path = Path(test_file)
        else:
            # Auto-generate test file path
            test_path = self._get_test_file_path(file_path)

        # Write test file if auto_write is enabled
        if self.auto_write_tests:
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(test_code, encoding="utf-8")

        # Run tests
        run_result = await self._run_pytest(
            test_path if self.auto_write_tests else None, [str(file_path)]
        )

        return {
            "type": "test",
            "test_code": test_code,
            "test_file": str(test_path),
            "written": self.auto_write_tests,
            "run_result": run_result,
            "expert_advice": expert_advice,  # Include expert recommendations
        }

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

        # Consult Testing expert for test generation guidance
        expert_guidance = ""
        if self.expert_registry:
            testing_consultation = await self.expert_registry.consult(
                query=f"Provide best practices for generating {'integration' if integration else 'unit'} tests for: {file_path.name}. Focus on test coverage, edge cases, and maintainability.",
                domain="testing-strategies",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if (
                testing_consultation.confidence
                >= testing_consultation.confidence_threshold
            ):
                expert_guidance = testing_consultation.weighted_answer

        # Generate tests
        if integration:
            test_code = await self.test_generator.generate_integration_tests(
                [file_path],
                test_path=Path(test_file) if test_file else None,
                expert_guidance=expert_guidance,
            )
        else:
            test_code = await self.test_generator.generate_unit_tests(
                file_path,
                test_path=Path(test_file) if test_file else None,
                expert_guidance=expert_guidance,
            )

        # Determine test file path
        if test_file:
            test_path = Path(test_file)
        else:
            test_path = self._get_test_file_path(file_path)

        # Write test file if auto_write is enabled
        if self.auto_write_tests:
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(test_code, encoding="utf-8")

        return {
            "type": "test_generation",
            "test_code": test_code,
            "test_file": str(test_path),
            "written": self.auto_write_tests,
        }

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
        if self.expert_registry:
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

        # Generate E2E tests
        test_code = await self.test_generator.generate_e2e_tests(
            project_root=proj_root,
            test_path=Path(test_file) if test_file else None,
            expert_guidance=expert_guidance,
        )

        # Check if E2E framework was detected
        e2e_framework = self.test_generator._detect_e2e_framework(proj_root)
        if not e2e_framework:
            return {
                "type": "e2e_test_generation",
                "error": "No E2E testing framework detected. Please install one of: playwright, pytest-playwright, selenium, or cypress.",
                "test_code": None,
                "test_file": None,
                "written": False,
                "framework_detected": False,
            }

        # Determine test file path
        if test_file:
            test_path = Path(test_file)
        else:
            # Default E2E test location
            test_path = proj_root / "tests" / "e2e" / "test_e2e.py"

        # Write test file if auto_write is enabled
        if self.auto_write_tests and test_code:
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(test_code, encoding="utf-8")

        return {
            "type": "e2e_test_generation",
            "test_code": test_code,
            "test_file": str(test_path),
            "written": self.auto_write_tests and bool(test_code),
            "framework_detected": e2e_framework,
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

    async def _help(self) -> dict[str, Any]:
        """Generate help text."""
        help_text = self.format_help()
        help_text += "\n\nExamples:\n"
        help_text += (
            "  *test file.py              # Generate and run tests for file.py\n"
        )
        help_text += "  *generate-tests file.py    # Generate tests only\n"
        help_text += "  *run-tests                 # Run all tests in tests/\n"
        help_text += "  *run-tests test_file.py    # Run specific test file\n"
        return {"type": "help", "content": help_text}

    async def close(self):
        """Close agent and clean up resources."""
        if self.mal:
            await self.mal.close()
