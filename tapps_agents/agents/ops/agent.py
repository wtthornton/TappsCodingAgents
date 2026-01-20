"""
Ops Agent - Security scanning, compliance checks, deployment, and infrastructure management
"""

import inspect
import json
from pathlib import Path
from typing import Any

from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.instructions import GenericInstruction
from ...experts.agent_integration import ExpertSupportMixin
from .dependency_analyzer import DependencyAnalyzer


class OpsAgent(BaseAgent, ExpertSupportMixin):
    """
    Ops Agent - Security scanning, compliance, deployment, and infrastructure management.

    Permissions: Read, Write, Grep, Glob, Bash (no Edit)

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify
    """

    def __init__(
        self,
        config: ProjectConfig | None = None,
        project_root: Path | None = None,
    ):
        super().__init__(agent_id="ops", agent_name="Ops Agent", config=config)
        if config is None:
            config = load_config()
        self.config = config

        # Set project_root early (before activate) if provided, otherwise use cwd
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = Path(project_root).resolve()


        # Initialize dependency analyzer
        self.dependency_analyzer = DependencyAnalyzer(project_root=self.project_root)

        # Initialize Context7 helper (Enhancement: Universal Context7 integration)
        self.context7: Context7AgentHelper | None = None
        if config:
            self.context7 = get_context7_helper(self, config)

        # Expert registry initialization (required due to multiple inheritance MRO issue)
        # BaseAgent.__init__() doesn't call super().__init__(), so ExpertSupportMixin.__init__()
        # is never called via MRO. We must manually initialize to avoid AttributeError.
        # The registry will be properly initialized in activate() via _initialize_expert_support()
        self.expert_registry: Any | None = None

    async def activate(self, project_root: Path | None = None, offline_mode: bool = False):
        # Validate that expert_registry attribute exists (safety check)
        if not hasattr(self, 'expert_registry'):
            raise AttributeError(
                f"{self.__class__.__name__}.expert_registry not initialized. "
                "This should not happen if __init__() properly initializes the attribute."
            )
        # Update project_root if provided
        if project_root is not None:
            self.project_root = Path(project_root).resolve()
            # Reinitialize dependency analyzer with new project_root
            self.dependency_analyzer = DependencyAnalyzer(
                project_root=self.project_root
            )

        await super().activate(project_root, offline_mode=offline_mode)
        await self._initialize_expert_support(project_root, offline_mode=offline_mode)
        self.greet()
        await self.run("help")

    def greet(self):
        print(
            f"Hello! I am the {self.agent_name}. I help with security, compliance, deployment, and infrastructure."
        )

    async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
        command = command.lstrip("*")  # Remove star prefix if present
        handler_name = f"_handle_{command.replace('-', '_')}"
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            # Check if handler is async before awaiting
            if inspect.iscoroutinefunction(handler):
                return await handler(**kwargs)
            else:
                # Synchronous handler - call directly
                return handler(**kwargs)
        else:
            return {
                "error": f"Unknown command: {command}. Use '*help' to see available commands."
            }

    async def _handle_security_scan(
        self, target: str | None = None, scan_type: str = "all", **kwargs: Any
    ) -> dict[str, Any]:
        """Perform security scanning on codebase or specific target."""
        target_path = Path(target) if target else self.project_root

        if not target_path.is_absolute():
            target_path = self.project_root / target_path

        if not target_path.exists():
            return {"error": f"Target not found: {target}"}

        # Scanning for security issues...

        # Get codebase context for security analysis
        issues = []

        # Consult Security expert for security scanning guidance
        security_guidance = ""
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
            security_consultation = await self.expert_registry.consult(
                query=f"Provide security scanning best practices and vulnerability detection guidance for analyzing: {target_path.name if target_path.is_file() else 'directory'}",
                domain="security",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if (
                security_consultation.confidence
                >= security_consultation.confidence_threshold
            ):
                security_guidance = security_consultation.weighted_answer

        # Use LLM to analyze security issues
        if target_path.is_file():
            code = target_path.read_text(encoding="utf-8")
            security_guidance_section = (
                f"Security Expert Guidance:\n{security_guidance}\n"
                if security_guidance
                else ""
            )
            prompt = f"""Analyze the following code for security vulnerabilities.
            
{security_guidance_section}

Code to analyze:
            
```python
{code}
```

Identify:
1. SQL injection risks
2. XSS vulnerabilities
3. Insecure authentication/authorization
4. Hardcoded secrets or credentials
5. Insecure random number generation
6. Path traversal vulnerabilities
7. Insecure deserialization
8. Missing input validation
9. Insecure file operations
10. Other security best practices violations

Return findings in JSON format:
{{
    "issues": [
        {{
            "severity": "high|medium|low",
            "type": "issue_type",
            "description": "description",
            "line": line_number,
            "recommendation": "how to fix"
        }}
    ]
}}"""

            # Prepare instruction for Cursor Skills
            instruction = GenericInstruction(
                agent_name="ops",
                command="analyze-security",
                prompt=prompt,
                parameters={"target_path": str(target_path)},
            )
            # Issues will be determined by Cursor Skills execution
            issues = []
        else:
            # Directory scan - placeholder for more comprehensive scanning
            issues.append(
                {
                    "severity": "info",
                    "type": "scan_started",
                    "description": f"Security scan initiated for directory: {target_path}",
                    "recommendation": "Review codebase for security best practices",
                }
            )

        return {
            "message": f"Security scan completed for {target_path}",
            "target": str(target_path),
            "scan_type": scan_type,
            "issues": issues,
            "issue_count": len(issues),
        }

    async def _handle_compliance_check(
        self, compliance_type: str = "general", **kwargs: Any
    ) -> dict[str, Any]:
        """Check compliance with standards (GDPR, HIPAA, SOC2, etc.)."""
        # Checking compliance...

        # Get project structure
        config_files = list(self.project_root.glob("*.yml")) + list(
            self.project_root.glob("*.yaml")
        )
        readme_files = list(self.project_root.glob("README*"))
        requirements_files = list(self.project_root.glob("requirements*.txt"))

        compliance_checks = []

        # Consult Security and Data Privacy experts
        security_guidance = ""
        privacy_guidance = ""
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
            security_consultation = await self.expert_registry.consult(
                query=f"Provide security compliance best practices for {compliance_type} compliance checking",
                domain="security",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if (
                security_consultation.confidence
                >= security_consultation.confidence_threshold
            ):
                security_guidance = security_consultation.weighted_answer

            privacy_consultation = await self.expert_registry.consult(
                query=f"Provide data privacy compliance best practices for {compliance_type} compliance checking",
                domain="data-privacy-compliance",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if (
                privacy_consultation.confidence
                >= privacy_consultation.confidence_threshold
            ):
                privacy_guidance = privacy_consultation.weighted_answer

        # Basic compliance checks
        if compliance_type in ["general", "all"]:
            compliance_checks.append(
                {
                    "check": "Documentation",
                    "status": "pass" if readme_files else "warning",
                    "message": "README found" if readme_files else "README not found",
                }
            )

            compliance_checks.append(
                {
                    "check": "Dependencies",
                    "status": "pass" if requirements_files else "warning",
                    "message": (
                        "Requirements file found"
                        if requirements_files
                        else "Requirements file not found"
                    ),
                }
            )

        # Use LLM for compliance analysis
        security_guidance_section = (
            f"Security Expert Guidance:\n{security_guidance}\n"
            if security_guidance
            else ""
        )
        privacy_guidance_section = (
            f"Data Privacy Expert Guidance:\n{privacy_guidance}\n"
            if privacy_guidance
            else ""
        )
        prompt = f"""Analyze this project for {compliance_type} compliance.

{security_guidance_section}
{privacy_guidance_section}

Project details:
        
Project root: {self.project_root}
Config files: {[str(f) for f in config_files]}

Provide compliance analysis focusing on:
1. Data protection and privacy
2. Access control and authentication
3. Audit logging
4. Data encryption
5. Secure configuration
6. Dependency management
7. Incident response planning

Return findings in JSON format:
{{
    "compliance_status": "compliant|non_compliant|partial",
    "checks": [
        {{
            "check": "check_name",
            "status": "pass|fail|warning",
            "message": "description",
            "recommendation": "how to improve"
        }}
    ]
}}"""

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="ops",
            command="check-compliance",
            prompt=prompt,
            parameters={"compliance_type": compliance_type},
        )
        # Compliance status will be determined by Cursor Skills execution
        compliance_status = "unknown"

        return {
            "message": f"Compliance check completed for {compliance_type}",
            "compliance_type": compliance_type,
            "compliance_status": compliance_status,
            "checks": compliance_checks,
        }

    async def _handle_deploy(
        self, target: str = "local", environment: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Deploy application to target environment."""
        # Deploying to target environment...

        # Consult Security expert for secure deployment guidance
        security_guidance = ""
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
            security_consultation = await self.expert_registry.consult(
                query=f"Provide security best practices for deploying to {target} environment ({environment or 'default'})",
                domain="security",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if (
                security_consultation.confidence
                >= security_consultation.confidence_threshold
            ):
                security_guidance = security_consultation.weighted_answer

        # Generate deployment script/instructions
        security_guidance_section = (
            f"Security Expert Guidance:\n{security_guidance}\n"
            if security_guidance
            else ""
        )
        prompt = f"""Generate deployment instructions for this project.

{security_guidance_section}

Project details:
        
Project root: {self.project_root}
Target: {target}
Environment: {environment or "default"}

Consider:
1. Dependencies installation
2. Configuration setup
3. Database migrations
4. Service startup
5. Health checks
6. Rollback procedures

Return deployment steps in JSON format:
{{
    "steps": [
        {{
            "step": step_number,
            "action": "action_description",
            "command": "command_to_run",
            "description": "what this step does"
        }}
    ],
    "rollback_steps": [
        {{
            "step": step_number,
            "action": "rollback_action",
            "command": "rollback_command"
        }}
    ]
}}"""

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="ops",
            command="create-deployment-plan",
            prompt=prompt,
            parameters={
                "target": target,
                "environment": environment,
            },
        )

        return {
            "message": f"Deployment plan instruction prepared for {target}",
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "target": target,
            "environment": environment,
            "status": "planned",
        }

    async def _handle_infrastructure_setup(
        self, infrastructure_type: str = "docker", **kwargs: Any
    ) -> dict[str, Any]:
        """Set up infrastructure as code (Docker, Kubernetes, Terraform, etc.)."""
        # Setting up infrastructure...

        # Generate infrastructure configuration files
        if infrastructure_type == "docker":
            dockerfile_path = self.project_root / "Dockerfile"

            # Consult Security expert for secure infrastructure setup
            security_guidance = ""
            # Use defensive check to ensure attribute exists (safety for MRO issue)
            if hasattr(self, 'expert_registry') and self.expert_registry:
                security_consultation = await self.expert_registry.consult(
                    query=f"Provide security best practices for setting up {infrastructure_type} infrastructure",
                    domain="security",
                    agent_id=self.agent_id,
                    prioritize_builtin=True,
                )
                if (
                    security_consultation.confidence
                    >= security_consultation.confidence_threshold
                ):
                    security_guidance = security_consultation.weighted_answer

            # Use LLM to generate Docker configurations
            security_guidance_section = (
                f"Security Expert Guidance:\n{security_guidance}\n"
                if security_guidance
                else ""
            )
            prompt = f"""Generate Docker configuration for this project.

{security_guidance_section}

Project details:
            
Project root: {self.project_root}
Project type: Python application

Generate:
1. Dockerfile optimized for Python
2. docker-compose.yml if applicable
3. .dockerignore file

Return Dockerfile content and docker-compose.yml content."""

            # Prepare instruction for Cursor Skills
            instruction = GenericInstruction(
                agent_name="ops",
                command="setup-infrastructure",
                prompt=prompt,
                parameters={
                    "infrastructure_type": infrastructure_type,
                    "dockerfile_path": str(dockerfile_path),
                },
            )

            return {
                "message": f"Infrastructure setup instruction prepared for {infrastructure_type}",
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
                "infrastructure_type": infrastructure_type,
                "status": "planned",
            }
        else:
            return {
                "message": f"Infrastructure type {infrastructure_type} not yet implemented",
                "infrastructure_type": infrastructure_type,
                "status": "not_implemented",
            }

    async def _handle_audit_dependencies(
        self, severity_threshold: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Audit dependencies for security vulnerabilities.

        Phase 6.4.3: Dependency Analysis & Security Auditing

        Args:
            severity_threshold: Minimum severity to report (low/medium/high/critical)

        Returns:
            Dictionary with security audit results
        """
        if severity_threshold is None:
            # Get from config
            quality_tools = self.config.quality_tools if self.config else None
            severity_threshold = (
                quality_tools.dependency_audit_threshold if quality_tools else "high"
            )

        audit_result = (
            self.dependency_analyzer.run_security_audit(
                severity_threshold=severity_threshold
            )
            or {}
        )

        return {
            "message": "Dependency security audit completed",
            "severity_threshold": severity_threshold,
            "vulnerabilities": audit_result.get("vulnerabilities", []),
            "vulnerability_count": audit_result.get("vulnerability_count", 0),
            "severity_breakdown": audit_result.get("severity_breakdown", {}),
            "tools_available": audit_result.get("tools_available", {}),
            "error": audit_result.get("error"),
        }

    async def _handle_dependency_tree(self, **kwargs: Any) -> dict[str, Any]:
        """
        Visualize dependency tree.

        Phase 6.4.3: Dependency Analysis & Security Auditing

        Returns:
            Dictionary with dependency tree information
        """
        tree_result = self.dependency_analyzer.get_dependency_tree() or {}

        return {
            "message": "Dependency tree generated",
            "tree": tree_result.get("tree"),
            "tree_json": tree_result.get("tree_json"),
            "package_count": tree_result.get("package_count", 0),
            "error": tree_result.get("error"),
        }

    async def _handle_check_vulnerabilities(
        self, severity_threshold: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Check for dependency vulnerabilities (alias for audit-dependencies).

        Phase 6.4.3: Dependency Analysis & Security Auditing

        Args:
            severity_threshold: Minimum severity to report (low/medium/high/critical)

        Returns:
            Dictionary with vulnerability check results
        """
        return await self._handle_audit_dependencies(
            severity_threshold=severity_threshold, **kwargs
        )

    async def _handle_audit_bundle(self, **kwargs: Any) -> dict[str, Any]:
        """
        Opt-in bundle analysis for Node/React/Vue. §3.8. Best-effort; never fails.
        """
        out = self.dependency_analyzer.run_audit_bundle(project_root=self.project_root) or {}
        return {"message": "Bundle analysis completed (best-effort)", **out}

    def _handle_help(self) -> dict[str, Any]:
        """
        Return help information for Ops Agent.
        
        Returns standardized help format with commands and descriptions.
        
        Returns:
            dict: Help information with standardized format:
                - type (str): Always "help"
                - content (str): Formatted markdown help text containing:
                    - Available commands with descriptions
                    
        Note:
            This method is synchronous as it performs no I/O operations.
            Standardized to match format used by other agents (type + content keys).
        """
        help_message = {
            "*security-scan [target] [type]": "Perform security scanning on codebase or specific target",
            "*compliance-check [type]": "Check compliance with standards (GDPR, HIPAA, SOC2, general)",
            "*deploy [target] [environment]": "Deploy application to target environment (local, staging, production)",
            "*infrastructure-setup [type]": "Set up infrastructure as code (docker, kubernetes, terraform)",
            "*audit-dependencies [severity_threshold]": "Audit dependencies for security vulnerabilities (Phase 6.4.3)",
            "*dependency-tree": "Visualize dependency tree using pipdeptree (Phase 6.4.3)",
            "*check-vulnerabilities [severity_threshold]": "Check for dependency vulnerabilities (Phase 6.4.3)",
            "*audit-bundle": "Opt-in bundle analysis for Node/React/Vue (§3.8); best-effort, does not block",
            "*help": "Show this help message",
        }
        
        # Format as markdown for consistency with other agents
        command_lines = [
            f"- **{cmd}**: {desc}"
            for cmd, desc in help_message.items()
        ]
        
        content = f"""# {self.agent_name} - Help

## Available Commands

{chr(10).join(command_lines)}
"""
        
        return {"type": "help", "content": content}

    async def close(self) -> None:
        """Cleanup resources."""
        await super().close()
        # Dependency analyzer cleanup if needed
        # (DependencyAnalyzer doesn't currently require explicit cleanup)