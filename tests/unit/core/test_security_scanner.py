"""
Unit tests for SecurityScanner module.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from tapps_agents.core.security_scanner import SecurityScanner


class TestSecurityScanner:
    """Test SecurityScanner functionality."""

    def test_init(self):
        """Test SecurityScanner initialization."""
        scanner = SecurityScanner()
        assert scanner is not None
        assert hasattr(scanner, "has_bandit")

    def test_scan_code_with_bandit(self, tmp_path):
        """Test scanning code with Bandit available."""
        # Create a test file
        test_file = tmp_path / "test_code.py"
        test_file.write_text("import os\nos.system('ls')")

        scanner = SecurityScanner()

        with patch.object(scanner, "has_bandit", True):
            with patch("tapps_agents.core.security_scanner.bandit") as mock_bandit:
                with patch(
                    "tapps_agents.core.security_scanner.manager"
                ) as mock_manager:
                    with patch(
                        "tapps_agents.core.security_scanner.bandit_config"
                    ) as mock_config:
                        # Mock BanditManager
                        mock_b_mgr = MagicMock()
                        mock_issue = MagicMock()
                        mock_issue.severity = mock_bandit.MEDIUM
                        mock_issue.test_id = "B601"
                        mock_issue.test = "shell_injection_subprocess"
                        mock_issue.lineno = 2
                        mock_issue.text = "Possible shell injection"
                        mock_issue.confidence = mock_bandit.MEDIUM

                        mock_b_mgr.get_issue_list.return_value = [mock_issue]
                        mock_manager.BanditManager.return_value = mock_b_mgr
                        mock_config.BanditConfig.return_value = MagicMock()

                        result = scanner.scan_code(file_path=test_file)

                        assert "security_score" in result
                        assert "vulnerabilities" in result
                        assert "is_safe" in result
                        assert isinstance(result["security_score"], float)
                        assert isinstance(result["vulnerabilities"], list)

    def test_scan_code_without_bandit(self):
        """Test scanning code when Bandit is not available."""
        scanner = SecurityScanner()

        with patch.object(scanner, "has_bandit", False):
            code = "import os\nos.system('ls')"
            result = scanner.scan_code(code=code)

            assert "security_score" in result
            assert "vulnerabilities" in result
            assert "is_safe" in result
            # Should use heuristic scanning
            assert result["security_score"] < 10.0  # Should detect insecure pattern

    def test_scan_code_heuristic(self):
        """Test heuristic security scanning."""
        scanner = SecurityScanner()

        with patch.object(scanner, "has_bandit", False):
            # Test with insecure code
            insecure_code = "eval('dangerous')"
            result = scanner._heuristic_scan(insecure_code)

            assert result["security_score"] < 10.0
            assert len(result["vulnerabilities"]) > 0

            # Test with secure code
            secure_code = "def hello():\n    return 'world'"
            result = scanner._heuristic_scan(secure_code)

            assert result["security_score"] >= 10.0 or result["security_score"] == 0.0
            assert result["is_safe"] is True

    def test_get_security_score(self):
        """Test getting security score."""
        scanner = SecurityScanner()

        with patch.object(scanner, "has_bandit", False):
            code = "def safe_function():\n    return True"
            score = scanner.get_security_score(code=code)

            assert isinstance(score, float)
            assert 0.0 <= score <= 10.0

    def test_get_vulnerabilities(self):
        """Test getting vulnerabilities list."""
        scanner = SecurityScanner()

        with patch.object(scanner, "has_bandit", False):
            code = "eval('unsafe')"
            vulnerabilities = scanner.get_vulnerabilities(code=code)

            assert isinstance(vulnerabilities, list)
            if vulnerabilities:
                assert "severity" in vulnerabilities[0]
                assert "test_name" in vulnerabilities[0]

    def test_is_safe_for_learning(self):
        """Test is_safe_for_learning check."""
        scanner = SecurityScanner()

        with patch.object(scanner, "has_bandit", False):
            # Secure code
            secure_code = "def safe():\n    pass"
            assert scanner.is_safe_for_learning(code=secure_code, threshold=7.0) is True

            # Insecure code
            insecure_code = "eval('dangerous')"
            assert (
                scanner.is_safe_for_learning(code=insecure_code, threshold=7.0) is False
            )

    def test_is_safe_for_learning_custom_threshold(self):
        """Test is_safe_for_learning with custom threshold."""
        scanner = SecurityScanner()

        with patch.object(scanner, "has_bandit", False):
            code = "def moderate():\n    pass"
            # Lower threshold should allow more code
            assert scanner.is_safe_for_learning(code=code, threshold=5.0) is True
            # Higher threshold might reject
            assert scanner.is_safe_for_learning(code=code, threshold=9.0) is True

    def test_scan_file_error_handling(self, tmp_path):
        """Test error handling in file scanning."""
        scanner = SecurityScanner()

        with patch.object(scanner, "has_bandit", True):
            # Non-existent file
            non_existent = tmp_path / "nonexistent.py"
            result = scanner.scan_code(file_path=non_existent)

            # Should handle gracefully
            assert "security_score" in result
            assert isinstance(result["security_score"], float)

    def test_severity_to_string(self):
        """Test severity conversion to string."""
        scanner = SecurityScanner()

        with patch.object(scanner, "has_bandit", True):
            with patch("tapps_agents.core.security_scanner.bandit") as mock_bandit:
                mock_bandit.HIGH = 1
                mock_bandit.MEDIUM = 2
                mock_bandit.LOW = 3

                assert scanner._severity_to_string(1) == "high"
                assert scanner._severity_to_string(2) == "medium"
                assert scanner._severity_to_string(3) == "low"

    def test_confidence_to_string(self):
        """Test confidence conversion to string."""
        scanner = SecurityScanner()

        with patch.object(scanner, "has_bandit", True):
            with patch("tapps_agents.core.security_scanner.bandit") as mock_bandit:
                mock_bandit.HIGH = 1
                mock_bandit.MEDIUM = 2
                mock_bandit.LOW = 3

                assert scanner._confidence_to_string(1) == "high"
                assert scanner._confidence_to_string(2) == "medium"
                assert scanner._confidence_to_string(3) == "low"

