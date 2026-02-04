"""
Unit tests for Security Scanner Module.

Tests security scanning functionality, Bandit integration, heuristic scanning,
and safety checks for learning.
"""

from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.core.security_scanner import SecurityScanner

pytestmark = pytest.mark.unit


class TestSecurityScannerInitialization:
    """Tests for SecurityScanner initialization."""

    def test_security_scanner_init(self):
        """Test SecurityScanner initialization."""
        scanner = SecurityScanner()
        
        assert hasattr(scanner, "has_bandit")
        assert isinstance(scanner.has_bandit, bool)

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", True)
    def test_security_scanner_init_with_bandit(self):
        """Test SecurityScanner initialization when Bandit is available."""
        scanner = SecurityScanner()
        
        assert scanner.has_bandit is True

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_security_scanner_init_without_bandit(self):
        """Test SecurityScanner initialization when Bandit is not available."""
        scanner = SecurityScanner()
        
        assert scanner.has_bandit is False


class TestSecurityScannerScanCode:
    """Tests for scan_code method."""

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_scan_code_heuristic_fallback(self, tmp_path):
        """Test scan_code uses heuristic when Bandit not available."""
        scanner = SecurityScanner()
        
        code = "def test():\n    eval('code')\n    return True"
        result = scanner.scan_code(code=code)
        
        assert "security_score" in result
        assert "vulnerabilities" in result
        assert "is_safe" in result
        assert result["security_score"] < 10.0  # Should detect eval

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", True)
    @patch("tapps_agents.core.security_scanner.SecurityScanner._scan_file")
    def test_scan_code_with_file_path(self, mock_scan_file, tmp_path):
        """Test scan_code with file_path."""
        scanner = SecurityScanner()
        
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        
        mock_scan_file.return_value = {
            "security_score": 10.0,
            "vulnerabilities": [],
            "high_severity_count": 0,
            "medium_severity_count": 0,
            "low_severity_count": 0,
            "is_safe": True
        }
        
        result = scanner.scan_code(file_path=test_file)
        
        assert "security_score" in result
        mock_scan_file.assert_called_once()

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", True)
    def test_scan_code_with_code_string(self, tmp_path):
        """Test scan_code with code string creates temp file."""
        scanner = SecurityScanner()
        
        code = "def test(): pass"
        
        with patch.object(scanner, '_scan_file') as mock_scan_file:
            mock_scan_file.return_value = {
                "security_score": 10.0,
                "vulnerabilities": [],
                "high_severity_count": 0,
                "medium_severity_count": 0,
                "low_severity_count": 0,
                "is_safe": True
            }
            
            result = scanner.scan_code(code=code)
            
            assert "security_score" in result

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_scan_code_no_input(self):
        """Test scan_code with no file_path or code."""
        scanner = SecurityScanner()
        
        result = scanner.scan_code()
        
        assert "security_score" in result
        assert result["security_score"] == 5.0  # Default score
        assert result["is_safe"] is True
        assert len(result["vulnerabilities"]) == 0

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_scan_code_empty_string(self):
        """Test scan_code with empty code string (should scan and return 10.0)."""
        scanner = SecurityScanner()
        
        result = scanner.scan_code(code="")
        
        assert "security_score" in result
        assert result["security_score"] == 10.0  # Empty code has no issues
        assert result["is_safe"] is True
        assert len(result["vulnerabilities"]) == 0


class TestSecurityScannerHeuristicScan:
    """Tests for _heuristic_scan method."""

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_heuristic_scan_detects_eval(self):
        """Test _heuristic_scan detects eval()."""
        scanner = SecurityScanner()
        
        code = "eval('code')"
        result = scanner._heuristic_scan(code)
        
        assert result["security_score"] < 10.0
        assert len(result["vulnerabilities"]) > 0
        assert result["is_safe"] is False

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_heuristic_scan_detects_exec(self):
        """Test _heuristic_scan detects exec()."""
        scanner = SecurityScanner()
        
        code = "exec('code')"
        result = scanner._heuristic_scan(code)
        
        assert result["security_score"] < 10.0
        assert len(result["vulnerabilities"]) > 0

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_heuristic_scan_detects_subprocess_shell(self):
        """Test _heuristic_scan detects shell=True."""
        scanner = SecurityScanner()
        
        code = "subprocess.call(['cmd'], shell=True)"
        result = scanner._heuristic_scan(code)
        
        assert result["security_score"] < 10.0
        assert len(result["vulnerabilities"]) > 0

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_heuristic_scan_safe_code(self):
        """Test _heuristic_scan with safe code."""
        scanner = SecurityScanner()
        
        code = "def test():\n    return True"
        result = scanner._heuristic_scan(code)
        
        assert result["security_score"] == 10.0
        assert len(result["vulnerabilities"]) == 0
        assert result["is_safe"] is True

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_heuristic_scan_multiple_issues(self):
        """Test _heuristic_scan with multiple security issues."""
        scanner = SecurityScanner()
        
        code = "eval('code')\nexec('code')\nos.system('cmd')"
        result = scanner._heuristic_scan(code)
        
        assert result["security_score"] < 10.0
        assert len(result["vulnerabilities"]) > 1


class TestSecurityScannerBanditIntegration:
    """Tests for Bandit integration."""

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", True)
    @patch("tapps_agents.core.security_scanner.bandit")
    @patch("tapps_agents.core.security_scanner.bandit_config")
    @patch("tapps_agents.core.security_scanner.manager")
    def test_scan_file_with_bandit(self, mock_manager_class, mock_config_class, mock_bandit, tmp_path):
        """Test _scan_file uses Bandit when available."""
        scanner = SecurityScanner()
        
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        
        # Mock Bandit manager
        mock_manager = MagicMock()
        mock_issue = MagicMock()
        mock_issue.severity = mock_bandit.LOW
        mock_issue.test_id = "B101"
        mock_issue.test = "test_name"
        mock_issue.lineno = 1
        mock_issue.text = "test text"
        mock_issue.confidence = mock_bandit.MEDIUM
        
        mock_manager.get_issue_list.return_value = [mock_issue]
        mock_manager_class.BanditManager.return_value = mock_manager
        
        result = scanner._scan_file(test_file)
        
        assert "security_score" in result
        assert "vulnerabilities" in result
        assert mock_manager.run_tests.called

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", True)
    @patch("tapps_agents.core.security_scanner.bandit")
    @patch("tapps_agents.core.security_scanner.bandit_config")
    @patch("tapps_agents.core.security_scanner.manager")
    def test_scan_file_bandit_high_severity(self, mock_manager_class, mock_config_class, mock_bandit, tmp_path):
        """Test _scan_file handles high severity issues."""
        scanner = SecurityScanner()
        
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        
        # Mock Bandit manager with high severity issue
        mock_manager = MagicMock()
        mock_issue = MagicMock()
        mock_issue.severity = mock_bandit.HIGH
        mock_issue.test_id = "B101"
        mock_issue.test = "test_name"
        mock_issue.lineno = 1
        mock_issue.text = "test text"
        mock_issue.confidence = mock_bandit.HIGH
        
        mock_manager.get_issue_list.return_value = [mock_issue]
        mock_manager_class.BanditManager.return_value = mock_manager
        
        result = scanner._scan_file(test_file)
        
        assert result["high_severity_count"] == 1
        assert result["security_score"] < 10.0
        assert result["is_safe"] is False

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", True)
    def test_scan_file_bandit_fallback_on_error(self, tmp_path):
        """Test _scan_file falls back to heuristic on Bandit error."""
        scanner = SecurityScanner()
        
        test_file = tmp_path / "test.py"
        test_file.write_text("eval('code')")
        
        # Mock Bandit to raise exception
        with patch("tapps_agents.core.security_scanner.bandit_config") as mock_config:
            mock_config.BanditConfig.side_effect = Exception("Bandit error")
            
            result = scanner._scan_file(test_file)
            
            # Should fall back to heuristic
            assert "security_score" in result
            assert result["security_score"] < 10.0


class TestSecurityScannerHelperMethods:
    """Tests for helper methods."""

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_get_security_score(self):
        """Test get_security_score returns score."""
        scanner = SecurityScanner()
        
        code = "def test(): pass"
        score = scanner.get_security_score(code=code)
        
        assert isinstance(score, float)
        assert 0 <= score <= 10

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_get_vulnerabilities(self):
        """Test get_vulnerabilities returns list."""
        scanner = SecurityScanner()
        
        code = "eval('code')"
        vulnerabilities = scanner.get_vulnerabilities(code=code)
        
        assert isinstance(vulnerabilities, list)
        assert len(vulnerabilities) > 0

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_is_safe_for_learning_safe_code(self):
        """Test is_safe_for_learning with safe code."""
        scanner = SecurityScanner()
        
        code = "def test(): return True"
        is_safe = scanner.is_safe_for_learning(code=code, threshold=7.0)
        
        assert is_safe is True

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_is_safe_for_learning_unsafe_code(self):
        """Test is_safe_for_learning with unsafe code."""
        scanner = SecurityScanner()
        
        code = "eval('code')"
        is_safe = scanner.is_safe_for_learning(code=code, threshold=7.0)
        
        assert is_safe is False

    @patch("tapps_agents.core.security_scanner.HAS_BANDIT", False)
    def test_is_safe_for_learning_below_threshold(self):
        """Test is_safe_for_learning with code below threshold."""
        scanner = SecurityScanner()
        
        code = "eval('code')"
        is_safe = scanner.is_safe_for_learning(code=code, threshold=5.0)
        
        # Score will be low due to eval, so should be False
        assert is_safe is False

    def test_severity_to_string(self):
        """Test _severity_to_string conversion."""
        scanner = SecurityScanner()
        
        if scanner.has_bandit:
            # Test with actual Bandit constants if available
            with patch("tapps_agents.core.security_scanner.bandit") as mock_bandit:
                mock_bandit.HIGH = 1
                mock_bandit.MEDIUM = 2
                mock_bandit.LOW = 3
                
                assert scanner._severity_to_string(1) == "high"
                assert scanner._severity_to_string(2) == "medium"
                assert scanner._severity_to_string(3) == "low"
        else:
            # Without Bandit, should return "unknown"
            assert scanner._severity_to_string(1) == "unknown"

    def test_confidence_to_string(self):
        """Test _confidence_to_string conversion."""
        scanner = SecurityScanner()
        
        if scanner.has_bandit:
            with patch("tapps_agents.core.security_scanner.bandit") as mock_bandit:
                mock_bandit.HIGH = 1
                mock_bandit.MEDIUM = 2
                mock_bandit.LOW = 3
                
                assert scanner._confidence_to_string(1) == "high"
                assert scanner._confidence_to_string(2) == "medium"
                assert scanner._confidence_to_string(3) == "low"
        else:
            assert scanner._confidence_to_string(1) == "unknown"
