# Context7 Usage Examples

This document provides practical examples of using Context7 integration in TappsCodingAgents.

## Example 1: Basic CLI Lookup

### Scenario
You're implementing a FastAPI endpoint and need current routing documentation.

### Command
```bash
python -m tapps_agents.cli reviewer docs fastapi routing
```

### Expected Output
```
FastAPI Routing Documentation
=============================

## App Router
The App Router uses a file-system based routing mechanism...

### Dynamic Routes
// Example: app/blog/[slug]/page.tsx
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

### Route Groups
// Example: app/(marketing)/about/page.tsx
...
```

## Example 2: Cursor Chat Integration

### Scenario
You're reviewing code and want to check if FastAPI patterns are current.

### In Cursor Chat
```cursor
@reviewer *docs fastapi dependency-injection
```

### What Happens
1. Reviewer agent queries Context7 for FastAPI dependency injection patterns
2. Compares your code against current best practices
3. Provides feedback with Context7 documentation references

## Example 3: Python API - Library Detection

### Scenario
You want to programmatically detect libraries in code and fetch their documentation.

### Code
```python
from pathlib import Path
from tapps_agents.core.config import ProjectConfig
from tapps_agents.context7.agent_integration import Context7AgentHelper
from tapps_agents.context7.library_detector import LibraryDetector

# Initialize
config = ProjectConfig.load()
helper = Context7AgentHelper(config=config, project_root=Path.cwd())

# Detect libraries in code
detector = LibraryDetector()
code = """
from fastapi import FastAPI
import pytest
from pydantic import BaseModel
"""

libraries = detector.detect_libraries(code)
print(f"Detected libraries: {libraries}")
# Output: ['fastapi', 'pytest', 'pydantic']

# Fetch documentation for each
for lib in libraries:
    result = await helper.lookup_docs(library=lib)
    if result.success:
        print(f"{lib}: {len(result.content)} chars from {result.source}")
```

## Example 4: Error Message Library Detection

### Scenario
An error message mentions a library, and you want to get documentation for it.

### Code
```python
from tapps_agents.context7.library_detector import LibraryDetector

error_message = """
ImportError: No module named 'pydantic'
  File "app.py", line 5, in <module>
    from pydantic import BaseModel
"""

detector = LibraryDetector()
detected = detector.detect_from_error(error_message)
print(f"Detected from error: {detected}")
# Output: ['pydantic']

# Now fetch documentation
result = await helper.lookup_docs(library="pydantic", topic="installation")
```

## Example 5: Cache-First Lookup

### Scenario
You want to check cache before querying Context7 API.

### Code
```python
from tapps_agents.context7.lookup import KBLookup
from tapps_agents.context7.kb_cache import KBCache

# Perform lookup (automatically uses cache first)
result = await lookup.lookup(
    library="pytest",
    topic="fixtures"
)

print(f"Source: {result.source}")  # "cache" or "api"
print(f"Response time: {result.response_time_ms}ms")

if result.source == "cache":
    print("✅ Served from cache (fast!)")
else:
    print("⚠️  Fetched from API (will be cached for next time)")
```

## Example 6: Fuzzy Topic Matching

### Scenario
You query for "routing" but cache has "routes" - fuzzy matching finds it.

### Code
```python
# Cache has "routes" topic
# Query for "routing"
result = await lookup.lookup(
    library="fastapi",
    topic="routing"  # Not exact match
)

if result.fuzzy_score and result.fuzzy_score > 0.7:
    print(f"✅ Fuzzy matched: {result.matched_topic} (score: {result.fuzzy_score})")
    print(f"Content: {result.content[:100]}...")
```

## Example 7: Batch Library Documentation

### Scenario
You want to pre-fetch documentation for multiple libraries.

### Code
```python
libraries = ["fastapi", "pytest", "pydantic", "sqlalchemy"]

for lib in libraries:
    result = await helper.lookup_docs(library=lib)
    if result.success:
        print(f"✅ {lib}: Cached")
    else:
        print(f"❌ {lib}: {result.error}")
```

## Example 8: Agent Automatic Usage

### Scenario
Reviewer agent automatically uses Context7 when reviewing code.

### Code Being Reviewed
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"id": user_id}
```

### What Reviewer Agent Does
1. Detects `fastapi` import
2. Automatically queries Context7 for FastAPI best practices
3. Compares code against current patterns
4. Provides feedback:

```
Review Feedback:
- ✅ Uses type hints correctly
- ⚠️  Consider using async/await for better performance (FastAPI best practice)
- ✅ Route parameter naming follows conventions
```

## Example 9: Topic-Specific Query

### Scenario
You need specific documentation on a topic.

### Command
```bash
python -m tapps_agents.cli reviewer docs fastapi dependency-injection
```

### What Happens
1. Resolves "fastapi" to `/fastapi/fastapi`
2. Queries Context7 for "dependency-injection" topic
3. Returns relevant documentation and examples
4. Caches result for future use

## Example 10: Cache Analytics

### Scenario
You want to see cache performance metrics.

### Code
```python
from tapps_agents.context7.analytics import Analytics
from tapps_agents.context7.cache_structure import CacheStructure

cache_root = Path(".tapps-agents/kb/context7-cache")
cache_structure = CacheStructure(cache_root)
metadata_manager = MetadataManager(cache_structure)

analytics = Analytics(cache_structure, metadata_manager)
stats = analytics.get_cache_stats()

print(f"Cache hit rate: {stats['hit_rate']:.1%}")
print(f"Total queries: {stats['total_queries']}")
print(f"Cache hits: {stats['cache_hits']}")
print(f"API calls: {stats['api_calls']}")
print(f"Token savings: {stats['token_savings']:.0f} tokens")
```

## Example 11: Error Handling

### Scenario
Context7 is unavailable, but you want graceful degradation.

### Code
```python
try:
    result = await helper.lookup_docs(library="fastapi", topic="routing")
    if result.success:
        # Use Context7 documentation
        use_docs(result.content)
    else:
        # Fallback to local docs or skip
        logger.warning(f"Context7 unavailable: {result.error}")
        use_local_docs()
except Exception as e:
    # Graceful degradation
    logger.error(f"Context7 error: {e}")
    use_local_docs()
```

## Example 12: Pre-populate Cache

### Scenario
You want to warm up the cache with common libraries.

### Command
```bash
python -m tapps_agents.cli context7 prepopulate --libraries fastapi pytest pydantic
```

### What Happens
1. Queries Context7 for each library
2. Caches general documentation
3. Pre-fetches common topics
4. Reports cache status

## Example 13: Refresh Stale Cache

### Scenario
You want to refresh documentation that might be outdated.

### Code
```python
from tapps_agents.context7.refresh_queue import RefreshQueue
from tapps_agents.context7.staleness_policies import StalenessPolicyManager

policy_manager = StalenessPolicyManager()
refresh_queue = RefreshQueue(
    cache_structure.refresh_queue_file,
    policy_manager
)

# Add library to refresh queue
refresh_queue.enqueue("fastapi", priority="high")

# Process queue
await refresh_queue.process(max_items=5)
```

## Example 14: Multi-Agent Context7 Usage

### Scenario
Multiple agents use Context7 in a workflow.

### Workflow
```python
# 1. Planner agent uses Context7 to understand library requirements
plan = planner.plan("Create FastAPI app with Pydantic models")
# Automatically queries Context7 for FastAPI and Pydantic patterns

# 2. Architect agent uses Context7 for architecture patterns
architecture = architect.design("FastAPI microservice architecture")
# Queries Context7 for FastAPI best practices

# 3. Implementer agent uses Context7 for code generation
code = implementer.implement("FastAPI endpoint", "src/api.py")
# Uses Context7 documentation for current patterns

# 4. Reviewer agent uses Context7 for code review
review = reviewer.review("src/api.py")
# Compares code against Context7 best practices
```

## Best Practices from Examples

1. **Use topic-specific queries** for faster, more relevant results
2. **Pre-populate cache** with common libraries during setup
3. **Monitor cache hit rate** to optimize performance
4. **Handle errors gracefully** with fallback strategies
5. **Use fuzzy matching** for flexible topic queries
6. **Batch operations** when fetching multiple libraries
7. **Refresh strategically** based on staleness policies
