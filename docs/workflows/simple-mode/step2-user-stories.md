# Step 2: User Stories - TypeScript Enhancement Suite

**Workflow**: Simple Mode *full  
**Date**: 2025-01-16  
**Sprint**: TypeScript Enhancement Sprint

---

## Epic: TypeScript Quality Analysis Enhancement

**Epic ID**: EPIC-TS-001  
**Priority**: Critical  
**Total Story Points**: 34

---

## Story 1: Enhanced TypeScript Review Feedback

**Story ID**: TS-001  
**Priority**: Critical  
**Story Points**: 8  
**Assignee**: TappsCodingAgents

### User Story
As a **TypeScript developer**, I want **detailed review feedback with line numbers and specific issues**, so that I can **quickly identify and fix problems in my code**.

### Acceptance Criteria

```gherkin
Feature: Enhanced TypeScript Review Feedback

  Scenario: Review TypeScript file with ESLint issues
    Given I have a TypeScript file with linting issues
    When I run "reviewer review <file.ts>"
    Then I should see each ESLint issue with:
      | Field      | Example                          |
      | file       | src/app.ts                       |
      | line       | 42                               |
      | column     | 15                               |
      | rule_id    | @typescript-eslint/no-unused-vars|
      | message    | 'foo' is declared but never used |
      | severity   | warning                          |

  Scenario: Review TypeScript file with type errors
    Given I have a TypeScript file with type errors
    When I run "reviewer review <file.ts>"
    Then I should see each type error with:
      | Field      | Example                          |
      | file       | src/app.ts                       |
      | line       | 55                               |
      | column     | 10                               |
      | code       | TS2345                           |
      | message    | Argument of type 'string' is not assignable |

  Scenario: Review JavaScript file with ESLint issues
    Given I have a JavaScript file with linting issues
    When I run "reviewer review <file.js>"
    Then I should see ESLint issues with line numbers
    And type checking should show "not applicable" for JS files

  Scenario: No tools available
    Given ESLint is not installed
    When I run "reviewer review <file.ts>"
    Then I should see a neutral score (5.0)
    And I should see a message "ESLint not available - install via npm"
```

### Technical Tasks
- [ ] Update `_extract_detailed_findings()` to process TypeScript errors
- [ ] Parse ESLint JSON output for detailed issue extraction
- [ ] Parse TypeScript compiler output for error extraction
- [ ] Add TypeScript-specific finding types to ReviewFinding
- [ ] Limit findings to top 10 per category

---

## Story 2: TypeScript Security Analysis

**Story ID**: TS-002  
**Priority**: Critical  
**Story Points**: 8  
**Assignee**: TappsCodingAgents

### User Story
As a **security-conscious developer**, I want **real security analysis for my TypeScript code**, so that I can **identify and fix vulnerabilities before deployment**.

### Acceptance Criteria

```gherkin
Feature: TypeScript Security Analysis

  Scenario: Detect dangerous patterns
    Given I have a TypeScript file with dangerous patterns
      """
      const result = eval(userInput);
      element.innerHTML = userData;
      """
    When I run "reviewer security-scan <file.ts>"
    Then I should see security issues:
      | pattern      | severity | line |
      | eval()       | HIGH     | 1    |
      | innerHTML    | MEDIUM   | 2    |

  Scenario: React dangerouslySetInnerHTML detection
    Given I have a React component with dangerouslySetInnerHTML
    When I run "reviewer security-scan <file.tsx>"
    Then I should see a HIGH severity issue for dangerouslySetInnerHTML

  Scenario: Security score calculation
    Given I have a TypeScript file with 2 security issues
    When I run "reviewer score <file.ts>"
    Then security_score should be less than 10.0
    And security_score should reflect actual issues (not default 5.0)

  Scenario: No security issues
    Given I have a clean TypeScript file
    When I run "reviewer score <file.ts>"
    Then security_score should be 10.0
    And I should see "No security issues detected"
```

### Technical Tasks
- [ ] Implement `_calculate_security_score()` in TypeScriptScorer
- [ ] Add dangerous pattern detection (eval, innerHTML, etc.)
- [ ] Add React-specific security patterns
- [ ] Integrate npm audit for dependency vulnerabilities (optional)
- [ ] Update security score calculation formula

---

## Story 3: Improver Auto-Apply Option

**Story ID**: TS-003  
**Priority**: High  
**Story Points**: 5  
**Assignee**: TappsCodingAgents

### User Story
As a **developer**, I want **to automatically apply suggested improvements**, so that I can **save time and avoid manual copy-paste errors**.

### Acceptance Criteria

```gherkin
Feature: Improver Auto-Apply

  Scenario: Auto-apply improvements
    Given I have a file with quality issues
    When I run "improver improve-quality <file> 'Fix issues' --auto-apply"
    Then the file should be modified with improvements
    And a backup should be created at <file>.backup
    And I should see a diff of changes made
    And a verification review should run

  Scenario: Preview before apply
    Given I have a file with quality issues
    When I run "improver improve-quality <file> 'Fix issues' --preview"
    Then I should see a diff of proposed changes
    And the file should NOT be modified
    And I should see "Use --auto-apply to apply these changes"

  Scenario: Rollback on failure
    Given I have applied changes that broke the code
    When verification fails
    Then I should see option to rollback
    And backup file should be preserved

  Scenario: No backup directory
    Given backup directory doesn't exist
    When I run with --auto-apply
    Then backup directory should be created
    And backup should be saved
```

### Technical Tasks
- [ ] Add `--auto-apply` flag to improve commands
- [ ] Implement `_create_backup()` method
- [ ] Implement `_apply_improvements()` method
- [ ] Implement `_generate_diff()` method
- [ ] Add verification review after apply
- [ ] Handle rollback scenarios

---

## Story 4: Score Explanation Mode

**Story ID**: TS-004  
**Priority**: High  
**Story Points**: 5  
**Assignee**: TappsCodingAgents

### User Story
As a **developer**, I want **explanations for my code quality scores**, so that I can **understand why scores are low and how to improve them**.

### Acceptance Criteria

```gherkin
Feature: Score Explanations

  Scenario: Low security score explanation
    Given I have a TypeScript file with security issues
    When I run "reviewer score <file.ts> --explain"
    Then I should see security_score with explanation:
      | Field          | Example                              |
      | score          | 6.5                                  |
      | reason         | 2 security issues detected           |
      | issues         | eval() usage, innerHTML assignment   |
      | recommendations| Replace eval with JSON.parse, use textContent |

  Scenario: Tool unavailable explanation
    Given ESLint is not installed
    When I run "reviewer score <file.ts> --explain"
    Then I should see:
      | Field          | Value                                |
      | linting_score  | 5.0                                  |
      | reason         | ESLint not available                 |
      | recommendations| Install ESLint: npm install -g eslint|

  Scenario: All scores explained
    Given I run "reviewer score <file.ts> --explain"
    Then each score should have:
      - score (number)
      - reason (string)
      - recommendations (list)
      - tool_status (available/unavailable/error)
```

### Technical Tasks
- [ ] Add `--explain` flag to score command
- [ ] Add `_explanations` field to score output
- [ ] Generate explanations for each metric
- [ ] Include tool availability status
- [ ] Add recommendations for improvement

---

## Story 5: Before/After Code Diffs

**Story ID**: TS-005  
**Priority**: High  
**Story Points**: 3  
**Assignee**: TappsCodingAgents

### User Story
As a **developer**, I want **to see a diff of proposed changes**, so that I can **review improvements before applying them**.

### Acceptance Criteria

```gherkin
Feature: Code Diffs

  Scenario: Generate unified diff
    Given I request improvements to a file
    When the improver generates changes
    Then I should see a unified diff:
      """
      --- original/app.ts
      +++ improved/app.ts
      @@ -10,3 +10,5 @@
      -const x = eval(input);
      +const x = JSON.parse(input);
      """

  Scenario: Diff statistics
    Given improvements are generated
    Then I should see statistics:
      | Metric         | Value |
      | lines_added    | 5     |
      | lines_removed  | 3     |
      | files_changed  | 1     |

  Scenario: No changes needed
    Given file is already optimal
    When I request improvements
    Then I should see "No changes recommended"
    And diff should be empty
```

### Technical Tasks
- [ ] Implement `_generate_unified_diff()` method
- [ ] Add diff statistics calculation
- [ ] Include diff in improver output
- [ ] Handle no-change scenarios

---

## Story 6: Language Support Documentation

**Story ID**: TS-006  
**Priority**: Medium  
**Story Points**: 5  
**Assignee**: TappsCodingAgents

### User Story
As a **developer**, I want **clear documentation of supported languages and capabilities**, so that I can **understand what the tools can and cannot do**.

### Acceptance Criteria

```gherkin
Feature: Language Documentation

  Scenario: TypeScript support guide
    Given I access the documentation
    Then I should find TYPESCRIPT_SUPPORT.md with:
      - Supported file extensions (.ts, .tsx, .js, .jsx)
      - Available analysis types (linting, type-checking, security)
      - Required tools (ESLint, TypeScript)
      - Known limitations

  Scenario: CLI help includes language info
    Given I run "tapps-agents reviewer review --help"
    Then I should see supported languages listed
    And I should see tool requirements

  Scenario: Review output includes tool status
    Given I review a TypeScript file
    Then output should include tool_status:
      | Tool    | Status    |
      | eslint  | available |
      | tsc     | available |
      | security| basic     |
```

### Technical Tasks
- [ ] Create docs/TYPESCRIPT_SUPPORT.md
- [ ] Update CLI help text with language info
- [ ] Add tool_status to review output
- [ ] Update README with language matrix
- [ ] Document known limitations

---

## Story Dependencies

```
TS-001 (Review Feedback)
    |
    v
TS-002 (Security Analysis) --> TS-004 (Score Explanations)
    |
    v
TS-003 (Auto-Apply) --> TS-005 (Code Diffs)
    |
    v
TS-006 (Documentation)
```

---

## Sprint Summary

| Story ID | Title | Points | Priority | Status |
|----------|-------|--------|----------|--------|
| TS-001 | Enhanced TypeScript Review Feedback | 8 | Critical | Ready |
| TS-002 | TypeScript Security Analysis | 8 | Critical | Ready |
| TS-003 | Improver Auto-Apply Option | 5 | High | Ready |
| TS-004 | Score Explanation Mode | 5 | High | Ready |
| TS-005 | Before/After Code Diffs | 3 | High | Ready |
| TS-006 | Language Support Documentation | 5 | Medium | Ready |

**Total Story Points**: 34  
**Estimated Duration**: 5-7 days

---

**Stories Status**: APPROVED  
**Next Step**: Step 3 - Architecture Design