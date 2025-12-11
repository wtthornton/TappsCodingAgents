# OpenTelemetry Standards and Instrumentation

## Overview

OpenTelemetry is a collection of APIs, SDKs, and tools used to instrument, generate, collect, and export telemetry data (metrics, logs, and traces) for analysis to understand software performance and behavior.

## Key Concepts

### OpenTelemetry Components

**APIs:**
- Language-specific APIs for instrumentation
- Vendor-neutral interface
- Standard abstractions

**SDKs:**
- Implementation of APIs
- Configuration and setup
- Resource detection
- Exporters

**Collectors:**
- Receives, processes, and exports telemetry data
- Vendor-neutral
- Flexible routing and processing

**Instrumentation Libraries:**
- Auto-instrumentation for common frameworks
- Manual instrumentation helpers
- Language-specific implementations

## Architecture

### Data Flow

```
Application → OpenTelemetry SDK → OTLP Exporter → Collector → Backend
```

**Components:**
1. **Instrumentation:** Code in application
2. **SDK:** Collects and processes data
3. **Exporter:** Sends to collector or backend
4. **Collector:** Receives, processes, routes data
5. **Backend:** Storage and analysis (Jaeger, Prometheus, etc.)

### Signals

**Traces:**
- Distributed tracing
- Request flow through services
- Span-based model

**Metrics:**
- Time-series measurements
- Aggregated data points
- Counter, gauge, histogram

**Logs:**
- Event records
- Structured logging
- Correlation with traces

## Language Support

### Python

**Installation:**
```bash
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-instrumentation
pip install opentelemetry-exporter-otlp
```

**Basic Setup:**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Set up tracer provider
trace.set_tracer_provider(TracerProvider())

# Add exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://collector:4317")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Get tracer
tracer = trace.get_tracer(__name__)
```

**Instrumentation:**
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("operation")
def my_function():
    span = trace.get_current_span()
    span.set_attribute("custom.attribute", "value")
    # Your code
    pass
```

### JavaScript/Node.js

**Installation:**
```bash
npm install @opentelemetry/api
npm install @opentelemetry/sdk-node
npm install @opentelemetry/exporter-otlp-http
```

**Setup:**
```javascript
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-otlp-http');
const { Resource } = require('@opentelemetry/resources');

const sdk = new NodeSDK({
  resource: new Resource({
    'service.name': 'my-service',
    'service.version': '1.0.0',
  }),
  traceExporter: new OTLPTraceExporter({
    url: 'http://collector:4318/v1/traces',
  }),
});

sdk.start();
```

### Java

**Dependencies:**
```xml
<dependency>
    <groupId>io.opentelemetry</groupId>
    <artifactId>opentelemetry-api</artifactId>
</dependency>
<dependency>
    <groupId>io.opentelemetry</groupId>
    <artifactId>opentelemetry-sdk</artifactId>
</dependency>
```

**Setup:**
```java
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.trace.Tracer;

OpenTelemetry openTelemetry = OpenTelemetrySdk.builder()
    .setTracerProvider(
        SdkTracerProvider.builder()
            .addSpanProcessor(BatchSpanProcessor.builder(
                OtlpGrpcSpanExporter.builder()
                    .setEndpoint("http://collector:4317")
                    .build())
                .build())
            .build())
    .build();

Tracer tracer = openTelemetry.getTracer("my-service");
```

### Go

**Installation:**
```bash
go get go.opentelemetry.io/otel
go get go.opentelemetry.io/otel/sdk
go get go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc
```

**Setup:**
```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/sdk/trace"
)

exporter, err := otlptracegrpc.New(context.Background(),
    otlptracegrpc.WithEndpoint("collector:4317"),
)
if err != nil {
    log.Fatal(err)
}

tp := trace.NewTracerProvider(
    trace.WithBatcher(exporter),
)
otel.SetTracerProvider(tp)
```

## Automatic Instrumentation

### Python Auto-Instrumentation

**Install Packages:**
```bash
pip install opentelemetry-instrumentation-requests
pip install opentelemetry-instrumentation-flask
pip install opentelemetry-instrumentation-sqlalchemy
```

**Use Auto-Instrumentation:**
```python
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from flask import Flask

# Auto-instrument requests library
RequestsInstrumentor().instrument()

# Auto-instrument Flask
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
```

**Command-Line Instrumentation:**
```bash
opentelemetry-instrument --traces_exporter otlp \
  --service_name my-service \
  python my_app.py
```

### Node.js Auto-Instrumentation

**Install:**
```bash
npm install @opentelemetry/auto-instrumentations-node
```

**Setup:**
```javascript
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');

const sdk = new NodeSDK({
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
```

## Manual Instrumentation

### Creating Spans

**Python:**
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        
        try:
            result = validate_order(order_id)
            span.set_status(trace.Status(trace.StatusCode.OK))
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise
```

### Span Attributes

**Semantic Conventions:**
```python
span.set_attribute("http.method", "GET")
span.set_attribute("http.url", "/api/users")
span.set_attribute("http.status_code", 200)
span.set_attribute("db.system", "postgresql")
span.set_attribute("db.name", "users")
span.set_attribute("db.operation", "SELECT")
span.set_attribute("net.peer.ip", "192.168.1.1")
```

**Custom Attributes:**
```python
span.set_attribute("business.order_id", order_id)
span.set_attribute("business.user_tier", "premium")
span.set_attribute("business.payment_method", "credit_card")
```

### Events

**Add Events to Spans:**
```python
span.add_event("order.validated", {
    "validation_result": "success",
    "items_count": 5
})

span.add_event("payment.processed", {
    "payment_method": "credit_card",
    "amount": 99.99
})
```

## Context Propagation

### W3C Trace Context

**Propagate Across Services:**
```python
from opentelemetry.propagate import inject, extract

# Client: Inject context
headers = {}
inject(headers)
response = requests.get(url, headers=headers)

# Server: Extract context
context = extract(request.headers)
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("handle_request", context=context):
    # Process request
    pass
```

### Baggage

**Propagate Custom Data:**
```python
from opentelemetry import baggage

# Set baggage
ctx = baggage.set_baggage("user.id", "user123")
ctx = baggage.set_baggage("experiment.flag", "true", context=ctx)

# Use baggage
user_id = baggage.get_baggage("user.id", context=ctx)
```

## Metrics

### Counter

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)
counter = meter.create_counter(
    "requests_total",
    description="Total number of requests"
)

counter.add(1, {"method": "GET", "status": "200"})
```

### Gauge

```python
gauge = meter.create_up_down_counter(
    "active_connections",
    description="Number of active connections"
)

gauge.add(1)  # Increment
gauge.add(-1)  # Decrement
```

### Histogram

```python
histogram = meter.create_histogram(
    "request_duration",
    description="Request duration",
    unit="ms"
)

histogram.record(245, {"method": "GET", "endpoint": "/api/users"})
```

## Resource Detection

### Resource Attributes

**Define Service Identity:**
```python
from opentelemetry.sdk.resources import Resource

resource = Resource.create({
    "service.name": "order-service",
    "service.version": "1.2.3",
    "service.namespace": "production",
    "deployment.environment": "prod",
})
```

**Automatic Detection:**
```python
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: "my-service",
    ResourceAttributes.SERVICE_VERSION: "1.0.0",
})
```

## OpenTelemetry Collector

### Configuration

**Receivers:**
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
```

**Processors:**
```yaml
processors:
  batch:
    timeout: 10s
    send_batch_size: 1024
  resource:
    attributes:
      - key: environment
        value: production
        action: upsert
```

**Exporters:**
```yaml
exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  prometheus:
    endpoint: "0.0.0.0:8889"
```

**Service:**
```yaml
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [prometheus]
```

## Best Practices

### 1. Use Semantic Conventions

**Follow Standards:**
- HTTP attributes
- Database attributes
- Messaging attributes
- Resource attributes

### 2. Sample Appropriately

**Head-Based Sampling:**
```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

sampler = TraceIdRatioBased(0.1)  # 10% sampling
tracer_provider = TracerProvider(sampler=sampler)
```

**Tail-Based Sampling:**
- Implement in collector
- Sample based on errors/slow traces

### 3. Minimize Overhead

**Async Export:**
```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor

processor = BatchSpanProcessor(exporter)
```

**Batch Exports:**
- Configure batch size
- Set timeout
- Balance latency and efficiency

### 4. Propagate Context

**Always Propagate:**
- HTTP requests
- Message queues
- RPC calls
- Database operations

### 5. Include Business Context

**Add Business Attributes:**
```python
span.set_attribute("business.user_id", user_id)
span.set_attribute("business.order_id", order_id)
span.set_attribute("business.payment_amount", amount)
```

## Integration with Backends

### Jaeger

**Exporter:**
```python
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
```

### Prometheus

**Metrics Exporter:**
```python
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider

reader = PrometheusMetricReader()
provider = MeterProvider(metric_readers=[reader])
```

### Zipkin

**Exporter:**
```python
from opentelemetry.exporter.zipkin.json import ZipkinExporter

zipkin_exporter = ZipkinExporter(
    endpoint="http://zipkin:9411/api/v2/spans"
)
```

## Summary

OpenTelemetry provides:

1. **Vendor-neutral** instrumentation
2. **Standard APIs** across languages
3. **Automatic instrumentation** for common frameworks
4. **Flexible exporters** to multiple backends
5. **Context propagation** standards
6. **Semantic conventions** for consistency
7. **Collector** for processing and routing
8. **Open standard** for observability

Adopting OpenTelemetry ensures:
- Future-proof instrumentation
- Easy backend switching
- Consistent telemetry
- Standard tooling ecosystem

