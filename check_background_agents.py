"""Check if Background Agents are configured and active."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tapps_agents.core.runtime_mode import detect_runtime_mode, is_cursor_mode
from tapps_agents.workflow.background_agent_api import BackgroundAgentAPI

print("=" * 70)
print("Background Agents Status Check")
print("=" * 70)
print()

# 1. Check runtime mode
print("[1] Runtime Mode Detection")
print("-" * 70)
runtime_mode = detect_runtime_mode()
print(f"Runtime Mode: {runtime_mode.value}")
print(f"Is Cursor Mode: {is_cursor_mode()}")
if is_cursor_mode():
    cursor_vars = ["CURSOR", "CURSOR_IDE", "CURSOR_SESSION_ID", "CURSOR_WORKSPACE_ROOT", "CURSOR_TRACE_ID"]
    found = [v for v in cursor_vars if os.getenv(v)]
    if found:
        print(f"Cursor env vars detected: {', '.join(found)}")
print()

# 2. Check background agents configuration
print("[2] Background Agents Configuration")
print("-" * 70)
bg_config_path = Path(".cursor/background-agents.yaml")
if bg_config_path.exists():
    print(f"[OK] Configuration file exists: {bg_config_path}")
    try:
        import yaml
        with open(bg_config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        agents = config.get("agents", [])
        print(f"[OK] Found {len(agents)} configured agents:")
        for i, agent in enumerate(agents, 1):
            name = agent.get("name", "Unknown")
            agent_type = agent.get("type", "unknown")
            enabled = agent.get("enabled", True)
            status = "ENABLED" if enabled else "DISABLED"
            print(f"  {i}. {name} ({agent_type}) - {status}")
    except Exception as e:
        print(f"[ERROR] Failed to parse config: {e}")
else:
    print(f"[MISSING] Configuration file not found: {bg_config_path}")
print()

# 3. Check for active worktrees (evidence of workflow execution)
print("[3] Active Worktrees (Evidence of Background Agent Activity)")
print("-" * 70)
worktrees_dir = Path(".tapps-agents/worktrees")
if worktrees_dir.exists():
    worktrees = [d for d in worktrees_dir.iterdir() if d.is_dir()]
    if worktrees:
        print(f"[ACTIVE] Found {len(worktrees)} worktree(s):")
        for wt in worktrees:
            print(f"  - {wt.name}")
            # Check for command files
            cmd_files = list(wt.glob("**/.cursor-skill-command.txt"))
            if cmd_files:
                print(f"    -> {len(cmd_files)} command file(s) found")
                for cmd_file in cmd_files:
                    print(f"       {cmd_file.relative_to(wt)}")
    else:
        print("[IDLE] No active worktrees found")
else:
    print(f"[MISSING] Worktrees directory not found: {worktrees_dir}")
print()

# 4. Check workflow state
print("[4] Workflow State")
print("-" * 70)
state_dir = Path(".tapps-agents/workflow-state")
if state_dir.exists():
    state_files = list(state_dir.glob("*.json"))
    if state_files:
        print(f"[ACTIVE] Found {len(state_files)} workflow state file(s):")
        for sf in state_files[:5]:  # Show first 5
            print(f"  - {sf.name}")
        if len(state_files) > 5:
            print(f"  ... and {len(state_files) - 5} more")
    else:
        print("[IDLE] No workflow state files found")
else:
    print(f"[MISSING] Workflow state directory not found: {state_dir}")
print()

# 5. Try to list agents via API (if available)
print("[5] Background Agent API Status")
print("-" * 70)
try:
    api = BackgroundAgentAPI()
    agents = api.list_agents()
    if agents:
        print(f"[OK] API available - Found {len(agents)} agent(s) via API")
        for agent in agents:
            name = agent.get("name", "Unknown")
            print(f"  - {name}")
    else:
        print("[INFO] API not available or no agents registered")
        print("       (This is normal - agents may be managed by Cursor directly)")
except Exception as e:
    print(f"[INFO] API check failed: {e}")
    print("       (This is normal - agents are managed by Cursor IDE)")
print()

# 6. Summary
print("=" * 70)
print("Summary")
print("=" * 70)
if is_cursor_mode():
    print("[CURSOR MODE] Background Agents should be available via Cursor IDE")
    if bg_config_path.exists():
        print("[CONFIGURED] Background agents configuration file exists")
    else:
        print("[WARNING] Background agents configuration file missing")
    
    if worktrees_dir.exists() and list(worktrees_dir.iterdir()):
        print("[ACTIVE] Evidence of background agent activity (worktrees found)")
    else:
        print("[IDLE] No current background agent activity detected")
else:
    print("[HEADLESS MODE] Background Agents not used in headless mode")
print()

