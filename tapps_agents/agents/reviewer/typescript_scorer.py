"""
TypeScript Scorer - Code quality scoring for TypeScript and JavaScript files

Phase 6.4.4: TypeScript & JavaScript Support
Phase 1.2: Enhanced maintainability scoring
"""

import json
import re
import shutil
import subprocess  # nosec B404 - used with fixed args, no shell
from pathlib import Path
from typing import Any

from ...core.subprocess_utils import wrap_windows_cmd_shim
from .scoring import BaseScorer


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
            "security_score": 5.0,  # Default neutral score
            "maintainability_score": 0.0,
            "test_coverage_score": 0.0,
            "performance_score": 5.0,  # Default, will be overridden by PerformanceScorer
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
        from .maintainability_scorer import MaintainabilityScorer
        from ...core.language_detector import Language

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

        # Overall Score (weighted average)
        # Weights: complexity 20%, security 15%, maintainability 25%,
        #          test_coverage 15%, performance 10%, linting 10%, type_checking 5%
        scores["overall_score"] = (
            (10 - scores["complexity_score"]) * 0.20  # Invert complexity
            + scores["security_score"] * 0.15
            + scores["maintainability_score"] * 0.25
            + scores["test_coverage_score"] * 0.15
            + scores["performance_score"] * 0.10
            + scores["linting_score"] * 0.10
            + scores["type_checking_score"] * 0.05
        ) * 10  # Scale to 0-100

        # Phase 3.3: Validate all scores before returning
        from .score_validator import ScoreValidator
        from ...core.language_detector import Language

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
        Calculate test coverage score.

        Checks for test files and basic test coverage indicators.
        """
        try:
            # Look for test files
            test_patterns = [
                file_path.stem + ".test" + file_path.suffix,
                file_path.stem + ".spec" + file_path.suffix,
                file_path.name.replace(".ts", ".test.ts").replace(".js", ".test.js"),
            ]

            parent_dir = file_path.parent
            test_files_found = 0

            for pattern in test_patterns:
                test_file = parent_dir / pattern
                if test_file.exists():
                    test_files_found += 1
                    break

            # Also check for test directory
            test_dir = parent_dir / "__tests__"
            if test_dir.exists():
                test_files_found += 1

            # Score: 5.0 base, +2.5 per test file found, max 10.0
            score = 5.0 + (test_files_found * 2.5)
            return min(10.0, score)

        except Exception:
            return 5.0  # Neutral on error

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
