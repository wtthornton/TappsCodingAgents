"""
CI/CD artifact bundling utilities for E2E tests.

Provides:
- Failure artifact collection
- JUnit report generation helpers
- Artifact redaction
- Correlation ID attachment
- Test summary generation
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .e2e_harness import redact_secrets

# Configure logging
logger = logging.getLogger(__name__)


def collect_failure_artifacts(
    project_path: Path,
    correlation_id: str | None = None,
    test_name: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    """
    Collect failure artifacts from a test project.

    Collects:
    - Logs from .tapps-agents/logs/
    - State snapshots from .tapps-agents/workflow-state/
    - Produced artifacts from project root
    - Test output and error messages

    Args:
        project_path: Path to the test project
        correlation_id: Optional correlation ID (generated if not provided)
        test_name: Optional test name (for artifact organization)
        output_dir: Optional output directory (uses tempdir if not provided)

    Returns:
        Path to the collected artifacts directory
    """
    import tempfile
    import uuid

    if correlation_id is None:
        correlation_id = f"ci-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

    if output_dir is None:
        output_dir = Path(tempfile.gettempdir()) / "ci_artifacts" / correlation_id
    else:
        output_dir = output_dir / correlation_id

    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, Any] = {
        "correlation_id": correlation_id,
        "test_name": test_name or "unknown",
        "project_path": str(project_path),
        "collected_at": datetime.now().isoformat(),
        "artifacts": [],
    }

    # Collect logs
    logs_dir = project_path / ".tapps-agents" / "logs"
    if logs_dir.exists():
        logs_output = output_dir / "logs"
        logs_output.mkdir(exist_ok=True)
        for log_file in logs_dir.glob("*.log"):
            try:
                # Redact secrets before copying
                content = log_file.read_text()
                redacted_content = redact_secrets(content)
                (logs_output / log_file.name).write_text(redacted_content)
                artifacts["artifacts"].append(f"logs/{log_file.name}")
            except Exception as e:
                logger.warning(f"Failed to collect log file {log_file}: {e}")

    # Collect state snapshots
    state_dir = project_path / ".tapps-agents" / "workflow-state"
    if state_dir.exists():
        state_output = output_dir / "state"
        state_output.mkdir(exist_ok=True)
        for state_file in state_dir.glob("**/*.json"):
            try:
                # Redact secrets in JSON files
                content = state_file.read_text()
                redacted_content = redact_secrets(content)
                relative_path = state_file.relative_to(state_dir)
                (state_output / relative_path).parent.mkdir(parents=True, exist_ok=True)
                (state_output / relative_path).write_text(redacted_content)
                artifacts["artifacts"].append(f"state/{relative_path}")
            except Exception as e:
                logger.warning(f"Failed to collect state file {state_file}: {e}")

    # Collect produced artifacts (non-sensitive files)
    for artifact_file in project_path.glob("**/*"):
        if artifact_file.is_file() and not artifact_file.name.startswith("."):
            try:
                # Skip large binary files
                if artifact_file.stat().st_size > 10 * 1024 * 1024:  # 10MB
                    continue

                # Skip sensitive files
                if any(
                    sensitive in artifact_file.name.lower()
                    for sensitive in ["secret", "key", "token", "password", ".env"]
                ):
                    continue

                relative_path = artifact_file.relative_to(project_path)
                artifact_output = output_dir / "artifacts" / relative_path
                artifact_output.parent.mkdir(parents=True, exist_ok=True)

                # Redact secrets in text files
                if artifact_file.suffix in [".py", ".md", ".txt", ".json", ".yaml", ".yml"]:
                    content = artifact_file.read_text()
                    redacted_content = redact_secrets(content)
                    artifact_output.write_text(redacted_content)
                else:
                    shutil.copy2(artifact_file, artifact_output)

                artifacts["artifacts"].append(f"artifacts/{relative_path}")
            except Exception as e:
                logger.warning(f"Failed to collect artifact {artifact_file}: {e}")

    # Write metadata
    metadata_file = output_dir / "metadata.json"
    metadata_file.write_text(json.dumps(artifacts, indent=2))

    # Write README
    readme_file = output_dir / "README.md"
    readme_content = f"""# Failure Artifacts

**Correlation ID:** {correlation_id}
**Test Name:** {test_name or "unknown"}
**Collected At:** {datetime.now().isoformat()}
**Project Path:** {project_path}

## Artifacts

- Logs: `logs/` (if available)
- State: `state/` (if available)
- Produced Files: `artifacts/` (if available)
- Metadata: `metadata.json`

## Notes

- All secrets have been redacted from collected artifacts
- Large binary files (>10MB) are excluded
- Sensitive files (secrets, keys, tokens) are excluded
"""
    readme_file.write_text(readme_content)

    logger.info(f"Collected failure artifacts to {output_dir}")
    return output_dir


def create_test_summary(
    test_results: dict[str, Any],
    output_file: Path | None = None,
) -> str:
    """
    Create a test summary in Markdown format.

    Args:
        test_results: Dictionary containing test results
        output_file: Optional file to write summary to

    Returns:
        Markdown summary string
    """
    total = test_results.get("total", 0)
    passed = test_results.get("passed", 0)
    failed = test_results.get("failed", 0)
    skipped = test_results.get("skipped", 0)
    duration = test_results.get("duration", 0.0)

    summary = f"""# Test Summary

## Results

- **Total:** {total}
- **Passed:** {passed} ✅
- **Failed:** {failed} ❌
- **Skipped:** {skipped} ⏭️
- **Duration:** {duration:.2f}s

## Status

"""
    if failed == 0:
        summary += "✅ All tests passed!\n"
    else:
        summary += f"❌ {failed} test(s) failed. Check artifacts for details.\n"

    if output_file:
        output_file.write_text(summary)

    return summary


def attach_correlation_id(correlation_id: str, env_var: str = "CI_CORRELATION_ID"):
    """
    Attach correlation ID to environment for CI/CD tracking.

    Args:
        correlation_id: Correlation ID to attach
        env_var: Environment variable name to set
    """
    os.environ[env_var] = correlation_id
    logger.info(f"Attached correlation ID: {correlation_id}")


def get_correlation_id(env_var: str = "CI_CORRELATION_ID") -> str | None:
    """
    Get correlation ID from environment.

    Args:
        env_var: Environment variable name to read

    Returns:
        Correlation ID or None if not set
    """
    return os.environ.get(env_var)


def create_junit_summary(junit_xml_path: Path) -> dict[str, Any]:
    """
    Parse JUnit XML and create summary.

    Args:
        junit_xml_path: Path to JUnit XML file

    Returns:
        Dictionary with test summary
    """
    try:
        import xml.etree.ElementTree as ET

        tree = ET.parse(junit_xml_path)
        root = tree.getroot()

        total = int(root.get("tests", 0))
        failures = int(root.get("failures", 0))
        errors = int(root.get("errors", 0))
        skipped = int(root.get("skipped", 0))
        time = float(root.get("time", 0.0))

        passed = total - failures - errors - skipped

        return {
            "total": total,
            "passed": passed,
            "failed": failures + errors,
            "skipped": skipped,
            "duration": time,
        }
    except Exception as e:
        logger.warning(f"Failed to parse JUnit XML: {e}")
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration": 0.0,
        }

