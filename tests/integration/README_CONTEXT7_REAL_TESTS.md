# Context7 Real Integration Tests

## Overview

These tests verify that the MCP Context7 integration **actually calls the real Context7 API**. Unlike unit tests that use mocks, these tests make **real HTTP requests** to Context7 API endpoints.

## Requirements

To run these tests, you need:

1. **CONTEXT7_API_KEY** environment variable set
   ```bash
   # Linux/macOS
   export CONTEXT7_API_KEY="your-api-key-here"
   
   # Windows PowerShell
   $env:CONTEXT7_API_KEY="your-api-key-here"
   ```

2. **Context7 API accessible** (either directly or via MCP server)
   - The tests attempt to call `https://api.context7.com/v1/resolve` and `https://api.context7.com/v1/docs/{id}`
   - If you're using a different endpoint, set `CONTEXT7_API_URL` environment variable

## Running the Tests

### Run all Context7 real integration tests:
```bash
pytest tests/integration/test_context7_real.py -v
```

### Run with marker:
```bash
pytest -m requires_context7 -v
```

### Skip if API key not available (automatic):
Tests are automatically skipped if `CONTEXT7_API_KEY` is not set.

## What These Tests Verify

### 1. **Real API Client Functions** (`TestContext7MCPReal`)
- Tests that client functions make actual HTTP calls to Context7 API
- Verifies `resolve_library_id` calls real API endpoint
- Verifies `get_library_docs` calls real API endpoint

### 2. **MCP Gateway Integration** (`TestContext7MCPGatewayReal`)
- Tests full flow: **MCP Gateway → Context7 Server → Real API**
- Verifies that `call_tool()` actually triggers real API calls
- Ensures the MCP integration is not just mocked

### 3. **KB Lookup with Real API** (`TestContext7LookupReal`)
- Tests that `KBLookup.lookup()` can trigger real API calls when cache misses
- Verifies the KB-first workflow with real API fallback

## Test Behavior

### If API is Available:
- Tests make real HTTP requests
- Verify actual API responses
- Test full integration flow

### If API is Unavailable:
- Tests handle errors gracefully
- Verify that errors are properly propagated
- Key is that **real API calls were attempted** (not mocked)

## Important Notes

1. **These are REAL API calls** - They will consume API quota if you have one
2. **Network required** - Tests need internet connection to reach Context7 API
3. **May be slow** - Real HTTP requests take time (tests have 30s timeout)
4. **API endpoints** - Tests use default endpoints, adjust via `CONTEXT7_API_URL` if needed

## Architecture Verification

These tests verify the architecture documented in `CONTEXT7_INTEGRATION_ARCHITECTURE.md`:

```
MCP Gateway
    ↓
Context7MCPServer
    ↓
Client Functions (resolve_library_client, get_docs_client)
    ↓
Real HTTP Requests to Context7 API
```

The tests ensure that:
- ✅ MCP Gateway calls Context7 Server tools
- ✅ Context7 Server calls client functions
- ✅ Client functions make real HTTP requests
- ✅ Real API responses are returned through the chain

## Troubleshooting

### Tests are skipped:
- Check that `CONTEXT7_API_KEY` is set: `echo $CONTEXT7_API_KEY` (Linux/macOS) or `echo $env:CONTEXT7_API_KEY` (Windows)

### Tests fail with connection errors:
- Context7 API endpoint may be different
- Set `CONTEXT7_API_URL` to your actual endpoint
- Check network connectivity

### Tests fail with authentication errors:
- Verify API key is correct
- Check API key permissions

