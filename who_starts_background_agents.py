"""Explain who starts Background Agents."""
import os
from pathlib import Path

print("=" * 70)
print("Who Starts Background Agents?")
print("=" * 70)
print()

print("[ANSWER] Cursor IDE automatically starts them!")
print("-" * 70)
print()
print("Background Agents are started by CURSOR IDE itself, not by:")
print("  - The TappsCodingAgents framework")
print("  - Any Python script")
print("  - Manual commands")
print()
print("How it works:")
print("  1. Cursor IDE scans your workspace for .cursor/background-agents.yaml")
print("  2. When it finds the file, it automatically:")
print("     - Parses the agent configurations")
print("     - Registers them in Cursor's Background Agents panel")
print("     - Makes them available for triggering")
print("  3. Agents can be triggered:")
print("     - Manually via Cursor's Background Agents panel")
print("     - Via natural language prompts (triggers)")
print("     - Automatically when watching for command files (watch_paths)")
print()

# Check if config file exists
config_path = Path(".cursor/background-agents.yaml")
if config_path.exists():
    print(f"[CONFIGURED] Cursor will auto-detect: {config_path}")
    print()
    print("The configuration file header says:")
    print('  "1. Cursor AI automatically detects this file"')
    print('  "2. Agents are available in Cursor\'s Background Agents panel"')
    print('  "3. Trigger agents via natural language prompts"')
else:
    print(f"[MISSING] Config file not found: {config_path}")
    print("         Cursor won't start any agents without this file.")
print()

# Check if we're in Cursor
cursor_vars = ["CURSOR", "CURSOR_IDE", "CURSOR_SESSION_ID", "CURSOR_WORKSPACE_ROOT", "CURSOR_TRACE_ID"]
found = [v for v in cursor_vars if os.getenv(v)]
if found:
    print(f"[CURSOR ACTIVE] Cursor IDE is running (detected via: {', '.join(found)})")
    print("                This means Cursor has likely already detected and")
    print("                registered the background agents from the config file.")
else:
    print("[NOT IN CURSOR] Cursor IDE environment not detected")
    print("                Background agents would start when Cursor IDE loads this workspace")
print()

print("=" * 70)
print("Summary")
print("=" * 70)
print("Background Agents are started by CURSOR IDE automatically when:")
print("  1. Cursor IDE loads your workspace")
print("  2. It finds .cursor/background-agents.yaml")
print("  3. It parses and registers the agents")
print()
print("You don't need to start them manually - Cursor does it!")
print("You can see and manage them in Cursor's Background Agents panel.")
print()

