"""
Ops Agent - Security scanning, compliance checks, deployment, and infrastructure management
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import subprocess

from ...core.mal import MAL
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from .dependency_analyzer import DependencyAnalyzer


class OpsAgent(BaseAgent):
    """
    Ops Agent - Security scanning, compliance, deployment, and infrastructure management.
    
    Permissions: Read, Write, Grep, Glob, Bash (no Edit)
    """
    
    def __init__(self, mal: Optional[MAL] = None, config: Optional[ProjectConfig] = None):
        super().__init__(agent_id="ops", agent_name="Ops Agent", config=config)
        if config is None:
            config = load_config()
        self.config = config
        
        # Initialize MAL with config
        mal_config = config.mal if config else None
        self.mal = mal or MAL(
            ollama_url=mal_config.ollama_url if mal_config else "http://localhost:11434"
        )
        
        # Initialize dependency analyzer
        self.dependency_analyzer = DependencyAnalyzer(project_root=self.project_root)
    
    async def activate(self, project_root: Optional[Path] = None):
        await super().activate(project_root)
        self.greet()
        await self.run("help")
    
    def greet(self):
        print(f"Hello! I am the {self.agent_name}. I help with security, compliance, deployment, and infrastructure.")
    
    async def run(self, command: str, **kwargs: Any) -> Dict[str, Any]:
        command = command.lstrip("*") # Remove star prefix if present
        handler_name = f"_handle_{command.replace('-', '_')}"
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            return await handler(**kwargs)
        else:
            return {"error": f"Unknown command: {command}. Use '*help' to see available commands."}
    
    async def _handle_security_scan(self, target: Optional[str] = None, scan_type: str = "all", **kwargs: Any) -> Dict[str, Any]:
        """Perform security scanning on codebase or specific target."""
        target_path = Path(target) if target else self.project_root
        
        if not target_path.is_absolute():
            target_path = self.project_root / target_path
        
        if not target_path.exists():
            return {"error": f"Target not found: {target}"}
        
        # Scanning for security issues...
        
        # Get codebase context for security analysis
        issues = []
        
        # Use LLM to analyze security issues
        if target_path.is_file():
            code = target_path.read_text(encoding="utf-8")
            prompt = f"""Analyze the following code for security vulnerabilities:
            
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

            try:
                response = await self.mal.generate(prompt)
                # Try to extract JSON from response
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    result = json.loads(response[json_start:json_end])
                    issues = result.get("issues", [])
            except Exception as e:
                return {"error": f"Failed to analyze security: {str(e)}"}
        else:
            # Directory scan - placeholder for more comprehensive scanning
            issues.append({
                "severity": "info",
                "type": "scan_started",
                "description": f"Security scan initiated for directory: {target_path}",
                "recommendation": "Review codebase for security best practices"
            })
        
        return {
            "message": f"Security scan completed for {target_path}",
            "target": str(target_path),
            "scan_type": scan_type,
            "issues": issues,
            "issue_count": len(issues)
        }
    
    async def _handle_compliance_check(self, compliance_type: str = "general", **kwargs: Any) -> Dict[str, Any]:
        """Check compliance with standards (GDPR, HIPAA, SOC2, etc.)."""
        # Checking compliance...
        
        # Get project structure
        config_files = list(self.project_root.glob("*.yml")) + list(self.project_root.glob("*.yaml"))
        readme_files = list(self.project_root.glob("README*"))
        requirements_files = list(self.project_root.glob("requirements*.txt"))
        
        compliance_checks = []
        
        # Basic compliance checks
        if compliance_type in ["general", "all"]:
            compliance_checks.append({
                "check": "Documentation",
                "status": "pass" if readme_files else "warning",
                "message": "README found" if readme_files else "README not found"
            })
            
            compliance_checks.append({
                "check": "Dependencies",
                "status": "pass" if requirements_files else "warning",
                "message": "Requirements file found" if requirements_files else "Requirements file not found"
            })
        
        # Use LLM for compliance analysis
        prompt = f"""Analyze this project for {compliance_type} compliance:
        
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

        try:
            response = await self.mal.generate(prompt)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response[json_start:json_end])
                compliance_checks.extend(result.get("checks", []))
                compliance_status = result.get("compliance_status", "unknown")
            else:
                compliance_status = "unknown"
        except Exception as e:
            compliance_status = "error"
            compliance_checks.append({
                "check": "Compliance Analysis",
                "status": "error",
                "message": f"Failed to analyze: {str(e)}"
            })
        
        return {
            "message": f"Compliance check completed for {compliance_type}",
            "compliance_type": compliance_type,
            "compliance_status": compliance_status,
            "checks": compliance_checks
        }
    
    async def _handle_deploy(self, target: str = "local", environment: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        """Deploy application to target environment."""
        # Deploying to target environment...
        
        # Generate deployment script/instructions
        prompt = f"""Generate deployment instructions for this project:
        
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

        try:
            response = await self.mal.generate(prompt)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                deployment_plan = json.loads(response[json_start:json_end])
                
                # For actual deployment, we'd execute the steps
                # For now, return the plan
                return {
                    "message": f"Deployment plan generated for {target}",
                    "target": target,
                    "environment": environment,
                    "deployment_plan": deployment_plan,
                    "status": "planned"  # vs "executed"
                }
            else:
                return {"error": "Failed to generate deployment plan"}
        except Exception as e:
            return {"error": f"Failed to create deployment plan: {str(e)}"}
    
    async def _handle_infrastructure_setup(self, infrastructure_type: str = "docker", **kwargs: Any) -> Dict[str, Any]:
        """Set up infrastructure as code (Docker, Kubernetes, Terraform, etc.)."""
        # Setting up infrastructure...
        
        # Generate infrastructure configuration files
        if infrastructure_type == "docker":
            dockerfile_path = self.project_root / "Dockerfile"
            docker_compose_path = self.project_root / "docker-compose.yml"
            
            # Use LLM to generate Docker configurations
            prompt = f"""Generate Docker configuration for this project:
            
Project root: {self.project_root}
Project type: Python application

Generate:
1. Dockerfile optimized for Python
2. docker-compose.yml if applicable
3. .dockerignore file

Return Dockerfile content and docker-compose.yml content."""

            try:
                response = await self.mal.generate(prompt)
                
                # Extract Dockerfile and docker-compose.yml from response
                # This is simplified - in production, you'd have better parsing
                dockerfile_content = "# Generated Dockerfile\n"
                if "FROM python" in response:
                    dockerfile_start = response.find("FROM python")
                    dockerfile_end = response.find("\n\n", dockerfile_start)
                    if dockerfile_end > dockerfile_start:
                        dockerfile_content = response[dockerfile_start:dockerfile_end]
                
                # Write files
                if dockerfile_content:
                    dockerfile_path.write_text(dockerfile_content, encoding="utf-8")
                
                return {
                    "message": f"Infrastructure setup completed for {infrastructure_type}",
                    "infrastructure_type": infrastructure_type,
                    "files_created": [
                        str(dockerfile_path) if dockerfile_path.exists() else None
                    ],
                    "status": "completed"
                }
            except Exception as e:
                return {"error": f"Failed to set up infrastructure: {str(e)}"}
        else:
            return {
                "message": f"Infrastructure type {infrastructure_type} not yet implemented",
                "infrastructure_type": infrastructure_type,
                "status": "not_implemented"
            }
    
    async def _handle_audit_dependencies(
        self,
        severity_threshold: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
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
            severity_threshold = quality_tools.dependency_audit_threshold if quality_tools else "high"
        
        audit_result = self.dependency_analyzer.run_security_audit(
            severity_threshold=severity_threshold
        )
        
        return {
            "message": "Dependency security audit completed",
            "severity_threshold": severity_threshold,
            "vulnerabilities": audit_result.get("vulnerabilities", []),
            "vulnerability_count": audit_result.get("vulnerability_count", 0),
            "severity_breakdown": audit_result.get("severity_breakdown", {}),
            "tools_available": audit_result.get("tools_available", {}),
            "error": audit_result.get("error")
        }
    
    async def _handle_dependency_tree(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Visualize dependency tree.
        
        Phase 6.4.3: Dependency Analysis & Security Auditing
        
        Returns:
            Dictionary with dependency tree information
        """
        tree_result = self.dependency_analyzer.get_dependency_tree()
        
        return {
            "message": "Dependency tree generated",
            "tree": tree_result.get("tree"),
            "tree_json": tree_result.get("tree_json"),
            "package_count": tree_result.get("package_count", 0),
            "error": tree_result.get("error")
        }
    
    async def _handle_check_vulnerabilities(
        self,
        severity_threshold: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Check for dependency vulnerabilities (alias for audit-dependencies).
        
        Phase 6.4.3: Dependency Analysis & Security Auditing
        
        Args:
            severity_threshold: Minimum severity to report (low/medium/high/critical)
        
        Returns:
            Dictionary with vulnerability check results
        """
        return await self._handle_audit_dependencies(severity_threshold=severity_threshold, **kwargs)
    
    async def _handle_help(self) -> Dict[str, Any]:
        """Show this help message."""
        help_message = {
            "*security-scan [target] [type]": "Perform security scanning on codebase or specific target",
            "*compliance-check [type]": "Check compliance with standards (GDPR, HIPAA, SOC2, general)",
            "*deploy [target] [environment]": "Deploy application to target environment (local, staging, production)",
            "*infrastructure-setup [type]": "Set up infrastructure as code (docker, kubernetes, terraform)",
            "*audit-dependencies [severity_threshold]": "Audit dependencies for security vulnerabilities (Phase 6.4.3)",
            "*dependency-tree": "Visualize dependency tree using pipdeptree (Phase 6.4.3)",
            "*check-vulnerabilities [severity_threshold]": "Check for dependency vulnerabilities (Phase 6.4.3)",
            "*help": "Show this help message"
        }
        return {"content": help_message}

