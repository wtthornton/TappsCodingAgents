"""Quick script to check runtime mode detection."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tapps_agents.core.runtime_mode import detect_runtime_mode, is_cursor_mode

print("=" * 60)
print("Runtime Mode Detection")
print("=" * 60)
print()

runtime_mode = detect_runtime_mode()
print(f"Runtime Mode: {runtime_mode.value}")
print(f"Is Cursor Mode: {is_cursor_mode()}")
print()

# Check environment variables
cursor_vars = ["CURSOR", "CURSOR_IDE", "CURSOR_SESSION_ID", "CURSOR_WORKSPACE_ROOT", "CURSOR_TRACE_ID"]
found_vars = [var for var in cursor_vars if os.getenv(var)]
if found_vars:
    print("Cursor environment variables detected:")
    for var in found_vars:
        print(f"  - {var} = {os.getenv(var)}")
else:
    print("No Cursor environment variables found")
print()

# Check TAPPS_AGENTS_MODE
tapps_mode = os.getenv("TAPPS_AGENTS_MODE")
if tapps_mode:
    print(f"TAPPS_AGENTS_MODE: {tapps_mode}")
else:
    print("TAPPS_AGENTS_MODE: (not set)")
print()

print("=" * 60)
print("Conclusion:")
if is_cursor_mode():
    print("[CURSOR MODE] Running in CURSOR mode - will use Background Agents")
    print("  Workflows will create command files and wait for manual execution")
    print("  unless auto-execution is enabled in config.")
else:
    print("[HEADLESS MODE] Running in HEADLESS mode - will use direct execution")
    print("  Workflows will run automatically with terminal output.")

