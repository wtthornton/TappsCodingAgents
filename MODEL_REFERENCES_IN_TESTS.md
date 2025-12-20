# Tests and Classes Still Looking for Local Model Configuration

This document lists all tests and classes that reference a `model` attribute in agent configuration, which has been removed from the project.

## Summary

- **Total Test Files Affected**: 2
- **Total Test Classes Affected**: 2
- **Total Test Methods Affected**: 6
- **Fixture Files Affected**: 1
- **CLI Test Files Affected**: 1 (passing model as parameter, but not checking config)
- **ProgressiveReview Model**: 1 (this is a data model field, not config - may need separate decision)

---

## 1. Configuration Tests (`tests/unit/test_config.py`)

### Test Class: `TestReviewerAgentConfig`
**File**: `tests/unit/test_config.py:76-100`

#### Test Method: `test_default_values` (Line 79-86)
- **Line 82**: `assert config.model == "qwen2.5-coder:7b"`
- **Issue**: Checks for `model` attribute on `ReviewerAgentConfig` instance
- **Status**: ❌ FAILING

---

### Test Class: `TestLoadConfig`
**File**: `tests/unit/test_config.py:138-212`

#### Test Method: `test_load_config_from_file` (Line 147-164)
- **Line 153**: Config data includes `"model": "custom-model:7b"`
- **Line 163**: `assert config.agents.reviewer.model == "custom-model:7b"`
- **Issue**: Tests loading model from YAML config file
- **Status**: ❌ FAILING

---

### Test Class: `TestConfigIntegration`
**File**: `tests/unit/test_config.py:212-388`

#### Test Method: `test_full_config_example` (Line 215-253)
- **Line 223**: Config data includes `"model": "qwen2.5-coder:7b"`
- **Line 249**: `assert config.agents.reviewer.model == "qwen2.5-coder:7b"`
- **Issue**: Tests complete config example with model field
- **Status**: ❌ FAILING

#### Test Method: `test_config_merging_partial_config` (Line 255-297)
- **Line 284**: `assert config.agents.reviewer.model == "qwen2.5-coder:7b"`
- **Issue**: Tests that default model value is applied when not specified
- **Status**: ❌ FAILING

#### Test Method: `test_config_default_values_application` (Line 299-336)
- **Line 310**: `assert config.agents.reviewer.model == "qwen2.5-coder:7b"`
- **Issue**: Tests that default model value is applied from defaults
- **Status**: ❌ FAILING

#### Test Method: `test_config_merging_nested_structures` (Line 338-388)
- **Line 346**: Config data includes `"model": "custom-model:7b"`
- **Line 363**: `assert config.agents.reviewer.model == "custom-model:7b"`
- **Issue**: Tests nested config structure merging with model field
- **Status**: ❌ FAILING

---

## 2. Test Fixtures (`tests/conftest.py`)

### Fixture: `test_config` (Line 94-109)
- **Line 98**: `"reviewer": {"model": "qwen2.5-coder:7b", "quality_threshold": 70.0}`
- **Issue**: Test fixture includes model in reviewer config
- **Status**: ⚠️ MAY CAUSE ISSUES (if used by other tests)

---

## 3. CLI Tests (`tests/unit/cli/test_cli_base.py`)

### Test Class: `TestRunAgentCommand`
**File**: `tests/unit/cli/test_cli_base.py:330-346`

#### Test Method: `test_run_agent_command_with_kwargs` (Line 330-345)
- **Line 342**: Passes `model="test-model"` as parameter to `run_agent_command()`
- **Line 345**: Asserts that `agent.run()` was called with `model="test-model"`
- **Issue**: Tests passing model as a parameter (not checking config)
- **Status**: ⚠️ MAY NEED UPDATE (agent.run() no longer uses model parameter per line 179 in reviewer/agent.py: "Model parameter deprecated")

---

## 4. Progressive Review Tests (`tests/unit/agents/test_progressive_review.py`)

### Test Class: `TestProgressiveReviewSerialization`
**File**: `tests/unit/agents/test_progressive_review.py:362-413`

#### Test Method: `test_to_dict_roundtrip` (Line 365-413)
- **Line 373**: `model="test-model"` - Creates `ProgressiveReview` instance with model field
- **Issue**: `ProgressiveReview` dataclass has a `model` field (line 80 in `progressive_review.py`)
- **Status**: ⚠️ NEEDS DECISION - This is a data model field (metadata), not a config field
- **Note**: The `ProgressiveReview.model` field stores which model was used for the review (metadata), not a configuration setting. This may be intentionally kept for tracking purposes.

---

## Detailed Breakdown by File

### `tests/unit/test_config.py`
**Total Issues**: 6 test methods

1. `TestReviewerAgentConfig.test_default_values` - Line 82
2. `TestLoadConfig.test_load_config_from_file` - Lines 153, 163
3. `TestConfigIntegration.test_full_config_example` - Lines 223, 249
4. `TestConfigIntegration.test_config_merging_partial_config` - Line 284
5. `TestConfigIntegration.test_config_default_values_application` - Line 310
6. `TestConfigIntegration.test_config_merging_nested_structures` - Lines 346, 363

### `tests/conftest.py`
**Total Issues**: 1 fixture

1. `test_config` fixture - Line 98

### `tests/unit/cli/test_cli_base.py`
**Total Issues**: 1 test method (parameter passing, not config)

1. `TestRunAgentCommand.test_run_agent_command_with_kwargs` - Lines 342, 345

### `tests/unit/agents/test_progressive_review.py`
**Total Issues**: 1 test method (data model field, not config)

1. `TestProgressiveReviewSerialization.test_to_dict_roundtrip` - Line 373

---

## Recommended Actions

### High Priority (Config Model References)
1. **Remove all `model` assertions from `tests/unit/test_config.py`**
   - Remove lines checking `config.model` or `config.agents.reviewer.model`
   - Remove `"model"` from test config data dictionaries
   - Update test docstrings if they mention model

2. **Update `tests/conftest.py` fixture**
   - Remove `"model": "qwen2.5-coder:7b"` from `test_config` fixture

### Medium Priority (Parameter Passing)
3. **Review `tests/unit/cli/test_cli_base.py`**
   - Decide if `model` parameter should still be passed (even if ignored)
   - Update test to reflect that model parameter is deprecated

### Low Priority (Data Model Field)
4. **Review `ProgressiveReview.model` field**
   - Decide if this metadata field should be kept or removed
   - If kept, ensure it's clear this is metadata, not configuration
   - If removed, update `test_progressive_review.py` and `progressive_review.py`

---

## Current Implementation Status

- ✅ `ReviewerAgentConfig` class does NOT have `model` field (confirmed in `tapps_agents/core/config.py:57-79`)
- ✅ `ReviewerAgent.run()` method has comment: "Model parameter deprecated - all LLM operations handled by Cursor Skills" (line 179)
- ❌ Tests still expect `model` field in config
- ❌ Test fixtures still include `model` in config data

