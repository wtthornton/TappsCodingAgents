# Context7 Research Recommendations

> **Status Note (2025-12-11):** This file is a historical snapshot.  
> **Canonical status:** See `implementation/IMPLEMENTATION_STATUS.md`.

**Date**: December 2025  
**Research Focus**: Resolving timeout issues with large file refactoring  
**Sources**: Context7 documentation for Ollama and httpx

## Executive Summary

Based on Context7 research, the timeout issues can be resolved by:
1. **Implementing streaming** for Ollama requests (recommended for large files)
2. **Configuring granular httpx timeouts** (connect, read, write, pool)
3. **Using chunked processing** for very large files
4. **Implementing progress tracking** with streaming responses

## Key Findings from Context7

### 1. Ollama Streaming Support

**Finding**: Ollama supports streaming by default, which is **better for long generations** and provides:
- Real-time response generation
- Lower perceived latency
- Better handling of lengthy outputs
- Progressive response accumulation

**Current Implementation Issue**: 
- We're using `"stream": False` which forces a single response
- This causes timeouts on large files because we wait for the entire response

**Recommendation**: 
```python
# Enable streaming for large files
{
    "model": model,
    "prompt": prompt,
    "stream": True  # Enable streaming
}
```

### 2. httpx Timeout Configuration

**Finding**: httpx supports granular timeout configuration:
- `connect`: Time to establish connection (default: 5s)
- `read`: Time to read response data (default: 5s) 
- `write`: Time to send request data (default: 5s)
- `pool`: Time to acquire connection from pool (default: 5s)

**Current Implementation Issue**:
- Using a single timeout value
- Not configuring read timeout appropriately for long responses
- Not handling different timeout types separately

**Recommendation**:
```python
from httpx import Timeout

timeout = Timeout(
    connect=10.0,   # 10s to establish connection
    read=600.0,    # 10 minutes to read response (for large files)
    write=30.0,    # 30s to send request
    pool=10.0      # 10s to acquire connection
)
```

### 3. Streaming Response Handling

**Finding**: Streaming responses return newline-delimited JSON (ndjson):
- Each line is a partial response token
- `done: false` indicates more data coming
- `done: true` indicates completion

**Recommendation**: Implement streaming response handler:
```python
async def _ollama_generate_streaming(self, prompt: str, model: str, **kwargs):
    """Generate using Ollama with streaming"""
    timeout = Timeout(connect=10.0, read=600.0, write=30.0, pool=10.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream(
            "POST",
            f"{self.ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": True  # Enable streaming
            }
        ) as response:
            response.raise_for_status()
            
            accumulated_response = ""
            async for line in response.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    accumulated_response += chunk.get("response", "")
                    if chunk.get("done", False):
                        break
            
            return accumulated_response
```

## Recommended Implementation Plan

### Phase 1: Enable Streaming (High Priority)

**File**: `tapps_agents/core/mal.py`

**Changes**:
1. Add `stream` parameter to `generate()` method
2. Implement `_ollama_generate_streaming()` method
3. Use streaming by default for large prompts (>5000 chars)
4. Fall back to non-streaming for small prompts

**Benefits**:
- ✅ No more timeouts on large files
- ✅ Real-time progress feedback
- ✅ Better user experience

### Phase 2: Improve Timeout Configuration

**File**: `tapps_agents/core/mal.py`

**Changes**:
1. Replace single timeout with `httpx.Timeout` object
2. Configure granular timeouts:
   - `connect`: 10s
   - `read`: 600s (10 min) for large files
   - `write`: 30s
   - `pool`: 10s
3. Make timeouts configurable via `MALConfig`

**Benefits**:
- ✅ Better timeout handling
- ✅ Configurable per use case
- ✅ Prevents premature timeouts

### Phase 3: Add Progress Tracking (Optional)

**File**: `tapps_agents/core/mal.py`

**Changes**:
1. Add optional progress callback
2. Emit progress events during streaming
3. Allow agents to track refactoring progress

**Benefits**:
- ✅ User feedback during long operations
- ✅ Better UX for large file processing

## Code Changes Required

### 1. Update MALConfig

```python
# tapps_agents/core/config.py
class MALConfig(BaseModel):
    # ... existing fields ...
    
    # Timeout configuration
    connect_timeout: float = Field(default=10.0, description="Connection timeout")
    read_timeout: float = Field(default=60.0, description="Read timeout")
    write_timeout: float = Field(default=30.0, description="Write timeout")
    pool_timeout: float = Field(default=10.0, description="Pool timeout")
    
    # Streaming configuration
    use_streaming: bool = Field(default=True, description="Use streaming for large prompts")
    streaming_threshold: int = Field(default=5000, description="Prompt length to enable streaming")
```

### 2. Update MAL._ollama_generate()

```python
# tapps_agents/core/mal.py
async def _ollama_generate(self, prompt: str, model: str, **kwargs) -> str:
    """Generate using Ollama with streaming support"""
    use_streaming = kwargs.get("stream", None)
    if use_streaming is None:
        # Auto-detect: use streaming for large prompts
        use_streaming = len(prompt) > self.config.streaming_threshold
    
    if use_streaming:
        return await self._ollama_generate_streaming(prompt, model, **kwargs)
    else:
        return await self._ollama_generate_non_streaming(prompt, model, **kwargs)
```

### 3. Implement Streaming Method

```python
async def _ollama_generate_streaming(self, prompt: str, model: str, **kwargs) -> str:
    """Generate using Ollama with streaming"""
    from httpx import Timeout
    
    timeout = Timeout(
        connect=self.config.connect_timeout,
        read=self.config.read_timeout,
        write=self.config.write_timeout,
        pool=self.config.pool_timeout
    )
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream(
            "POST",
            f"{self.ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": True
            }
        ) as response:
            response.raise_for_status()
            
            accumulated_response = ""
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        chunk = json.loads(line)
                        accumulated_response += chunk.get("response", "")
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue  # Skip invalid JSON lines
            
            return accumulated_response
```

## Testing Recommendations

1. **Test with small files** (< 100 lines) - should work with non-streaming
2. **Test with medium files** (100-500 lines) - should auto-enable streaming
3. **Test with large files** (500+ lines) - should use streaming with progress
4. **Test timeout handling** - verify timeouts work correctly
5. **Test error recovery** - ensure errors are handled gracefully

## Expected Outcomes

After implementing these changes:

✅ **No more timeouts** on large file refactoring  
✅ **Faster perceived response** with streaming  
✅ **Better error messages** with granular timeout handling  
✅ **Configurable timeouts** per use case  
✅ **Progress tracking** for long operations  

## Migration Path

1. **Week 1**: Implement streaming support (Phase 1)
2. **Week 2**: Improve timeout configuration (Phase 2)
3. **Week 3**: Add progress tracking (Phase 3, optional)
4. **Week 4**: Testing and refinement

## Alternative: Chunked Processing

If streaming doesn't fully solve the issue, consider chunked processing:

1. Split large files into logical sections
2. Refactor each section separately
3. Combine results
4. This reduces prompt size per request

## References

- **Ollama Streaming Docs**: https://github.com/ollama/ollama/blob/main/docs/api/streaming.mdx
- **httpx Timeout Docs**: https://github.com/encode/httpx/blob/master/docs/advanced/timeouts.md
- **Context7 Ollama Library**: `/ollama/ollama` (Benchmark Score: 94.1)
- **Context7 httpx Library**: `/encode/httpx` (Benchmark Score: 91.8)

---

**Next Step**: Review these recommendations and approve implementation approach.

