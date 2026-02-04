## Summary / TL;DR

- **What:** Enhance this project or feature description.
- **How:** - **Created**: 2026-02-04T06:45:28.612299

---

# Enhanced Prompt: Enhance this project or feature description.

## Metadata
- **Created**: 2026-02-04T06:45:28.612299

## Analysis
- **Intent**: feature
- **Scope**: small
- **Workflow Type**: brownfield
- **Complexity**: low
- **Detected Domains**: None detected
- **Technologies**: Home Assistant, aiofiles, aiohttp, bandit, coverage, httpx, jinja2, mypy, packaging, pip-audit, pip-tools, psutil, pydantic, pytest, pytest-asyncio, pytest-cov, pytest-html, pytest-mock, pytest-rich, pytest-sugar, pytest-timeout, pytest-xdist, pyyaml, radon, rich, ruff, types-pyyaml

### Analysis Details
```
Analyze the following prompt and extract structured information.

Prompt:
Enhance this project or feature description.



Please analyze and extract:
1. Intent (feature, bug-fix, refactor, documentation, testing, etc.)
2. Detected domains (security, user-management, payments, database, api, ui, integration, etc.)
3. Estimated scope (small: 1-2 files, medium: 3-5 files, large: 6+ files)
4. Recommended workflow type (greenfield: new code, brownfield: existing code modification, quick-fix: urgent b...
```

## Requirements
### Functional Requirements
- *No functional requirements extracted yet. This will be populated during requirements gathering stage.*

### Non-Functional Requirements
- *No non-functional requirements extracted yet.*

### Library Best Practices (from Context7)
#### aiofiles
**Source**: cache
**Best Practices Preview**:
```
## Async Standard Streams with aiofiles (Python)

```python
import asyncio
import aiofiles

async def console_operations():
    # Writing to stdout asynchronously
    await aiofiles.stdout.write("Enter your name: ")
    await aiofiles.stdout.flush()

    # Reading from stdin asynchronously
    name = await aiofiles.stdin.readline()
    await aiofiles.stdout.write(f"Hello, {name}")

    # Writing to stderr
    await aiofiles.stderr.write("This is an error message\n")

    # Binary streams
    awa
```

#### aiohttp
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Basic httpx Library Integration in Go

```go
package main

import (
    "fmt"
    "log"
    "github.com/projectdiscovery/goflags"
    "github.com/projectdiscovery/gologger"
    "github.com/projectdiscovery/gologger/levels"
    "github.com/projectdiscovery/httpx/runner"
)

func main() {
    // Increase verbosity (optional)
    gologger.DefaultLogger.SetMaxLevel(levels.LevelVerbose)

    // Configure options
    options := runner.Options{
        Methods:         "GET",
        InputTargetHost:
```

#### bandit
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Bandit Issue Example: Partial Executable Path

```none
>> Issue: Starting a process with a partial executable path
Severity: Low   Confidence: High
```

## Advanced Bandit Usage with Filtering and Context

```bash
bandit examples/*.py -n 3 --severity-level=high
```

## Advanced Bandit Usage with Filtering and Context

```bash
bandit examples/*.py -n 3 -lll
```

## Advanced Bandit Usage with Filtering and Context

```bash
bandit examples/*.py -p ShellInjection
```

## Bandit B112: Example Issu
```

#### coverage
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Development Tools and Linters

```text
mypy
pytest
pytest-cov
black
flake8
isort
autoflake
typer
mathy_pydoc
```

## Example Usage: Build and Initialize Model (Python)

```python
text, X, Y = to_example("14x + 2y - 3x + 7x")
m = build_model(12)
m.initialize([X], m.ops.asarray(Y, dtype="f"))
mY = m.predict([X])
print(mY.shape)
assert mY.shape == (1, 1)
```

## Pinning mathy_core version for stability

```bash
mathy_core>=0.1.37,<0.2.0
```

## MathExpression Methods

```python
MathExpression.ad
```

#### httpx
**Source**: cache
**Best Practices Preview**:
```
## Basic httpx Library Integration in Go

```go
package main

import (
    "fmt"
    "log"
    "github.com/projectdiscovery/goflags"
    "github.com/projectdiscovery/gologger"
    "github.com/projectdiscovery/gologger/levels"
    "github.com/projectdiscovery/httpx/runner"
)

func main() {
    // Increase verbosity (optional)
    gologger.DefaultLogger.SetMaxLevel(levels.LevelVerbose)

    // Configure options
    options := runner.Options{
        Methods:         "GET",
        InputTargetHost:
```

#### jinja2
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Initializing aiohttp-jinja2 with setup function in Python

```python
import jinja2
import aiohttp_jinja2
from aiohttp import web

app = web.Application()
aiohttp_jinja2.setup(
   app,
   loader=jinja2.FileSystemLoader('/path/to/templates/folder'),
)
```

## Importing aiohttp-jinja2 and Jinja2 Libraries Python

```Python
import aiohttp_jinja2
import jinja2
```

## Initializing Jinja2 Environment for aiohttp Application Python

```Python
app = web.Application()
aiohttp_jinja2.setup(app,
    loa
```

#### mypy
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Package Structure with Stub Files and py.typed

```text
setup.py
package_b/
    __init__.py
    lib.py
    lib.pyi
    py.typed

```

## Package Structure with Stub Files and py.typed

```python
from setuptools import setup

setup(
    name="SuperPackageB",
    author="Me",
    version="0.1",
    package_data={"package_b": ["py.typed", "lib.pyi"]},
    packages=["package_b"]
)

```

## Enabling Experimental Features

```APIDOC
## --enable-incomplete-feature

### Description
Enables incomplete
```

#### packaging
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Main Salesforce Packaging API Classes Overview

```APIDOC
Package1Version: Work with 1st generation package versions.
Package: Work with 2nd generation packages.
PackageVersion: Work with 2nd generation package versions.
SubscriberPackageVersion: Work with 2nd generation subscriber package versions.
```

## APIDOC: Create Result ID Cannot Be Empty

```APIDOC
createResultIdCannotBeEmpty:
  Message: The package version create result ID must be defined when checking for completion.
```

## Sales
```

#### pip-audit
**Source**: cache
**Best Practices Preview**:
```
## Apply Linting Reforms

```Bash
make reformat
```

## pip-audit Environment Variables

```APIDOC
pip-audit Environment Variables:

Flag                      | Environment equivalent            | Example
--------------------------|-----------------------------------|-------------------------------------
`--format`                | `PIP_AUDIT_FORMAT`                | `PIP_AUDIT_FORMAT=markdown`
`--vulnerability-service` | `PIP_AUDIT_VULNERABILITY_SERVICE` | `PIP_AUDIT_VULNERABILITY_SERVICE=osv`

```

#### pip-tools
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Fast Local Build

```bash
.\build.cmd Publish -s
```

## Fast Local Build

```bash
.\build.cmd Pack -s
```

## Generate TMSL/BIM File

```bash
pbi-tools.core generate-bim <folder> [transforms]
```

## Convert Power BI Artifacts Offline

```bash
pbi-tools convert <source> [<outPath>] [<modelSerialization>] [<mashupSerialization>] [<settingsFile>] [<updateSettings>] [<modelOnly>] [<overwrite>]
```

## System Parameters Expansion in pbi-tools Manifest

```json
{
  "parameters": {
    "[Version]"
```

#### psutil
**Source**: cache
**Best Practices Preview**:
```
## Combine grep and exp for Pattern Extraction

```PowerShell
"abc def ghi" | grep "(d\w+)" | exp
```

## Use grep Alias for Select-String

```PowerShell
dir | grep
```

## Use exp Alias for Expand-PSUObject

```PowerShell
dir | exp FullName
```

## Use desktop Function for Directory Navigation

```PowerShell
desktop
desktop someotheruser
```

## Preimport.ps1 Loaded Files (PowerShell)

```powershell
internal\scripts\strings.ps1
internal\configurations\validations\*
internal\configurations\*.ps1
```

#### pydantic
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Safe Bare Except Usage

```python
try:
    # Code that might raise an exception
    pass
except Exception as e:
    # Log the exception and traceback
    import traceback
    traceback.print_exc()
    # Or log it using a logging framework
    # logging.exception("An error occurred")

try:
    # Code that might raise an exception
    pass
except Exception as e:
    # Perform cleanup actions
    # ...
    # Re-raise the exception
    raise

# Alternative for cleanup: try...finally
try:
    # Co
```

#### pytest
**Source**: fuzzy_match
**Best Practices Preview**:
```
## pytest-mock mocker.patch Usage

```python
import os

def test_patch_function(mocker):
    # Mock os.remove function
    mock_remove = mocker.patch('os.remove')

    os.remove('/fake/path')

    # Assert it was called with expected arguments
    mock_remove.assert_called_once_with('/fake/path')
    # File still exists - real function never executed

def test_patch_with_return_value(mocker):
    # Mock with specific return value
    mocker.patch('os.listdir', return_value=['file1.txt', 'file2.t
```

#### pytest-asyncio
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Parametrization with Async Tests in pytest

```python
import asyncio
import pytest
import pytest_asyncio

@pytest.mark.asyncio
@pytest.mark.parametrize("value", [1, 2, 3, 4, 5])
async def test_parametrized_async(value):
    await asyncio.sleep(0.01)
    result = await compute(value)
    assert result == value * 2

@pytest.mark.asyncio
@pytest.mark.parametrize("x,y,expected", [
    (1, 2, 3),
    (5, 3, 8),
    (10, -5, 5),
])
async def test_async_addition(x, y, expected):
    result = await a
```

#### pytest-cov
**Source**: fuzzy_match
**Best Practices Preview**:
```
## pytest-mock mocker.patch Usage

```python
import os

def test_patch_function(mocker):
    # Mock os.remove function
    mock_remove = mocker.patch('os.remove')

    os.remove('/fake/path')

    # Assert it was called with expected arguments
    mock_remove.assert_called_once_with('/fake/path')
    # File still exists - real function never executed

def test_patch_with_return_value(mocker):
    # Mock with specific return value
    mocker.patch('os.listdir', return_value=['file1.txt', 'file2.t
```

#### pytest-html
**Source**: fuzzy_match
**Best Practices Preview**:
```
## pytest-mock mocker.patch Usage

```python
import os

def test_patch_function(mocker):
    # Mock os.remove function
    mock_remove = mocker.patch('os.remove')

    os.remove('/fake/path')

    # Assert it was called with expected arguments
    mock_remove.assert_called_once_with('/fake/path')
    # File still exists - real function never executed

def test_patch_with_return_value(mocker):
    # Mock with specific return value
    mocker.patch('os.listdir', return_value=['file1.txt', 'file2.t
```

#### pytest-mock
**Source**: cache
**Best Practices Preview**:
```
## pytest-mock mocker.patch Usage

```python
import os

def test_patch_function(mocker):
    # Mock os.remove function
    mock_remove = mocker.patch('os.remove')

    os.remove('/fake/path')

    # Assert it was called with expected arguments
    mock_remove.assert_called_once_with('/fake/path')
    # File still exists - real function never executed

def test_patch_with_return_value(mocker):
    # Mock with specific return value
    mocker.patch('os.listdir', return_value=['file1.txt', 'file2.t
```

#### pytest-rich
**Source**: fuzzy_match
**Best Practices Preview**:
```
## pytest-mock mocker.patch Usage

```python
import os

def test_patch_function(mocker):
    # Mock os.remove function
    mock_remove = mocker.patch('os.remove')

    os.remove('/fake/path')

    # Assert it was called with expected arguments
    mock_remove.assert_called_once_with('/fake/path')
    # File still exists - real function never executed

def test_patch_with_return_value(mocker):
    # Mock with specific return value
    mocker.patch('os.listdir', return_value=['file1.txt', 'file2.t
```

#### pytest-sugar
**Source**: fuzzy_match
**Best Practices Preview**:
```
## pytest-mock mocker.patch Usage

```python
import os

def test_patch_function(mocker):
    # Mock os.remove function
    mock_remove = mocker.patch('os.remove')

    os.remove('/fake/path')

    # Assert it was called with expected arguments
    mock_remove.assert_called_once_with('/fake/path')
    # File still exists - real function never executed

def test_patch_with_return_value(mocker):
    # Mock with specific return value
    mocker.patch('os.listdir', return_value=['file1.txt', 'file2.t
```

#### pytest-timeout
**Source**: fuzzy_match
**Best Practices Preview**:
```
## pytest-mock mocker.patch Usage

```python
import os

def test_patch_function(mocker):
    # Mock os.remove function
    mock_remove = mocker.patch('os.remove')

    os.remove('/fake/path')

    # Assert it was called with expected arguments
    mock_remove.assert_called_once_with('/fake/path')
    # File still exists - real function never executed

def test_patch_with_return_value(mocker):
    # Mock with specific return value
    mocker.patch('os.listdir', return_value=['file1.txt', 'file2.t
```

#### pytest-xdist
**Source**: fuzzy_match
**Best Practices Preview**:
```
## pytest-mock mocker.patch Usage

```python
import os

def test_patch_function(mocker):
    # Mock os.remove function
    mock_remove = mocker.patch('os.remove')

    os.remove('/fake/path')

    # Assert it was called with expected arguments
    mock_remove.assert_called_once_with('/fake/path')
    # File still exists - real function never executed

def test_patch_with_return_value(mocker):
    # Mock with specific return value
    mocker.patch('os.listdir', return_value=['file1.txt', 'file2.t
```

#### pyyaml
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Streaming YAML Events for Low-Level Processing with PyYAML

```python
import yaml

yaml_document = """
users:
  - name: Alice
    role: admin
  - name: Bob
    role: user
"""

# Scan for tokens
print("Tokens:")
for token in yaml.scan(yaml_document):
    print(f"{token.__class__.__name__}: {token}")

# Parse for events
print("\nEvents:")
for event in yaml.parse(yaml_document):
    print(f"{event.__class__.__name__}: {event}")

# Compose to get representation tree
node = yaml.compose(yaml_docum
```

#### radon
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Develop Components in Isolation with Radon IDE

```javascript
import { preview } from "radon-ide";  
  
preview(<MyComponent param={42} />);  

```

## Install radon-ide Package (YARN)

```bash
yarn add radon-ide
```

## Import and Call Preview Function (JavaScript/TypeScript)

```jsx
import { preview } from "radon-ide";

preview(<MyComponent param={42} />);

```

## Install radon-ide Package (NPM)

```bash
npm i radon-ide
```

## Sample Radon IDE Launch Configuration (launch.json)

```json
{
```

#### rich
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Durum Bildirimi Kullanımı (Python)

```python
from time import sleep
from rich.console import Console

console = Console()
tasks = [f"task {n}" for n in range(1, 11)]

with console.status("[bold green]Working on tasks...") as status:
    while tasks:

```

## Create Virtual Environment with Poetry

```Shell
poetry shell
```

## Create Virtual Environment with Poetry

```Shell
poetry install
```

## Create Style Object and Apply (Python)

```python
from rich.console import Console
from rich.st
```

#### ruff
**Source**: fuzzy_match
**Best Practices Preview**:
```
## Type Context Propagation in Nested Comprehensions in Python

```python
table = [[(x, y) for x in range(3)] for y in range(3)]
reveal_type(table)  # revealed: list[list[tuple[int, int] | Unknown] | Unknown]

table_with_content: list[list[tuple[int, int, str | None]]] = [[(x, y, None) for x in range(3)] for y in range(3)]
reveal_type(table_with_content)  # revealed: list[list[tuple[int, int, str | None]]]
```

## Python Project Structure with pyproject.toml

```text
name = "my_proj"
version = "
```

#### types-pyyaml
**Source**: cache
**Best Practices Preview**:
```
## Streaming YAML Events for Low-Level Processing with PyYAML

```python
import yaml

yaml_document = """
users:
  - name: Alice
    role: admin
  - name: Bob
    role: user
"""

# Scan for tokens
print("Tokens:")
for token in yaml.scan(yaml_document):
    print(f"{token.__class__.__name__}: {token}")

# Parse for events
print("\nEvents:")
for event in yaml.parse(yaml_document):
    print(f"{event.__class__.__name__}: {event}")

# Compose to get representation tree
node = yaml.compose(yaml_docum
```

### API Compatibility Status
- ✅ **aiofiles**: Docs=True, Best Practices=True
- ✅ **aiohttp**: Docs=True, Best Practices=True
- ✅ **bandit**: Docs=True, Best Practices=True
- ✅ **coverage**: Docs=True, Best Practices=True
- ✅ **httpx**: Docs=True, Best Practices=True
- ✅ **jinja2**: Docs=True, Best Practices=True
- ✅ **mypy**: Docs=True, Best Practices=True
- ✅ **packaging**: Docs=True, Best Practices=True
- ✅ **pip-audit**: Docs=True, Best Practices=True
- ✅ **pip-tools**: Docs=True, Best Practices=True
- ✅ **psutil**: Docs=True, Best Practices=True
- ✅ **pydantic**: Docs=True, Best Practices=True
- ✅ **pytest**: Docs=True, Best Practices=True
- ✅ **pytest-asyncio**: Docs=True, Best Practices=True
- ✅ **pytest-cov**: Docs=True, Best Practices=True
- ✅ **pytest-html**: Docs=True, Best Practices=True
- ✅ **pytest-mock**: Docs=True, Best Practices=True
- ✅ **pytest-rich**: Docs=True, Best Practices=True
- ✅ **pytest-sugar**: Docs=True, Best Practices=True
- ✅ **pytest-timeout**: Docs=True, Best Practices=True
- ✅ **pytest-xdist**: Docs=True, Best Practices=True
- ✅ **pyyaml**: Docs=True, Best Practices=True
- ✅ **radon**: Docs=True, Best Practices=True
- ✅ **rich**: Docs=True, Best Practices=True
- ✅ **ruff**: Docs=True, Best Practices=True
- ✅ **types-pyyaml**: Docs=True, Best Practices=True

## Architecture Guidance
*Architecture guidance will be generated during the architecture stage.*

### Library-Specific Architecture Patterns (from Context7)
#### aiofiles
*No specific patterns found for this library.*

#### aiohttp
*No specific patterns found for this library.*

#### bandit
*No specific patterns found for this library.*

#### coverage
*No specific patterns found for this library.*

#### httpx
*No specific patterns found for this library.*

#### jinja2
*No specific patterns found for this library.*

#### mypy
*No specific patterns found for this library.*

#### packaging
*No specific patterns found for this library.*

#### pip-audit
*No specific patterns found for this library.*

#### pip-tools
*No specific patterns found for this library.*

#### psutil
*No specific patterns found for this library.*

#### pydantic
*No specific patterns found for this library.*

#### pytest
*No specific patterns found for this library.*

#### pytest-asyncio
*No specific patterns found for this library.*

#### pytest-cov
*No specific patterns found for this library.*

#### pytest-html
*No specific patterns found for this library.*

#### pytest-mock
*No specific patterns found for this library.*

#### pytest-rich
*No specific patterns found for this library.*

#### pytest-sugar
*No specific patterns found for this library.*

#### pytest-timeout
*No specific patterns found for this library.*

#### pytest-xdist
*No specific patterns found for this library.*

#### pyyaml
*No specific patterns found for this library.*

#### radon
*No specific patterns found for this library.*

#### rich
*No specific patterns found for this library.*

#### ruff
*No specific patterns found for this library.*

#### types-pyyaml
*No specific patterns found for this library.*

### Integration Examples (from Context7)
#### aiofiles
*No integration examples found for this library.*

#### aiohttp
*No integration examples found for this library.*

#### bandit
*No integration examples found for this library.*

#### coverage
*No integration examples found for this library.*

#### httpx
*No integration examples found for this library.*

#### mypy
*No integration examples found for this library.*

#### pip-audit
*No integration examples found for this library.*

#### pydantic
*No integration examples found for this library.*

#### pytest
*No integration examples found for this library.*

#### pytest-asyncio
*No integration examples found for this library.*

#### pytest-cov
*No integration examples found for this library.*

#### pytest-html
*No integration examples found for this library.*

#### pytest-mock
*No integration examples found for this library.*

#### pytest-rich
*No integration examples found for this library.*

#### pytest-sugar
*No integration examples found for this library.*

#### pytest-timeout
*No integration examples found for this library.*

#### pytest-xdist
*No integration examples found for this library.*

#### pyyaml
*No integration examples found for this library.*

#### rich
*No integration examples found for this library.*

#### types-pyyaml
*No integration examples found for this library.*

## Codebase Context
## Codebase Context

### Related Files
- `billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-security\scripts\prepopulate_context7_cache.py`
- `.tapps-agents\worktrees\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\tapps_agents\core\doctor.py`
- `billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-requirements\scripts\prepopulate_context7_cache.py`
- `.tapps-agents\worktrees\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\scripts\prepopulate_context7_cache.py`
- `tapps_agents\core\doctor.py`
- `billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-review\scripts\prepopulate_context7_cache.py`
- `billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-testing\scripts\prepopulate_context7_cache.py`
- `billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-planning\scripts\prepopulate_context7_cache.py`
- `billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-implementation\scripts\prepopulate_context7_cache.py`
- `scripts\prepopulate_context7_cache.py`

### Existing Patterns
- **Common Import Patterns** (architectural): Commonly imported modules: argparse, asyncio, re, sys, tapps_agents

### Cross-References
- `billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-security\scripts\prepopulate_context7_cache.py` → `.tapps-agents\worktrees\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\tapps_agents\core\doctor.py` (import)
  - imports from tapps_agents.core.config
- `billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-security\scripts\prepopulate_context7_cache.py` → `tapps_agents\core\doctor.py` (import)
  - imports from tapps_agents.core.config
- `billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-requirements\scripts\prepopulate_context7_cache.py` → `.tapps-agents\worktrees\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\tapps_agents\core\doctor.py` (import)
  - imports from tapps_agents.core.config
- `billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-requirements\scripts\prepopulate_context7_cache.py` → `tapps_agents\core\doctor.py` (import)
  - imports from tapps_agents.core.config
- `.tapps-agents\worktrees\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\scripts\prepopulate_context7_cache.py` → `.tapps-agents\worktrees\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\tapps_agents\core\doctor.py` (import)
  - imports from tapps_agents.core.unicode_safe

### Context Summary
Found 10 related files in the codebase. Extracted 1 patterns and 20 cross-references. Use these as reference when implementing new features.

### Related Files
- c:\cursor\TappsCodingAgents\billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-security\scripts\prepopulate_context7_cache.py
- c:\cursor\TappsCodingAgents\.tapps-agents\worktrees\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\tapps_agents\core\doctor.py
- c:\cursor\TappsCodingAgents\billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-requirements\scripts\prepopulate_context7_cache.py
- c:\cursor\TappsCodingAgents\.tapps-agents\worktrees\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\scripts\prepopulate_context7_cache.py
- c:\cursor\TappsCodingAgents\tapps_agents\core\doctor.py
- c:\cursor\TappsCodingAgents\billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-review\scripts\prepopulate_context7_cache.py
- c:\cursor\TappsCodingAgents\billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-testing\scripts\prepopulate_context7_cache.py
- c:\cursor\TappsCodingAgents\billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-planning\scripts\prepopulate_context7_cache.py
- c:\cursor\TappsCodingAgents\billstest\.tapps-agents\worktrees\workflow-full-sdlc-20251213-153627-step-implementation\scripts\prepopulate_context7_cache.py
- c:\cursor\TappsCodingAgents\scripts\prepopulate_context7_cache.py

### Existing Patterns
- {'type': 'architectural', 'name': 'Common Import Patterns', 'description': 'Commonly imported modules: argparse, asyncio, re, sys, tapps_agents', 'examples': ['c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-security\\scripts\\prepopulate_context7_cache.py', 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\tapps_agents\\core\\doctor.py', 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-requirements\\scripts\\prepopulate_context7_cache.py'], 'confidence': 1.0}

### Cross References
- {'source': 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-security\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-security\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-requirements\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-requirements\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.unicode_safe'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.unicode_safe'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-review\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-review\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-testing\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-testing\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-planning\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-planning\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-implementation\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\billstest\\.tapps-agents\\worktrees\\workflow-full-sdlc-20251213-153627-step-implementation\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.unicode_safe'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.unicode_safe'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\.tapps-agents\\worktrees\\workflow-rapid-dev-20260204-064525-512023-step-enhance-14b9e796\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}
- {'source': 'c:\\cursor\\TappsCodingAgents\\scripts\\prepopulate_context7_cache.py', 'target': 'c:\\cursor\\TappsCodingAgents\\tapps_agents\\core\\doctor.py', 'type': 'import', 'details': 'imports from tapps_agents.core.config'}

## Quality Standards
### Code Quality Thresholds
- **Overall Score Threshold**: 70.0

## Implementation Strategy
## Enhanced Prompt