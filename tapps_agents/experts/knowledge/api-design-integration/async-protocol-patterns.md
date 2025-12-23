# Async Protocol Patterns

## Overview

This guide covers general patterns for async protocols (WebSocket, MQTT, gRPC streaming) used in HomeIQ and similar real-time systems.

## Common Patterns

### Pattern 1: Connection Management

```python
class AsyncProtocolClient:
    def __init__(self, uri: str):
        self.uri = uri
        self.connection = None
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
    
    async def connect(self):
        """Establish connection with retry."""
        # Implementation specific
        pass
    
    async def ensure_connected(self):
        """Ensure connection is active."""
        if not self.connection or self.connection.closed:
            await self.connect()
```

### Pattern 2: Message Handling

```python
async def message_handler(message):
    """Handle incoming message."""
    try:
        # Process message
        result = await process_message(message)
        return result
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        # Handle error appropriately
```

### Pattern 3: Reconnection Strategy

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=1, min=2, max=60)
)
async def connect_with_retry(client):
    """Connect with exponential backoff."""
    await client.connect()
```

## References

See `websocket-patterns.md` and `mqtt-patterns.md` for protocol-specific patterns.

