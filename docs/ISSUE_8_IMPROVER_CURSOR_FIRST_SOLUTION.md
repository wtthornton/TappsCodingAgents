# Issue 8: Improver Agent - Cursor-First Solution

## Problem Statement

**Issue**: When running `improver improve-quality` from CLI, the command returns an instruction object with `prompt` and `skill_command`, but Cursor AI doesn't execute it - it just returns the instruction object instead of actually improving the code.

**Root Cause**: 
1. The Cursor Skill definition didn't have explicit instructions about how to handle instruction objects returned from CLI commands
2. The JSON output format didn't include clear directives for Cursor AI to recognize that it should execute the instruction
3. Cursor AI was confused about what to do when it encountered an instruction object in the output

## Solution: Multi-Layer Approach

### Changes Made

#### 1. Enhanced Cursor Skill Definition (`.claude/skills/improver/SKILL.md`)

**Added general guidance** at the top of the Instructions section:
- Explicit explanation that instruction objects from CLI must be executed
- Clear directive: "YOU MUST ACTUALLY IMPROVE/REFACTOR/OPTIMIZE THE CODE" - do not just return the instruction object
- Step-by-step instructions on how to handle instruction objects:
  1. Extract the `prompt` field from the instruction object
  2. Use it as the directive to improve/refactor/optimize
  3. Actually edit the file (do not just return the instruction)
  4. Explain what improvements were made

**Enhanced command documentation** for `*improve-quality`, `*refactor`, and `*optimize`:
- Added explicit instructions about executing instruction objects
- Clearer parameter documentation
- Better examples showing how to handle instruction objects

#### 2. Enhanced Agent Return Values (`tapps_agents/agents/improver/agent.py`)

**Added execution instructions** to all methods that return instruction objects:
- `_handle_improve_quality()` - Added `execution_instructions` list with step-by-step guidance
- `_handle_refactor()` - Added `execution_instructions` 
- `_handle_optimize()` - Added `execution_instructions`
- Each includes clear note: "⚠️ IMPORTANT: When you see this instruction object in Cursor, you MUST execute it by:"
- Explicit steps for Cursor AI to follow

#### 3. Enhanced CLI Output Formatting (`tapps_agents/cli/feedback.py`)

**Added automatic detection** of instruction objects in CLI output:
- When `output_result()` detects an instruction object in the result, it:
  1. **Prints a clear text directive to stderr** BEFORE the JSON output:
     - Prominent header: "⚠️  CURSOR AI: EXECUTION REQUIRED"
     - Step-by-step instructions on what to do
     - Clear directive: "DO NOT just return this JSON - you must execute it"
     - This appears in Cursor chat before the JSON, so Cursor AI sees it
  2. **Adds `_cursor_execution_directive` field** to the JSON output:
     - Structured directive with action, description, steps
     - Programmatic access to execution instructions
     - Can be used by other tools/automation

**Why This Works:**
- When CLI command runs and outputs JSON to Cursor chat, Cursor AI sees:
  1. Clear text instructions on stderr (printed first)
  2. JSON output with execution directive embedded
  3. Both together provide clear guidance on what to do

### How It Works

1. **CLI Command Executes**: User runs `improver improve-quality <file>`
2. **Agent Prepares Instruction**: Agent creates a `GenericInstruction` object with:
   - `prompt`: Detailed prompt for improving the code
   - `parameters`: File path and other parameters
   - `command`: "improve-quality"
3. **CLI Output Formatting**: `feedback.output_result()` detects instruction object and:
   - Prints clear text directive to stderr (visible in Cursor chat)
   - Adds `_cursor_execution_directive` to JSON output
4. **Cursor Chat Processing**: When output appears in Cursor chat, Cursor AI sees:
   - Clear text instructions: "⚠️  CURSOR AI: EXECUTION REQUIRED"
   - Step-by-step instructions on what to do
   - JSON output with embedded execution directive
5. **Cursor Skill Execution**: Cursor AI (guided by SKILL.md and the directives) should:
   - Read the instruction object from JSON
   - Extract the `prompt` field
   - Read the target file
   - Use the prompt to improve the code
   - Actually edit the file (doesn't just return the instruction)
   - Explain what improvements were made
6. **Code Improved**: File is actually improved with better quality code

### Benefits

1. **Triple-Layer Protection**: 
   - Cursor Skill definition has general guidance
   - Agent return values include execution instructions
   - CLI output includes clear text directives
2. **Better Execution**: Code is actually improved, not just instruction objects returned
3. **Consistent Behavior**: All three commands (`improve-quality`, `refactor`, `optimize`) follow the same pattern
4. **Backward Compatible**: Existing CLI usage continues to work
5. **Cursor-First**: Designed to work seamlessly in Cursor chat environment
6. **Clear Guidance**: Multiple layers of instructions ensure Cursor AI understands what to do

### Example Output

When running:
```bash
python -m tapps_agents.cli improver improve-quality src/main.py --focus "complexity,type-safety" --format json
```

**stderr output (visible in Cursor chat):**
```
================================================================================
⚠️  CURSOR AI: EXECUTION REQUIRED
================================================================================

This command returned an instruction object that YOU MUST EXECUTE.

DO NOT just return this JSON - you must:
  1. Read the file: src/main.py
  2. Extract the 'prompt' field from the instruction object below
  3. Use that prompt as your directive to improve/refactor/optimize the code
  4. Actually edit the file with improvements
  5. Explain what improvements you made and why

The instruction is in: data.instruction.prompt
Execute using: @improver *improve-quality or follow the prompt directly.
================================================================================
```

**stdout output (JSON):**
```json
{
  "success": true,
  "message": "Improvement completed successfully",
  "data": {
    "message": "Code quality improvement instruction prepared for src/main.py",
    "instruction": {
      "agent_name": "improver",
      "command": "improve-quality",
      "prompt": "Improve the overall code quality of the following code:\n\nCurrent code:\n```python\n[code here]\n```\n\n[context and guidance]...",
      "parameters": {
        "file_path": "src/main.py",
        "focus": "complexity,type-safety,maintainability"
      }
    },
    "skill_command": "@improver *improve-quality --file_path \"src/main.py\" --focus \"complexity,type-safety,maintainability\"",
    "file": "src/main.py",
    "execution_instructions": [
      "1. Read the file: src/main.py",
      "2. Use the 'prompt' field from the instruction object as your improvement directive",
      "3. Actually improve the code by editing the file according to the prompt",
      "4. Apply all quality improvements (best practices, type hints, documentation, etc.)",
      "5. Explain what improvements you made and why",
      "",
      "DO NOT just return the instruction object - you must execute it by improving the code!"
    ]
  },
  "_cursor_execution_directive": {
    "action": "execute_instruction",
    "description": "This result contains an instruction object that must be executed. DO NOT just return this JSON - you must execute the instruction by improving the code.",
    "steps": [
      "1. Read the file: src/main.py",
      "2. Extract the 'prompt' field from data.instruction as your improvement directive",
      "3. Actually improve/refactor/optimize the code by editing the file according to the prompt",
      "4. Apply all improvements (best practices, type hints, documentation, etc.)",
      "5. Explain what improvements you made and why"
    ],
    "critical": "DO NOT just return this instruction object - you must execute it by improving the code!"
  }
}
```

### Testing

To test this solution:

1. Run the CLI command:
   ```bash
   python -m tapps_agents.cli improver improve-quality src/main.py --focus "complexity,type-safety" --format json
   ```

2. Copy both the stderr text directive AND the JSON output and paste into Cursor chat

3. Cursor AI should:
   - Recognize the execution directive from the text output
   - See the instruction object in the JSON
   - Read the file specified in `file_path`
   - Use the `prompt` field as the improvement directive
   - Actually edit the file with improvements
   - Explain what improvements were made

### Related Issues

This solution addresses the same pattern seen in:
- Issue 3: Planner Agent - similar instruction object confusion
- Issue 4: Tester Agent - similar instruction object confusion

**Recommendation**: Apply the same pattern to other agents that return instruction objects.

### Files Modified

1. `.claude/skills/improver/SKILL.md` - Enhanced with execution instructions
2. `tapps_agents/agents/improver/agent.py` - Added execution_instructions to return values
3. `tapps_agents/cli/feedback.py` - Added automatic detection and formatting of instruction objects

### Next Steps

1. ✅ Test the solution with actual code improvement scenarios
2. Consider applying similar enhancements to:
   - Planner Agent (Issue 3)
   - Tester Agent (Issue 4)
   - Other agents that return GenericInstruction objects
3. Document this pattern in agent development guidelines

## Summary

The solution makes instruction objects **actionable** through a triple-layer approach:
1. **Cursor Skill Definition** - General guidance on handling instruction objects
2. **Agent Return Values** - Execution instructions embedded in the response
3. **CLI Output Formatting** - Clear text directives printed before JSON output

This ensures Cursor AI has multiple opportunities to understand that it must execute the instruction, not just return it. The solution aligns with the "Cursor-first" design philosophy where CLI commands prepare instructions that Cursor AI executes, but now with clear, multi-layered guidance on how to handle those instructions.
