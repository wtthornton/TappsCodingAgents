"""
Security Scanner Module

Provides reusable security scanning functionality using Bandit.
Extracted from CodeScorer for use in agent learning system.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Try to import bandit
try:
    import bandit
    from bandit.core import config as bandit_config
    from bandit.core import manager

    HAS_BANDIT = True
except ImportError:
    HAS_BANDIT = False
    bandit = None  # type: ignore
    bandit_config = None  # type: ignore
    manager = None  # type: ignore


class SecurityScanner:
    """
    Reusable security scanner using Bandit.

    Provides security scanning functionality for code patterns
    to prevent learning from vulnerable code.
    """

    def __init__(self):
        """Initialize security scanner."""
        self.has_bandit = HAS_BANDIT
        if not self.has_bandit:
            logger.warning(
                "Bandit not available. Security scanning will use basic heuristics only."
            )

    def scan_code(
        self, file_path: Path | None = None, code: str | None = None
    ) -> dict[str, Any]:
        """
        Scan code for security vulnerabilities.

        Args:
            file_path: Optional path to file (preferred for Bandit)
            code: Optional code string (fallback if file_path not available)

        Returns:
            Dictionary with:
            - security_score: float (0-10, higher is better)
            - vulnerabilities: list of vulnerability dicts
            - high_severity_count: int
            - medium_severity_count: int
            - low_severity_count: int
            - is_safe: bool
        """
        if not self.has_bandit:
            # Fallback to basic heuristic check
            code_str = code or ""
            if file_path and file_path.exists():
                try:
                    code_str = file_path.read_text(encoding="utf-8")
                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {e}")
                    code_str = code or ""

            return self._heuristic_scan(code_str)

        # Use Bandit for proper security analysis
        try:
            # Prefer file_path if available
            if file_path and file_path.exists():
                return self._scan_file(file_path)
            elif code:
                # Create temporary file for Bandit
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".py", delete=False
                ) as tmp_file:
                    tmp_path = Path(tmp_file.name)
                    tmp_path.write_text(code, encoding="utf-8")
                    try:
                        result = self._scan_file(tmp_path)
                    finally:
                        # Clean up temp file
                        try:
                            tmp_path.unlink()
                        except Exception:
                            pass
                    return result
            else:
                logger.warning("No file_path or code provided for security scan")
                return {
                    "security_score": 5.0,
                    "vulnerabilities": [],
                    "high_severity_count": 0,
                    "medium_severity_count": 0,
                    "low_severity_count": 0,
                    "is_safe": True,
                }
        except Exception as e:
            logger.warning(f"Security scan failed: {e}")
            # Fallback to heuristic
            code_str = code or ""
            if file_path and file_path.exists():
                try:
                    code_str = file_path.read_text(encoding="utf-8")
                except Exception:
                    pass
            return self._heuristic_scan(code_str)

    def _scan_file(self, file_path: Path) -> dict[str, Any]:
        """
        Scan a file using Bandit.

        Args:
            file_path: Path to file to scan

        Returns:
            Security scan results dictionary
        """
        if not self.has_bandit:
            return self._heuristic_scan(file_path.read_text(encoding="utf-8"))

        try:
            b_conf = bandit_config.BanditConfig()
            b_mgr = manager.BanditManager(
                config=b_conf,
                agg_type="file",
                debug=False,
                verbose=False,
                quiet=True,
                profile=None,
                ignore_nosec=False,
            )
            b_mgr.discover_files([str(file_path)], False)
            b_mgr.run_tests()

            # Get issues
            issues = b_mgr.get_issue_list()

            # Count by severity
            high_severity = sum(1 for i in issues if i.severity == bandit.HIGH)
            medium_severity = sum(1 for i in issues if i.severity == bandit.MEDIUM)
            low_severity = sum(1 for i in issues if i.severity == bandit.LOW)

            # Calculate security score (0-10, higher is better)
            # Score: 10 - (high*3 + medium*1 + low*0.5)
            score = 10.0 - (high_severity * 3.0 + medium_severity * 1.0 + low_severity * 0.5)
            score = max(0.0, score)

            # Build vulnerability list
            vulnerabilities = []
            for issue in issues:
                vulnerabilities.append(
                    {
                        "severity": self._severity_to_string(issue.severity),
                        "test_id": issue.test_id,
                        "test_name": issue.test,
                        "line": issue.lineno,
                        "text": issue.text,
                        "confidence": self._confidence_to_string(issue.confidence),
                    }
                )

            return {
                "security_score": score,
                "vulnerabilities": vulnerabilities,
                "high_severity_count": high_severity,
                "medium_severity_count": medium_severity,
                "low_severity_count": low_severity,
                "is_safe": high_severity == 0 and medium_severity == 0,
            }
        except (FileNotFoundError, PermissionError, ValueError) as e:
            logger.warning(f"Bandit scan failed for {file_path}: {e}")
            # Fallback to heuristic
            try:
                code = file_path.read_text(encoding="utf-8")
                return self._heuristic_scan(code)
            except Exception:
                return {
                    "security_score": 5.0,
                    "vulnerabilities": [],
                    "high_severity_count": 0,
                    "medium_severity_count": 0,
                    "low_severity_count": 0,
                    "is_safe": True,
                }
        except Exception as e:
            logger.warning(f"Unexpected error in Bandit scan: {e}")
            return {
                "security_score": 5.0,
                "vulnerabilities": [],
                "high_severity_count": 0,
                "medium_severity_count": 0,
                "low_severity_count": 0,
                "is_safe": True,
            }

    def _heuristic_scan(self, code: str) -> dict[str, Any]:
        """
        Basic heuristic security check when Bandit is not available.

        Args:
            code: Code string to check

        Returns:
            Security scan results dictionary
        """
        insecure_patterns = [
            "eval(",
            "exec(",
            "__import__",
            "pickle.loads",
            "subprocess.call",
            "os.system",
            "shell=True",
            "input(",
        ]
        issues = sum(1 for pattern in insecure_patterns if pattern in code)

        # Score: 10 - (issues * 2)
        score = max(0.0, 10.0 - (issues * 2.0))

        vulnerabilities = []
        for pattern in insecure_patterns:
            if pattern in code:
                vulnerabilities.append(
                    {
                        "severity": "medium",
                        "test_id": "heuristic",
                        "test_name": f"Insecure pattern: {pattern}",
                        "line": 0,
                        "text": f"Found potentially insecure pattern: {pattern}",
                        "confidence": "medium",
                    }
                )

        return {
            "security_score": score,
            "vulnerabilities": vulnerabilities,
            "high_severity_count": 0,
            "medium_severity_count": len(vulnerabilities),
            "low_severity_count": 0,
            "is_safe": len(vulnerabilities) == 0,
        }

    def _severity_to_string(self, severity: int) -> str:
        """Convert Bandit severity integer to string."""
        if not self.has_bandit:
            return "unknown"
        if severity == bandit.HIGH:
            return "high"
        elif severity == bandit.MEDIUM:
            return "medium"
        elif severity == bandit.LOW:
            return "low"
        return "unknown"

    def _confidence_to_string(self, confidence: int) -> str:
        """Convert Bandit confidence integer to string."""
        if not self.has_bandit:
            return "unknown"
        if confidence == bandit.HIGH:
            return "high"
        elif confidence == bandit.MEDIUM:
            return "medium"
        elif confidence == bandit.LOW:
            return "low"
        return "unknown"

    def get_security_score(
        self, file_path: Path | None = None, code: str | None = None
    ) -> float:
        """
        Get security score (0-10, higher is better).

        Args:
            file_path: Optional path to file
            code: Optional code string

        Returns:
            Security score (0-10)
        """
        result = self.scan_code(file_path=file_path, code=code)
        return result["security_score"]

    def get_vulnerabilities(
        self, file_path: Path | None = None, code: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get list of detected vulnerabilities.

        Args:
            file_path: Optional path to file
            code: Optional code string

        Returns:
            List of vulnerability dictionaries
        """
        result = self.scan_code(file_path=file_path, code=code)
        return result["vulnerabilities"]

    def is_safe_for_learning(
        self,
        file_path: Path | None = None,
        code: str | None = None,
        threshold: float = 7.0,
    ) -> bool:
        """
        Check if code is safe to learn from.

        Args:
            file_path: Optional path to file
            code: Optional code string
            threshold: Minimum security score (default: 7.0)

        Returns:
            True if code is safe for learning
        """
        result = self.scan_code(file_path=file_path, code=code)
        return result["security_score"] >= threshold and result["is_safe"]

