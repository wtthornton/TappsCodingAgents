# WebSocket Patterns

## Overview

WebSocket provides full-duplex communication over a single TCP connection. This guide covers WebSocket patterns for HomeIQ's Home Assistant integration and similar real-time IoT applications.

## WebSocket Basics

### Connection Lifecycle

1. **Handshake:** HTTP upgrade request
2. **Open:** Connection established
3. **Message Exchange:** Bidirectional communication
4. **Close:** Connection terminated

### Use Cases

- Real-time data streaming (sensor data, device states)
- Live updates (Home Assistant events)
- Bidirectional communication
- Low-latency messaging

## Python WebSocket Patterns

### Pattern 1: Basic WebSocket Client (websockets)

```python
import asyncio
import websockets
import json

async def websocket_client(uri: str):
    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({"type": "subscribe_events"}))
        
        # Receive messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
```

### Pattern 2: WebSocket with Reconnection

```python
import asyncio
import websockets
import json
from tenacity import retry, stop_after_attempt, wait_exponential

class WebSocketClient:
    def __init__(self, uri: str):
        self.uri = uri
        self.websocket = None
        self.running = False
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    async def connect(self):
        """Connect to WebSocket with retry logic."""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise
    
    async def send(self, message: dict):
        """Send message to WebSocket."""
        if not self.websocket:
            await self.connect()
        
        try:
            await self.websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed, reconnecting...")
            await self.connect()
            await self.websocket.send(json.dumps(message))
    
    async def receive(self):
        """Receive message from WebSocket."""
        try:
            message = await self.websocket.recv()
            return json.loads(message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed, reconnecting...")
            await self.connect()
            return await self.receive()
    
    async def listen(self, callback):
        """Listen for messages and call callback."""
        while self.running:
            try:
                message = await self.receive()
                await callback(message)
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                await asyncio.sleep(1)
    
    async def close(self):
        """Close WebSocket connection."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
```

### Pattern 3: Home Assistant WebSocket Integration

```python
import asyncio
import websockets
import json
from typing import Callable, Any

class HomeAssistantWebSocket:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.websocket = None
        self.message_id = 0
        self.pending_requests = {}
    
    async def connect(self):
        """Connect to Home Assistant WebSocket API."""
        uri = f"{self.url}/api/websocket"
        self.websocket = await websockets.connect(uri)
        
        # Receive auth required message
        auth_required = await self.websocket.recv()
        
        # Send auth
        await self.websocket.send(json.dumps({
            "type": "auth",
            "access_token": self.token
        }))
        
        # Receive auth result
        auth_result = json.loads(await self.websocket.recv())
        if auth_result["type"] != "auth_ok":
            raise Exception(f"Authentication failed: {auth_result}")
    
    async def send_command(self, command: dict) -> dict:
        """Send command and wait for response."""
        self.message_id += 1
        command["id"] = self.message_id
        
        # Store future for response
        future = asyncio.Future()
        self.pending_requests[self.message_id] = future
        
        await self.websocket.send(json.dumps(command))
        
        # Wait for response
        response = await future
        return response
    
    async def subscribe_events(self, event_type: str = None):
        """Subscribe to Home Assistant events."""
        command = {
            "type": "subscribe_events",
            "event_type": event_type  # None for all events
        }
        return await self.send_command(command)
    
    async def get_states(self):
        """Get all Home Assistant states."""
        command = {"type": "get_states"}
        return await self.send_command(command)
    
    async def listen_events(self, callback: Callable[[dict], None]):
        """Listen for Home Assistant events."""
        while True:
            try:
                message = json.loads(await self.websocket.recv())
                
                # Handle responses to our commands
                if "id" in message and message["id"] in self.pending_requests:
                    future = self.pending_requests.pop(message["id"])
                    future.set_result(message)
                    continue
                
                # Handle event messages
                if message.get("type") == "event":
                    await callback(message["event"])
            
            except websockets.exceptions.ConnectionClosed:
                logger.error("WebSocket connection closed")
                await self.connect()
                await self.subscribe_events()
            except Exception as e:
                logger.error(f"Error in listen_events: {e}")
                await asyncio.sleep(1)
```

## FastAPI WebSocket Patterns

### Pattern 1: Basic WebSocket Endpoint

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process message
            response = process_message(message)
            
            # Send response
            await websocket.send_text(json.dumps(response))
    except WebSocketDisconnect:
        logger.info("Client disconnected")
```

### Pattern 2: WebSocket with Connection Manager

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(
                json.dumps(message)
            )
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Broadcast to all clients
            await manager.broadcast(message)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

## Error Handling Patterns

### Pattern 1: Graceful Reconnection

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientWebSocket:
    def __init__(self, uri: str):
        self.uri = uri
        self.websocket = None
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
    
    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=2, max=60)
    )
    async def connect(self):
        """Connect with exponential backoff."""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.reconnect_delay = 1  # Reset delay on success
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
    
    async def ensure_connected(self):
        """Ensure WebSocket is connected, reconnect if needed."""
        if not self.websocket or self.websocket.closed:
            await self.connect()
```

### Pattern 2: Heartbeat/Ping Pattern

```python
async def heartbeat_task(websocket, interval: int = 30):
    """Send periodic ping to keep connection alive."""
    while True:
        try:
            await asyncio.sleep(interval)
            pong_waiter = await websocket.ping()
            await pong_waiter
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed during heartbeat")
            break
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            break
```

## Best Practices

### 1. Always Handle Disconnections

```python
try:
    async for message in websocket:
        process_message(message)
except websockets.exceptions.ConnectionClosed:
    logger.warning("Connection closed")
    # Implement reconnection logic
```

### 2. Use Async Context Managers

```python
async with websockets.connect(uri) as websocket:
    # Automatic cleanup on exit
    await websocket.send(message)
```

### 3. Implement Message Queuing

```python
class MessageQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
    
    async def send(self, message: dict):
        """Queue message for sending."""
        await self.queue.put(message)
    
    async def process_queue(self, websocket):
        """Process queued messages."""
        while True:
            message = await self.queue.get()
            try:
                await websocket.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                # Re-queue message if connection lost
                await self.queue.put(message)
                break
```

### 4. Validate Messages

```python
def validate_message(message: dict) -> bool:
    """Validate WebSocket message structure."""
    required_fields = ["type", "data"]
    return all(field in message for field in required_fields)

async def receive_and_validate(websocket):
    """Receive and validate message."""
    message = json.loads(await websocket.recv())
    if not validate_message(message):
        raise ValueError("Invalid message format")
    return message
```

## HomeIQ-Specific Patterns

### Pattern 1: Home Assistant Event Streaming

```python
class HomeAssistantStreamer:
    def __init__(self, ha_ws: HomeAssistantWebSocket):
        self.ha_ws = ha_ws
        self.event_handlers = {}
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register handler for specific event type."""
        self.event_handlers[event_type] = handler
    
    async def stream_events(self):
        """Stream Home Assistant events."""
        await self.ha_ws.subscribe_events()
        
        async def handle_event(event: dict):
            event_type = event.get("event_type")
            if event_type in self.event_handlers:
                await self.event_handlers[event_type](event)
        
        await self.ha_ws.listen_events(handle_event)
```

### Pattern 2: State Change Monitoring

```python
async def monitor_state_changes(ha_ws: HomeAssistantWebSocket, entity_id: str):
    """Monitor state changes for specific entity."""
    last_state = None
    
    async def handle_event(event: dict):
        if event.get("event_type") == "state_changed":
            data = event.get("data", {})
            if data.get("entity_id") == entity_id:
                new_state = data.get("new_state", {}).get("state")
                if new_state != last_state:
                    logger.info(f"State changed: {entity_id} -> {new_state}")
                    last_state = new_state
                    # Process state change
    
    await ha_ws.subscribe_events("state_changed")
    await ha_ws.listen_events(handle_event)
```

## Testing Patterns

### Mock WebSocket Server

```python
import asyncio
import websockets
from unittest.mock import AsyncMock

class MockWebSocketServer:
    def __init__(self, port: int = 8765):
        self.port = port
        self.messages = []
    
    async def handler(self, websocket, path):
        """Handle WebSocket connections."""
        async for message in websocket:
            self.messages.append(message)
            # Echo message back
            await websocket.send(message)
    
    async def start(self):
        """Start mock server."""
        async with websockets.serve(self.handler, "localhost", self.port):
            await asyncio.Future()  # Run forever
```

### Integration Testing

```python
import pytest
import websockets

@pytest.fixture
async def websocket_client():
    async with websockets.connect("ws://localhost:8765") as ws:
        yield ws

@pytest.mark.asyncio
async def test_websocket_connection(websocket_client):
    await websocket_client.send('{"type": "test"}')
    response = await websocket_client.recv()
    assert response == '{"type": "test"}'
```

## References

- [websockets Library](https://websockets.readthedocs.io/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Home Assistant WebSocket API](https://developers.home-assistant.io/docs/api/websocket/)

