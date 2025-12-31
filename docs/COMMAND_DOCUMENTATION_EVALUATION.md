{
  "description": "Evaluate whether all tapps-agents commands, subcommands, and @simple-mode commands are documented in cursor rules and README files that are installed during init and release processes. Identify gaps and provide recommendations.",
  "instruction": {
    "agent_name": "analyst",
    "command": "analyze-requirements",
    "prompt": "Analyze the following requirement description and extract detailed requirements.\n\nDescription:\nEvaluate whether all tapps-agents commands, subcommands, and @simple-mode commands are documented in cursor rules and README files that are installed during init and release processes. Identify gaps and provide recommendations.\n\n\n\nPlease provide:\n1. Functional Requirements (what the system should do)\n2. Non-Functional Requirements (performance, security, scalability, etc.)\n3. Technical Constraints\n4. Assumptions\n5. Open Questions\n\nFormat as structured JSON with sections.",
    "parameters": {
      "description": "Evaluate whether all tapps-agents commands, subcommands, and @simple-mode commands are documented in cursor rules and README files that are installed during init and release processes. Identify gaps and provide recommendations."
    }
  },
  "skill_command": "@analyst analyze-requirements --description \"Evaluate whether all tapps-agents commands, subcommands, and @simple-mode commands are documented in cursor rules and README files that are installed during init and release processes. Identify gaps and provide recommendations.\""
}