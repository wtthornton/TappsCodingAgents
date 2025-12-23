# OpenVINO Patterns

## Overview

OpenVINO (Open Visual Inference & Neural network Optimization) is Intel's toolkit for optimizing AI inference. This guide covers OpenVINO patterns for HomeIQ's device intelligence and similar edge AI applications.

## Core Concepts

### Model Optimization

**IR (Intermediate Representation):**
- Convert models to OpenVINO IR format
- Optimized for CPU inference
- Reduced model size

**Supported Frameworks:**
- TensorFlow
- PyTorch
- ONNX
- Keras

## Basic Patterns

### Pattern 1: Model Conversion

```python
from openvino.tools import mo

# Convert TensorFlow model
mo.convert_model(
    saved_model_dir="model/saved_model",
    output_dir="model/ir",
    model_name="device_intelligence"
)

# Convert PyTorch model
mo.convert_model(
    model_path="model/model.pth",
    output_dir="model/ir",
    model_name="device_intelligence"
)
```

### Pattern 2: Model Loading and Inference

```python
from openvino.runtime import Core

# Initialize OpenVINO Core
core = Core()

# Load model
model = core.read_model("model/ir/device_intelligence.xml")
compiled_model = core.compile_model(model, "CPU")

# Get input/output info
input_layer = compiled_model.input(0)
output_layer = compiled_model.output(0)

# Run inference
import numpy as np
input_data = np.array([...])  # Your input data
result = compiled_model([input_data])[output_layer]
```

### Pattern 3: Async Inference

```python
from openvino.runtime import AsyncInferQueue

# Create async inference queue
infer_queue = AsyncInferQueue(compiled_model, num_requests=4)

# Define callback
def callback(request, userdata):
    result = request.get_output_tensor().data
    # Process result
    pass

infer_queue.set_callback(callback)

# Submit inference requests
for input_data in input_batch:
    infer_queue.start_async({input_layer.any_name: input_data})

# Wait for all requests
infer_queue.wait_all()
```

## Optimization Patterns

### Pattern 1: CPU Optimization

```python
from openvino.runtime import Core

core = Core()

# Set CPU optimization
core.set_property("CPU", {
    "CPU_THREADS_NUM": "4",
    "CPU_BIND_THREAD": "YES"
})

# Load and compile model
model = core.read_model("model.xml")
compiled_model = core.compile_model(model, "CPU")
```

### Pattern 2: Model Quantization

```python
from openvino.tools import mo
from openvino.tools.pot import DataLoader, Metric, Pipeline, create_pipeline

# Quantize model for INT8
pipeline = create_pipeline([], "DefaultQuantization")
quantized_model = pipeline.apply(model, dataset)
```

### Pattern 3: Batch Processing

```python
# Process multiple inputs in batch
batch_size = 8
input_batch = np.array([...])  # Shape: (batch_size, ...)

results = []
for i in range(0, len(input_batch), batch_size):
    batch = input_batch[i:i+batch_size]
    result = compiled_model([batch])[output_layer]
    results.append(result)
```

## HomeIQ-Specific Patterns

### Pattern 1: Device Intelligence Inference

```python
from openvino.runtime import Core
import numpy as np

class DeviceIntelligenceModel:
    def __init__(self, model_path: str):
        self.core = Core()
        self.model = self.core.read_model(model_path)
        self.compiled_model = self.core.compile_model(self.model, "CPU")
        self.input_layer = self.compiled_model.input(0)
        self.output_layer = self.compiled_model.output(0)
    
    def predict(self, sensor_data: np.ndarray) -> dict:
        """Predict device behavior from sensor data."""
        # Preprocess sensor data
        input_data = self.preprocess(sensor_data)
        
        # Run inference
        result = self.compiled_model([input_data])[self.output_layer]
        
        # Postprocess result
        prediction = self.postprocess(result)
        return prediction
    
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Preprocess input data."""
        # Normalize, reshape, etc.
        return data
    
    def postprocess(self, result: np.ndarray) -> dict:
        """Postprocess output data."""
        # Convert to prediction format
        return {
            "prediction": result.tolist(),
            "confidence": float(np.max(result))
        }
```

### Pattern 2: Real-Time Inference

```python
import asyncio
from openvino.runtime import AsyncInferQueue

class RealTimeInference:
    def __init__(self, model_path: str):
        self.core = Core()
        self.model = self.core.read_model(model_path)
        self.compiled_model = self.core.compile_model(self.model, "CPU")
        self.infer_queue = AsyncInferQueue(self.compiled_model, num_requests=4)
        self.infer_queue.set_callback(self.callback)
        self.results = []
    
    def callback(self, request, userdata):
        """Callback for async inference."""
        result = request.get_output_tensor().data
        self.results.append(result)
    
    async def process_stream(self, data_stream):
        """Process data stream with async inference."""
        for data in data_stream:
            input_data = self.preprocess(data)
            self.infer_queue.start_async({
                self.compiled_model.input(0).any_name: input_data
            })
            await asyncio.sleep(0.01)  # Small delay
        
        # Wait for all requests
        self.infer_queue.wait_all()
        return self.results
```

## Best Practices

### 1. Use Appropriate Precision

- **FP32:** High accuracy, slower
- **FP16:** Good balance
- **INT8:** Fastest, may reduce accuracy

### 2. Optimize Input Shape

```python
# Reshape model for optimal batch size
model.reshape({input_layer.any_name: [1, 3, 224, 224]})
```

### 3. Cache Compiled Models

```python
# Cache compiled model for reuse
compiled_model = core.compile_model(model, "CPU")
# Reuse compiled_model for multiple inferences
```

### 4. Use Async Inference for Throughput

```python
# Use async inference queue for better throughput
infer_queue = AsyncInferQueue(compiled_model, num_requests=4)
```

### 5. Monitor Performance

```python
# Enable performance counters
compiled_model = core.compile_model(
    model,
    "CPU",
    {"PERF_COUNT": "YES"}
)

# Get performance metrics
perf_counts = compiled_model.get_property("PERF_COUNT")
```

## References

- [OpenVINO Documentation](https://docs.openvino.ai/)
- [OpenVINO Python API](https://docs.openvino.ai/latest/api/ie_python_api/_autosummary/openvino.runtime.html)
- [Model Optimizer](https://docs.openvino.ai/latest/openvino_docs_MO_DG_Deep_Learning_Model_Optimizer_DevGuide.html)

