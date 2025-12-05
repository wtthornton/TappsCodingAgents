# Ops Agent Skills

The Ops Agent is responsible for **security scanning**, **compliance checks**, **deployment automation**, and **infrastructure management**.

## Commands

All commands are prefixed with `*` when called via the CLI.

### `*security-scan [target] [type]`
- **Description**: Performs security scanning on codebase or specific files to identify vulnerabilities.
- **Usage**: `tapps ops *security-scan src/api.py all`
- **Arguments**:
    - `target` (string, optional): File or directory to scan. Defaults to project root.
    - `type` (string, optional): Type of scan (`all`, `sql_injection`, `xss`, `secrets`, etc.). Defaults to `all`.
- **Output**: Security scan report with identified issues, severity levels, and recommendations.

### `*compliance-check [type]`
- **Description**: Checks compliance with regulatory standards and best practices.
- **Usage**: `tapps ops *compliance-check GDPR`
- **Arguments**:
    - `type` (string, optional): Compliance type (`general`, `GDPR`, `HIPAA`, `SOC2`, `all`). Defaults to `general`.
- **Output**: Compliance status report with check results and recommendations.

### `*deploy [target] [environment]`
- **Description**: Deploys application to target environment with deployment plan and rollback procedures.
- **Usage**: `tapps ops *deploy staging production`
- **Arguments**:
    - `target` (string, optional): Deployment target (`local`, `staging`, `production`). Defaults to `local`.
    - `environment` (string, optional): Environment configuration name.
- **Output**: Deployment plan with steps, commands, and rollback procedures.

### `*infrastructure-setup [type]`
- **Description**: Sets up infrastructure as code for containerization and orchestration.
- **Usage**: `tapps ops *infrastructure-setup docker`
- **Arguments**:
    - `type` (string, optional): Infrastructure type (`docker`, `kubernetes`, `terraform`). Defaults to `docker`.
- **Output**: Generated infrastructure configuration files and setup status.

### `*help`
- **Description**: Displays this help message.
- **Usage**: `tapps ops *help`
- **Output**: A dictionary of commands and their descriptions.

## Permissions

The Ops Agent has `Read`, `Write`, `Grep`, `Glob`, and `Bash` permissions. It can create configuration files and execute deployment commands but does not have `Edit` permissions for direct code modification.

## Workflow Integration

The Ops Agent typically works in coordination with:
- **Reviewer Agent**: Security reviews before deployment
- **Tester Agent**: Validation before deployment
- **Orchestrator Agent**: Deployment workflows and gates
- **Analyst Agent**: Risk assessment and compliance requirements

## Use Cases

1. **Security Audits**: Identify vulnerabilities and security risks
2. **Compliance Validation**: Ensure regulatory compliance
3. **Deployment Automation**: Streamline deployment processes
4. **Infrastructure Provisioning**: Set up development and production environments
5. **Monitoring Setup**: Configure logging and monitoring systems
6. **CI/CD Pipeline**: Integrate with continuous integration/deployment

