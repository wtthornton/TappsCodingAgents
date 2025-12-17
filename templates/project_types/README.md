# Project Type Templates

This directory contains project archetype templates that provide optimal default configuration based on the type of project being built.

## Available Templates

- **api-service.yaml**: REST/GraphQL API services
- **web-app.yaml**: Full-stack web applications
- **cli-tool.yaml**: Command-line tools
- **library.yaml**: Reusable libraries/packages
- **microservice.yaml**: Microservice architectures

## Template Structure

Each template includes:

- **workflow_defaults**: Recommended workflow track and specific workflow
- **quality_thresholds**: Quality gates and thresholds per agent
- **docs_skeleton**: Documentation structure recommendations
- **expert_priorities**: Expert priority mappings (0.0-1.0 scale)
- **testing_strategy**: Testing focus areas and mock strategies

## Merge Order

Project type templates are merged in this order (precedence from lowest to highest):

1. Default configuration
2. Project type template
3. Tech stack template(s)
4. User config/customizations

## Usage

Project type templates are automatically selected during `tapps-agents init` based on detected project characteristics. You can also explicitly specify a project type via configuration.

## Conditional Blocks

Templates support conditional blocks using `{{#if variable.path}}...{{/if}}` syntax. 

**See the [Template Conditional Blocks Guide](../../docs/TEMPLATE_CONDITIONAL_BLOCKS_GUIDE.md) for:**
- Complete syntax reference
- Evaluation rules and examples
- Real-world template examples
- Troubleshooting guide

