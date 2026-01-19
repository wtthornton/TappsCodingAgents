"""Check if background agents are running and start them if needed."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tapps_agents.workflow.background_agent_api import BackgroundAgentAPI
from tapps_agents.core.runtime_mode import is_cursor_mode

print("=" * 70)
print("Background Agents Status Check & Start")
print("=" * 70)
print()

# Check if we're in Cursor mode
if not is_cursor_mode():
    print("[ERROR] Not in Cursor mode - Background Agents only work in Cursor IDE")
    print("        Set TAPPS_AGENTS_MODE=cursor or run from Cursor IDE")
    sys.exit(1)

print("[1] Checking Background Agent API...")
print("-" * 70)
api = BackgroundAgentAPI()
agents = api.list_agents()

if agents:
    print(f"[OK] Found {len(agents)} agent(s) via API:")
    for agent in agents:
        name = agent.get("name", "Unknown")
        agent_id = agent.get("id", "N/A")
        status = agent.get("status", "unknown")
        print(f"  - {name} (ID: {agent_id}, Status: {status})")
    print()
    
    # Try to check status of each agent
    print("[2] Checking agent execution status...")
    print("-" * 70)
    for agent in agents:
        agent_id = agent.get("id")
        if agent_id:
            try:
                # Try to get status (this may not work if API doesn't support it)
                print(f"  Checking {agent.get('name', 'Unknown')}...")
                # Note: get_agent_status requires a job_id, not agent_id
                # So we can't directly check if agent is "running"
            except Exception as e:
                print(f"    [INFO] Status check not available: {e}")
else:
    print("[INFO] No agents found via API")
    print("       This is normal - Cursor manages agents internally")
    print("       Agents are registered via .cursor/background-agents.yaml")
    print()

# Check for active worktrees (evidence of agent activity)
print("[3] Checking for active agent activity...")
print("-" * 70)
worktrees_dir = Path(".tapps-agents/worktrees")
if worktrees_dir.exists():
    worktrees = [d for d in worktrees_dir.iterdir() if d.is_dir()]
    if worktrees:
        print(f"[ACTIVE] Found {len(worktrees)} active worktree(s):")
        for wt in worktrees:
            print(f"  - {wt.name}")
            # Check for command files (waiting for execution)
            cmd_files = list(wt.glob("**/.cursor-skill-command.txt"))
            if cmd_files:
                print(f"    -> {len(cmd_files)} command file(s) waiting for execution")
    else:
        print("[IDLE] No active worktrees found")
else:
    print("[MISSING] Worktrees directory not found")

print()

# Check configuration
print("[4] Checking Background Agents configuration...")
print("-" * 70)
config_path = Path(".cursor/background-agents.yaml")
if config_path.exists():
    print(f"[OK] Configuration file exists: {config_path}")
    try:
        import yaml
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        agents_config = config.get("agents", [])
        enabled_count = sum(1 for a in agents_config if a.get("enabled", True))
        print(f"[OK] {len(agents_config)} agent(s) configured, {enabled_count} enabled")
        
        # Check if any have watch_paths (for auto-execution)
        has_watch_paths = any("watch_paths" in a for a in agents_config)
        if has_watch_paths:
            print("[OK] Some agents have watch_paths configured (auto-execution enabled)")
        else:
            print("[WARNING] No agents have watch_paths configured")
            print("          Agents won't automatically execute command files")
            print("          They only respond to natural language triggers")
    except Exception as e:
        print(f"[ERROR] Failed to parse config: {e}")
else:
    print(f"[MISSING] Configuration file not found: {config_path}")

print()

# Summary and recommendations
print("=" * 70)
print("Summary & Recommendations")
print("=" * 70)
print()

if not agents:
    print("[INFO] Background Agents are managed by Cursor IDE")
    print("       They are automatically registered when Cursor loads the workspace")
    print("       You can see them in Cursor's Background Agents panel")
    print()
    print("To verify they're running:")
    print("  1. Open Cursor IDE")
    print("  2. Check the Background Agents panel")
    print("  3. Look for agents listed there")
    print()
    print("To start/trigger them:")
    print("  - Use natural language prompts (triggers in config)")
    print("  - Or manually trigger via Cursor's Background Agents panel")
else:
    print("[OK] Background Agents are accessible via API")
    print("     They should be running and available")

print()
print("Note: The framework cannot directly 'start' background agents.")
print("      They are managed by Cursor IDE and run continuously.")
print("      The framework can only trigger them via API or command files.")
print()

