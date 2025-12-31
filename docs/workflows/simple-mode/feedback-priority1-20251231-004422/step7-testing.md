# Step 7: Test Plan and Test Code Generation

**Workflow ID:** feedback-priority1-20251231-004422  
**Date:** January 16, 2025  
**Step:** 7/7 - Testing Plan and Validation

---

## Test Strategy

### Test Levels

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test component interactions
3. **End-to-End Tests** - Test complete workflows

### Test Coverage Target: 80%+

### Testing Tools

- **Framework:** pytest
- **Mocking:** unittest.mock
- **Fixtures:** pytest fixtures
- **Coverage:** pytest-cov

---

## Test Plan

### 1. WorkflowDocumentationManager Tests

**Test File:** `tests/unit/simple_mode/test_documentation_manager.py`

**Test Cases:**

#### Unit Tests

1. **test_generate_workflow_id()**
   - Generate workflow ID with default base name
   - Generate workflow ID with custom base name
   - Verify format: `{base_name}-{timestamp}`
   - Verify uniqueness (multiple calls produce different IDs)

2. **test_get_documentation_dir()**
   - Get directory path
   - Verify path construction
   - Verify caching (same instance returns same path)

3. **test_get_step_file_path()**
   - Get path with step number only
   - Get path with step number and name
   - Verify filename format

4. **test_create_directory()**
   - Create directory successfully
   - Handle existing directory (no error)
   - Handle permission errors
   - Verify directory exists after creation

5. **test_save_step_documentation()**
   - Save documentation successfully
   - Verify file content matches input
   - Verify UTF-8 encoding
   - Handle write errors

6. **test_create_latest_symlink()**
   - Create symlink on Unix systems
   - Create pointer file on Windows
   - Handle symlink creation errors gracefully
   - Verify symlink points to correct directory

7. **test_workflow_id_validation()**
   - Validate workflow ID format
   - Reject invalid characters
   - Prevent path traversal

---

### 2. StepCheckpointManager Tests

**Test File:** `tests/unit/workflow/test_step_checkpoint.py`

**Test Cases:**

#### Unit Tests

1. **test_step_checkpoint_to_dict()**
   - Convert checkpoint to dictionary
   - Verify datetime serialization (ISO format)
   - Verify artifacts serialization

2. **test_step_checkpoint_from_dict()**
   - Create checkpoint from dictionary
   - Verify datetime deserialization
   - Verify artifacts reconstruction

3. **test_step_checkpoint_checksum()**
   - Calculate checksum correctly
   - Verify checksum validation
   - Detect tampered checkpoints

4. **test_save_checkpoint()**
   - Save checkpoint successfully
   - Verify file creation
   - Verify checksum in saved data
   - Handle write errors

5. **test_load_checkpoint()**
   - Load checkpoint by step_id and step_number
   - Load latest checkpoint
   - Verify checkpoint validation on load
   - Handle missing checkpoint errors
   - Handle invalid checkpoint errors

6. **test_get_latest_checkpoint()**
   - Get latest checkpoint (highest step_number)
   - Return None if no checkpoints exist
   - Handle multiple checkpoints correctly

7. **test_list_checkpoints()**
   - List all checkpoints
   - Verify sorting by step_number
   - Handle empty checkpoint directory
   - Skip invalid checkpoints gracefully

8. **test_cleanup_old_checkpoints()**
   - Delete checkpoints older than retention period
   - Keep checkpoints within retention period
   - Return count of deleted checkpoints
   - Handle errors gracefully

---

### 3. BuildOrchestrator Tests

**Test File:** `tests/unit/simple_mode/test_build_orchestrator.py`

**Test Cases:**

#### Unit Tests

1. **test_fast_mode_skips_steps()**
   - Verify steps 1-4 are skipped in fast mode
   - Verify step 5 (implementation) executes
   - Verify original prompt used (not enhanced)

2. **test_full_mode_executes_all_steps()**
   - Verify all 7 steps execute in full mode
   - Verify enhanced prompt used

3. **test_documentation_manager_integration()**
   - Verify documentation manager initialized
   - Verify workflow directory created
   - Verify documentation saved for each step

4. **test_checkpoint_manager_integration()**
   - Verify checkpoint manager initialized
   - Verify checkpoints saved after each step
   - Verify checkpoint data correctness

5. **test_workflow_id_generation()**
   - Verify workflow ID generated
   - Verify workflow ID format
   - Verify workflow ID used in documentation/checkpoints

---

### 4. Integration Tests

**Test File:** `tests/integration/test_priority1_features.py`

**Test Cases:**

1. **test_fast_mode_workflow_execution()**
   - Execute complete fast mode workflow
   - Verify steps skipped correctly
   - Verify quality gates still enforced
   - Verify time savings

2. **test_state_persistence_workflow()**
   - Execute workflow with state persistence
   - Verify checkpoints saved after each step
   - Verify checkpoint integrity
   - Verify resume capability

3. **test_documentation_organization()**
   - Execute workflow with documentation organization
   - Verify workflow directory created
   - Verify all documentation in workflow directory
   - Verify no naming conflicts

4. **test_resume_workflow()**
   - Execute workflow partially
   - Save checkpoint
   - Resume from checkpoint
   - Verify continuation from correct step

5. **test_concurrent_workflows()**
   - Execute multiple workflows concurrently
   - Verify no documentation conflicts
   - Verify no checkpoint conflicts
   - Verify workflow isolation

---

## Test Code Generation

### Test File 1: WorkflowDocumentationManager

```python
"""Tests for WorkflowDocumentationManager."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tapps_agents.simple_mode.documentation_manager import (
    WorkflowDocumentationManager,
    DocumentationError,
)


@pytest.fixture
def tmp_docs_dir(tmp_path):
    """Create temporary documentation directory."""
    return tmp_path / "docs" / "workflows" / "simple-mode"


@pytest.fixture
def doc_manager(tmp_docs_dir):
    """Create WorkflowDocumentationManager instance."""
    return WorkflowDocumentationManager(
        base_dir=tmp_docs_dir,
        workflow_id="test-workflow-123",
        create_symlink=False,
    )


class TestWorkflowDocumentationManager:
    """Test WorkflowDocumentationManager."""

    def test_generate_workflow_id_default(self):
        """Test workflow ID generation with default base name."""
        workflow_id = WorkflowDocumentationManager.generate_workflow_id()
        assert workflow_id.startswith("build-")
        assert len(workflow_id) > len("build-")

    def test_generate_workflow_id_custom(self):
        """Test workflow ID generation with custom base name."""
        workflow_id = WorkflowDocumentationManager.generate_workflow_id("test")
        assert workflow_id.startswith("test-")
        assert len(workflow_id) > len("test-")

    def test_generate_workflow_id_uniqueness(self):
        """Test that workflow IDs are unique."""
        id1 = WorkflowDocumentationManager.generate_workflow_id()
        id2 = WorkflowDocumentationManager.generate_workflow_id()
        assert id1 != id2

    def test_get_documentation_dir(self, doc_manager, tmp_docs_dir):
        """Test getting documentation directory."""
        expected = tmp_docs_dir / "test-workflow-123"
        assert doc_manager.get_documentation_dir() == expected

    def test_get_documentation_dir_caching(self, doc_manager):
        """Test that directory path is cached."""
        dir1 = doc_manager.get_documentation_dir()
        dir2 = doc_manager.get_documentation_dir()
        assert dir1 is dir2

    def test_get_step_file_path_with_name(self, doc_manager):
        """Test getting step file path with step name."""
        path = doc_manager.get_step_file_path(1, "enhanced-prompt")
        assert path.name == "step1-enhanced-prompt.md"
        assert path.parent == doc_manager.get_documentation_dir()

    def test_get_step_file_path_without_name(self, doc_manager):
        """Test getting step file path without step name."""
        path = doc_manager.get_step_file_path(1)
        assert path.name == "step1.md"
        assert path.parent == doc_manager.get_documentation_dir()

    def test_create_directory(self, doc_manager):
        """Test directory creation."""
        doc_dir = doc_manager.create_directory()
        assert doc_dir.exists()
        assert doc_dir.is_dir()

    def test_create_directory_existing(self, doc_manager):
        """Test directory creation when directory already exists."""
        doc_dir1 = doc_manager.create_directory()
        doc_dir2 = doc_manager.create_directory()  # Should not raise error
        assert doc_dir1 == doc_dir2

    def test_create_directory_permission_error(self, doc_manager):
        """Test directory creation with permission error."""
        with patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")):
            with pytest.raises(DocumentationError):
                doc_manager.create_directory()

    def test_save_step_documentation(self, doc_manager):
        """Test saving step documentation."""
        content = "# Step 1: Enhanced Prompt\n\nTest content"
        file_path = doc_manager.save_step_documentation(1, content, "enhanced-prompt")
        
        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == content

    def test_save_step_documentation_creates_directory(self, doc_manager):
        """Test that save creates directory if needed."""
        content = "Test content"
        file_path = doc_manager.save_step_documentation(1, content)
        
        assert doc_manager.get_documentation_dir().exists()
        assert file_path.exists()

    def test_save_step_documentation_utf8(self, doc_manager):
        """Test that documentation saves with UTF-8 encoding."""
        content = "Test with unicode: ✅ ❌ ⚠️"
        file_path = doc_manager.save_step_documentation(1, content)
        
        assert file_path.read_text(encoding="utf-8") == content

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Symlink tests require Unix platform",
    )
    def test_create_latest_symlink_unix(self, doc_manager):
        """Test symlink creation on Unix."""
        doc_manager.create_symlink = True
        doc_manager.create_directory()
        symlink_path = doc_manager.create_latest_symlink()
        
        assert symlink_path is not None
        assert symlink_path.is_symlink()
        assert symlink_path.resolve() == doc_manager.get_documentation_dir()

    def test_create_latest_symlink_windows(self, doc_manager):
        """Test pointer file creation on Windows."""
        doc_manager.create_symlink = True
        doc_manager.create_directory()
        
        with patch("sys.platform", "win32"):
            symlink_path = doc_manager.create_latest_symlink()
            
            assert symlink_path is not None
            assert symlink_path.exists()
            assert "test-workflow-123" in symlink_path.read_text(encoding="utf-8")
```

---

### Test File 2: StepCheckpointManager

```python
"""Tests for StepCheckpointManager."""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from tapps_agents.workflow.step_checkpoint import (
    StepCheckpointManager,
    StepCheckpoint,
    CheckpointNotFoundError,
    CheckpointValidationError,
)
from tapps_agents.workflow.models import Artifact


@pytest.fixture
def tmp_state_dir(tmp_path):
    """Create temporary state directory."""
    return tmp_path / ".tapps-agents" / "workflow-state"


@pytest.fixture
def checkpoint_manager(tmp_state_dir):
    """Create StepCheckpointManager instance."""
    return StepCheckpointManager(
        state_dir=tmp_state_dir,
        workflow_id="test-workflow-123",
    )


@pytest.fixture
def sample_checkpoint_data():
    """Create sample checkpoint data."""
    return {
        "workflow_id": "test-workflow-123",
        "step_id": "enhance",
        "step_number": 1,
        "step_name": "enhanced-prompt",
        "completed_at": datetime.now(),
        "step_output": {"enhanced_prompt": "Enhanced content"},
        "artifacts": {},
        "metadata": {},
    }


class TestStepCheckpoint:
    """Test StepCheckpoint data model."""

    def test_to_dict(self, sample_checkpoint_data):
        """Test checkpoint to dictionary conversion."""
        checkpoint = StepCheckpoint(**sample_checkpoint_data)
        data = checkpoint.to_dict()
        
        assert isinstance(data["completed_at"], str)  # ISO format
        assert data["workflow_id"] == "test-workflow-123"
        assert data["step_id"] == "enhance"

    def test_from_dict(self, sample_checkpoint_data):
        """Test checkpoint from dictionary creation."""
        data = sample_checkpoint_data.copy()
        data["completed_at"] = data["completed_at"].isoformat()
        
        checkpoint = StepCheckpoint.from_dict(data)
        
        assert isinstance(checkpoint.completed_at, datetime)
        assert checkpoint.workflow_id == "test-workflow-123"

    def test_checksum_calculation(self, sample_checkpoint_data):
        """Test checksum calculation."""
        checkpoint = StepCheckpoint(**sample_checkpoint_data)
        checkpoint.update_checksum()
        
        assert len(checkpoint.checksum) == 64  # SHA256 hex length
        assert checkpoint.validate()

    def test_checksum_validation(self, sample_checkpoint_data):
        """Test checksum validation."""
        checkpoint = StepCheckpoint(**sample_checkpoint_data)
        checkpoint.update_checksum()
        
        assert checkpoint.validate()
        
        # Tamper with data
        checkpoint.step_output["tampered"] = True
        assert not checkpoint.validate()


class TestStepCheckpointManager:
    """Test StepCheckpointManager."""

    def test_save_checkpoint(self, checkpoint_manager, sample_checkpoint_data):
        """Test saving checkpoint."""
        checkpoint_path = checkpoint_manager.save_checkpoint(
            step_id="enhance",
            step_number=1,
            step_output=sample_checkpoint_data["step_output"],
            artifacts={},
            step_name="enhanced-prompt",
        )
        
        assert checkpoint_path.exists()
        assert checkpoint_path.name == "step1-enhance.json"

    def test_load_checkpoint(self, checkpoint_manager, sample_checkpoint_data):
        """Test loading checkpoint."""
        # Save checkpoint first
        checkpoint_manager.save_checkpoint(
            step_id="enhance",
            step_number=1,
            step_output=sample_checkpoint_data["step_output"],
            artifacts={},
        )
        
        # Load checkpoint
        checkpoint = checkpoint_manager.load_checkpoint(
            step_id="enhance",
            step_number=1,
        )
        
        assert checkpoint.step_id == "enhance"
        assert checkpoint.step_number == 1
        assert checkpoint.validate()

    def test_load_checkpoint_not_found(self, checkpoint_manager):
        """Test loading non-existent checkpoint."""
        with pytest.raises(CheckpointNotFoundError):
            checkpoint_manager.load_checkpoint(step_id="nonexistent", step_number=999)

    def test_get_latest_checkpoint(self, checkpoint_manager):
        """Test getting latest checkpoint."""
        # Save multiple checkpoints
        for i in range(1, 4):
            checkpoint_manager.save_checkpoint(
                step_id=f"step{i}",
                step_number=i,
                step_output={"result": f"step{i}"},
                artifacts={},
            )
        
        latest = checkpoint_manager.get_latest_checkpoint()
        
        assert latest is not None
        assert latest.step_number == 3  # Latest step

    def test_get_latest_checkpoint_none(self, checkpoint_manager):
        """Test getting latest checkpoint when none exist."""
        latest = checkpoint_manager.get_latest_checkpoint()
        assert latest is None

    def test_list_checkpoints(self, checkpoint_manager):
        """Test listing all checkpoints."""
        # Save multiple checkpoints
        for i in range(1, 4):
            checkpoint_manager.save_checkpoint(
                step_id=f"step{i}",
                step_number=i,
                step_output={"result": f"step{i}"},
                artifacts={},
            )
        
        checkpoints = checkpoint_manager.list_checkpoints()
        
        assert len(checkpoints) == 3
        assert all(c.step_number == i + 1 for i, c in enumerate(checkpoints))

    def test_cleanup_old_checkpoints(self, checkpoint_manager):
        """Test cleaning up old checkpoints."""
        # Save old checkpoint
        old_checkpoint = StepCheckpoint(
            workflow_id="test-workflow-123",
            step_id="step1",
            step_number=1,
            step_name="step1",
            completed_at=datetime(2020, 1, 1),  # Old date
            step_output={},
            artifacts={},
        )
        old_checkpoint.update_checksum()
        
        # Manually write old checkpoint
        checkpoint_file = checkpoint_manager.checkpoint_dir / "step1-step1.json"
        import json
        checkpoint_file.write_text(
            json.dumps(old_checkpoint.to_dict(), default=str),
            encoding="utf-8",
        )
        
        # Cleanup
        deleted = checkpoint_manager.cleanup_old_checkpoints(retention_days=30)
        
        assert deleted >= 1
        assert not checkpoint_file.exists()
```

---

## Test Execution Plan

### Phase 1: Unit Tests (Priority 1)
1. Write `WorkflowDocumentationManager` tests
2. Write `StepCheckpoint` tests
3. Write `StepCheckpointManager` tests
4. Target: 80%+ coverage

### Phase 2: Integration Tests (Priority 2)
1. Write fast mode workflow tests
2. Write state persistence tests
3. Write documentation organization tests
4. Target: Critical paths covered

### Phase 3: End-to-End Tests (Priority 3)
1. Write complete workflow tests
2. Write resume capability tests
3. Write concurrent workflow tests
4. Target: Real-world scenarios

---

## Validation Criteria

### Test Coverage
- ✅ Unit tests: 80%+ coverage
- ✅ Integration tests: Critical paths covered
- ✅ All edge cases handled

### Test Quality
- ✅ Tests are independent
- ✅ Tests are fast (<1s per test)
- ✅ Tests are deterministic
- ✅ Tests have clear assertions

### Test Execution
- ✅ All tests pass
- ✅ No flaky tests
- ✅ Tests run in CI/CD
- ✅ Tests provide clear failure messages

---

## Next Steps

1. **Implement Test Files:**
   - Create test files in `tests/unit/` and `tests/integration/`
   - Write all test cases
   - Ensure 80%+ coverage

2. **Run Tests:**
   - Execute test suite
   - Verify all tests pass
   - Check coverage report

3. **Fix Issues:**
   - Address any test failures
   - Fix code issues found by tests
   - Improve test coverage if needed

---

## Test Summary

- **Test Files:** 3 unit test files, 1 integration test file
- **Test Cases:** ~30+ test cases
- **Coverage Target:** 80%+
- **Estimated Effort:** 4-6 hours

**Status:** Test plan complete, test code templates generated. Ready for implementation.
