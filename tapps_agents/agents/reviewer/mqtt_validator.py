"""
MQTT Validator - Validates MQTT client implementations

Phase 2.3: WebSocket & MQTT Protocol Support for HomeIQ
"""

import re
from pathlib import Path

# Use typing_extensions.TypedDict on Python < 3.12 for Pydantic compatibility
from typing import Any, TypedDict


class MQTTReviewResult(TypedDict):
    """Type definition for MQTT review results."""

    has_mqtt: bool
    connection_issues: list[str]
    topic_issues: list[str]
    suggestions: list[str]


class MQTTValidator:
    """
    Validates MQTT client patterns and implementations.

    Checks for:
    - Connection management
    - Topic structure
    - QoS usage
    - Error handling
    - Reconnection logic
    """

    def __init__(self):
        """Initialize MQTT validator."""
        self.mqtt_patterns = [
            re.compile(r"paho\.mqtt", re.IGNORECASE),
            re.compile(r"asyncio_mqtt", re.IGNORECASE),
            re.compile(r"mqtt\.Client", re.IGNORECASE),
            re.compile(r"MQTT", re.IGNORECASE),
        ]

    def validate_connection_pattern(self, code: str) -> dict[str, Any]:
        """
        Validate MQTT connection patterns.

        Args:
            code: Python code containing MQTT usage

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

        # Check if MQTT code exists
        has_mqtt = any(pattern.search(code) for pattern in self.mqtt_patterns)
        if not has_mqtt:
            return {"valid": True, "issues": [], "suggestions": []}

        # Check for connection callbacks
        if "mqtt.Client" in code and "on_connect" not in code:
            issues.append("Missing on_connect callback")
            suggestions.append(
                "Implement on_connect callback to handle connection events"
            )

        # Check for reconnection logic
        if "mqtt" in code.lower() and "reconnect" not in code.lower():
            issues.append("Missing reconnection logic")
            suggestions.append(
                "Implement automatic reconnection with reconnect_delay_set()"
            )

        # Check for error handling
        if "mqtt" in code.lower() and "except" not in code:
            issues.append("Missing error handling for MQTT operations")
            suggestions.append("Add try/except blocks for MQTT errors")

        # Check for QoS usage
        if "publish" in code and "qos" not in code.lower():
            suggestions.append("Specify QoS level for publish operations (0, 1, or 2)")

        # Check for topic structure
        if "publish" in code or "subscribe" in code:
            # Check for wildcard usage in subscriptions
            if "subscribe" in code and "#" in code:
                suggestions.append(
                    "Be careful with multi-level wildcard (#) - can receive many messages"
                )

            # Check for topic naming
            topics = re.findall(r'(?:publish|subscribe)\(["\']([^"\']+)["\']', code)
            for topic in topics:
                if len(topic.split("/")) > 5:
                    suggestions.append(
                        f"Topic '{topic}' is deeply nested - consider flattening"
                    )

        # Check for retain usage
        if "publish" in code and "retain" not in code.lower():
            suggestions.append("Consider using retain=True for state messages")

        # Check for will message
        if "mqtt.Client" in code and "will_set" not in code:
            suggestions.append(
                "Consider setting will message for unexpected disconnects"
            )

        return {"valid": len(issues) == 0, "issues": issues, "suggestions": suggestions}

    def review_file(self, file_path: Path, code: str) -> MQTTReviewResult:
        """
        Review a file for MQTT patterns.

        Args:
            file_path: Path to the file
            code: File content

        Returns:
            Dictionary with review results:
            {
                "has_mqtt": bool,
                "connection_issues": list[str],
                "topic_issues": list[str],
                "suggestions": list[str]
            }
        """
        results: MQTTReviewResult = {
            "has_mqtt": False,
            "connection_issues": [],
            "topic_issues": [],
            "suggestions": [],
        }

        # Check if file contains MQTT code
        has_mqtt = any(pattern.search(code) for pattern in self.mqtt_patterns)

        if not has_mqtt:
            return results

        results["has_mqtt"] = True

        # Validate connection patterns
        validation = self.validate_connection_pattern(code)
        results["connection_issues"].extend(validation.get("issues", []))
        results["suggestions"].extend(validation.get("suggestions", []))

        return results
