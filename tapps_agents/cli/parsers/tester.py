"""
Tester agent parser definitions
"""
import argparse


def add_tester_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add tester agent parser and subparsers"""
    tester_parser = subparsers.add_parser(
        "tester",
        help="Tester Agent commands",
        description="""Test generation and execution agent.
        
The Tester Agent creates and runs tests for your code:
  • Generate unit tests from code
  • Create integration tests
  • Run existing test suites
  • Generate test coverage reports
  • Identify untested code paths

Use this agent to ensure code quality through comprehensive testing.""",
    )
    tester_subparsers = tester_parser.add_subparsers(
        dest="command", help="Tester agent subcommand (use 'help' to see all available commands)"
    )

    test_parser = tester_subparsers.add_parser(
        "test",
        aliases=["*test"],
        help="Generate and run tests for a file",
        description="""Generate tests for a file and run them immediately.
        
Analyzes the source code and generates comprehensive tests including:
  • Unit tests for all functions and methods
  • Edge case testing
  • Error handling tests
  • Integration tests (if --integration specified)

After generation, automatically runs the tests and reports results.

Example:
  tapps-agents tester test src/utils.py
  tapps-agents tester test src/api.py --test-file tests/test_api.py --integration""",
    )
    test_parser.add_argument("file", help="Path to the source code file to test. The file will be analyzed and comprehensive tests will be generated and executed.")
    test_parser.add_argument(
        "--test-file", help="Path where the generated test file should be written. Defaults to auto-generated path in tests/ directory matching the source file structure."
    )
    test_parser.add_argument(
        "--integration",
        action="store_true",
        help="Generate integration tests in addition to unit tests. Integration tests verify component interactions and end-to-end functionality.",
    )

    generate_tests_parser = tester_subparsers.add_parser(
        "generate-tests",
        aliases=["*generate-tests"],
        help="Generate tests without running them",
        description="""Generate test code without executing it.
        
Useful for:
  • Reviewing tests before running
  • Customizing generated tests
  • Batch test generation
  • CI/CD integration

Example:
  tapps-agents tester generate-tests src/models.py
  tapps-agents tester generate-tests src/api.py --test-file tests/test_api.py""",
    )
    generate_tests_parser.add_argument("file", help="Path to the source code file to generate tests for. The file will be analyzed and test code will be generated without execution.")
    generate_tests_parser.add_argument("--test-file", help="Path where the generated test file should be written. If not provided, test code is printed to stdout.")
    generate_tests_parser.add_argument(
        "--integration", action="store_true", help="Generate integration tests in addition to unit tests. Integration tests verify component interactions and system behavior."
    )

    run_tests_parser = tester_subparsers.add_parser(
        "run-tests",
        aliases=["*run-tests"],
        help="Run existing test suite",
        description="""Run existing tests and generate coverage reports.
        
Executes pytest on the specified test path (or default tests/ directory)
and generates coverage reports. Use --no-coverage to skip coverage analysis.

Example:
  tapps-agents tester run-tests
  tapps-agents tester run-tests tests/unit/
  tapps-agents tester run-tests --no-coverage""",
    )
    run_tests_parser.add_argument(
        "test_path", nargs="?", help="Path to test file, test directory, or test pattern to run. Defaults to 'tests/' directory if not specified. Supports pytest-style patterns."
    )
    run_tests_parser.add_argument(
        "--no-coverage", action="store_true", help="Skip test coverage analysis. By default, generates coverage reports showing which code is tested. Use this flag to run tests faster without coverage."
    )

    tester_subparsers.add_parser("help", aliases=["*help"], help="Show tester commands")

