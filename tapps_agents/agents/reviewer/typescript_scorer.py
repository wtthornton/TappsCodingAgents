"""
TypeScript Scorer - Code quality scoring for TypeScript and JavaScript files

Phase 6.4.4: TypeScript & JavaScript Support
Phase 1.2: Enhanced maintainability scoring
Phase 7.1: Security Analysis & Score Explanations (Evaluation Enhancement)
"""

import json
import re
import shutil
import subprocess  # nosec B404 - used with fixed args, no shell
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ...core.subprocess_utils import wrap_windows_cmd_shim
from .scoring import BaseScorer


def _js_coverage_from_reports(project_root: Path, file_path: Path) -> float | None:
    """Parse coverage from lcov or coverage-summary.json. §3.6. Returns 0-10 or None."""
    import json as _json

    root = Path(project_root)
    try:
        rel = str(file_path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        rel = file_path.name
    for cov_path in (root / "coverage" / "coverage-summary.json",):
        if not cov_path.exists():
            continue
        try:
            data = _json.loads(cov_path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(data, dict) and "total" in data and isinstance(data["total"], dict):
                pct = (data["total"].get("lines") or {}).get("pct")
                if pct is not None:
                    return min(10.0, max(0.0, float(pct) / 10.0))
            for k, v in (data if isinstance(data, dict) else {}).items():
                if k != "total" and isinstance(v, dict) and (rel in k or file_path.name in k):
                    pct = (v.get("lines") or {}).get("pct")
                    if pct is not None:
                        return min(10.0, max(0.0, float(pct) / 10.0))
        except Exception:
            pass
    for lcov in (root / "coverage" / "lcov.info", root / "lcov.info"):
        if not lcov.exists():
            continue
        try:
            text = lcov.read_text(encoding="utf-8", errors="replace")
            cur_lh = cur_lf = 0
            in_file = False
            for line in text.splitlines():
                if line.startswith("SF:"):
                    p = line[3:].replace("\\", "/")
                    in_file = rel in p or file_path.name in p
                    cur_lh = cur_lf = 0
                elif in_file and line.startswith("LF:"):
                    cur_lf = int(line[3:].strip())
                elif in_file and line.startswith("LH:"):
                    cur_lh = int(line[3:].strip())
                elif in_file and line == "end_of_record" and cur_lf > 0:
                    return min(10.0, 10.0 * cur_lh / cur_lf)
        except Exception:
            pass
    return None


def _apply_npm_audit_to_security(scores: dict[str, Any], file_path: Path) -> None:
    """Fold npm audit into security_score. MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS §3.3."""
    root = BaseScorer._find_project_root(file_path)
    if not root or not (root / "package.json").exists():
        return
    try:
        from ...agents.ops.dependency_analyzer import DependencyAnalyzer

        da = DependencyAnalyzer(project_root=root)
        audit = da.run_npm_audit(project_root=root)
        if not audit or audit.get("vulnerability_count", 0) <= 0:
            return
        sb = audit.get("severity_breakdown") or {}
        penalty = (
            sb.get("critical", 0) * 3.0
            + sb.get("high", 0) * 2.0
            + sb.get("medium", 0) * 1.0
            + sb.get("low", 0) * 0.5
        )
        scores["security_score"] = max(0.0, float(scores.get("security_score", 10.0)) - penalty)
    except Exception:
        pass


# Security patterns for JavaScript/TypeScript code analysis
# Phase 7.1: Comprehensive security pattern detection
DANGEROUS_PATTERNS: dict[str, dict[str, Any]] = {
    "eval": {
        "pattern": r"\beval\s*\(",
        "severity": "HIGH",
        "message": "eval() can execute arbitrary code",
        "recommendation": "Use JSON.parse() for JSON, or safer alternatives like Function constructors with validation",
        "cwe_id": "CWE-95",
    },
    "innerHTML": {
        "pattern": r"\.innerHTML\s*=",
        "severity": "MEDIUM",
        "message": "innerHTML can lead to XSS vulnerabilities",
        "recommendation": "Use textContent for plain text, or sanitize input with DOMPurify",
        "cwe_id": "CWE-79",
    },
    "outerHTML": {
        "pattern": r"\.outerHTML\s*=",
        "severity": "MEDIUM",
        "message": "outerHTML can lead to XSS vulnerabilities",
        "recommendation": "Use DOM manipulation methods instead",
        "cwe_id": "CWE-79",
    },
    "document.write": {
        "pattern": r"\bdocument\.write\s*\(",
        "severity": "MEDIUM",
        "message": "document.write can be exploited for XSS",
        "recommendation": "Use DOM manipulation methods like appendChild instead",
        "cwe_id": "CWE-79",
    },
    "Function constructor": {
        "pattern": r"\bnew\s+Function\s*\(",
        "severity": "HIGH",
        "message": "Function constructor can execute arbitrary code",
        "recommendation": "Use arrow functions or regular function declarations",
        "cwe_id": "CWE-95",
    },
    "setTimeout string": {
        "pattern": r"\bsetTimeout\s*\(\s*['\"`]",
        "severity": "MEDIUM",
        "message": "setTimeout with string argument can execute arbitrary code",
        "recommendation": "Use function reference instead of string",
        "cwe_id": "CWE-95",
    },
    "setInterval string": {
        "pattern": r"\bsetInterval\s*\(\s*['\"`]",
        "severity": "MEDIUM",
        "message": "setInterval with string argument can execute arbitrary code",
        "recommendation": "Use function reference instead of string",
        "cwe_id": "CWE-95",
    },
    "insertAdjacentHTML": {
        "pattern": r"\.insertAdjacentHTML\s*\(",
        "severity": "MEDIUM",
        "message": "insertAdjacentHTML can lead to XSS vulnerabilities",
        "recommendation": "Sanitize input before insertion or use safe DOM methods",
        "cwe_id": "CWE-79",
    },
}

# React-specific security patterns
REACT_SECURITY_PATTERNS: dict[str, dict[str, Any]] = {
    "dangerouslySetInnerHTML": {
        "pattern": r"dangerouslySetInnerHTML",
        "severity": "HIGH",
        "message": "dangerouslySetInnerHTML can lead to XSS vulnerabilities",
        "recommendation": "Sanitize content with DOMPurify or avoid using if possible",
        "cwe_id": "CWE-79",
    },
    "javascript: URL": {
        "pattern": r"href\s*=\s*[{'\"`]javascript:",
        "severity": "HIGH",
        "message": "javascript: URLs can execute arbitrary code",
        "recommendation": "Use onClick handlers instead of javascript: URLs",
        "cwe_id": "CWE-79",
    },
    "target _blank": {
        "pattern": r"target\s*=\s*['\"`]_blank['\"`](?!.*rel\s*=)",
        "severity": "LOW",
        "message": "Links with target='_blank' without rel='noopener' can be exploited",
        "recommendation": "Add rel='noopener noreferrer' to external links",
        "cwe_id": "CWE-1022",
    },
}


@dataclass
class SecurityIssue:
    """Represents a security issue found in code."""
    
    pattern: str
    severity: str  # "HIGH", "MEDIUM", "LOW"
    line: int
    column: int | None
    message: str
    recommendation: str
    cwe_id: str | None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ScoreExplanation:
    """Explanation for a code quality score."""
    
    score: float
    reason: str
    issues: list[str]
    recommendations: list[str]
    tool_status: str  # "available", "unavailable", "error", "pattern_based"
    tool_name: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class TypeScriptScorer(BaseScorer):
    """
    Calculate code quality scores for TypeScript and JavaScript files.

    Phase 6.4.4: TypeScript & JavaScript Support

    Supports:
    - TypeScript files: .ts, .tsx
    - JavaScript files: .js, .jsx
    """

    def __init__(
        self, eslint_config: str | None = None, tsconfig_path: str | None = None
    ):
        """
        Initialize TypeScript scorer.

        Args:
            eslint_config: Path to ESLint config file (optional)
            tsconfig_path: Path to tsconfig.json (optional)
        """
        self.eslint_config = eslint_config
        self.tsconfig_path = tsconfig_path

        # Check for tool availability
        self.has_tsc = self._check_tsc_available()
        self.has_eslint = self._check_eslint_available()
        self.has_npm = shutil.which("npm") is not None
        self.has_npx = shutil.which("npx") is not None

    def _check_tsc_available(self) -> bool:
        """Check if TypeScript compiler (tsc) is available."""
        if shutil.which("tsc"):
            return True
        npx_path = shutil.which("npx")
        if npx_path:
            try:
                result = subprocess.run(  # nosec B603 - fixed args
                    wrap_windows_cmd_shim([npx_path, "--yes", "tsc", "--version"]),
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False
        return False

    def _check_eslint_available(self) -> bool:
        """Check if ESLint is available."""
        if shutil.which("eslint"):
            return True
        npx_path = shutil.which("npx")
        if npx_path:
            try:
                result = subprocess.run(  # nosec B603 - fixed args
                    wrap_windows_cmd_shim([npx_path, "--yes", "eslint", "--version"]),
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False
        return False

    def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """
        Score a TypeScript/JavaScript file.

        Args:
            file_path: Path to the file
            code: File content (for complexity analysis)

        Returns:
            Dictionary with scores:
            {
                "complexity_score": float (0-10),
                "security_score": float (0-10),
                "maintainability_score": float (0-10),
                "test_coverage_score": float (0-10),
                "performance_score": float (0-10),
                "linting_score": float (0-10),
                "type_checking_score": float (0-10),
                "overall_score": float (0-100),
                "metrics": {...}
            }
        """
        metrics: dict[str, float] = {}
        scores: dict[str, Any] = {
            "complexity_score": 0.0,
            "security_score": 0.0,
            "maintainability_score": 0.0,
            "test_coverage_score": 0.0,
            "performance_score": 5.0,
            "structure_score": 0.0,  # 7-category §3.2
            "devex_score": 0.0,  # 7-category §3.2
            "linting_score": 0.0,
            "type_checking_score": 0.0,
            "metrics": metrics,
        }

        # Complexity Score (0-10, lower is better)
        scores["complexity_score"] = self._calculate_complexity(code)
        metrics["complexity"] = float(scores["complexity_score"])

        # Linting Score (0-10, higher is better) - ESLint
        scores["linting_score"] = self._calculate_linting_score(file_path)
        metrics["linting"] = float(scores["linting_score"])
        
        # Security Score (0-10, higher is better) - Phase 7.1 + npm audit §3.3
        security_result = self._calculate_security_score(code, file_path)
        scores["security_score"] = security_result["score"]
        scores["_security_issues"] = security_result.get("issues", [])
        # npm audit: fold into security (MCP_SYSTEMS_IMPROVEMENT_RECOMMENDATIONS §3.3)
        _apply_npm_audit_to_security(scores, file_path)
        metrics["security"] = float(scores["security_score"])

        # Type Checking Score (0-10, higher is better) - TypeScript compiler
        if file_path.suffix in [".ts", ".tsx"]:
            scores["type_checking_score"] = self._calculate_type_checking_score(
                file_path
            )
        else:
            scores["type_checking_score"] = 5.0  # Neutral for JavaScript
        metrics["type_checking"] = float(scores["type_checking_score"])

        # Maintainability Score (0-10, higher is better)
        # Phase 3.1: Use context-aware maintainability scorer
        from ...core.language_detector import Language
        from .maintainability_scorer import MaintainabilityScorer

        maintainability_scorer = MaintainabilityScorer()
        language = (
            Language.TYPESCRIPT
            if file_path and file_path.suffix in [".ts", ".tsx"]
            else Language.JAVASCRIPT
        )
        scores["maintainability_score"] = maintainability_scorer.calculate(
            code, language, file_path, context=None
        )

        # Phase 3.2: Use context-aware performance scorer
        from .performance_scorer import PerformanceScorer

        performance_scorer = PerformanceScorer()
        scores["performance_score"] = performance_scorer.calculate(
            code, language, file_path, context=None
        )
        metrics["maintainability"] = float(scores["maintainability_score"])

        # Test Coverage Score (0-10, higher is better)
        scores["test_coverage_score"] = self._calculate_test_coverage(file_path)
        metrics["test_coverage"] = float(scores["test_coverage_score"])

        # Structure and DevEx (0-10, higher is better) - 7-category §3.2
        scores["structure_score"] = self._calculate_structure_score(file_path)
        scores["devex_score"] = self._calculate_devex_score(file_path)
        metrics["structure"] = float(scores["structure_score"])
        metrics["devex"] = float(scores["devex_score"])

        # Overall Score (weighted average, 7-category)
        # complexity 18%, security 13%, maintainability 23%, test 13%, perf 8%, lint 8%, type 5%, structure 6%, devex 6%
        scores["overall_score"] = (
            (10 - scores["complexity_score"]) * 0.18
            + scores["security_score"] * 0.13
            + scores["maintainability_score"] * 0.23
            + scores["test_coverage_score"] * 0.13
            + scores["performance_score"] * 0.08
            + scores["linting_score"] * 0.08
            + scores["type_checking_score"] * 0.05
            + scores["structure_score"] * 0.06
            + scores["devex_score"] * 0.06
        ) * 10  # Scale to 0-100

        # Phase 3.3: Validate all scores before returning
        from ...core.language_detector import Language
        from .score_validator import ScoreValidator

        validator = ScoreValidator()
        language = (
            Language.TYPESCRIPT
            if file_path and file_path.suffix in [".ts", ".tsx"]
            else Language.JAVASCRIPT
        )
        validation_results = validator.validate_all_scores(
            scores, language=language, context=None
        )

        # Update scores with validated/clamped values and add explanations
        validated_scores = {}
        score_explanations = {}
        for category, result in validation_results.items():
            if result.valid and result.calibrated_score is not None:
                validated_scores[category] = result.calibrated_score
                if result.explanation:
                    score_explanations[category] = {
                        "explanation": result.explanation,
                        "suggestions": result.suggestions,
                    }
            else:
                validated_scores[category] = scores.get(category, 0.0)

        # Merge validated scores back into scores
        for key, value in validated_scores.items():
            if key != "_explanations":
                scores[key] = value

        # Add explanations to result if any
        if score_explanations:
            scores["_explanations"] = score_explanations

        # Phase 7.1: Generate comprehensive explanations
        enhanced_explanations = self._generate_explanations(
            scores,
            scores.get("_security_issues", []),
            self.has_eslint,
            self.has_tsc
        )
        if enhanced_explanations:
            # Merge with existing explanations
            if "_explanations" not in scores:
                scores["_explanations"] = {}
            scores["_explanations"].update(enhanced_explanations)
        
        # Add tool status
        scores["_tool_status"] = {
            "eslint": "available" if self.has_eslint else "unavailable",
            "tsc": "available" if self.has_tsc else "unavailable",
            "security_scanner": "pattern_based",
            "npm": "available" if self.has_npm else "unavailable",
        }

        return scores

    def _calculate_complexity(self, code: str) -> float:
        """
        Calculate cyclomatic complexity for TypeScript/JavaScript.

        Simple heuristic-based complexity analysis.
        """
        try:
            # Count decision points
            decision_keywords = [
                "if",
                "else",
                "for",
                "while",
                "do",
                "switch",
                "case",
                "catch",
                "&&",
                "||",
                "?",
                ":",
                "try",
            ]

            complexity = 1  # Base complexity
            lines = code.split("\n")

            for line in lines:
                stripped = line.strip()
                # Skip comments
                if (
                    stripped.startswith("//")
                    or stripped.startswith("*")
                    or stripped.startswith("/*")
                ):
                    continue

                for keyword in decision_keywords:
                    # Count occurrences (rough estimate)
                    if f" {keyword} " in f" {stripped} ":
                        complexity += 1
                    elif f" {keyword}(" in f" {stripped} ":
                        complexity += 1

            # Scale to 0-10 (max complexity ~50 = 10)
            return min(complexity / 5.0, 10.0)

        except Exception:
            return 5.0  # Neutral on error

    def _calculate_linting_score(self, file_path: Path) -> float:
        """
        Calculate linting score using ESLint (0-10 scale, higher is better).

        Returns:
            Linting score (0-10)
        """
        if not self.has_eslint:
            return 5.0  # Neutral score if ESLint not available

        if file_path.suffix not in [".ts", ".tsx", ".js", ".jsx"]:
            return 10.0  # Perfect score for unsupported file types

        try:
            # Build ESLint command
            npx_path = shutil.which("npx")
            if not npx_path:
                return 5.0  # Neutral if npx not available
            command = [npx_path, "--yes", "eslint", str(file_path), "--format", "json"]

            # Add config if provided
            if self.eslint_config:
                command.extend(["--config", self.eslint_config])

            result = subprocess.run(  # nosec B603 - fixed args
                wrap_windows_cmd_shim(command),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                cwd=file_path.parent if file_path.parent.exists() else None,
            )

            # ESLint returns non-zero exit code if there are errors/warnings
            if result.returncode != 0 and result.stdout:
                try:
                    # Parse JSON output
                    eslint_output = json.loads(result.stdout)

                    if not eslint_output:
                        return 10.0  # No output = no issues

                    # Count errors and warnings
                    total_errors = 0
                    total_warnings = 0

                    for file_result in eslint_output:
                        messages = file_result.get("messages", [])
                        for message in messages:
                            severity = message.get("severity", 1)
                            if severity == 2:  # Error
                                total_errors += 1
                            elif severity == 1:  # Warning
                                total_warnings += 1

                    # Score: 10 - (errors * 2 + warnings * 1), minimum 0
                    score = 10.0 - (total_errors * 2.0 + total_warnings * 1.0)
                    return max(0.0, min(10.0, score))

                except json.JSONDecodeError:
                    # If JSON parsing fails, assume no issues if exit code is 0
                    if result.returncode == 0:
                        return 10.0
                    return 5.0  # Neutral on parsing error

            # Exit code 0 = no issues
            return 10.0

        except subprocess.TimeoutExpired:
            return 5.0  # Neutral on timeout
        except FileNotFoundError:
            return 5.0  # ESLint not found
        except Exception:
            return 5.0  # Any other error

    def _calculate_type_checking_score(self, file_path: Path) -> float:
        """
        Calculate type checking score using TypeScript compiler (tsc).

        Returns:
            Type checking score (0-10, higher is better)
        """
        if not self.has_tsc:
            return 5.0  # Neutral score if tsc not available

        if file_path.suffix not in [".ts", ".tsx"]:
            return 5.0  # Neutral for JavaScript files

        try:
            # Build tsc command
            npx_path = shutil.which("npx")
            if not npx_path:
                return 5.0  # Neutral if npx not available
            command = [npx_path, "--yes", "tsc", "--noEmit", "--pretty", "false"]

            # Add tsconfig if provided
            if self.tsconfig_path:
                command.extend(["--project", self.tsconfig_path])

            # Add file to check
            command.append(str(file_path))

            result = subprocess.run(  # nosec B603 - fixed args
                wrap_windows_cmd_shim(command),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                cwd=file_path.parent if file_path.parent.exists() else None,
            )

            # tsc returns non-zero exit code if there are type errors
            if result.returncode != 0:
                # Count errors (lines with "error TS")
                error_count = result.stderr.count("error TS") + result.stdout.count(
                    "error TS"
                )

                # Score: 10 - (error_count * 0.5), minimum 0
                score = 10.0 - (error_count * 0.5)
                return max(0.0, min(10.0, score))

            # Exit code 0 = no type errors
            return 10.0

        except subprocess.TimeoutExpired:
            return 5.0  # Neutral on timeout
        except FileNotFoundError:
            return 5.0  # tsc not found
        except Exception:
            return 5.0  # Any other error

    def _calculate_maintainability(
        self, code: str, file_path: Path | None = None
    ) -> float:
        """
        Calculate maintainability score for TypeScript/JavaScript.

        Enhanced heuristic-based maintainability analysis with context-aware scoring.
        """
        try:
            lines = code.split("\n")
            total_lines = len(lines)

            if total_lines == 0:
                return 5.0

            # Base score - start higher for TypeScript (type safety helps)
            is_typescript = file_path and file_path.suffix in [".ts", ".tsx"]
            score = 6.0 if is_typescript else 5.0

            # Factors that improve maintainability
            has_comments = sum(
                1 for line in lines if line.strip().startswith("//") or "/*" in line
            )
            has_javadoc = sum(1 for line in lines if "/**" in line or "* @" in line)
            
            # Enhanced type safety detection
            has_types = sum(
                1
                for line in lines
                if ": " in line
                and (
                    "string" in line
                    or "number" in line
                    or "boolean" in line
                    or "object" in line
                    or "Array<" in line
                    or "Promise<" in line
                    or "Record<" in line
                )
            )
            
            # Check for interfaces and type aliases (TypeScript)
            has_interfaces = len(re.findall(r"interface\s+\w+", code))
            has_type_aliases = len(re.findall(r"type\s+\w+\s*=", code))
            has_generics = len(re.findall(r"<\w+>", code))
            
            # Check for proper exports/imports structure
            has_exports = len(re.findall(r"export\s+(const|function|class|interface|type)", code))
            has_imports = len(re.findall(r"import\s+.*from\s+['\"]", code))
            
            # Error handling patterns
            has_error_handling = bool(
                re.search(r"try\s*\{|catch\s*\(|throw\s+new\s+Error", code)
            )
            
            # Documentation patterns
            has_jsdoc = bool(re.search(r"/\*\*[\s\S]*?\*/", code))

            # Factors that reduce maintainability
            long_lines = sum(1 for line in lines if len(line) > 120)
            # Better nesting calculation
            nesting_depth = self._calculate_nesting_depth(code)
            
            # Function/class complexity
            function_count = len(re.findall(r"(function|const\s+\w+\s*=\s*\(|=>\s*\{)", code))
            avg_function_length = total_lines / max(function_count, 1)

            # Positive factors
            if has_comments > 0:
                score += min(has_comments / total_lines * 2, 2.0)
            if has_javadoc > 0 or has_jsdoc:
                score += min((has_javadoc + (1 if has_jsdoc else 0)) / total_lines * 1.5, 1.5)
            if is_typescript:
                # TypeScript-specific bonuses
                if has_types > 0:
                    score += min(has_types / total_lines * 2.5, 2.5)
                if has_interfaces > 0:
                    score += min(has_interfaces * 0.3, 1.0)
                if has_type_aliases > 0:
                    score += min(has_type_aliases * 0.2, 0.5)
                if has_generics > 0:
                    score += min(has_generics * 0.1, 0.5)
            
            # Code organization
            if has_exports > 0:
                score += min(has_exports * 0.1, 0.5)
            if has_imports > 0:
                score += min(has_imports * 0.05, 0.3)
            
            # Error handling
            if has_error_handling:
                score += 0.5

            # Negative factors
            if long_lines > 0:
                score -= min(long_lines / total_lines * 1.5, 1.5)
            if nesting_depth > 3:
                score -= min((nesting_depth - 3) * 0.5, 2.0)
            if avg_function_length > 50:
                score -= min((avg_function_length - 50) / 50 * 1.0, 1.5)

            return max(0.0, min(10.0, score))

        except Exception:
            return 5.0  # Neutral on error
    
    def _calculate_nesting_depth(self, code: str) -> int:
        """Calculate maximum nesting depth in code."""
        max_depth = 0
        current_depth = 0
        
        for char in code:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth = max(0, current_depth - 1)
        
        return max_depth

    def _calculate_test_coverage(self, file_path: Path) -> float:
        """
        Test coverage for JS/TS. §3.6: reuse coverage from Vitest/Jest/c8/nyc (lcov, coverage-summary.json).
        Fallback: heuristic from test file presence.
        """
        root = BaseScorer._find_project_root(file_path)
        if root:
            v = _js_coverage_from_reports(root, file_path)
            if v is not None:
                return float(v)
        try:
            test_patterns = [
                file_path.stem + ".test" + file_path.suffix,
                file_path.stem + ".spec" + file_path.suffix,
                file_path.name.replace(".ts", ".test.ts").replace(".js", ".test.js"),
            ]
            parent_dir = file_path.parent
            test_files_found = 0
            for pattern in test_patterns:
                if (parent_dir / pattern).exists():
                    test_files_found += 1
                    break
            if (parent_dir / "__tests__").exists():
                test_files_found += 1
            return min(10.0, 5.0 + test_files_found * 2.5)
        except Exception:
            return 5.0

    def get_eslint_issues(self, file_path: Path) -> dict[str, Any]:
        """
        Get ESLint issues for a file.

        Returns:
            Dictionary with ESLint results
        """
        if not self.has_eslint:
            return {"available": False, "error": "ESLint not available"}

        try:
            npx_path = shutil.which("npx")
            if not npx_path:
                return {"available": False, "error": "npx not available"}
            command = [npx_path, "--yes", "eslint", str(file_path), "--format", "json"]

            if self.eslint_config:
                command.extend(["--config", self.eslint_config])

            result = subprocess.run(  # nosec B603 - fixed args
                wrap_windows_cmd_shim(command),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                cwd=file_path.parent if file_path.parent.exists() else None,
            )

            if result.returncode == 0:
                return {"available": True, "issues": []}

            try:
                eslint_output = json.loads(result.stdout)
                return {"available": True, "issues": eslint_output}
            except json.JSONDecodeError:
                return {
                    "available": True,
                    "issues": [],
                    "error": "Failed to parse ESLint output",
                }

        except Exception as e:
            return {"available": False, "error": str(e)}

    def get_type_errors(self, file_path: Path) -> dict[str, Any]:
        """
        Get TypeScript type errors for a file.

        Returns:
            Dictionary with type checking results
        """
        if not self.has_tsc:
            return {"available": False, "error": "TypeScript compiler not available"}

        if file_path.suffix not in [".ts", ".tsx"]:
            return {"available": False, "error": "File is not TypeScript"}

        try:
            npx_path = shutil.which("npx")
            if not npx_path:
                return {"available": False, "error": "npx not available"}
            command = [npx_path, "--yes", "tsc", "--noEmit", "--pretty", "false"]

            if self.tsconfig_path:
                command.extend(["--project", self.tsconfig_path])

            command.append(str(file_path))

            result = subprocess.run(  # nosec B603 - fixed args
                wrap_windows_cmd_shim(command),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                cwd=file_path.parent if file_path.parent.exists() else None,
            )

            errors = []
            if result.returncode != 0:
                # Parse errors from output
                for line in (result.stderr + result.stdout).split("\n"):
                    if "error TS" in line:
                        errors.append(line.strip())

            return {
                "available": True,
                "errors": errors,
                "error_count": len(errors),
                "passed": len(errors) == 0,
            }

        except Exception as e:
            return {"available": False, "error": str(e)}

    # ========================================================================
    # Phase 7.1: Security Analysis Enhancement
    # ========================================================================
    
    def _calculate_security_score(
        self, code: str, file_path: Path
    ) -> dict[str, Any]:
        """
        Calculate security score based on dangerous patterns.
        
        Phase 7.1: Security Analysis Enhancement
        
        Args:
            code: Source code content
            file_path: Path to the file (for React detection)
            
        Returns:
            Dictionary with:
                - score: Security score from 0.0 to 10.0 (higher is better)
                - issues: List of SecurityIssue dictionaries
                - high_count, medium_count, low_count: Issue counts by severity
        """
        issues = self._detect_dangerous_patterns(code, file_path)
        
        # Calculate score based on issues
        # Base score: 10.0
        # HIGH severity: -2.0 each
        # MEDIUM severity: -1.0 each
        # LOW severity: -0.5 each
        base_score = 10.0
        high_count = sum(1 for i in issues if i.severity == "HIGH")
        medium_count = sum(1 for i in issues if i.severity == "MEDIUM")
        low_count = sum(1 for i in issues if i.severity == "LOW")
        
        penalty = (high_count * 2.0) + (medium_count * 1.0) + (low_count * 0.5)
        score = max(0.0, min(10.0, base_score - penalty))
        
        return {
            "score": score,
            "issues": [i.to_dict() for i in issues],
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "total_issues": len(issues),
        }
    
    def _detect_dangerous_patterns(
        self, code: str, file_path: Path | None = None
    ) -> list[SecurityIssue]:
        """
        Detect dangerous JavaScript/TypeScript patterns.
        
        Phase 7.1: Security Analysis Enhancement
        
        Args:
            code: Source code to analyze
            file_path: Optional path to detect React files
            
        Returns:
            List of SecurityIssue objects
        """
        issues: list[SecurityIssue] = []
        lines = code.split("\n")
        
        # Check if this is a React file
        is_react = False
        if file_path and file_path.suffix in [".tsx", ".jsx"]:
            is_react = True
        elif "react" in code.lower() or "import React" in code:
            is_react = True
        
        # Detect general JavaScript/TypeScript patterns
        for pattern_name, pattern_info in DANGEROUS_PATTERNS.items():
            regex = re.compile(pattern_info["pattern"])
            for line_num, line in enumerate(lines, 1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("*"):
                    continue
                
                matches = list(regex.finditer(line))
                for match in matches:
                    issues.append(SecurityIssue(
                        pattern=pattern_name,
                        severity=pattern_info["severity"],
                        line=line_num,
                        column=match.start() + 1,
                        message=pattern_info["message"],
                        recommendation=pattern_info["recommendation"],
                        cwe_id=pattern_info.get("cwe_id"),
                    ))
        
        # Detect React-specific patterns
        if is_react:
            for pattern_name, pattern_info in REACT_SECURITY_PATTERNS.items():
                regex = re.compile(pattern_info["pattern"])
                for line_num, line in enumerate(lines, 1):
                    # Skip comments
                    stripped = line.strip()
                    if stripped.startswith("//") or stripped.startswith("*"):
                        continue
                    
                    matches = list(regex.finditer(line))
                    for match in matches:
                        issues.append(SecurityIssue(
                            pattern=pattern_name,
                            severity=pattern_info["severity"],
                            line=line_num,
                            column=match.start() + 1,
                            message=pattern_info["message"],
                            recommendation=pattern_info["recommendation"],
                            cwe_id=pattern_info.get("cwe_id"),
                        ))
        
        return issues
    
    def get_security_issues(
        self, code: str, file_path: Path
    ) -> dict[str, Any]:
        """
        Get detailed security issues for external access.
        
        Phase 7.1: Security Analysis Enhancement
        
        Args:
            code: Source code content
            file_path: Path to the file
            
        Returns:
            Dictionary with security analysis results
        """
        result = self._calculate_security_score(code, file_path)
        result["available"] = True
        return result
    
    def _generate_explanations(
        self,
        scores: dict[str, Any],
        security_issues: list[dict[str, Any]],
        eslint_available: bool,
        tsc_available: bool,
    ) -> dict[str, dict[str, Any]]:
        """
        Generate explanations for each score.
        
        Phase 7.1: Score Explanation Enhancement
        
        Args:
            scores: Calculated scores dictionary
            security_issues: List of security issues found
            eslint_available: Whether ESLint is available
            tsc_available: Whether TypeScript compiler is available
            
        Returns:
            Dictionary of explanations keyed by score name
        """
        explanations: dict[str, dict[str, Any]] = {}
        
        # Security score explanation
        security_score = scores.get("security_score", 5.0)
        if security_issues:
            high_issues = [i for i in security_issues if i.get("severity") == "HIGH"]
            medium_issues = [i for i in security_issues if i.get("severity") == "MEDIUM"]
            low_issues = [i for i in security_issues if i.get("severity") == "LOW"]
            
            issue_summary = []
            if high_issues:
                issue_summary.append(f"{len(high_issues)} HIGH severity")
            if medium_issues:
                issue_summary.append(f"{len(medium_issues)} MEDIUM severity")
            if low_issues:
                issue_summary.append(f"{len(low_issues)} LOW severity")
            
            explanations["security_score"] = ScoreExplanation(
                score=security_score,
                reason=f"{len(security_issues)} security issue(s) detected: {', '.join(issue_summary)}",
                issues=[f"{i.get('pattern')} at line {i.get('line')}: {i.get('message')}" for i in security_issues[:5]],
                recommendations=[i.get("recommendation", "") for i in security_issues[:3] if i.get("recommendation")],
                tool_status="pattern_based",
                tool_name="TypeScriptSecurityScanner",
            ).to_dict()
        else:
            explanations["security_score"] = ScoreExplanation(
                score=security_score,
                reason="No security issues detected",
                issues=[],
                recommendations=["Code appears secure. Continue following security best practices."],
                tool_status="pattern_based",
                tool_name="TypeScriptSecurityScanner",
            ).to_dict()
        
        # Linting score explanation
        linting_score = scores.get("linting_score", 5.0)
        if not eslint_available:
            explanations["linting_score"] = ScoreExplanation(
                score=linting_score,
                reason="ESLint not available - using neutral score",
                issues=["ESLint is not installed or not accessible via npx"],
                recommendations=["Install ESLint: npm install -g eslint", "Or install locally: npm install --save-dev eslint"],
                tool_status="unavailable",
                tool_name="ESLint",
            ).to_dict()
        elif linting_score < 7.0:
            explanations["linting_score"] = ScoreExplanation(
                score=linting_score,
                reason=f"ESLint found issues (score: {linting_score:.1f}/10)",
                issues=["Multiple linting violations detected"],
                recommendations=["Run 'npx eslint --fix' to auto-fix issues", "Review ESLint configuration"],
                tool_status="available",
                tool_name="ESLint",
            ).to_dict()
        
        # Type checking score explanation
        type_checking_score = scores.get("type_checking_score", 5.0)
        if not tsc_available:
            explanations["type_checking_score"] = ScoreExplanation(
                score=type_checking_score,
                reason="TypeScript compiler not available - using neutral score",
                issues=["TypeScript is not installed or not accessible via npx"],
                recommendations=["Install TypeScript: npm install -g typescript", "Or install locally: npm install --save-dev typescript"],
                tool_status="unavailable",
                tool_name="TypeScript Compiler (tsc)",
            ).to_dict()
        elif type_checking_score < 7.0:
            explanations["type_checking_score"] = ScoreExplanation(
                score=type_checking_score,
                reason=f"TypeScript compiler found type errors (score: {type_checking_score:.1f}/10)",
                issues=["Type checking errors detected"],
                recommendations=["Fix type errors reported by tsc", "Enable strict mode in tsconfig.json for better type safety"],
                tool_status="available",
                tool_name="TypeScript Compiler (tsc)",
            ).to_dict()
        
        # Complexity score explanation
        complexity_score = scores.get("complexity_score", 5.0)
        if complexity_score > 7.0:
            explanations["complexity_score"] = ScoreExplanation(
                score=complexity_score,
                reason=f"High cyclomatic complexity detected (score: {complexity_score:.1f}/10)",
                issues=["Code has many decision points (if/else, loops, ternary operators)"],
                recommendations=[
                    "Extract complex logic into smaller functions",
                    "Consider using early returns to reduce nesting",
                    "Apply the single responsibility principle",
                ],
                tool_status="available",
                tool_name="Complexity Analyzer",
            ).to_dict()
        
        # Maintainability score explanation
        maintainability_score = scores.get("maintainability_score", 5.0)
        if maintainability_score < 6.0:
            explanations["maintainability_score"] = ScoreExplanation(
                score=maintainability_score,
                reason=f"Low maintainability score (score: {maintainability_score:.1f}/10)",
                issues=["Code may be difficult to maintain"],
                recommendations=[
                    "Add JSDoc comments to functions and classes",
                    "Use TypeScript interfaces for type definitions",
                    "Break down large functions into smaller ones",
                    "Follow consistent naming conventions",
                ],
                tool_status="available",
                tool_name="Maintainability Analyzer",
            ).to_dict()
        
        return explanations
