"""
Tester agent parser definitions
"""
import argparse


def add_tester_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add tester agent parser and subparsers"""
    tester_parser = subparsers.add_parser("tester", help="Tester Agent commands")
    tester_subparsers = tester_parser.add_subparsers(dest="command", help="Commands")

    test_parser = tester_subparsers.add_parser(
        "test", aliases=["*test"], help="Generate and run tests for a file"
    )
    test_parser.add_argument("file", help="Source code file to test")
    test_parser.add_argument("--test-file", help="Path to write test file")
    test_parser.add_argument(
        "--integration", action="store_true", help="Generate integration tests"
    )

    generate_tests_parser = tester_subparsers.add_parser(
        "generate-tests",
        aliases=["*generate-tests"],
        help="Generate tests without running",
    )
    generate_tests_parser.add_argument("file", help="Source code file to test")
    generate_tests_parser.add_argument("--test-file", help="Path to write test file")
    generate_tests_parser.add_argument(
        "--integration", action="store_true", help="Generate integration tests"
    )

    run_tests_parser = tester_subparsers.add_parser(
        "run-tests", aliases=["*run-tests"], help="Run existing tests"
    )
    run_tests_parser.add_argument(
        "test_path", nargs="?", help="Path to test file or directory (default: tests/)"
    )
    run_tests_parser.add_argument(
        "--no-coverage", action="store_true", help="Don't include coverage report"
    )

    tester_subparsers.add_parser("help", aliases=["*help"], help="Show tester commands")

