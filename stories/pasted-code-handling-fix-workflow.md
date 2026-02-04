---
story_id: pasted-code-002
epic: simple-mode-enhancements
user: developer
priority: high
points: 5
status: todo
---

# User Story: Pasted Code Handling for *fix Workflow

As a developer, I want to paste code snippets directly in chat for the `*fix` workflow, so that I can quickly iterate on fixes without manually creating temporary files.

## Problem Statement

Currently, the `*fix` workflow requires a file path:
```
@simple-mode *fix <file> "description"
```

**Pain Point:** Users must:
1. Manually create a temporary file
2. Save pasted code to the file
3. Remember the file path
4. Invoke `*fix` with the file path

**Desired Experience:** Users should be able to:
1. Paste code directly in chat
2. System auto-detects pasted code
3. System auto-creates temp file in scratchpad
4. Workflow automatically invoked with temp file

## Acceptance Criteria

### 1. Pasted Code Detection
- [ ] Detect code blocks in user input (markdown code fences)
- [ ] Detect inline code spans for short snippets
- [ ] Detect language from code fence (e.g., ```python)
- [ ] Confidence threshold ≥0.7 for auto-detection

### 2. Temporary File Creation
- [ ] Create temp files in scratchpad directory: `C:\Users\tappt\AppData\Local\Temp\claude\c--cursor-TappsCodingAgents\2fbc8bb2-4600-4720-b2d4-4f8fa56149e7\scratchpad`
- [ ] Generate unique filenames: `pasted_code_{timestamp}_{hash}.{ext}`
- [ ] Infer file extension from language hint (python → .py, typescript → .ts)
- [ ] Default to `.txt` if language unknown
- [ ] Write pasted code to temp file

### 3. Workflow Integration
- [ ] Auto-invoke `*fix` workflow with temp file path
- [ ] Pass user description to fix workflow
- [ ] Report temp file path to user
- [ ] Clean up temp file after workflow completes (optional)

### 4. User Experience
- [ ] Inform user when pasted code is detected
- [ ] Show temp file path
- [ ] Allow user to override auto-detection
- [ ] Handle multiple code blocks (use first or prompt user)

### 5. Error Handling
- [ ] Handle empty code blocks
- [ ] Handle invalid language hints
- [ ] Handle scratchpad directory not writable
- [ ] Fall back to direct edit if temp file creation fails

## Tasks

### Task 1: Pasted Code Detection (3 hours)
- [ ] Add `detect_pasted_code()` function in `workflow_suggester.py` or new module
- [ ] Regex patterns for markdown code fences: ````lang ... ````
- [ ] Regex patterns for inline code: `` `code` ``
- [ ] Language detection from fence info string
- [ ] Confidence scoring (presence of code fence = high confidence)
- [ ] Unit tests for detection

**Files to Create/Modify:**
- `tapps_agents/simple_mode/code_snippet_handler.py` (NEW)

### Task 2: Temporary File Manager (2 hours)
- [ ] Create `TempFileManager` class
- [ ] Generate unique filenames with timestamp + hash
- [ ] Write code to temp file in scratchpad directory
- [ ] Infer file extensions from language
- [ ] Optional: Track temp files for cleanup
- [ ] Unit tests for file creation

**Files to Create/Modify:**
- `tapps_agents/simple_mode/code_snippet_handler.py` (NEW)

### Task 3: Workflow Integration (3 hours)
- [ ] Update `WorkflowSuggester.suggest_workflow()` to detect pasted code
- [ ] Create temp file when pasted code detected
- [ ] Modify suggestion to include temp file path
- [ ] Update `*fix` workflow handler to accept temp file
- [ ] Integration tests

**Files to Modify:**
- `tapps_agents/simple_mode/workflow_suggester.py` (integrate detection)
- `tapps_agents/simple_mode/nl_handler.py` (update fix workflow handler)

### Task 4: User Experience (2 hours)
- [ ] Add user notification when pasted code detected
- [ ] Show temp file path in suggestion
- [ ] Format suggestion message clearly
- [ ] Add documentation

**Files to Modify:**
- `tapps_agents/simple_mode/workflow_suggester.py` (format suggestion)
- `.claude/skills/simple-mode/skill.md` (update documentation)

### Task 5: Testing and Documentation (2 hours)
- [ ] Unit tests for code detection
- [ ] Unit tests for temp file creation
- [ ] Integration tests for workflow
- [ ] Update documentation

**Files to Modify:**
- `tests/simple_mode/test_code_snippet_handler.py` (NEW)
- `tests/simple_mode/test_workflow_suggester.py` (add pasted code tests)
- `docs/SIMPLE_MODE_GUIDE.md` (update with pasted code examples)

## Story Points: 5

**Complexity:** Medium
- Pattern matching for code blocks (straightforward)
- Temp file creation (straightforward)
- Workflow integration (medium complexity)
- User experience (requires clear messaging)

**Scope:** Medium
- 1 new module (`code_snippet_handler.py`)
- 2 modified modules (`workflow_suggester.py`, `nl_handler.py`)
- Tests and documentation

**Files Affected:**
1. `tapps_agents/simple_mode/code_snippet_handler.py` (NEW)
2. `tapps_agents/simple_mode/workflow_suggester.py` (integrate)
3. `tapps_agents/simple_mode/nl_handler.py` (workflow handler)
4. `tests/simple_mode/test_code_snippet_handler.py` (NEW)
5. `tests/simple_mode/test_workflow_suggester.py` (add tests)
6. `.claude/skills/simple-mode/skill.md` (docs)
7. `docs/SIMPLE_MODE_GUIDE.md` (docs)

## Estimated Effort: 12 hours

**Breakdown:**
- Pasted code detection: 3 hours
- Temporary file manager: 2 hours
- Workflow integration: 3 hours
- User experience: 2 hours
- Testing & documentation: 2 hours

## Priority: High

**Impact:** High user satisfaction - removes friction for quick iterations
**Frequency:** Medium-High - users often paste code for quick fixes
**Complexity:** Medium - straightforward implementation

## Dependencies

- None (self-contained within simple_mode module)

## Technical Design

### Code Block Detection

**Markdown Code Fences:**
```python
MARKDOWN_CODE_FENCE = r'```(?P<lang>\w+)?\s*\n(?P<code>.*?)```'
```

**Example Detection:**
```python
user_input = '''
Fix this code:
```python
def calculate(a, b):
    return a / b  # Bug: no zero check
```
'''

# Detect code block
match = re.search(MARKDOWN_CODE_FENCE, user_input, re.DOTALL)
if match:
    language = match.group('lang') or 'txt'
    code = match.group('code')
```

### Temporary File Creation

**Scratchpad Directory:**
```
C:\Users\tappt\AppData\Local\Temp\claude\c--cursor-TappsCodingAgents\2fbc8bb2-4600-4720-b2d4-4f8fa56149e7\scratchpad
```

**Filename Pattern:**
```python
import hashlib
import time

timestamp = int(time.time())
code_hash = hashlib.md5(code.encode()).hexdigest()[:8]
extension = LANGUAGE_EXTENSIONS.get(language, '.txt')
filename = f"pasted_code_{timestamp}_{code_hash}{extension}"
```

**Language Extensions Mapping:**
```python
LANGUAGE_EXTENSIONS = {
    'python': '.py',
    'javascript': '.js',
    'typescript': '.ts',
    'java': '.java',
    'go': '.go',
    'rust': '.rs',
    'c': '.c',
    'cpp': '.cpp',
    'csharp': '.cs',
    'ruby': '.rb',
    'php': '.php',
}
```

### Workflow Integration

**Updated `suggest_workflow()` Logic:**
```python
def suggest_workflow(self, user_input: str, context: dict[str, Any] | None = None):
    # ... existing logic ...

    # Detect pasted code
    pasted_code = detect_pasted_code(user_input)
    if pasted_code and intent.type == IntentType.FIX:
        # Create temp file
        temp_file = create_temp_file(pasted_code)

        # Update suggestion
        return WorkflowSuggestion(
            workflow_command=f'@simple-mode *fix {temp_file.path} "{description}"',
            workflow_type="fix",
            benefits=[
                "Automatic temporary file creation",
                "Systematic root cause analysis",
                "Automatic test verification",
            ],
            confidence=0.90,
            reason=f"Pasted code detected, temp file created: {temp_file.path}",
        )
```

### User Experience Flow

**Before (Manual):**
```
User: "Fix this code [pastes code]"
Assistant: "Please save the code to a file first, then use @simple-mode *fix <file>"
User: *manually creates file*
User: "@simple-mode *fix temp.py"
```

**After (Automatic):**
```
User: "Fix this code:
```python
def calculate(a, b):
    return a / b
```"