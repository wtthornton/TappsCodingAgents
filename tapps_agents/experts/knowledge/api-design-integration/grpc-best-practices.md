# gRPC Best Practices

## Overview

gRPC is a high-performance RPC (Remote Procedure Call) framework that uses HTTP/2 and Protocol Buffers. It's ideal for microservices communication, streaming, and high-performance APIs.

## Core Concepts

### Protocol Buffers

**Define Service:**
```protobuf
syntax = "proto3";

package user;

service UserService {
  rpc GetUser(GetUserRequest) returns (User);
  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse);
  rpc CreateUser(CreateUserRequest) returns (User);
  rpc UpdateUser(UpdateUserRequest) returns (User);
  rpc DeleteUser(DeleteUserRequest) returns (google.protobuf.Empty);
}

message User {
  int64 id = 1;
  string name = 2;
  string email = 3;
  string role = 4;
  google.protobuf.Timestamp created_at = 5;
}

message GetUserRequest {
  int64 id = 1;
}

message ListUsersRequest {
  int32 page = 1;
  int32 limit = 2;
  string filter = 3;
}

message ListUsersResponse {
  repeated User users = 1;
  int32 total = 2;
  int32 page = 3;
}
```

### Service Definitions

**Unary RPC:**
```protobuf
rpc GetUser(GetUserRequest) returns (User);
```

**Server Streaming:**
```protobuf
rpc ListUsers(ListUsersRequest) returns (stream User);
```

**Client Streaming:**
```protobuf
rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse);
```

**Bidirectional Streaming:**
```protobuf
rpc Chat(stream Message) returns (stream Message);
```

## Best Practices

### 1. Naming Conventions

**Service Names:** PascalCase
```protobuf
service UserService { ... }
service OrderService { ... }
```

**RPC Names:** PascalCase
```protobuf
rpc GetUser(...) returns (...);
rpc CreateUser(...) returns (...);
```

**Message Types:** PascalCase
```protobuf
message UserRequest { ... }
message UserResponse { ... }
```

**Field Names:** snake_case
```protobuf
message User {
  int64 user_id = 1;
  string full_name = 2;
  string email_address = 3;
}
```

### 2. Field Numbers

**Don't Reuse Numbers:**
- Field numbers are permanent
- Once used, can't be reused
- Mark deprecated fields as reserved

**Reserved Fields:**
```protobuf
message User {
  reserved 5, 10 to 15;
  reserved "old_field";
  
  int64 id = 1;
  string name = 2;
}
```

### 3. Versioning

**Package Versioning:**
```protobuf
package user.v1;

service UserService {
  rpc GetUser(GetUserRequest) returns (User);
}
```

**Add New Fields:**
```protobuf
message User {
  int64 id = 1;
  string name = 2;
  string email = 3;
  // New field added
  string phone = 4;  // New fields at end
}
```

**Backward Compatibility:**
- New fields should be optional
- Don't remove fields (mark reserved)
- Don't change field numbers
- Don't change field types

### 4. Error Handling

**Standard Status Codes:**
```python
from grpc import StatusCode

# Success
return user, StatusCode.OK

# Not found
return None, StatusCode.NOT_FOUND

# Invalid argument
return None, StatusCode.INVALID_ARGUMENT

# Internal error
return None, StatusCode.INTERNAL
```

**Error Details:**
```python
from google.rpc import status_pb2, error_details_pb2

def create_error_status(code, message, details=None):
    error_status = status_pb2.Status()
    error_status.code = code
    error_status.message = message
    
    if details:
        error_detail = error_details_pb2.ErrorInfo()
        error_detail.reason = details.get("reason")
        error_detail.domain = details.get("domain")
        error_status.details.add().Pack(error_detail)
    
    return error_status
```

### 5. Streaming

**Server Streaming:**
```python
def ListUsers(request, context):
    users = db.user.list(request.filter)
    
    for user in users:
        yield user_pb2.User(
            id=user.id,
            name=user.name,
            email=user.email
        )
```

**Client Streaming:**
```python
def CreateUsers(request_iterator, context):
    created_users = []
    
    for create_request in request_iterator:
        user = db.user.create(
            name=create_request.name,
            email=create_request.email
        )
        created_users.append(user)
    
    return user_pb2.CreateUsersResponse(
        users=created_users,
        count=len(created_users)
    )
```

**Bidirectional Streaming:**
```python
def Chat(request_iterator, context):
    for message in request_iterator:
        # Process message
        response = process_message(message)
        
        # Send response
        yield response
```

## Implementation Patterns

### Server Implementation (Python)

**Basic Server:**
```python
import grpc
from concurrent import futures
import user_pb2
import user_pb2_grpc

class UserService(user_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        user = db.user.get_by_id(request.id)
        if not user:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('User not found')
            return user_pb2.User()
        
        return user_pb2.User(
            id=user.id,
            name=user.name,
            email=user.email
        )
    
    def ListUsers(self, request, context):
        users = db.user.list(
            page=request.page,
            limit=request.limit,
            filter=request.filter
        )
        
        return user_pb2.ListUsersResponse(
            users=[to_proto(u) for u in users],
            total=len(users),
            page=request.page
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(
        UserService(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()
```

### Client Implementation (Python)

**Basic Client:**
```python
import grpc
import user_pb2
import user_pb2_grpc

def get_user(user_id):
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
        request = user_pb2.GetUserRequest(id=user_id)
        
        try:
            response = stub.GetUser(request, timeout=10)
            return response
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                print(f"User {user_id} not found")
            raise
```

### Server Implementation (Node.js)

```javascript
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');

const packageDefinition = protoLoader.loadSync('user.proto');
const userProto = grpc.loadPackageDefinition(packageDefinition).user;

const server = new grpc.Server();

server.addService(userProto.UserService.service, {
  getUser: (call, callback) => {
    const user = db.user.getById(call.request.id);
    if (!user) {
      callback({
        code: grpc.status.NOT_FOUND,
        message: 'User not found'
      });
      return;
    }
    callback(null, user);
  },
  
  listUsers: (call) => {
    const users = db.user.list(call.request);
    users.forEach(user => call.write(user));
    call.end();
  }
});

server.bindAsync('0.0.0.0:50051', grpc.ServerCredentials.createInsecure(), () => {
  server.start();
});
```

## Security

### TLS/SSL

**Server:**
```python
# Load credentials
with open('server.key', 'rb') as f:
    private_key = f.read()
with open('server.crt', 'rb') as f:
    certificate_chain = f.read()

server_credentials = grpc.ssl_server_credentials(
    [(private_key, certificate_chain)]
)

server.add_secure_port('[::]:50051', server_credentials)
```

**Client:**
```python
# Load credentials
with open('ca.crt', 'rb') as f:
    root_certificates = f.read()

credentials = grpc.ssl_channel_credentials(root_certificates)
channel = grpc.secure_channel('myserver:50051', credentials)
```

### Authentication

**Token-Based Auth:**
```python
def authenticate_client(context):
    metadata = context.invocation_metadata()
    for key, value in metadata:
        if key == 'authorization':
            token = value.replace('Bearer ', '')
            return verify_token(token)
    return None

class UserService(user_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        user = authenticate_client(context)
        if not user:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details('Invalid token')
            return user_pb2.User()
        # Continue with request
```

## Performance Optimization

### Connection Pooling

**Reuse Channels:**
```python
class GRPCClient:
    def __init__(self, address):
        self.channel = grpc.secure_channel(
            address,
            grpc.ssl_channel_credentials()
        )
        self.stub = user_pb2_grpc.UserServiceStub(self.channel)
    
    def get_user(self, user_id):
        return self.stub.GetUser(
            user_pb2.GetUserRequest(id=user_id)
        )
    
    def close(self):
        self.channel.close()

# Reuse client instance
client = GRPCClient('myserver:50051')
```

### Compression

**Enable Compression:**
```python
channel = grpc.insecure_channel(
    'localhost:50051',
    options=[
        ('grpc.default_compression_algorithm', grpc.Compression.Gzip)
    ]
)
```

### Timeouts

**Set Timeouts:**
```python
response = stub.GetUser(request, timeout=5.0)  # 5 seconds
```

### Keepalive

**Keep Connections Alive:**
```python
channel = grpc.insecure_channel(
    'localhost:50051',
    options=[
        ('grpc.keepalive_time_ms', 30000),
        ('grpc.keepalive_timeout_ms', 5000),
        ('grpc.keepalive_permit_without_calls', True),
        ('grpc.http2.max_pings_without_data', 0),
    ]
)
```

## Interceptors

### Server Interceptor

**Logging:**
```python
class LoggingInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        print(f"Calling: {handler_call_details.method}")
        start_time = time.time()
        
        def logging_wrapper(behavior, request_streaming, response_streaming):
            def new_behavior(request_or_iterator, servicer_context):
                response = behavior(request_or_iterator, servicer_context)
                duration = time.time() - start_time
                print(f"Completed in {duration:.2f}s")
                return response
            return new_behavior
        
        return continuation(handler_call_details).replace(
            unary_unary=logging_wrapper
        )
```

### Client Interceptor

**Retry:**
```python
class RetryInterceptor(grpc.UnaryUnaryClientInterceptor):
    def intercept_unary_unary(self, continuation, client_call_details, request):
        for attempt in range(3):
            try:
                return continuation(client_call_details, request)
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.UNAVAILABLE and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise
```

## Best Practices Summary

1. **Follow naming conventions:** Service/RPC PascalCase, fields snake_case
2. **Never reuse field numbers:** Mark deprecated as reserved
3. **Version carefully:** Use package versioning
4. **Handle errors properly:** Use standard status codes
5. **Use streaming appropriately:** For large datasets or real-time
6. **Secure connections:** Use TLS/SSL
7. **Authenticate requests:** Token-based or mTLS
8. **Optimize performance:** Connection pooling, compression
9. **Set timeouts:** Prevent hanging requests
10. **Use interceptors:** For cross-cutting concerns

