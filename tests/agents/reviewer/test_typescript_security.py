"""
Tests for TypeScript Security Analysis Enhancement (Phase 7.1)

Tests the new security analysis features added to TypeScriptScorer.

TRACEABILITY:
- Story TS-001: Enhanced TypeScript Review Feedback
- Story TS-002: TypeScript Security Analysis  
- Story TS-004: Score Explanation Mode

Acceptance Criteria (from step2-user-stories.md):
- TS-002: Detect dangerous patterns (eval, innerHTML, dangerouslySetInnerHTML)
- TS-002: Security score reflects actual issues found
- TS-004: Each score includes explanation, reason, recommendations
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.agents.reviewer.typescript_scorer import (
    DANGEROUS_PATTERNS,
    REACT_SECURITY_PATTERNS,
    ScoreExplanation,
    SecurityIssue,
    TypeScriptScorer,
)

# =============================================================================
# ACCEPTANCE CRITERIA TESTS - Mapped from Gherkin in step2-user-stories.md
# =============================================================================

class TestTS002AcceptanceCriteria:
    """
    Story TS-002: TypeScript Security Analysis
    
    Gherkin Acceptance Criteria:
    
    Scenario: Detect dangerous patterns
      Given I have a TypeScript file with dangerous patterns
      When I run security analysis
      Then I should see security issues with pattern, severity, line, message
      
    Scenario: React dangerouslySetInnerHTML detection
      Given I have a React component with dangerouslySetInnerHTML
      When I run security analysis
      Then I should see a HIGH severity issue
      
    Scenario: Security score calculation
      Given I have a TypeScript file with 2 security issues
      When I score the file
      Then security_score should be less than 10.0
      
    Scenario: No security issues
      Given I have a clean TypeScript file
      When I score the file
      Then security_score should be 10.0
    """
    
    @pytest.fixture
    def scorer(self):
        """Create a TypeScriptScorer instance."""
        with patch.object(TypeScriptScorer, '_check_tsc_available', return_value=False):
            with patch.object(TypeScriptScorer, '_check_eslint_available', return_value=False):
                return TypeScriptScorer()
    
    def test_scenario_detect_dangerous_patterns(self, scorer):
        """
        Scenario: Detect dangerous patterns
        
        Given I have a TypeScript file with dangerous patterns:
            const result = eval(userInput);
            element.innerHTML = userData;
        When I run security analysis
        Then I should see security issues with:
            | Field      | Example                          |
            | pattern    | eval                             |
            | severity   | HIGH                             |
            | line       | (line number)                    |
            | message    | eval() can execute arbitrary code|
        """
        # Given
        code = '''
const result = eval(userInput);
element.innerHTML = userData;
'''
        # When
        issues = scorer._detect_dangerous_patterns(code, Path("test.ts"))
        
        # Then
        assert len(issues) >= 2, "Should detect at least 2 issues"
        
        eval_issues = [i for i in issues if i.pattern == "eval"]
        assert len(eval_issues) == 1, "Should detect eval()"
        assert eval_issues[0].severity == "HIGH"
        assert eval_issues[0].line == 2
        assert "arbitrary code" in eval_issues[0].message
        
        html_issues = [i for i in issues if i.pattern == "innerHTML"]
        assert len(html_issues) == 1, "Should detect innerHTML"
        assert html_issues[0].severity == "MEDIUM"
    
    def test_scenario_react_dangerously_set_inner_html(self, scorer):
        """
        Scenario: React dangerouslySetInnerHTML detection
        
        Given I have a React component with dangerouslySetInnerHTML
        When I run security analysis on .tsx file
        Then I should see a HIGH severity issue for dangerouslySetInnerHTML
        """
        # Given
        code = '''
import React from 'react';

function Component() {
    return <div dangerouslySetInnerHTML={{ __html: userData }} />;
}
'''
        # When
        issues = scorer._detect_dangerous_patterns(code, Path("test.tsx"))
        
        # Then
        dangerous_issues = [i for i in issues if i.pattern == "dangerouslySetInnerHTML"]
        assert len(dangerous_issues) == 1, "Should detect dangerouslySetInnerHTML"
        assert dangerous_issues[0].severity == "HIGH"
    
    def test_scenario_security_score_with_issues(self, scorer):
        """
        Scenario: Security score calculation
        
        Given I have a TypeScript file with 2 security issues
        When I calculate security score
        Then security_score should be less than 10.0
        And security_score should reflect actual issues (not default 5.0)
        """
        # Given - 2 issues: 1 HIGH (eval), 1 MEDIUM (innerHTML)
        code = '''
const a = eval(input);
element.innerHTML = data;
'''
        # When
        result = scorer._calculate_security_score(code, Path("test.ts"))
        
        # Then
        assert result["score"] < 10.0, "Score should be reduced for issues"
        assert result["score"] != 5.0, "Score should not be default 5.0"
        assert result["total_issues"] == 2
        # 1 HIGH (-2.0) + 1 MEDIUM (-1.0) = 10 - 3 = 7.0
        assert result["score"] == 7.0
    
    def test_scenario_no_security_issues(self, scorer):
        """
        Scenario: No security issues
        
        Given I have a clean TypeScript file
        When I calculate security score
        Then security_score should be 10.0
        And I should see "No security issues detected"
        """
        # Given
        code = '''
const data = JSON.parse(jsonString);
element.textContent = userData;
console.log("Hello, world!");
'''
        # When
        result = scorer._calculate_security_score(code, Path("test.ts"))
        
        # Then
        assert result["score"] == 10.0, "Clean code should have perfect score"
        assert result["total_issues"] == 0


class TestTS004AcceptanceCriteria:
    """
    Story TS-004: Score Explanation Mode
    
    Gherkin Acceptance Criteria:
    
    Scenario: Low security score explanation
      Given I have a TypeScript file with security issues
      When I generate explanations
      Then I should see security_score with:
        | Field          | Example                              |
        | score          | 6.5                                  |
        | reason         | 2 security issues detected           |
        | issues         | eval() usage, innerHTML assignment   |
        | recommendations| Replace eval with JSON.parse         |
        
    Scenario: Tool unavailable explanation
      Given ESLint is not installed
      When I generate explanations
      Then I should see:
        | Field          | Value                                |
        | linting_score  | 5.0                                  |
        | reason         | ESLint not available                 |
        | recommendations| Install ESLint: npm install -g eslint|
    """
    
    @pytest.fixture
    def scorer(self):
        """Create a TypeScriptScorer instance."""
        with patch.object(TypeScriptScorer, '_check_tsc_available', return_value=True):
            with patch.object(TypeScriptScorer, '_check_eslint_available', return_value=True):
                return TypeScriptScorer()
    
    def test_scenario_low_security_score_explanation(self, scorer):
        """
        Scenario: Low security score explanation
        
        Given I have a TypeScript file with security issues
        When I generate explanations with security_score 6.0
        Then explanation should include reason, issues list, recommendations
        """
        # Given
        scores = {"security_score": 6.0}
        security_issues = [
            {"pattern": "eval", "severity": "HIGH", "line": 42, 
             "message": "eval() can execute arbitrary code", 
             "recommendation": "Use JSON.parse()"},
            {"pattern": "innerHTML", "severity": "MEDIUM", "line": 55, 
             "message": "innerHTML can lead to XSS", 
             "recommendation": "Use textContent"},
        ]
        
        # When
        explanations = scorer._generate_explanations(scores, security_issues, True, True)
        
        # Then
        assert "security_score" in explanations
        sec_exp = explanations["security_score"]
        assert sec_exp["score"] == 6.0
        assert "2 security issue" in sec_exp["reason"]
        assert len(sec_exp["issues"]) == 2
        assert len(sec_exp["recommendations"]) >= 1
    
    def test_scenario_tool_unavailable_explanation(self, scorer):
        """
        Scenario: Tool unavailable explanation
        
        Given ESLint is not installed (eslint_available=False)
        When I generate explanations
        Then linting_score explanation should show unavailable status
        """
        # Given
        scores = {"linting_score": 5.0}
        
        # When - ESLint not available
        explanations = scorer._generate_explanations(scores, [], eslint_available=False, tsc_available=True)
        
        # Then
        assert "linting_score" in explanations
        lint_exp = explanations["linting_score"]
        assert lint_exp["tool_status"] == "unavailable"
        assert "not available" in lint_exp["reason"]
        assert any("npm install" in rec for rec in lint_exp["recommendations"])


class TestSecurityPatterns:
    """Test dangerous pattern detection."""
    
    def test_dangerous_patterns_defined(self):
        """Verify all expected dangerous patterns are defined."""
        expected_patterns = [
            "eval", "innerHTML", "outerHTML", "document.write",
            "Function constructor", "setTimeout string", "setInterval string",
            "insertAdjacentHTML"
        ]
        for pattern in expected_patterns:
            assert pattern in DANGEROUS_PATTERNS, f"Missing pattern: {pattern}"
    
    def test_react_security_patterns_defined(self):
        """Verify React-specific patterns are defined."""
        expected_patterns = [
            "dangerouslySetInnerHTML", "javascript: URL", "target _blank"
        ]
        for pattern in expected_patterns:
            assert pattern in REACT_SECURITY_PATTERNS, f"Missing React pattern: {pattern}"
    
    def test_patterns_have_required_fields(self):
        """Verify each pattern has required fields."""
        required_fields = ["pattern", "severity", "message", "recommendation"]
        
        for name, info in DANGEROUS_PATTERNS.items():
            for field in required_fields:
                assert field in info, f"Pattern {name} missing field: {field}"
        
        for name, info in REACT_SECURITY_PATTERNS.items():
            for field in required_fields:
                assert field in info, f"React pattern {name} missing field: {field}"


class TestSecurityIssueDataclass:
    """Test SecurityIssue dataclass."""
    
    def test_create_security_issue(self):
        """Test creating a SecurityIssue."""
        issue = SecurityIssue(
            pattern="eval",
            severity="HIGH",
            line=42,
            column=10,
            message="eval() can execute arbitrary code",
            recommendation="Use JSON.parse()",
            cwe_id="CWE-95"
        )
        
        assert issue.pattern == "eval"
        assert issue.severity == "HIGH"
        assert issue.line == 42
        assert issue.column == 10
        assert issue.cwe_id == "CWE-95"
    
    def test_to_dict(self):
        """Test SecurityIssue.to_dict()."""
        issue = SecurityIssue(
            pattern="innerHTML",
            severity="MEDIUM",
            line=55,
            column=None,
            message="XSS vulnerability",
            recommendation="Use textContent",
            cwe_id="CWE-79"
        )
        
        result = issue.to_dict()
        
        assert isinstance(result, dict)
        assert result["pattern"] == "innerHTML"
        assert result["severity"] == "MEDIUM"
        assert result["line"] == 55
        assert result["column"] is None


class TestScoreExplanationDataclass:
    """Test ScoreExplanation dataclass."""
    
    def test_create_score_explanation(self):
        """Test creating a ScoreExplanation."""
        explanation = ScoreExplanation(
            score=6.0,
            reason="2 security issues detected",
            issues=["eval at line 42", "innerHTML at line 55"],
            recommendations=["Use JSON.parse()", "Use textContent"],
            tool_status="pattern_based",
            tool_name="TypeScriptSecurityScanner"
        )
        
        assert explanation.score == 6.0
        assert explanation.reason == "2 security issues detected"
        assert len(explanation.issues) == 2
        assert explanation.tool_status == "pattern_based"
    
    def test_to_dict(self):
        """Test ScoreExplanation.to_dict()."""
        explanation = ScoreExplanation(
            score=10.0,
            reason="No issues",
            issues=[],
            recommendations=["Continue following best practices"],
            tool_status="available"
        )
        
        result = explanation.to_dict()
        
        assert isinstance(result, dict)
        assert result["score"] == 10.0
        assert result["issues"] == []


class TestTypeScriptScorerSecurity:
    """Test TypeScriptScorer security analysis methods."""
    
    @pytest.fixture
    def scorer(self):
        """Create a TypeScriptScorer instance."""
        with patch.object(TypeScriptScorer, '_check_tsc_available', return_value=False):
            with patch.object(TypeScriptScorer, '_check_eslint_available', return_value=False):
                return TypeScriptScorer()
    
    def test_detect_eval(self, scorer):
        """Test detection of eval() usage."""
        code = '''
const result = eval(userInput);
console.log(result);
'''
        issues = scorer._detect_dangerous_patterns(code, Path("test.ts"))
        
        assert len(issues) >= 1
        eval_issues = [i for i in issues if i.pattern == "eval"]
        assert len(eval_issues) == 1
        assert eval_issues[0].severity == "HIGH"
        assert eval_issues[0].line == 2
    
    def test_detect_innerhtml(self, scorer):
        """Test detection of innerHTML assignment."""
        code = '''
const element = document.getElementById("test");
element.innerHTML = userData;
'''
        issues = scorer._detect_dangerous_patterns(code, Path("test.ts"))
        
        assert len(issues) >= 1
        html_issues = [i for i in issues if i.pattern == "innerHTML"]
        assert len(html_issues) == 1
        assert html_issues[0].severity == "MEDIUM"
    
    def test_detect_document_write(self, scorer):
        """Test detection of document.write()."""
        code = '''
document.write("<script>alert('xss')</script>");
'''
        issues = scorer._detect_dangerous_patterns(code, Path("test.js"))
        
        doc_write_issues = [i for i in issues if i.pattern == "document.write"]
        assert len(doc_write_issues) == 1
    
    def test_detect_function_constructor(self, scorer):
        """Test detection of new Function()."""
        code = '''
const fn = new Function("return " + userInput);
'''
        issues = scorer._detect_dangerous_patterns(code, Path("test.ts"))
        
        fn_issues = [i for i in issues if i.pattern == "Function constructor"]
        assert len(fn_issues) == 1
        assert fn_issues[0].severity == "HIGH"
    
    def test_detect_settimeout_string(self, scorer):
        """Test detection of setTimeout with string."""
        code = '''
setTimeout("alert('test')", 1000);
'''
        issues = scorer._detect_dangerous_patterns(code, Path("test.js"))
        
        timeout_issues = [i for i in issues if i.pattern == "setTimeout string"]
        assert len(timeout_issues) == 1
    
    def test_detect_react_dangerous_set_inner_html(self, scorer):
        """Test detection of dangerouslySetInnerHTML in React."""
        code = '''
import React from 'react';

function Component() {
    return <div dangerouslySetInnerHTML={{ __html: userData }} />;
}
'''
        issues = scorer._detect_dangerous_patterns(code, Path("test.tsx"))
        
        dangerous_issues = [i for i in issues if i.pattern == "dangerouslySetInnerHTML"]
        assert len(dangerous_issues) == 1
        assert dangerous_issues[0].severity == "HIGH"
    
    def test_skip_comments(self, scorer):
        """Test that patterns in comments are skipped."""
        code = '''
// Don't use eval() in production
/* eval is dangerous */
const safe = JSON.parse(data);
'''
        issues = scorer._detect_dangerous_patterns(code, Path("test.ts"))
        
        eval_issues = [i for i in issues if i.pattern == "eval"]
        assert len(eval_issues) == 0
    
    def test_no_issues_clean_code(self, scorer):
        """Test that clean code has no security issues."""
        code = '''
const data = JSON.parse(jsonString);
element.textContent = userData;
console.log("Hello, world!");
'''
        issues = scorer._detect_dangerous_patterns(code, Path("test.ts"))
        
        assert len(issues) == 0
    
    def test_calculate_security_score_no_issues(self, scorer):
        """Test security score calculation with no issues."""
        code = '''
const safe = JSON.parse(data);
'''
        result = scorer._calculate_security_score(code, Path("test.ts"))
        
        assert result["score"] == 10.0
        assert result["total_issues"] == 0
    
    def test_calculate_security_score_high_issues(self, scorer):
        """Test security score with HIGH severity issues."""
        code = '''
const a = eval(input);
const b = new Function(code);
'''
        result = scorer._calculate_security_score(code, Path("test.ts"))
        
        assert result["score"] < 10.0
        assert result["high_count"] >= 2
        # 2 HIGH issues = -4.0, so score should be 6.0
        assert result["score"] <= 6.0
    
    def test_calculate_security_score_mixed_issues(self, scorer):
        """Test security score with mixed severity issues."""
        code = '''
const a = eval(input);
element.innerHTML = data;
'''
        result = scorer._calculate_security_score(code, Path("test.ts"))
        
        assert result["high_count"] >= 1
        assert result["medium_count"] >= 1
        # 1 HIGH (-2.0) + 1 MEDIUM (-1.0) = 7.0
        assert result["score"] <= 7.0
    
    def test_get_security_issues(self, scorer):
        """Test get_security_issues() external access method."""
        code = '''
eval(input);
'''
        result = scorer.get_security_issues(code, Path("test.ts"))
        
        assert result["available"] is True
        assert "issues" in result
        assert "score" in result
        assert len(result["issues"]) >= 1


class TestScoreExplanations:
    """Test score explanation generation."""
    
    @pytest.fixture
    def scorer(self):
        """Create a TypeScriptScorer instance."""
        with patch.object(TypeScriptScorer, '_check_tsc_available', return_value=True):
            with patch.object(TypeScriptScorer, '_check_eslint_available', return_value=True):
                return TypeScriptScorer()
    
    def test_generate_security_explanation_with_issues(self, scorer):
        """Test explanation generation when security issues exist."""
        scores = {"security_score": 6.0}
        security_issues = [
            {"pattern": "eval", "severity": "HIGH", "line": 42, "message": "eval() is dangerous", "recommendation": "Use JSON.parse()"},
            {"pattern": "innerHTML", "severity": "MEDIUM", "line": 55, "message": "XSS risk", "recommendation": "Use textContent"},
        ]
        
        explanations = scorer._generate_explanations(scores, security_issues, True, True)
        
        assert "security_score" in explanations
        assert explanations["security_score"]["score"] == 6.0
        assert "2 security issue" in explanations["security_score"]["reason"]
        assert len(explanations["security_score"]["issues"]) == 2
    
    def test_generate_security_explanation_no_issues(self, scorer):
        """Test explanation generation when no security issues."""
        scores = {"security_score": 10.0}
        security_issues = []
        
        explanations = scorer._generate_explanations(scores, security_issues, True, True)
        
        assert "security_score" in explanations
        assert "No security issues" in explanations["security_score"]["reason"]
    
    def test_generate_linting_explanation_unavailable(self, scorer):
        """Test explanation when ESLint unavailable."""
        scores = {"linting_score": 5.0}
        
        explanations = scorer._generate_explanations(scores, [], False, True)
        
        assert "linting_score" in explanations
        assert explanations["linting_score"]["tool_status"] == "unavailable"
        assert "not available" in explanations["linting_score"]["reason"]
    
    def test_generate_type_checking_explanation_unavailable(self, scorer):
        """Test explanation when TypeScript unavailable."""
        scores = {"type_checking_score": 5.0}
        
        explanations = scorer._generate_explanations(scores, [], True, False)
        
        assert "type_checking_score" in explanations
        assert explanations["type_checking_score"]["tool_status"] == "unavailable"
    
    def test_generate_complexity_explanation_high(self, scorer):
        """Test explanation for high complexity."""
        scores = {"complexity_score": 8.5}
        
        explanations = scorer._generate_explanations(scores, [], True, True)
        
        assert "complexity_score" in explanations
        assert "High cyclomatic complexity" in explanations["complexity_score"]["reason"]


class TestToolStatus:
    """Test tool status reporting."""
    
    def test_tool_status_in_score_file(self):
        """Test that tool status is included in score_file output."""
        with patch.object(TypeScriptScorer, '_check_tsc_available', return_value=True):
            with patch.object(TypeScriptScorer, '_check_eslint_available', return_value=True):
                scorer = TypeScriptScorer()
                
                code = "const x = 1;"
                scores = scorer.score_file(Path("test.ts"), code)
                
                assert "_tool_status" in scores
                assert scores["_tool_status"]["eslint"] == "available"
                assert scores["_tool_status"]["tsc"] == "available"
                assert scores["_tool_status"]["security_scanner"] == "pattern_based"
    
    def test_tool_status_unavailable(self):
        """Test tool status when tools unavailable."""
        with patch.object(TypeScriptScorer, '_check_tsc_available', return_value=False):
            with patch.object(TypeScriptScorer, '_check_eslint_available', return_value=False):
                scorer = TypeScriptScorer()
                
                code = "const x = 1;"
                scores = scorer.score_file(Path("test.js"), code)
                
                assert scores["_tool_status"]["eslint"] == "unavailable"
                assert scores["_tool_status"]["tsc"] == "unavailable"
