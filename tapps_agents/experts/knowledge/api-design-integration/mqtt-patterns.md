# MQTT Patterns

## Overview

MQTT (Message Queuing Telemetry Transport) is a lightweight publish-subscribe messaging protocol ideal for IoT applications. This guide covers MQTT patterns for HomeIQ and similar home automation systems.

## MQTT Basics

### Core Concepts

- **Broker:** Central message server
- **Client:** Publisher or subscriber
- **Topic:** Message routing path (e.g., `home/sensor/temperature`)
- **QoS (Quality of Service):** Message delivery guarantee
  - QoS 0: At most once (fire and forget)
  - QoS 1: At least once (acknowledged)
  - QoS 2: Exactly once (guaranteed)
- **Retain:** Keep last message on topic
- **Will:** Last message sent on disconnect

### Use Cases

- IoT sensor data publishing
- Device control commands
- Real-time monitoring
- Low-bandwidth environments

## Python MQTT Patterns

### Pattern 1: Basic MQTT Client (paho-mqtt)

```python
import paho.mqtt.client as mqtt
import json

class MQTTClient:
    def __init__(self, broker: str, port: int = 1883):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker."""
        if rc == 0:
            print("Connected to MQTT broker")
            # Subscribe to topics
            client.subscribe("home/sensor/#")
        else:
            print(f"Connection failed with code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback when message received."""
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        print(f"Received on {topic}: {payload}")
    
    def connect(self):
        """Connect to MQTT broker."""
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()
    
    def publish(self, topic: str, payload: dict, qos: int = 1):
        """Publish message to topic."""
        self.client.publish(topic, json.dumps(payload), qos=qos)
    
    def disconnect(self):
        """Disconnect from broker."""
        self.client.loop_stop()
        self.client.disconnect()
```

### Pattern 2: Async MQTT Client (asyncio-mqtt)

```python
import asyncio
from asyncio_mqtt import Client
import json

class AsyncMQTTClient:
    def __init__(self, broker: str, port: int = 1883):
        self.broker = broker
        self.port = port
        self.client = None
    
    async def connect(self):
        """Connect to MQTT broker."""
        self.client = Client(hostname=self.broker, port=self.port)
        await self.client.connect()
    
    async def subscribe(self, topic: str, qos: int = 1):
        """Subscribe to topic."""
        await self.client.subscribe(topic, qos=qos)
    
    async def publish(self, topic: str, payload: dict, qos: int = 1, retain: bool = False):
        """Publish message to topic."""
        await self.client.publish(
            topic,
            json.dumps(payload).encode(),
            qos=qos,
            retain=retain
        )
    
    async def listen(self, callback):
        """Listen for messages."""
        async with self.client.messages() as messages:
            async for message in messages:
                payload = json.loads(message.payload.decode())
                await callback(message.topic, payload)
    
    async def disconnect(self):
        """Disconnect from broker."""
        await self.client.disconnect()
```

### Pattern 3: MQTT with Reconnection

```python
import paho.mqtt.client as mqtt
import time
import logging

class ResilientMQTTClient:
    def __init__(self, broker: str, port: int = 1883):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.connected = False
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected."""
        if rc == 0:
            self.connected = True
            self.reconnect_delay = 1  # Reset delay
            logger.info("Connected to MQTT broker")
            # Resubscribe to topics
            client.subscribe("home/sensor/#")
        else:
            logger.error(f"Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected."""
        self.connected = False
        logger.warning("Disconnected from MQTT broker")
    
    def on_message(self, client, userdata, msg):
        """Callback when message received."""
        # Handle message
        pass
    
    def connect_with_retry(self):
        """Connect with automatic retry."""
        while not self.connected:
            try:
                self.client.connect(self.broker, self.port, 60)
                self.client.loop_start()
                break
            except Exception as e:
                logger.error(f"Connection failed: {e}")
                time.sleep(self.reconnect_delay)
                self.reconnect_delay = min(
                    self.reconnect_delay * 2,
                    self.max_reconnect_delay
                )
```

## Topic Structure Patterns

### Pattern 1: Hierarchical Topics

```
home/
  ├── sensor/
  │   ├── temperature/
  │   │   ├── kitchen
  │   │   └── bedroom
  │   └── humidity/
  │       ├── kitchen
  │       └── bedroom
  ├── device/
  │   ├── light/
  │   │   └── living_room
  │   └── switch/
  │       └── kitchen
  └── command/
      ├── light/
      │   └── living_room
      └── switch/
          └── kitchen
```

### Pattern 2: Topic Naming Conventions

**Format:** `{location}/{device_type}/{device_id}/{property}`

**Examples:**
- `home/kitchen/sensor/temperature` - Kitchen temperature sensor
- `home/bedroom/light/main/state` - Bedroom light state
- `home/kitchen/switch/appliance/command` - Kitchen switch command

**Best Practices:**
- Use forward slashes for hierarchy
- Keep topics short but descriptive
- Use consistent naming conventions
- Avoid special characters

### Pattern 3: Wildcard Subscriptions

```python
# Single-level wildcard (+)
client.subscribe("home/+/sensor/temperature")

# Multi-level wildcard (#)
client.subscribe("home/sensor/#")

# Specific device
client.subscribe("home/kitchen/sensor/temperature")
```

## QoS Patterns

### Pattern 1: Sensor Data (QoS 0)

```python
# High-frequency, low-criticality data
client.publish(
    "home/sensor/temperature/kitchen",
    {"value": 72.5, "unit": "fahrenheit"},
    qos=0  # Fire and forget
)
```

### Pattern 2: Commands (QoS 1)

```python
# Important commands that must be delivered
client.publish(
    "home/device/light/living_room/command",
    {"action": "turn_on", "brightness": 80},
    qos=1  # At least once
)
```

### Pattern 3: Critical Messages (QoS 2)

```python
# Critical messages requiring exactly-once delivery
client.publish(
    "home/security/alarm/trigger",
    {"alarm_type": "intrusion", "location": "front_door"},
    qos=2  # Exactly once
)
```

## Retain and Will Patterns

### Pattern 1: Last Known Value (Retain)

```python
# Publish with retain to keep last value
client.publish(
    "home/device/light/living_room/state",
    {"state": "on", "brightness": 80},
    qos=1,
    retain=True  # Broker keeps this message
)
```

### Pattern 2: Last Will and Testament

```python
# Set will message for unexpected disconnects
client.will_set(
    "home/device/status",
    json.dumps({"device": "sensor_001", "status": "offline"}),
    qos=1,
    retain=True
)
```

## HomeIQ-Specific Patterns

### Pattern 1: Sensor Data Publishing

```python
class SensorPublisher:
    def __init__(self, mqtt_client, device_id: str, location: str):
        self.client = mqtt_client
        self.device_id = device_id
        self.location = location
        self.base_topic = f"home/{location}/sensor/{device_id}"
    
    def publish_reading(self, sensor_type: str, value: float, unit: str):
        """Publish sensor reading."""
        topic = f"{self.base_topic}/{sensor_type}"
        payload = {
            "value": value,
            "unit": unit,
            "timestamp": time.time(),
            "device_id": self.device_id,
            "location": self.location
        }
        self.client.publish(topic, payload, qos=0, retain=False)
```

### Pattern 2: Device Control

```python
class DeviceController:
    def __init__(self, mqtt_client, device_id: str, location: str):
        self.client = mqtt_client
        self.device_id = device_id
        self.location = location
        self.command_topic = f"home/{location}/device/{device_id}/command"
        self.state_topic = f"home/{location}/device/{device_id}/state"
    
    def send_command(self, action: str, **kwargs):
        """Send command to device."""
        payload = {"action": action, **kwargs}
        self.client.publish(
            self.command_topic,
            payload,
            qos=1,
            retain=False
        )
    
    def update_state(self, state: dict):
        """Update device state."""
        self.client.publish(
            self.state_topic,
            state,
            qos=1,
            retain=True  # Retain state for new subscribers
        )
```

## Error Handling Patterns

### Pattern 1: Connection Error Handling

```python
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected successfully")
    elif rc == 1:
        logger.error("Connection refused - incorrect protocol version")
    elif rc == 2:
        logger.error("Connection refused - invalid client identifier")
    elif rc == 3:
        logger.error("Connection refused - server unavailable")
    elif rc == 4:
        logger.error("Connection refused - bad username or password")
    elif rc == 5:
        logger.error("Connection refused - not authorized")
```

### Pattern 2: Publish Error Handling

```python
def on_publish(client, userdata, mid):
    """Callback when message published."""
    logger.debug(f"Message {mid} published successfully")

def publish_with_error_handling(client, topic, payload, qos=1):
    """Publish with error handling."""
    try:
        result = client.publish(topic, payload, qos=qos)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(f"Publish failed: {result.rc}")
            return False
        return True
    except Exception as e:
        logger.error(f"Publish error: {e}")
        return False
```

## Testing Patterns

### Mock MQTT Broker

```python
from unittest.mock import Mock, MagicMock

class MockMQTTClient:
    def __init__(self):
        self.published_messages = []
        self.subscribed_topics = []
        self.connected = False
    
    def connect(self, broker, port, keepalive):
        self.connected = True
    
    def publish(self, topic, payload, qos=0, retain=False):
        self.published_messages.append({
            "topic": topic,
            "payload": payload,
            "qos": qos,
            "retain": retain
        })
        return Mock(rc=0)
    
    def subscribe(self, topic, qos=0):
        self.subscribed_topics.append({"topic": topic, "qos": qos})
```

## Best Practices

### 1. Use Appropriate QoS Levels

- **QoS 0:** High-frequency sensor data
- **QoS 1:** Commands and state updates
- **QoS 2:** Critical messages (use sparingly)

### 2. Implement Reconnection Logic

```python
client.reconnect_delay_set(min_delay=1, max_delay=60)
```

### 3. Use Retain for State

```python
# Retain last known state
client.publish("device/state", state, qos=1, retain=True)
```

### 4. Clean Session Management

```python
# Use clean_session=False for persistent sessions
client = mqtt.Client(clean_session=False)
```

### 5. Topic Security

```python
# Use authentication
client.username_pw_set(username, password)

# Use TLS for secure connections
client.tls_set(ca_certs="ca.crt")
```

## References

- [paho-mqtt Documentation](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php)
- [asyncio-mqtt](https://github.com/sbtinstruments/asyncio-mqtt)
- [MQTT Specification](https://mqtt.org/mqtt-specification/)

