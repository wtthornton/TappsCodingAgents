# Serverless Architecture

## Overview

Serverless computing runs code without managing servers. Functions are triggered by events and automatically scale. This guide covers serverless patterns, architectures, and best practices.

## Characteristics

- **Event-Driven:** Functions triggered by events
- **Auto-Scaling:** Scales automatically to zero
- **Pay-Per-Use:** Pay only for execution time
- **No Server Management:** Platform handles infrastructure

## Serverless Platforms

### AWS Lambda

**Function Example:**
```python
import json

def lambda_handler(event, context):
    # Process event
    name = event.get('name', 'World')
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Hello {name}!')
    }
```

**Triggers:**
- API Gateway
- S3 events
- DynamoDB streams
- SQS queues
- EventBridge

### Azure Functions

**HTTP Trigger:**
```python
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get('name')
    return func.HttpResponse(f"Hello {name}!")
```

### Google Cloud Functions

**HTTP Function:**
```python
def hello_world(request):
    name = request.args.get('name', 'World')
    return f'Hello {name}!'
```

## Patterns

### API Backend

**RESTful API:**
```python
def api_handler(event, context):
    method = event['httpMethod']
    path = event['path']
    
    if method == 'GET' and path == '/users':
        return get_users()
    elif method == 'POST' and path == '/users':
        return create_user(event['body'])
    
    return {'statusCode': 404}
```

### Event Processing

**Process Events:**
```python
def process_event(event, context):
    for record in event['Records']:
        # Process S3 event, SQS message, etc.
        process_record(record)
```

### Scheduled Tasks

**Cron Jobs:**
```yaml
# AWS EventBridge rule
schedule_expression: rate(5 minutes)
```

### Microservices

**Service Decomposition:**
- Each function = microservice
- Independent deployment
- Event-driven communication

## Best Practices

### 1. Stateless Functions

**No State Storage:**
- Use external storage (database, cache)
- Pass state via parameters
- Don't rely on memory

### 2. Cold Start Optimization

**Reduce Cold Starts:**
- Minimize dependencies
- Use connection pooling
- Keep functions warm (if needed)
- Provisioned concurrency (if required)

### 3. Error Handling

**Handle Errors Gracefully:**
```python
def lambda_handler(event, context):
    try:
        result = process(event)
        return {'statusCode': 200, 'body': json.dumps(result)}
    except Exception as e:
        # Log error
        logger.error(str(e))
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
```

### 4. Timeout Management

**Set Appropriate Timeouts:**
- Short timeouts for API endpoints (< 30s)
- Longer for batch processing
- Consider step functions for long-running

### 5. Resource Limits

**Configure Memory:**
- More memory = more CPU
- Balance cost and performance
- Monitor and optimize

### 6. Security

**Least Privilege:**
- Minimal IAM permissions
- Use VPC for network isolation
- Encrypt sensitive data
- Validate inputs

### 7. Monitoring

**Logging and Metrics:**
- Structured logging
- CloudWatch metrics
- Distributed tracing
- Error tracking

## Limitations

### Execution Time

- Platform limits (e.g., 15 min for Lambda)
- Use step functions for longer tasks

### Cold Starts

- First invocation slower
- Keep functions warm if needed
- Use provisioned concurrency

### Vendor Lock-In

- Platform-specific APIs
- Consider abstractions
- Multi-cloud strategies

### Debugging

- Limited local debugging
- Use platform tools
- Logging is crucial

## Best Practices Summary

1. **Keep functions small** and focused
2. **Optimize cold starts** with minimal dependencies
3. **Handle errors** gracefully
4. **Set appropriate timeouts** for use case
5. **Use external storage** for state
6. **Implement retries** for transient failures
7. **Monitor** performance and errors
8. **Secure** with least privilege
9. **Test** locally and in cloud
10. **Document** functions and triggers

