"""
Unit tests for Secret Scanner.
"""

from pathlib import Path

import pytest

from tapps_agents.quality.secret_scanner import (
    SecretFinding,
    SecretScanner,
    SecretScanResult,
)

pytestmark = pytest.mark.unit


class TestSecretScanner:
    """Test cases for SecretScanner."""

    @pytest.fixture
    def scanner(self):
        """Create a SecretScanner instance."""
        return SecretScanner()

    def test_scanner_initialization(self, scanner):
        """Test scanner initialization."""
        assert scanner is not None
        assert hasattr(scanner, "SECRET_PATTERNS")

    def test_scan_file_no_secrets(self, scanner, tmp_path):
        """Test scanning file with no secrets."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    print('Hello, World!')\n")
        
        result = scanner.scan_file(test_file)
        
        assert isinstance(result, SecretScanResult)
        assert result.total_findings == 0
        assert result.passed is True

    def test_scan_file_with_api_key(self, scanner, tmp_path):
        """Test scanning file with API key."""
        test_file = tmp_path / "test.py"
        test_file.write_text("api_key = 'AKIAIOSFODNN7EXAMPLE'\n")
        
        result = scanner.scan_file(test_file)
        
        assert isinstance(result, SecretScanResult)
        assert result.total_findings > 0
        assert result.passed is False  # High severity finding

    def test_scan_file_with_password(self, scanner, tmp_path):
        """Test scanning file with password."""
        test_file = tmp_path / "test.py"
        test_file.write_text("password = 'mypassword123'\n")
        
        result = scanner.scan_file(test_file)
        
        assert isinstance(result, SecretScanResult)
        assert result.total_findings > 0

    def test_scan_file_with_token(self, scanner, tmp_path):
        """Test scanning file with token."""
        test_file = tmp_path / "test.py"
        test_file.write_text("token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'\n")
        
        result = scanner.scan_file(test_file)
        
        assert isinstance(result, SecretScanResult)
        assert result.total_findings > 0

    def test_scan_directory(self, scanner, tmp_path):
        """Test scanning directory."""
        # Create files with and without secrets
        clean_file = tmp_path / "clean.py"
        clean_file.write_text("def hello(): pass\n")
        
        secret_file = tmp_path / "secret.py"
        secret_file.write_text("api_key = 'secret123'\n")
        
        result = scanner.scan_directory(tmp_path)
        
        assert isinstance(result, SecretScanResult)
        assert result.scanned_files >= 2
        assert result.total_findings > 0

    def test_scan_directory_exclude_patterns(self, scanner, tmp_path):
        """Test scanning directory with exclude patterns."""
        # Create file in excluded directory
        excluded_dir = tmp_path / "venv"
        excluded_dir.mkdir()
        excluded_file = excluded_dir / "test.py"
        excluded_file.write_text("api_key = 'secret'\n")
        
        result = scanner.scan_directory(tmp_path, exclude_patterns=["venv/**"])
        
        # Should not find secrets in excluded directory
        assert isinstance(result, SecretScanResult)


class TestSecretFinding:
    """Test cases for SecretFinding."""

    def test_finding_creation(self):
        """Test creating a secret finding."""
        finding = SecretFinding(
            file_path="test.py",
            line_number=10,
            secret_type="api_key",
            pattern="api_key = '...'",
            severity="high",
            context="api_key = 'secret123'"
        )
        
        assert finding.file_path == "test.py"
        assert finding.line_number == 10
        assert finding.secret_type == "api_key"
        assert finding.severity == "high"
        assert finding.context == "api_key = 'secret123'"


class TestSecretScanResult:
    """Test cases for SecretScanResult."""

    def test_result_creation(self):
        """Test creating a scan result."""
        findings = [
            SecretFinding(
                file_path="test.py",
                line_number=1,
                secret_type="api_key",
                pattern="api_key",
                severity="high"
            )
        ]
        
        result = SecretScanResult(
            total_findings=1,
            high_severity=1,
            medium_severity=0,
            low_severity=0,
            findings=findings,
            scanned_files=1,
            passed=False
        )
        
        assert result.total_findings == 1
        assert result.high_severity == 1
        assert result.passed is False
        assert len(result.findings) == 1

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        findings = [
            SecretFinding(
                file_path="test.py",
                line_number=1,
                secret_type="api_key",
                pattern="api_key",
                severity="high"
            )
        ]
        
        result = SecretScanResult(
            total_findings=1,
            high_severity=1,
            medium_severity=0,
            low_severity=0,
            findings=findings,
            scanned_files=1,
            passed=False
        )
        
        data = result.to_dict()
        
        assert data["total_findings"] == 1
        assert data["high_severity"] == 1
        assert data["passed"] is False
        assert len(data["findings"]) == 1
        assert data["findings"][0]["file_path"] == "test.py"

