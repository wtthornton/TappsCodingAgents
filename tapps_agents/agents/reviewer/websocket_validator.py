"""
WebSocket Validator - Validates WebSocket implementations

Phase 2.2: WebSocket & MQTT Protocol Support for HomeIQ
"""

import re
from pathlib import Path
from typing import Any


class WebSocketValidator:
    """
    Validates WebSocket connection patterns and implementations.
    
    Checks for:
    - Connection management
    - Reconnection logic
    - Error handling
    - Async patterns
    - Message handling
    """

    def __init__(self):
        """Initialize WebSocket validator."""
        self.websocket_patterns = [
            re.compile(r'websockets\.connect', re.IGNORECASE),
            re.compile(r'WebSocket', re.IGNORECASE),
            re.compile(r'websocket', re.IGNORECASE),
            re.compile(r'@app\.websocket', re.IGNORECASE),
        ]

    def validate_connection_pattern(self, code: str) -> dict[str, Any]:
        """
        Validate WebSocket connection patterns.
        
        Args:
            code: Python code containing WebSocket usage
            
        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "issues": list[str],
                "suggestions": list[str]
            }
        """
        issues = []
        suggestions = []
        
        # Check if WebSocket code exists
        has_websocket = any(pattern.search(code) for pattern in self.websocket_patterns)
        if not has_websocket:
            return {
                "valid": True,
                "issues": [],
                "suggestions": []
            }
        
        # Check for context manager usage
        if "websockets.connect" in code and "async with" not in code:
            suggestions.append(
                "Consider using 'async with websockets.connect()' for automatic cleanup"
            )
        
        # Check for reconnection logic
        if "websockets.connect" in code and "retry" not in code.lower():
            issues.append("Missing reconnection logic - WebSocket connections can fail")
            suggestions.append("Implement retry logic with exponential backoff")
        
        # Check for error handling
        if "websockets" in code.lower() and "except" not in code:
            issues.append("Missing error handling for WebSocket operations")
            suggestions.append("Add try/except blocks for ConnectionClosed exceptions")
        
        # Check for async/await usage
        if "websockets" in code.lower() and "async" not in code:
            issues.append("WebSocket operations should be async")
            suggestions.append("Use async/await for WebSocket operations")
        
        # Check for message validation
        if "websocket.recv" in code or "websocket.receive" in code:
            if "json.loads" not in code and "validate" not in code.lower():
                suggestions.append("Consider validating received messages")
        
        # Check for heartbeat/ping
        if "websocket" in code.lower() and "ping" not in code.lower():
            suggestions.append("Consider implementing heartbeat/ping to keep connection alive")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions
        }

    def review_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """
        Review a file for WebSocket patterns.
        
        Args:
            file_path: Path to the file
            code: File content
            
        Returns:
            Dictionary with review results:
            {
                "has_websocket": bool,
                "connection_issues": list[str],
                "suggestions": list[str]
            }
        """
        results = {
            "has_websocket": False,
            "connection_issues": [],
            "suggestions": []
        }
        
        # Check if file contains WebSocket code
        has_websocket = any(pattern.search(code) for pattern in self.websocket_patterns)
        
        if not has_websocket:
            return results
        
        results["has_websocket"] = True
        
        # Validate connection patterns
        validation = self.validate_connection_pattern(code)
        results["connection_issues"].extend(validation.get("issues", []))
        results["suggestions"].extend(validation.get("suggestions", []))
        
        return results

