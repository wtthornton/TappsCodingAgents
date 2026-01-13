# Enhancer Agent Analysis: Issues and Recommendations

## Problem Summary

The Enhancer Agent is producing blank/unknown values in the Analysis section (and cascading to other sections) because it's calling a non-existent analyst command.

## Root Cause Analysis

### Issue 1: Non-Existent Command Call

**Location**: `tapps_agents/agents/enhancer/agent.py:754`

```python
analysis_result = await self.analyst.run(
    "analyze-prompt",  # ❌ This command doesn't exist!
    description=prompt,
)
```

**Problem**: The Analyst Agent doesn't have an `analyze-prompt` command. Available commands are:
- `gather-requirements`
- `analyze-stakeholders`
- `research-technology`
- `estimate-effort`
- `assess-risk`
- `competitive-analysis`

**Result**: The analyst returns `{"error": "Unknown command: analyze-prompt"}`, which gets converted to a string and fails to parse, leading to "unknown" values.

### Issue 2: Error Handling Doesn't Check for Error Dict

**Location**: `tapps_agents/agents/enhancer/agent.py:761-764`

```python
if isinstance(analysis_result, dict):
    analysis_text = analysis_result.get("analysis", "") or analysis_result.get("result", "") or str(analysis_result)
```

**Problem**: When `analysis_result` contains `{"error": "..."}`, it doesn't check for the `error` key, so it tries to parse the error dict as if it were valid analysis data.

### Issue 3: Missing Analysis Stage Implementation

The enhancer expects structured analysis data (intent, scope, workflow_type, domains, technologies, complexity) but:
1. The analyst agent doesn't provide this analysis
2. The enhancer doesn't have a fallback to perform this analysis itself
3. The parsing logic expects JSON/markdown that never comes

### Issue 4: Cascading Failures

Because the Analysis stage fails:
- **Requirements stage** gets empty/unknown analysis context
- **Architecture stage** gets empty requirements context
- **Codebase Context** gets empty analysis (missing domains/technologies for search)
- All sections appear blank in the output

## Evidence from Code Review

1. **Analyst Agent** (`tapps_agents/agents/analyst/agent.py:76-133`):
   - No `analyze-prompt` command exists
   - Commands return `GenericInstruction` objects (for Cursor Skills) or error dicts
   - No direct analysis output method

2. **Enhancer Analysis Stage** (`tapps_agents/agents/enhancer/agent.py:667-804`):
   - Creates detailed analysis prompt (lines 732-750)
   - But calls wrong command (line 754)
   - Has parsing logic that never gets valid input (lines 2096-2170)

3. **Markdown Generation** (`tapps_agents/agents/enhancer/agent.py:1871-2094`):
   - Expects populated `stages["analysis"]` dict
   - Falls back to displaying "unknown" values (lines 1887-1905)
   - Requirements/Architecture sections empty if analysis failed

## Recommendations

### Recommendation 1: Fix Immediate Issue - Implement Analysis Directly

**Priority**: HIGH (Fixes current broken functionality)

**Solution**: Since the enhancer already has a detailed analysis prompt, it should either:
1. Use Cursor Skills/MAL directly to perform analysis, OR
2. Implement basic analysis locally without calling analyst

**Implementation**:

```python
async def _stage_analysis(self, prompt: str) -> dict[str, Any]:
    """Stage 1: Analyze prompt intent, scope, and domains."""
    # ... existing Context7 library detection code ...
    
    # Build analysis prompt (already exists, lines 732-750)
    analysis_prompt = f"""Analyze the following prompt and extract:
1. Intent (feature, bug fix, refactor, documentation, etc.)
2. Detected domains (security, user-management, payments, etc.)
3. Estimated scope (small: 1-2 files, medium: 3-5 files, large: 6+ files)
4. Recommended workflow type (greenfield, brownfield, quick-fix)
5. Key technologies mentioned
6. Complexity level (low, medium, high)

Prompt: {prompt}

Provide structured JSON response with the following format:
{{
  "intent": "feature",
  "scope": "medium",
  "workflow_type": "greenfield",
  "domains": ["security", "user-management"],
  "technologies": ["Python", "FastAPI"],
  "complexity": "medium"
}}"""

    # Use MAL or Cursor Skills directly instead of analyst.run()
    if is_cursor_mode():
        # In Cursor mode, create instruction for skill execution
        instruction = GenericInstruction(
            agent_name="enhancer",
            command="analyze-prompt",
            prompt=analysis_prompt,
            parameters={"prompt": prompt},
        )
        # Return instruction structure - skill will execute
        analysis_text = instruction.to_skill_command()
        # Parse the instruction as structured data (skill execution happens in Cursor)
        parsed = self._parse_analysis_response(analysis_text)
    else:
        # In headless mode, use MAL directly
        try:
            from ...core.mal import MAL, MALDisabledInCursorModeError
            mal_config = self.config.mal if self.config else None
            if mal_config and mal_config.enabled:
                mal = MAL(config=mal_config)
                analysis_text = await mal.generate(
                    prompt=analysis_prompt,
                    model=mal_config.default_model if mal_config else None,
                    temperature=0.3,
                )
                parsed = self._parse_analysis_response(analysis_text)
            else:
                # Fallback: Basic keyword-based analysis
                parsed = self._fallback_analysis(prompt)
                analysis_text = json.dumps(parsed, indent=2)
        except Exception as e:
            logger.warning(f"Analysis failed: {e}, using fallback")
            parsed = self._fallback_analysis(prompt)
            analysis_text = json.dumps(parsed, indent=2)
    
    # ... rest of existing code ...
```

**Add fallback analysis method**:

```python
def _fallback_analysis(self, prompt: str) -> dict[str, Any]:
    """Fallback keyword-based analysis when MAL/LLM unavailable."""
    prompt_lower = prompt.lower()
    
    # Detect intent
    if any(word in prompt_lower for word in ["fix", "bug", "error", "issue", "problem"]):
        intent = "bug-fix"
    elif any(word in prompt_lower for word in ["refactor", "improve", "optimize", "update"]):
        intent = "refactor"
    elif any(word in prompt_lower for word in ["document", "docs", "readme"]):
        intent = "documentation"
    elif any(word in prompt_lower for word in ["test", "tests", "testing"]):
        intent = "testing"
    else:
        intent = "feature"
    
    # Estimate scope (rough heuristic)
    word_count = len(prompt.split())
    if word_count < 20:
        scope = "small"
    elif word_count < 50:
        scope = "medium"
    else:
        scope = "large"
    
    # Detect workflow type
    if any(word in prompt_lower for word in ["new", "create", "build", "add"]):
        workflow_type = "greenfield"
    elif any(word in prompt_lower for word in ["existing", "current", "modify", "change"]):
        workflow_type = "brownfield"
    else:
        workflow_type = "greenfield"
    
    # Detect domains (keyword-based)
    domains = []
    domain_keywords = {
        "security": ["security", "auth", "authentication", "authorization", "encrypt", "ssl"],
        "user-management": ["user", "account", "profile", "login", "logout"],
        "database": ["database", "db", "sql", "query", "model"],
        "api": ["api", "endpoint", "route", "request", "response"],
        "ui": ["ui", "interface", "page", "component", "frontend"],
    }
    for domain, keywords in domain_keywords.items():
        if any(keyword in prompt_lower for keyword in keywords):
            domains.append(domain)
    
    # Detect technologies (keyword-based)
    technologies = []
    tech_keywords = {
        "Python": ["python", "py", "fastapi", "flask", "django"],
        "JavaScript": ["javascript", "js", "node", "react", "vue"],
        "TypeScript": ["typescript", "ts"],
        "FastAPI": ["fastapi"],
        "React": ["react"],
    }
    for tech, keywords in tech_keywords.items():
        if any(keyword in prompt_lower for keyword in keywords):
            technologies.append(tech)
    
    # Estimate complexity
    complexity_keywords = ["complex", "advanced", "sophisticated", "integrate", "system"]
    if any(keyword in prompt_lower for keyword in complexity_keywords):
        complexity = "high"
    elif word_count < 30:
        complexity = "low"
    else:
        complexity = "medium"
    
    return {
        "intent": intent,
        "scope": scope,
        "workflow_type": workflow_type,
        "domains": domains,
        "technologies": technologies,
        "complexity": complexity,
    }
```

### Recommendation 2: Improve Error Handling

**Priority**: MEDIUM (Prevents silent failures)

**Solution**: Check for error dicts before parsing:

```python
# Extract analysis text from result
analysis_text = ""
if isinstance(analysis_result, dict):
    # Check for error first
    if "error" in analysis_result:
        logger.warning(f"Analyst returned error: {analysis_result['error']}")
        # Use fallback analysis
        parsed = self._fallback_analysis(prompt)
        analysis_text = json.dumps(parsed, indent=2)
    else:
        analysis_text = analysis_result.get("analysis", "") or analysis_result.get("result", "") or str(analysis_result)
else:
    analysis_text = str(analysis_result)

# Only parse if we have valid text
if analysis_text and not analysis_text.startswith("{'error'"):
    parsed = self._parse_analysis_response(analysis_text)
else:
    parsed = self._fallback_analysis(prompt)
```

### Recommendation 3: Add Analyze-Prompt Command to Analyst Agent

**Priority**: ✅ COMPLETED (Better architecture - implemented)

**Solution**: If analysis should be done by analyst agent, add the command:

```python
# In AnalystAgent.run()
elif command == "analyze-prompt":
    description = kwargs.get("description", "")
    return await self._analyze_prompt(description)

# New method
async def _analyze_prompt(self, description: str) -> dict[str, Any]:
    """Analyze prompt for intent, scope, domains, etc."""
    prompt = f"""Analyze the following prompt and extract:
1. Intent (feature, bug fix, refactor, documentation, etc.)
2. Detected domains (security, user-management, payments, etc.)
3. Estimated scope (small: 1-2 files, medium: 3-5 files, large: 6+ files)
4. Recommended workflow type (greenfield, brownfield, quick-fix)
5. Key technologies mentioned
6. Complexity level (low, medium, high)

Prompt: {description}

Provide structured JSON response..."""

    instruction = GenericInstruction(
        agent_name="analyst",
        command="analyze-prompt",
        prompt=prompt,
        parameters={"description": description},
    )
    
    return {
        "success": True,
        "instruction": instruction.to_dict(),
        "skill_command": instruction.to_skill_command(),
    }
```

### Recommendation 4: Improve Parsing Logic

**Priority**: LOW (Edge case handling)

**Solution**: The parsing logic should handle more formats and be more robust:

1. Check for error messages in response
2. Handle markdown with structured sections
3. Extract fields even from partial matches
4. Provide better logging for debugging

### Recommendation 5: Add Validation and Testing

**Priority**: MEDIUM (Prevents regression)

**Solution**: 
1. Add unit tests for `_stage_analysis` with various prompt types
2. Test error handling paths
3. Test parsing logic with different response formats
4. Integration test for full enhancement pipeline

## Implementation Plan

### Phase 1: Quick Fix (Immediate) - ✅ COMPLETED
1. ✅ Implement `_fallback_analysis` method
2. ✅ Fix `_stage_analysis` to use fallback when analyst fails
3. ✅ Add error checking for error dicts
4. ✅ Add `analyze-prompt` command to Analyst Agent (proper architectural fix)
5. ✅ Update enhancer to handle analyst's response format
6. ⏳ Test with the Blueprint Suggestions prompt (pending user testing)

### Phase 2: Robust Analysis (Next Sprint)
1. Implement proper MAL/LLM integration for analysis
2. Improve parsing logic for multiple formats
3. Add better logging and debugging output
4. Add validation tests

### Phase 3: Architecture Improvement (Future)
1. Consider adding `analyze-prompt` to analyst agent
2. Refactor to use proper agent orchestration
3. Add caching for repeated analyses
4. Improve markdown generation with better fallbacks

## Testing Strategy

### Test Cases

1. **Happy Path**: Valid prompt with clear intent
   - Should extract intent, scope, workflow_type, domains, technologies, complexity

2. **Error Handling**: Analyst returns error
   - Should use fallback analysis, not crash or show "unknown"

3. **Edge Cases**:
   - Very short prompts (< 10 words)
   - Very long prompts (> 200 words)
   - Prompts with no clear intent
   - Prompts with multiple intents

4. **Parsing**: Different response formats
   - JSON in code blocks
   - JSON without code blocks
   - Markdown with sections
   - Plain text with keywords

## Expected Outcomes

After implementing these fixes:

1. ✅ Analysis section will have real values (not "unknown")
2. ✅ Requirements section will have context from analysis
3. ✅ Architecture section will have context from requirements
4. ✅ Codebase Context will have domains/technologies for search
5. ✅ All sections will be populated instead of blank
6. ✅ Better error messages and logging for debugging

## Related Files

- `tapps_agents/agents/enhancer/agent.py` - Main enhancer implementation
- `tapps_agents/agents/analyst/agent.py` - Analyst agent (missing command)
- `tapps_agents/cli/commands/enhancer.py` - CLI command handler
- `.claude/skills/enhancer/SKILL.md` - Cursor Skill definition
