"""
Secret Scanning Module.

Story 6.5: Dependency & Secret Scanning Gates
- Add secret scanning checks for workflows/agents
- Prevent leaking API keys/tokens in artifacts
- Document override/exception process with audit trail
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SecretFinding:
    """A detected secret or potential secret."""

    file_path: str
    line_number: int
    secret_type: str
    pattern: str
    severity: str  # "high", "medium", "low"
    context: str | None = None  # Line content for context


@dataclass
class SecretScanResult:
    """Result of secret scanning."""

    total_findings: int
    high_severity: int
    medium_severity: int
    low_severity: int
    findings: list[SecretFinding]
    scanned_files: int
    passed: bool  # True if no high-severity findings

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_findings": self.total_findings,
            "high_severity": self.high_severity,
            "medium_severity": self.medium_severity,
            "low_severity": self.low_severity,
            "findings": [
                {
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "secret_type": f.secret_type,
                    "pattern": f.pattern,
                    "severity": f.severity,
                    "context": f.context,
                }
                for f in self.findings
            ],
            "scanned_files": self.scanned_files,
            "passed": self.passed,
        }


class SecretScanner:
    """
    Scan code for potential secrets and API keys.

    Story 6.5: Dependency & Secret Scanning Gates
    """

    # Common secret patterns
    SECRET_PATTERNS = {
        "api_key": [
            r'api[_-]?key\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            r'apikey\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        ],
        "secret_key": [
            r'secret[_-]?key\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            r'secret_key\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        ],
        "password": [
            r'password\s*[=:]\s*["\']?([^\s"\']{8,})["\']?',
            r'pwd\s*[=:]\s*["\']?([^\s"\']{8,})["\']?',
        ],
        "token": [
            r'token\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            r'access[_-]?token\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            r'auth[_-]?token\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        ],
        "aws_key": [
            r'aws[_-]?access[_-]?key[_-]?id\s*[=:]\s*["\']?(AKIA[0-9A-Z]{16})["\']?',
            r'aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?',
        ],
        "private_key": [
            r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
            r'-----BEGIN\s+EC\s+PRIVATE\s+KEY-----',
        ],
        "oauth": [
            r'oauth[_-]?token\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            r'client[_-]?secret\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        ],
    }

    # Severity mapping
    SEVERITY_MAP = {
        "api_key": "high",
        "secret_key": "high",
        "aws_key": "high",
        "private_key": "high",
        "token": "medium",
        "oauth": "medium",
        "password": "low",  # Often false positives
    }

    # Files/directories to exclude
    EXCLUDE_PATTERNS = [
        r".*\.pyc$",
        r".*__pycache__.*",
        r".*\.git.*",
        r".*node_modules.*",
        r".*\.venv.*",
        r".*venv.*",
        r".*\.env$",  # .env files are expected to have secrets
        r".*\.env\..*",
    ]

    def __init__(self, project_root: Path | None = None):
        """
        Initialize secret scanner.

        Args:
            project_root: Root directory of project (default: current directory)
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = Path(project_root).resolve()

    def scan(
        self,
        target_path: Path | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> SecretScanResult:
        """
        Scan for secrets in codebase.

        Args:
            target_path: Optional specific path to scan (default: project root)
            exclude_patterns: Optional additional exclude patterns

        Returns:
            SecretScanResult with findings
        """
        if target_path is None:
            target_path = self.project_root
        else:
            target_path = Path(target_path).resolve()

        findings: list[SecretFinding] = []
        scanned_files = 0

        # Combine exclude patterns
        all_exclude_patterns = self.EXCLUDE_PATTERNS.copy()
        if exclude_patterns:
            all_exclude_patterns.extend(exclude_patterns)

        # Find files to scan
        files_to_scan = self._find_files_to_scan(target_path, all_exclude_patterns)

        # Scan each file
        for file_path in files_to_scan:
            scanned_files += 1
            file_findings = self._scan_file(file_path)
            findings.extend(file_findings)

        # Count by severity
        high_severity = sum(1 for f in findings if f.severity == "high")
        medium_severity = sum(1 for f in findings if f.severity == "medium")
        low_severity = sum(1 for f in findings if f.severity == "low")

        # Gate passes if no high-severity findings
        passed = high_severity == 0

        return SecretScanResult(
            total_findings=len(findings),
            high_severity=high_severity,
            medium_severity=medium_severity,
            low_severity=low_severity,
            findings=findings,
            scanned_files=scanned_files,
            passed=passed,
        )

    def _find_files_to_scan(
        self, target_path: Path, exclude_patterns: list[str]
    ) -> list[Path]:
        """Find files to scan, excluding patterns."""
        files: list[Path] = []

        if target_path.is_file():
            # Single file
            if self._should_scan_file(target_path, exclude_patterns):
                files.append(target_path)
        else:
            # Directory - find Python files
            for file_path in target_path.rglob("*.py"):
                if self._should_scan_file(file_path, exclude_patterns):
                    files.append(file_path)

        return files

    def _should_scan_file(self, file_path: Path, exclude_patterns: list[str]) -> bool:
        """Check if file should be scanned."""
        file_str = str(file_path)
        for pattern in exclude_patterns:
            if re.match(pattern, file_str, re.IGNORECASE):
                return False
        return True

    def _scan_file(self, file_path: Path) -> list[SecretFinding]:
        """Scan a single file for secrets."""
        findings: list[SecretFinding] = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")

            for line_num, line in enumerate(lines, start=1):
                # Check each secret pattern
                for secret_type, patterns in self.SECRET_PATTERNS.items():
                    for pattern in patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            # Skip if it's a comment or docstring (basic check)
                            stripped_line = line.strip()
                            if stripped_line.startswith("#") or stripped_line.startswith('"""'):
                                continue

                            severity = self.SEVERITY_MAP.get(secret_type, "medium")

                            # Try to get relative path, fall back to absolute if outside project root
                            try:
                                rel_path = str(file_path.relative_to(self.project_root))
                            except ValueError:
                                # File is outside project root, use absolute path
                                rel_path = str(file_path)

                            findings.append(
                                SecretFinding(
                                    file_path=rel_path,
                                    line_number=line_num,
                                    secret_type=secret_type,
                                    pattern=match.group(0) if match.groups() else match.group(0),
                                    severity=severity,
                                    context=line.strip()[:100],  # First 100 chars
                                )
                            )

        except (UnicodeDecodeError, PermissionError, FileNotFoundError):
            # Skip files that can't be read
            pass

        return findings

    def scan_file(self, file_path: Path) -> SecretScanResult:
        """
        Scan a single file for secrets.
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            SecretScanResult with findings
        """
        return self.scan(target_path=file_path)

    def scan_directory(
        self, directory_path: Path, exclude_patterns: list[str] | None = None
    ) -> SecretScanResult:
        """
        Scan a directory for secrets.
        
        Args:
            directory_path: Path to directory to scan
            exclude_patterns: Optional additional exclude patterns
            
        Returns:
            SecretScanResult with findings
        """
        return self.scan(target_path=directory_path, exclude_patterns=exclude_patterns)

    def check_gate(
        self,
        result: SecretScanResult,
        fail_on_high: bool = True,
        fail_on_medium: bool = False,
    ) -> dict[str, Any]:
        """
        Check if secret scan result passes gate.

        Args:
            result: SecretScanResult to check
            fail_on_high: Fail gate if high-severity findings (default: True)
            fail_on_medium: Fail gate if medium-severity findings (default: False)

        Returns:
            Dictionary with gate check results
        """
        passed = True
        failures: list[str] = []
        warnings: list[str] = []

        if fail_on_high and result.high_severity > 0:
            passed = False
            failures.append(
                f"Found {result.high_severity} high-severity secret(s). "
                "Remove secrets from code or use environment variables."
            )

        if fail_on_medium and result.medium_severity > 0:
            passed = False
            failures.append(
                f"Found {result.medium_severity} medium-severity potential secret(s)."
            )

        if result.low_severity > 0:
            warnings.append(f"Found {result.low_severity} low-severity potential secret(s).")

        return {
            "passed": passed,
            "total_findings": result.total_findings,
            "high_severity": result.high_severity,
            "medium_severity": result.medium_severity,
            "low_severity": result.low_severity,
            "failures": failures,
            "warnings": warnings,
        }
