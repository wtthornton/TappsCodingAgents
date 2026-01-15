# Step 7: Testing Plan - Brownfield System Review Feature

## Test Strategy

### Test Coverage Goals
- **Unit Tests:** > 80% coverage for core components
- **Integration Tests:** End-to-end workflow validation
- **CLI Tests:** Command parsing and execution
- **Error Handling Tests:** Graceful failure scenarios

## Test Plan

### 1. Unit Tests

#### 1.1 BrownfieldAnalyzer Tests

**File:** `tests/unit/core/test_brownfield_analyzer.py`

**Test Cases:**
- `test_detect_languages()` - Detect Python, TypeScript, JavaScript from files
- `test_detect_languages_from_config()` - Detect from package.json, requirements.txt
- `test_detect_frameworks()` - Detect FastAPI, React, Django from dependencies
- `test_detect_frameworks_from_files()` - Detect from config files (next.config.js)
- `test_detect_dependencies_python()` - Extract from requirements.txt
- `test_detect_dependencies_python_pyproject()` - Extract from pyproject.toml
- `test_detect_dependencies_nodejs()` - Extract from package.json
- `test_detect_dependencies_go()` - Extract from go.mod
- `test_analyze_complete()` - Complete analysis workflow
- `test_analyze_empty_project()` - Handle empty project gracefully
- `test_analyze_polyglot_project()` - Handle multiple languages

**Mock Requirements:**
- Mock file system operations
- Mock DomainStackDetector
- Sample project structures

#### 1.2 ExpertConfigGenerator Tests

**File:** `tests/unit/core/test_expert_config_generator.py`

**Test Cases:**
- `test_generate_expert_configs()` - Generate configs from domains
- `test_generate_expert_configs_low_confidence()` - Skip low confidence domains
- `test_generate_expert_configs_existing()` - Skip existing experts
- `test_write_expert_configs_new()` - Write new configs
- `test_write_expert_configs_merge()` - Merge with existing configs
- `test_write_expert_configs_overwrite()` - Overwrite mode
- `test_validate_config_valid()` - Validate correct config
- `test_validate_config_missing_fields()` - Validate missing fields
- `test_validate_config_invalid_id()` - Validate invalid expert ID
- `test_generate_expert_name()` - Generate human-readable names

**Mock Requirements:**
- Mock file system operations
- Mock YAML file reading/writing
- Sample expert configurations

#### 1.3 BrownfieldReviewOrchestrator Tests

**File:** `tests/unit/core/test_brownfield_review.py`

**Test Cases:**
- `test_review_complete()` - Complete review workflow
- `test_review_dry_run()` - Dry-run mode
- `test_review_without_context7()` - Without Context7 helper
- `test_review_error_handling()` - Error recovery
- `test_analyze_codebase()` - Analysis step
- `test_create_experts()` - Expert creation step
- `test_populate_rag()` - RAG population step
- `test_generate_report()` - Report generation
- `test_review_partial_failure()` - Continue on partial failures

**Mock Requirements:**
- Mock all components (Analyzer, ConfigGenerator, IngestionPipeline)
- Mock Context7 helper
- Mock file system operations

### 2. Integration Tests

#### 2.1 End-to-End Workflow Tests

**File:** `tests/integration/test_brownfield_review_workflow.py`

**Test Cases:**
- `test_brownfield_review_python_project()` - Complete review for Python project
- `test_brownfield_review_nodejs_project()` - Complete review for Node.js project
- `test_brownfield_review_polyglot_project()` - Review polyglot project
- `test_brownfield_review_with_context7()` - With Context7 integration
- `test_brownfield_review_without_context7()` - Without Context7 (graceful degradation)
- `test_brownfield_review_existing_experts()` - Merge with existing experts
- `test_brownfield_review_rag_population()` - Verify RAG population

**Test Fixtures:**
- Sample Python project (FastAPI)
- Sample Node.js project (React)
- Sample polyglot project (Python + TypeScript)

#### 2.2 Component Integration Tests

**File:** `tests/integration/test_brownfield_components.py`

**Test Cases:**
- `test_analyzer_with_domain_detector()` - Analyzer + DomainStackDetector
- `test_config_generator_with_registry()` - ConfigGenerator + ExpertRegistry
- `test_orchestrator_with_ingestion()` - Orchestrator + KnowledgeIngestionPipeline
- `test_orchestrator_with_context7()` - Orchestrator + Context7AgentHelper

### 3. CLI Tests

#### 3.1 Command Parsing Tests

**File:** `tests/unit/cli/test_brownfield_cli_parser.py`

**Test Cases:**
- `test_brownfield_review_parser()` - Parse review command
- `test_brownfield_review_with_auto()` - Parse with --auto flag
- `test_brownfield_review_with_dry_run()` - Parse with --dry-run flag
- `test_brownfield_review_with_output_dir()` - Parse with --output-dir
- `test_brownfield_review_with_no_context7()` - Parse with --no-context7

#### 3.2 Command Execution Tests

**File:** `tests/integration/cli/test_brownfield_cli_command.py`

**Test Cases:**
- `test_brownfield_review_command_success()` - Successful execution
- `test_brownfield_review_command_dry_run()` - Dry-run execution
- `test_brownfield_review_command_error()` - Error handling
- `test_brownfield_review_command_output()` - Output formatting (text)
- `test_brownfield_review_command_output_json()` - Output formatting (JSON)

### 4. Error Handling Tests

#### 4.1 Error Scenarios

**File:** `tests/unit/core/test_brownfield_errors.py`

**Test Cases:**
- `test_analyzer_file_read_error()` - Handle file read errors
- `test_config_generator_yaml_error()` - Handle YAML errors
- `test_orchestrator_context7_unavailable()` - Handle Context7 unavailability
- `test_orchestrator_domain_detection_failure()` - Handle domain detection failures
- `test_orchestrator_expert_creation_failure()` - Handle expert creation failures
- `test_orchestrator_rag_population_failure()` - Handle RAG population failures
- `test_orchestrator_partial_success()` - Continue on partial failures

## Test Implementation

### Test Structure

```
tests/
├── unit/
│   ├── core/
│   │   ├── test_brownfield_analyzer.py
│   │   ├── test_expert_config_generator.py
│   │   └── test_brownfield_review.py
│   └── cli/
│       └── test_brownfield_cli_parser.py
├── integration/
│   ├── test_brownfield_review_workflow.py
│   ├── test_brownfield_components.py
│   └── cli/
│       └── test_brownfield_cli_command.py
└── fixtures/
    ├── sample_python_project/
    ├── sample_nodejs_project/
    └── sample_polyglot_project/
```

### Test Fixtures

**Sample Python Project:**
```
sample_python_project/
├── requirements.txt (fastapi, pytest, pydantic)
├── pyproject.toml
├── src/
│   └── app.py
└── tests/
    └── test_app.py
```

**Sample Node.js Project:**
```
sample_nodejs_project/
├── package.json (react, typescript, jest)
├── tsconfig.json
├── src/
│   └── App.tsx
└── tests/
    └── App.test.tsx
```

## Test Execution

### Running Tests

```bash
# Run all brownfield tests
pytest tests/unit/core/test_brownfield*.py tests/integration/test_brownfield*.py -v

# Run with coverage
pytest tests/unit/core/test_brownfield*.py --cov=tapps_agents.core.brownfield --cov-report=html

# Run specific test file
pytest tests/unit/core/test_brownfield_analyzer.py -v

# Run CLI tests
pytest tests/unit/cli/test_brownfield_cli*.py tests/integration/cli/test_brownfield_cli*.py -v
```

### Coverage Goals

- **BrownfieldAnalyzer:** > 85%
- **ExpertConfigGenerator:** > 85%
- **BrownfieldReviewOrchestrator:** > 80%
- **CLI Command Handler:** > 80%
- **Overall:** > 80%

## Test Data

### Mock Data

1. **Domain Mappings:**
   - Python domain (confidence: 0.9)
   - FastAPI domain (confidence: 0.8)
   - Testing domain (confidence: 0.7)

2. **Expert Configs:**
   - expert-python
   - expert-fastapi
   - expert-testing

3. **Ingestion Results:**
   - Project sources: 10 entries ingested
   - Context7 sources: 5 entries ingested

## Test Validation Criteria

### Success Criteria

1. ✅ All unit tests pass
2. ✅ All integration tests pass
3. ✅ CLI tests pass
4. ✅ Error handling tests pass
5. ✅ Coverage > 80%
6. ✅ No linting errors
7. ✅ No type errors

### Performance Criteria

1. ✅ Analysis completes in < 30s for sample projects
2. ✅ Expert creation completes in < 5s
3. ✅ RAG population completes in < 60s (with Context7)

## Future Test Enhancements

1. **Performance Tests**
   - Large codebase handling (10k+ files)
   - Concurrent expert processing
   - Memory usage tests

2. **Security Tests**
   - Path traversal prevention
   - YAML injection prevention
   - Expert ID validation

3. **Simple Mode Integration Tests**
   - Command recognition
   - Workflow execution
   - Output formatting

## Test Maintenance

### Test Updates Required When:

1. **Component Changes**
   - Update tests when Analyzer, ConfigGenerator, or Orchestrator change
   - Update mocks when dependencies change

2. **CLI Changes**
   - Update parser tests when arguments change
   - Update command tests when behavior changes

3. **Integration Changes**
   - Update integration tests when external components change
   - Update fixtures when project structures change

## Conclusion

This test plan provides comprehensive coverage for the brownfield system review feature. Tests should be implemented incrementally, starting with unit tests, then integration tests, and finally CLI tests.

**Priority:** High - Tests are critical for ensuring feature reliability and maintainability.

**Estimated Effort:** 2-3 days for complete test implementation.
