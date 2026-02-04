#!/usr/bin/env python3
"""
Documentation Synchronization Check Script

Detects when code changes but documentation doesn't, checks for outdated API references,
and validates file path references in documentation.

Usage:
    python scripts/check_doc_sync.py [--baseline] [--format json|text] [--strict]
"""

import ast
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Try to import yaml for frontmatter extraction
try:
    import yaml  # noqa: F401 - Used to check availability
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class CodeAnalyzer:
    """Analyze Python code to extract public APIs."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.public_apis: dict[str, list[dict[str, Any]]] = {}
    
    def extract_public_apis(self, file_path: Path) -> list[dict[str, Any]]:
        """Extract public functions and classes from a Python file."""
        # Safety: Limit file size to prevent memory issues (10MB max)
        max_file_size = 10 * 1024 * 1024  # 10MB
        
        try:
            file_size = file_path.stat().st_size
            if file_size > max_file_size:
                print(f"Warning: Skipping large file {file_path} ({file_size} bytes)", file=sys.stderr)
                return []
                
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError, OSError):
            return []
        
        apis = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if it's public (not starting with _)
                if not node.name.startswith("_"):
                    apis.append({
                        "name": node.name,
                        "type": "function",
                        "line": node.lineno,
                        "file": str(file_path.relative_to(self.repo_root)),
                        "signature": self._get_function_signature(node)
                    })
            elif isinstance(node, ast.ClassDef):
                # Check if it's public (not starting with _)
                if not node.name.startswith("_"):
                    apis.append({
                        "name": node.name,
                        "type": "class",
                        "line": node.lineno,
                        "file": str(file_path.relative_to(self.repo_root)),
                        "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef) and not m.name.startswith("_")]
                    })
        
        return apis
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Get function signature as string."""
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                # Try to get annotation as string
                try:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                except (AttributeError, SyntaxError):
                    pass
            args.append(arg_str)
        
        signature = f"{node.name}({', '.join(args)})"
        if node.returns:
            try:
                signature += f" -> {ast.unparse(node.returns)}"
            except (AttributeError, SyntaxError):
                pass
        
        return signature
    
    def analyze_codebase(self, include_patterns: list[str] = None) -> dict[str, list[dict[str, Any]]]:
        """Analyze entire codebase for public APIs."""
        if include_patterns is None:
            include_patterns = ["tapps_agents/**/*.py"]
        
        apis_by_module = {}
        max_files = 500  # Safety limit to prevent memory issues
        
        for pattern in include_patterns:
            file_count = 0
            for py_file in self.repo_root.glob(pattern):
                if file_count >= max_files:
                    print(f"Warning: Reached file limit ({max_files}) for pattern {pattern}", file=sys.stderr)
                    break
                    
                # Skip test files and private modules
                if "test" in str(py_file) or "__pycache__" in str(py_file):
                    continue
                
                try:
                    module_apis = self.extract_public_apis(py_file)
                    if module_apis:
                        module_name = str(py_file.relative_to(self.repo_root))
                        apis_by_module[module_name] = module_apis
                    file_count += 1
                except Exception as e:
                    print(f"Warning: Failed to analyze {py_file}: {e}", file=sys.stderr)
                    continue
        
        self.public_apis = apis_by_module
        return apis_by_module


class DocAnalyzer:
    """Analyze documentation to extract API references."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.api_references: set[str] = set()
        self.file_references: set[str] = set()
    
    def extract_api_references(self, content: str) -> set[str]:
        """Extract API references from documentation content."""
        references = set()
        
        # Pattern 1: Code blocks with imports
        # ```python
        # from tapps_agents.module import Class, function
        import_pattern = r'from\s+([\w.]+)\s+import\s+([\w,\s]+)'
        for match in re.finditer(import_pattern, content):
            module = match.group(1)
            imports = match.group(2).split(',')
            for imp in imports:
                imp = imp.strip()
                if imp:
                    references.add(f"{module}.{imp}")
        
        # Pattern 2: Direct references like `Class.method()` or `function()`
        # Matches: `ClassName`, `function_name`, `module.ClassName`
        reference_pattern = r'`([a-zA-Z_][\w.]*(?:\.[a-zA-Z_][\w.]*)?)`'
        for match in re.finditer(reference_pattern, content):
            ref = match.group(1)
            # Filter out common false positives
            if not any(skip in ref for skip in ['http', 'https', 'www', 'example.com']):
                references.add(ref)
        
        # Pattern 3: Headers like "## ClassName" or "### function_name"
        header_pattern = r'^#+\s+([A-Z][\w.]+(?:\.[A-Z][\w.]+)?)'
        for match in re.finditer(header_pattern, content, re.MULTILINE):
            ref = match.group(1)
            references.add(ref)
        
        return references
    
    def is_false_positive(self, file_ref: str, context: str = "") -> bool:
        """
        Check if a file reference is likely a false positive (example, placeholder, etc.).
        
        Args:
            file_ref: The file reference to check
            context: Optional surrounding context for better detection
        
        Returns:
            True if likely a false positive, False otherwise
        """
        # Common false positive patterns
        false_positive_patterns = [
            r'^path/to/',  # Example paths
            r'^example',  # Example files
            r'^test\.py$',  # Generic test.py
            r'^file\.py$',  # Generic file.py
            r'^config\.yaml$',  # Generic config.yaml (if in example context)
            r'service-name',  # Placeholder service names
            r'\.\./\.\./',  # Too many parent dirs (likely example)
            r'^[a-z]+/[a-z]+/',  # Simple two-level paths (path/to, src/file, etc.)
        ]
        
        # Check patterns
        for pattern in false_positive_patterns:
            if re.search(pattern, file_ref, re.IGNORECASE):
                return True
        
        # Check if in code example context
        # Look for common example indicators in surrounding context
        if context:
            example_indicators = [
                'example:', 'usage:', 'example usage', 'for example',
                '```python', '```bash', '```yaml', '```json',
                'example code', 'sample', 'demonstration'
            ]
            context_lower = context.lower()
            if any(indicator in context_lower for indicator in example_indicators):
                # If it's a simple/generic filename, likely an example
                if file_ref.count('/') <= 1 and len(file_ref.split('/')[-1].split('.')[0]) < 10:
                    return True
        
        # Skip very generic filenames that are likely examples
        generic_names = ['test.py', 'file.py', 'config.yaml', 'example.py', 
                       'main.py', 'app.py', 'script.py', 'utils.py']
        if file_ref.split('/')[-1].lower() in generic_names and file_ref.count('/') <= 1:
            return True
        
        return False
    
    def extract_file_references(self, content: str) -> set[str]:
        """Extract file path references from documentation."""
        file_refs = set()
        
        # Pattern: Relative paths like `path/to/file.py` or `docs/file.md`
        path_pattern = r'`([\w/\\-]+\.(?:py|md|yaml|yml|json|txt))`'
        for match in re.finditer(path_pattern, content):
            file_ref = match.group(1)
            # Get context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end]
            
            if not self.is_false_positive(file_ref, context):
                file_refs.add(file_ref)
        
        # Pattern: Links like [text](path/to/file.md)
        link_pattern = r'\[([^\]]+)\]\(([\w/\\-]+\.(?:py|md|yaml|yml|json|txt))\)'
        for match in re.finditer(link_pattern, content):
            file_ref = match.group(2)
            # Get context
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end]
            
            if not self.is_false_positive(file_ref, context):
                file_refs.add(file_ref)
        
        return file_refs
    
    def analyze_documentation(self, doc_files: list[Path]) -> dict[str, Any]:
        """Analyze documentation files for API and file references."""
        all_api_refs = set()
        all_file_refs = set()
        max_file_size = 5 * 1024 * 1024  # 5MB max per doc file
        
        for doc_file in doc_files:
            try:
                # Safety: Check file size before reading
                file_size = doc_file.stat().st_size
                if file_size > max_file_size:
                    print(f"Warning: Skipping large file {doc_file} ({file_size} bytes)", file=sys.stderr)
                    continue
                
                content = doc_file.read_text(encoding="utf-8")
                
                # Extract frontmatter if present
                if YAML_AVAILABLE and content.startswith("---\n"):
                    parts = content.split("---\n", 2)
                    if len(parts) >= 3:
                        content = parts[2]  # Skip frontmatter
                
                api_refs = self.extract_api_references(content)
                file_refs = self.extract_file_references(content)
                
                all_api_refs.update(api_refs)
                all_file_refs.update(file_refs)
                
            except (OSError, UnicodeDecodeError) as e:
                print(f"Warning: Failed to analyze {doc_file}: {e}", file=sys.stderr)
                continue
            except Exception as e:
                print(f"Warning: Unexpected error analyzing {doc_file}: {e}", file=sys.stderr)
                continue
        
        self.api_references = all_api_refs
        self.file_references = all_file_refs
        
        return {
            "api_references": list(all_api_refs),
            "file_references": list(all_file_refs)
        }


class SyncChecker:
    """Check synchronization between code and documentation."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.code_analyzer = CodeAnalyzer(repo_root)
        self.doc_analyzer = DocAnalyzer(repo_root)
    
    def find_documentation_files(self) -> list[Path]:
        """Find all documentation files."""
        doc_files = []
        max_files = 1000  # Safety limit to prevent memory issues
        
        # More specific patterns to avoid matching too many files
        patterns = [
            "docs/**/*.md",  # Docs directory
            "README.md",     # Root README only
            "CHANGELOG.md",  # Changelog only
            "CONTRIBUTING.md",  # Contributing guide only
        ]
        
        for pattern in patterns:
            if len(doc_files) >= max_files:
                print(f"Warning: Reached file limit ({max_files}), stopping search", file=sys.stderr)
                break
                
            for doc_file in self.repo_root.glob(pattern):
                if len(doc_files) >= max_files:
                    break
                    
                # Skip workflow output files
                if "docs/workflows/" in str(doc_file):
                    continue
                # Skip node_modules and other excluded dirs
                if any(exclude in str(doc_file) for exclude in [".git", "node_modules", ".venv", "__pycache__", ".tapps-agents"]):
                    continue
                doc_files.append(doc_file)
        
        return sorted(set(doc_files))
    
    def check_file_references(self, strict: bool = False) -> list[dict[str, Any]]:
        """Check if file references in docs exist."""
        doc_files = self.find_documentation_files()
        doc_analysis = self.doc_analyzer.analyze_documentation(doc_files)
        
        issues = []
        
        for file_ref in doc_analysis["file_references"]:
            # Try to resolve the file reference
            resolved = None
            
            # Check if it's an absolute path from repo root
            if file_ref.startswith("/"):
                resolved = self.repo_root / file_ref.lstrip("/")
            else:
                # Try relative to each doc file
                for doc_file in doc_files:
                    potential = (doc_file.parent / file_ref).resolve()
                    if potential.exists() and potential.is_file():
                        resolved = potential
                        break
            
            if resolved is None or not resolved.exists():
                # Check if it might be a code reference (like `file.py:123`)
                if ":" in file_ref:
                    file_part = file_ref.split(":")[0]
                    potential = self.repo_root / file_part
                    if potential.exists():
                        continue  # File exists, line number might be outdated but that's OK
                
                issues.append({
                    "type": "missing_file_reference",
                    "file_reference": file_ref,
                    "severity": "error" if strict else "warning",
                    "message": f"File reference '{file_ref}' not found"
                })
        
        return issues
    
    def check_api_documentation(self, strict: bool = False) -> list[dict[str, Any]]:
        """Check if public APIs are documented."""
        # Analyze codebase
        code_apis = self.code_analyzer.analyze_codebase()
        
        # Analyze documentation
        doc_files = self.find_documentation_files()
        doc_analysis = self.doc_analyzer.analyze_documentation(doc_files)
        
        issues = []
        
        # Build a set of documented APIs (normalize names)
        documented_apis = set()
        for ref in doc_analysis["api_references"]:
            # Normalize: remove module prefix, keep class/function name
            parts = ref.split(".")
            if len(parts) > 1:
                # Keep last part (class/function name)
                documented_apis.add(parts[-1])
            else:
                documented_apis.add(ref)
        
        # Check if major public APIs are documented
        # Focus on top-level modules and commonly used APIs
        important_modules = [
            "tapps_agents.core",
            "tapps_agents.workflow",
            "tapps_agents.agents"
        ]
        
        for module_path, apis in code_apis.items():
            # Only check important modules
            if not any(important in module_path for important in important_modules):
                continue
            
            for api in apis:
                api_name = api["name"]
                # Check if it's documented (exact match or partial)
                if api_name not in documented_apis:
                    # Check if it's mentioned in any doc file
                    found = False
                    for doc_file in doc_files:
                        try:
                            content = doc_file.read_text(encoding="utf-8")
                            if api_name in content or api["signature"] in content:
                                found = True
                                break
                        except Exception:
                            pass
                    
                    if not found:
                        issues.append({
                            "type": "undocumented_api",
                            "api": api_name,
                            "file": api["file"],
                            "line": api["line"],
                            "severity": "warning",  # Not strict by default
                            "message": f"Public {api['type']} '{api_name}' in {api['file']} may not be documented"
                        })
        
        return issues
    
    def check_sync(self, strict: bool = False) -> dict[str, Any]:
        """Run all synchronization checks."""
        file_issues = self.check_file_references(strict)
        api_issues = self.check_api_documentation(strict)
        
        all_issues = file_issues + api_issues
        
        # Categorize by severity
        errors = [i for i in all_issues if i["severity"] == "error"]
        warnings = [i for i in all_issues if i["severity"] == "warning"]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(all_issues),
            "errors": len(errors),
            "warnings": len(warnings),
            "issues": all_issues,
            "summary": {
                "file_reference_issues": len(file_issues),
                "api_documentation_issues": len(api_issues)
            }
        }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check synchronization between code and documentation"
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Create baseline (save current state)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        help="Repository root directory (default: auto-detect)"
    )
    
    args = parser.parse_args()
    
    try:
        repo_root = Path(args.repo_root) if args.repo_root else Path(__file__).parent.parent
        
        if not repo_root.exists():
            print(f"Error: Repository root does not exist: {repo_root}", file=sys.stderr)
            sys.exit(1)
        
        checker = SyncChecker(repo_root)
        results = checker.check_sync(strict=args.strict)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    if args.baseline:
        # Save baseline to file
        baseline_file = repo_root / ".tapps-agents" / "doc_sync_baseline.json"
        baseline_file.parent.mkdir(parents=True, exist_ok=True)
        baseline_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Baseline saved to {baseline_file}")
        return
    
    if args.format == "json":
        print(json.dumps(results, indent=2))
        sys.exit(0 if results["errors"] == 0 else 1)
    else:
        # Text output
        print("=" * 70)
        print("Documentation Synchronization Check Results")
        print("=" * 70)
        print(f"Total issues: {results['total_issues']}")
        print(f"Errors: {results['errors']}")
        print(f"Warnings: {results['warnings']}")
        print(f"File reference issues: {results['summary']['file_reference_issues']}")
        print(f"API documentation issues: {results['summary']['api_documentation_issues']}")
        print("=" * 70)
        
        if results["issues"]:
            print("\nIssues found:")
            for issue in results["issues"]:
                severity_icon = "[ERROR]" if issue["severity"] == "error" else "[WARN]"
                print(f"\n  {severity_icon} {issue['type']}: {issue['message']}")
                if "file" in issue:
                    print(f"    File: {issue['file']}")
                if "line" in issue:
                    print(f"    Line: {issue['line']}")
        else:
            print("\n✅ No synchronization issues found!")
        
        sys.exit(0 if results["errors"] == 0 else 1)


if __name__ == "__main__":
    main()
