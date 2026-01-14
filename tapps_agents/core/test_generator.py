"""
Test Generator for TappsCodingAgents.

Provides test templates and automatic test file generation.
"""

from pathlib import Path
from typing import Any

from .code_generator import CodeGenerator


class TestGenerator:
    """
    Generates test files from templates.
    
    Provides templates for various test frameworks and languages.
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize test generator.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.code_generator = CodeGenerator(project_root=project_root)

    def generate_pytest_test(
        self,
        source_file: Path,
        test_content: str,
        output_file: Path | None = None,
    ) -> Path:
        """
        Generate a pytest test file.
        
        Args:
            source_file: Source file being tested
            test_content: Test code content
            output_file: Output test file path (auto-generated if None)
            
        Returns:
            Path to generated test file
        """
        if not output_file:
            # Determine test file path
            test_dir = self.project_root / "tests"
            
            # Maintain directory structure relative to project root
            if source_file.is_absolute():
                try:
                    rel_path = source_file.relative_to(self.project_root)
                except ValueError:
                    # Source file is outside project root
                    rel_path = Path(source_file.name)
            else:
                rel_path = source_file
            
            # Convert to test file path
            test_rel_path = rel_path.parent / f"test_{rel_path.name}"
            output_file = test_dir / test_rel_path
            
            # Create parent directories
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Wrap test content in pytest template
        template = self._get_pytest_template(source_file, test_content)
        
        # Write test file
        output_file.write_text(template, encoding="utf-8")
        return output_file

    def generate_jest_test(
        self,
        source_file: Path,
        test_content: str,
        output_file: Path | None = None,
    ) -> Path:
        """
        Generate a Jest test file.
        
        Args:
            source_file: Source file being tested
            test_content: Test code content
            output_file: Output test file path (auto-generated if None)
            
        Returns:
            Path to generated test file
        """
        if not output_file:
            # Determine test file path
            test_dir = self.project_root / "tests"
            
            # Maintain directory structure
            if source_file.is_absolute():
                try:
                    rel_path = source_file.relative_to(self.project_root)
                except ValueError:
                    rel_path = Path(source_file.name)
            else:
                rel_path = source_file
            
            # Convert to test file path (.test.js or .test.ts)
            extension = ".test.ts" if source_file.suffix == ".ts" else ".test.js"
            test_rel_path = rel_path.parent / f"{rel_path.stem}{extension}"
            output_file = test_dir / test_rel_path
            
            # Create parent directories
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Wrap test content in Jest template
        template = self._get_jest_template(source_file, test_content)
        
        # Write test file
        output_file.write_text(template, encoding="utf-8")
        return output_file

    def generate_unittest_test(
        self,
        source_file: Path,
        test_content: str,
        output_file: Path | None = None,
    ) -> Path:
        """
        Generate a unittest test file.
        
        Args:
            source_file: Source file being tested
            test_content: Test code content
            output_file: Output test file path (auto-generated if None)
            
        Returns:
            Path to generated test file
        """
        if not output_file:
            # Determine test file path
            test_dir = self.project_root / "tests"
            
            # Maintain directory structure
            if source_file.is_absolute():
                try:
                    rel_path = source_file.relative_to(self.project_root)
                except ValueError:
                    rel_path = Path(source_file.name)
            else:
                rel_path = source_file
            
            # Convert to test file path
            test_rel_path = rel_path.parent / f"test_{rel_path.name}"
            output_file = test_dir / test_rel_path
            
            # Create parent directories
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Wrap test content in unittest template
        template = self._get_unittest_template(source_file, test_content)
        
        # Write test file
        output_file.write_text(template, encoding="utf-8")
        return output_file

    def _get_pytest_template(self, source_file: Path, test_content: str) -> str:
        """Get pytest test template."""
        # Extract module name for import
        if source_file.is_absolute():
            try:
                rel_path = source_file.relative_to(self.project_root)
                module_path = str(rel_path.with_suffix("")).replace("/", ".").replace("\\", ".")
                # Remove leading dots
                module_path = module_path.lstrip(".")
            except ValueError:
                module_path = source_file.stem
        else:
            module_path = str(source_file.with_suffix("")).replace("/", ".").replace("\\", ".")
        
        template = f'''"""
Test file for {source_file.name}

Generated automatically by TappsCodingAgents Test Generator.
"""

import pytest
from {module_path} import *


{test_content}
'''
        return template

    def _get_jest_template(self, source_file: Path, test_content: str) -> str:
        """Get Jest test template."""
        # Extract import path
        if source_file.is_absolute():
            try:
                rel_path = source_file.relative_to(self.project_root / "src")
                import_path = str(rel_path.with_suffix("")).replace("/", "/").replace("\\", "/")
            except ValueError:
                import_path = source_file.stem
        else:
            import_path = str(source_file.with_suffix("")).replace("/", "/").replace("\\", "/")
        
        template = f'''/**
 * Test file for {source_file.name}
 *
 * Generated automatically by TappsCodingAgents Test Generator.
 */

import {{ /* imports */ }} from '{import_path}';


{test_content}
'''
        return template

    def _get_unittest_template(self, source_file: Path, test_content: str) -> str:
        """Get unittest test template."""
        # Extract module name for import
        if source_file.is_absolute():
            try:
                rel_path = source_file.relative_to(self.project_root)
                module_path = str(rel_path.with_suffix("")).replace("/", ".").replace("\\", ".")
                module_path = module_path.lstrip(".")
            except ValueError:
                module_path = source_file.stem
        else:
            module_path = str(source_file.with_suffix("")).replace("/", ".").replace("\\", ".")
        
        template = f'''"""
Test file for {source_file.name}

Generated automatically by TappsCodingAgents Test Generator.
"""

import unittest
from {module_path} import *


class Test{source_file.stem.replace("_", "").title()}(unittest.TestCase):
    """Test cases for {source_file.name}"""

{self._indent(test_content, 4)}
'''
        return template

    def _indent(self, text: str, spaces: int) -> str:
        """Indent text by specified number of spaces."""
        lines = text.split("\n")
        indented = [" " * spaces + line if line.strip() else line for line in lines]
        return "\n".join(indented)

    def detect_test_framework(self, source_file: Path) -> str:
        """
        Detect test framework from project configuration.
        
        Args:
            source_file: Source file being tested
            
        Returns:
            Test framework name (pytest, jest, unittest, etc.)
        """
        # Check for pytest
        if (self.project_root / "pytest.ini").exists() or \
           (self.project_root / "setup.cfg").exists() or \
           (self.project_root / "pyproject.toml").exists():
            return "pytest"
        
        # Check for Jest
        if (self.project_root / "package.json").exists():
            try:
                import json
                package_json = json.loads((self.project_root / "package.json").read_text())
                if "jest" in package_json.get("devDependencies", {}) or \
                   "jest" in package_json.get("dependencies", {}):
                    return "jest"
            except Exception:
                pass
        
        # Check file extension for hints
        if source_file.suffix == ".py":
            return "pytest"  # Default for Python
        elif source_file.suffix in [".js", ".ts", ".jsx", ".tsx"]:
            return "jest"  # Default for JavaScript/TypeScript
        
        return "pytest"  # Default
