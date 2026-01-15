# Step 1: Enhanced Prompt - Brownfield System Review with Automatic Expert Creation and RAG Population

## Original Prompt

Create a feature for TappsCodingAgents that automatically reviews brownfield systems, analyzes the codebase to detect domains and technologies, automatically creates expert configurations based on detected domains, and populates RAG knowledge bases with project documentation, architecture docs, requirements, and library documentation from Context7. The feature should integrate with existing ExpertRegistry, KnowledgeIngestionPipeline, and DomainStackDetector components. It should provide a CLI command and be usable in Cursor chat via Simple Mode.

## Enhanced Prompt with Requirements Analysis

### Intent Analysis
- **Primary Intent**: Automate brownfield system analysis with expert creation and RAG population
- **Scope**: Framework enhancement (new CLI command + Simple Mode integration)
- **Workflow Type**: Brownfield (enhancing existing framework)
- **Complexity**: High (integrates multiple existing systems)
- **Domains**: Framework development, AI/ML (RAG), system analysis

### Functional Requirements

1. **Brownfield System Analysis**
   - Analyze existing codebase structure
   - Detect programming languages, frameworks, and libraries
   - Identify architectural patterns and conventions
   - Extract project metadata (dependencies, configuration files)

2. **Domain Detection**
   - Use existing `DomainStackDetector` to identify domains
   - Map technologies to business/technical domains
   - Detect multiple domains in polyglot systems
   - Prioritize domains based on codebase coverage

3. **Automatic Expert Creation**
   - Generate expert configurations (YAML) based on detected domains
   - Create expert entries in `.tapps-agents/experts.yaml`
   - Configure expert knowledge base directories
   - Set appropriate expert weights and confidence matrices
   - Integrate with existing `ExpertRegistry` system

4. **RAG Knowledge Base Population**
   - Ingest project documentation (requirements, architecture, ADRs, runbooks)
   - Fetch library documentation from Context7 for detected dependencies
   - Populate expert-specific knowledge bases
   - Build vector indexes for semantic search
   - Support both `SimpleKnowledgeBase` and `VectorKnowledgeBase`

5. **CLI Integration**
   - New command: `tapps-agents brownfield review [--auto] [--output-dir <dir>]`
   - Progress reporting and status updates
   - Dry-run mode for preview
   - Configuration options for expert creation

6. **Simple Mode Integration**
   - New Simple Mode command: `@simple-mode *brownfield-review`
   - Natural language interface
   - Automatic workflow orchestration

### Non-Functional Requirements

1. **Performance**
   - Analysis should complete in < 5 minutes for typical projects
   - RAG population should be incremental (resume capability)
   - Support large codebases (10k+ files)

2. **Reliability**
   - Graceful degradation if Context7 unavailable
   - Error recovery for failed ingestion steps
   - Validation of created expert configurations

3. **Maintainability**
   - Reuse existing components (ExpertRegistry, KnowledgeIngestionPipeline, DomainStackDetector)
   - Follow existing code patterns and architecture
   - Comprehensive logging and error messages

4. **Usability**
   - Clear progress indicators
   - Human-readable output
   - Detailed reports of what was created/updated

### Architecture Guidance

1. **Component Integration**
   - Leverage `DomainStackDetector` for technology detection
   - Use `KnowledgeIngestionPipeline` for RAG population
   - Extend `ExpertRegistry` for expert creation
   - Integrate with `Context7AgentHelper` for library docs

2. **Data Flow**
   ```
   Codebase → DomainStackDetector → Domain Detection
   Domain Detection → Expert Config Generator → experts.yaml
   Codebase + Domain → KnowledgeIngestionPipeline → RAG KB
   Dependencies → Context7 → Library Docs → RAG KB
   ```

3. **Configuration Management**
   - Store expert configs in `.tapps-agents/experts.yaml`
   - Store knowledge bases in `.tapps-agents/kb/{expert-id}/`
   - Maintain state in `.tapps-agents/brownfield-review-state.json`

### Codebase Context

**Existing Components to Reuse:**
- `tapps_agents/experts/domain_detector.py` - DomainStackDetector
- `tapps_agents/experts/knowledge_ingestion.py` - KnowledgeIngestionPipeline
- `tapps_agents/experts/expert_registry.py` - ExpertRegistry
- `tapps_agents/context7/agent_integration.py` - Context7AgentHelper
- `tapps_agents/experts/vector_rag.py` - VectorKnowledgeBase
- `tapps_agents/experts/simple_rag.py` - SimpleKnowledgeBase

**Integration Points:**
- CLI: `tapps_agents/cli/commands/top_level.py` - Add new command handler
- CLI Parser: `tapps_agents/cli/parsers/top_level.py` - Add command parser
- Simple Mode: `tapps_agents/simple_mode/orchestrators/` - Add brownfield orchestrator

### Quality Standards

1. **Code Quality**
   - Type hints for all functions
   - Comprehensive docstrings
   - Error handling with meaningful messages
   - Unit tests for core logic

2. **Security**
   - Validate file paths to prevent directory traversal
   - Sanitize expert IDs and domain names
   - Secure Context7 API key handling

3. **Testing**
   - Unit tests for domain detection integration
   - Integration tests for expert creation
   - Integration tests for RAG population
   - CLI command tests

### Implementation Strategy

1. **Phase 1: Core Analysis Engine**
   - Create `BrownfieldAnalyzer` class
   - Integrate DomainStackDetector
   - Generate domain detection report

2. **Phase 2: Expert Creation**
   - Create `ExpertConfigGenerator` class
   - Generate YAML configurations
   - Validate and write to experts.yaml

3. **Phase 3: RAG Population**
   - Integrate KnowledgeIngestionPipeline
   - Create expert-specific knowledge bases
   - Populate from project sources and Context7

4. **Phase 4: CLI Integration**
   - Add command handler and parser
   - Implement progress reporting
   - Add dry-run mode

5. **Phase 5: Simple Mode Integration**
   - Create brownfield orchestrator
   - Add Simple Mode command
   - Test end-to-end workflow

### Dependencies

- Existing: ExpertRegistry, KnowledgeIngestionPipeline, DomainStackDetector, Context7AgentHelper
- New: BrownfieldAnalyzer, ExpertConfigGenerator, BrownfieldReviewOrchestrator

### Success Criteria

1. Successfully detects domains in brownfield projects
2. Automatically creates expert configurations
3. Populates RAG knowledge bases with project and library docs
4. CLI command works end-to-end
5. Simple Mode command works in Cursor chat
6. All tests pass with >80% coverage
