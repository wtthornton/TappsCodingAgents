# FastAPI Patterns

## Overview

FastAPI is a modern Python web framework for building APIs. This guide covers FastAPI patterns for HomeIQ and similar microservices applications.

## Core Patterns

### Pattern 1: Basic FastAPI Application

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="HomeIQ API",
    description="Home automation API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "HomeIQ API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### Pattern 2: Dependency Injection

```python
from fastapi import Depends, FastAPI
from typing import Annotated

# Database dependency
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Service dependency
def get_user_service(db: Annotated[Session, Depends(get_db)]):
    return UserService(db)

@app.get("/users/{user_id}")
async def get_user(
    user_id: str,
    service: Annotated[UserService, Depends(get_user_service)]
):
    return await service.get_user(user_id)
```

### Pattern 3: Async Endpoints

```python
import asyncio
from fastapi import FastAPI

app = FastAPI()

@app.get("/sensors/{device_id}")
async def get_sensor_data(device_id: str):
    """Async endpoint for sensor data."""
    # Async database call
    data = await db.fetch_sensor_data(device_id)
    return data

@app.post("/devices/{device_id}/command")
async def send_command(device_id: str, command: dict):
    """Async endpoint for device commands."""
    # Async service call
    result = await device_service.send_command(device_id, command)
    return result
```

### Pattern 4: Request/Response Models

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SensorReading(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    value: float = Field(..., description="Sensor value")
    unit: str = Field(..., description="Unit of measurement")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SensorResponse(BaseModel):
    device_id: str
    readings: list[SensorReading]
    count: int

@app.post("/sensors", response_model=SensorResponse)
async def create_sensor_reading(reading: SensorReading):
    """Create sensor reading."""
    # Process reading
    return SensorResponse(
        device_id=reading.device_id,
        readings=[reading],
        count=1
    )
```

## Advanced Patterns

### Pattern 1: Background Tasks

```python
from fastapi import BackgroundTasks

@app.post("/devices/{device_id}/command")
async def send_command(
    device_id: str,
    command: dict,
    background_tasks: BackgroundTasks
):
    """Send command with background processing."""
    # Immediate response
    result = await device_service.send_command(device_id, command)
    
    # Background task
    background_tasks.add_task(
        log_command,
        device_id,
        command
    )
    
    return result

async def log_command(device_id: str, command: dict):
    """Background task to log command."""
    await logger.log(f"Command sent to {device_id}: {command}")
```

### Pattern 2: WebSocket Endpoints

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### Pattern 3: Error Handling

```python
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)}
    )

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User {user_id} not found"
        )
    return user
```

### Pattern 4: Middleware

```python
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## HomeIQ-Specific Patterns

### Pattern 1: Sensor Data Endpoint

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

class SensorData(BaseModel):
    device_id: str
    value: float
    unit: str
    timestamp: datetime

@app.post("/sensors/data")
async def ingest_sensor_data(
    data: SensorData,
    db: Session = Depends(get_db)
):
    """Ingest sensor data."""
    # Store in InfluxDB
    await influxdb_client.write(data.dict())
    return {"status": "success"}

@app.get("/sensors/{device_id}")
async def get_sensor_data(
    device_id: str,
    start_time: datetime,
    end_time: datetime
):
    """Get sensor data."""
    # Query InfluxDB
    data = await influxdb_client.query(
        device_id=device_id,
        start_time=start_time,
        end_time=end_time
    )
    return data
```

### Pattern 2: Device Control Endpoint

```python
@app.post("/devices/{device_id}/command")
async def send_device_command(
    device_id: str,
    command: dict,
    user: User = Depends(get_current_user)
):
    """Send command to device."""
    # Validate user permissions
    if not await user.has_permission(device_id, "control"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Send command via MQTT
    await mqtt_client.publish(
        f"home/device/{device_id}/command",
        command
    )
    
    return {"status": "command_sent"}
```

## Best Practices

### 1. Use Pydantic Models

```python
# GOOD: Type-safe models
class UserCreate(BaseModel):
    email: str
    name: str

@app.post("/users")
async def create_user(user: UserCreate):
    # Type checking and validation
    pass
```

### 2. Async Database Operations

```python
# GOOD: Async database calls
@app.get("/users")
async def get_users():
    users = await db.fetch_all("SELECT * FROM users")
    return users
```

### 3. Dependency Injection

```python
# GOOD: Dependency injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

### 4. Error Handling

```python
# GOOD: Proper error handling
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### 5. API Documentation

```python
# GOOD: Comprehensive documentation
@app.post(
    "/sensors",
    response_model=SensorResponse,
    summary="Create sensor reading",
    description="Create a new sensor reading",
    response_description="The created sensor reading"
)
async def create_sensor(reading: SensorReading):
    pass
```

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Pydantic Models](https://docs.pydantic.dev/)

