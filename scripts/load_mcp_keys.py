#!/usr/bin/env python3
"""
Load MCP API Keys from Encrypted Storage

Loads API keys from encrypted storage and sets them as environment variables.
Run this before starting Cursor, or source it in your shell.
"""

import os
import sys
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent

try:
    from tapps_agents.context7.security import APIKeyManager
    
    key_manager = APIKeyManager(project_root / ".tapps-agents")
    
    # Load Context7 key
    context7_key = key_manager.load_api_key("context7")
    if context7_key:
        os.environ["CONTEXT7_API_KEY"] = context7_key
        print("[OK] Loaded Context7 API key", file=sys.stderr)
    
    # Load GitHub key
    github_key = key_manager.load_api_key("github")
    if github_key:
        os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_key
        print("[OK] Loaded GitHub API key", file=sys.stderr)
    
    # Print export commands for shell sourcing
    if context7_key:
        print(f'export CONTEXT7_API_KEY="{context7_key}"')
    if github_key:
        print(f'export GITHUB_PERSONAL_ACCESS_TOKEN="{github_key}"')
    
except Exception as e:
    print(f"[ERROR] Failed to load keys: {e}", file=sys.stderr)
    sys.exit(1)
