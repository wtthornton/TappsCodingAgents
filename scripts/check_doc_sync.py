#!/usr/bin/env python3
"""
Documentation Synchronization Check Script

Detects when code changes but documentation doesn't, checks for outdated API references,
and validates file path references in documentation.

Usage:
    python scripts/check_doc_sync.py [--baseline] [--format json|text] [--strict]
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Set
from datetime import datetime
import json

# Try to import yaml for frontmatter extraction
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class CodeAnalyzer:
    """Analyze Python code to extract public APIs."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.public_apis: Dict[str, List[Dict[str, Any]]] = {}
    
    def extract_public_apis(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract public functions and classes from a Python file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError) as e:
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
    
    def analyze_codebase(self, include_patterns: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze entire codebase for public APIs."""
        if include_patterns is None:
            include_patterns = ["tapps_agents/**/*.py"]
        
        apis_by_module = {}
        
        for pattern in include_patterns:
            for py_file in self.repo_root.glob(pattern):
                # Skip test files and private modules
                if "test" in str(py_file) or "__pycache__" in str(py_file):
                    continue
                
                module_apis = self.extract_public_apis(py_file)
                if module_apis:
                    module_name = str(py_file.relative_to(self.repo_root))
                    apis_by_module[module_name] = module_apis
        
        self.public_apis = apis_by_module
        return apis_by_module


class DocAnalyzer:
    """Analyze documentation to extract API references."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.api_references: Set[str] = set()
        self.file_references: Set[str] = set()
    
    def extract_api_references(self, content: str) -> Set[str]:
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
    
    def extract_file_references(self, content: str) -> Set[str]:
        """Extract file path references from documentation."""
        file_refs = set()
        
        # Pattern: Relative paths like `path/to/file.py` or `docs/file.md`
        path_pattern = r'`([\w/\\-]+\.(?:py|md|yaml|yml|json|txt))`'
        for match in re.finditer(path_pattern, content):
            file_refs.add(match.group(1))
        
        # Pattern: Links like [text](path/to/file.md)
        link_pattern = r'\[([^\]]+)\]\(([\w/\\-]+\.(?:py|md|yaml|yml|json|txt))\)'
        for match in re.finditer(link_pattern, content):
            file_refs.add(match.group(2))
        
        return file_refs
    
    def analyze_documentation(self, doc_files: List[Path]) -> Dict[str, Any]:
        """Analyze documentation files for API and file references."""
        all_api_refs = set()
        all_file_refs = set()
        
        for doc_file in doc_files:
            try:
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
                
            except Exception as e:
                print(f"Warning: Failed to analyze {doc_file}: {e}", file=sys.stderr)
        
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
    
    def find_documentation_files(self) -> List[Path]:
        """Find all documentation files."""
        doc_files = []
        for pattern in ["docs/**/*.md", "*.md"]:
            for doc_file in self.repo_root.glob(pattern):
                # Skip workflow output files
                if "docs/workflows/" in str(doc_file):
                    continue
                # Skip node_modules and other excluded dirs
                if any(exclude in str(doc_file) for exclude in [".git", "node_modules", ".venv"]):
                    continue
                doc_files.append(doc_file)
        return sorted(set(doc_files))
    
    def check_file_references(self, strict: bool = False) -> List[Dict[str, Any]]:
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
    
    def check_api_documentation(self, strict: bool = False) -> List[Dict[str, Any]]:
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
    
    def check_sync(self, strict: bool = False) -> Dict[str, Any]:
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
    
    repo_root = Path(args.repo_root) if args.repo_root else Path(__file__).parent.parent
    
    checker = SyncChecker(repo_root)
    results = checker.check_sync(strict=args.strict)
    
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
