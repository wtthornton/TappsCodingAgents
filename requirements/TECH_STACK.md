# TappsCodingAgents - Technology Stack Document

**Version:** 1.0.0-draft  
**Date:** December 2025  
**Status:** Design Phase

---

## Table of Contents

1. [Overview](#1-overview)
2. [Core Framework](#2-core-framework)
3. [LLM Providers](#3-llm-providers)
4. [Model Abstraction Layer (MAL)](#4-model-abstraction-layer-mal)
5. [RAG Infrastructure](#5-rag-infrastructure)
6. [Fine-Tuning Stack](#6-fine-tuning-stack)
7. [Agent Orchestration](#7-agent-orchestration)
8. [Development Tools](#8-development-tools)
9. [Infrastructure](#9-infrastructure)
10. [Technology Matrix](#10-technology-matrix)
11. [Recommended Configurations](#11-recommended-configurations)
12. [Version Compatibility](#12-version-compatibility)

---

## 1. Overview

### 1.1 Design Philosophy

| Principle | Implementation |
|-----------|----------------|
| **Local-First** | Prefer local LLMs for cost efficiency and privacy |
| **Cloud Fallback** | Seamless fallback to cloud when local insufficient |
| **Framework Agnostic** | Support multiple RAG frameworks and tools |
| **Extensible** | Plugin architecture for new components |
| **Production Ready** | Enterprise-grade tooling with monitoring |

### 1.2 Stack Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                                 │
│   Claude Code Skills • IDE Integration • MCP Servers                │
├─────────────────────────────────────────────────────────────────────┤
│                    ORCHESTRATION LAYER                               │
│   Agent Coordination • Workflow Engine • Gate Decisions             │
├─────────────────────────────────────────────────────────────────────┤
│                    INTELLIGENCE LAYER                                │
│   RAG • Fine-Tuning • Embeddings • Vector Search                    │
├─────────────────────────────────────────────────────────────────────┤
│                    MODEL ABSTRACTION LAYER (MAL)                     │
│   Local Routing • Cloud Fallback • Load Balancing                   │
├─────────────────────────────────────────────────────────────────────┤
│                    LLM PROVIDERS                                     │
│   Ollama • LM Studio • Anthropic • OpenAI • Azure                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Framework

### 2.1 Primary Language

| Technology | Version | Purpose | Justification |
|------------|---------|---------|---------------|
| **Python** | 3.11+ | Core framework | Industry standard for AI, extensive library ecosystem |
| **TypeScript** | 5.0+ | MCP servers, IDE integration | Type safety, Claude Code compatibility |
| **YAML** | 1.2 | Configuration | Human-readable, agent definitions |
| **JSON Schema** | Draft-07 | Validation | Standard schema validation |

### 2.2 Core Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| **Pydantic** | 2.x | Data validation, settings |
| **FastAPI** | 0.100+ | API endpoints, webhooks |
| **asyncio** | stdlib | Async operations |
| **httpx** | 0.25+ | Async HTTP client |
| **PyYAML** | 6.x | YAML parsing |
| **jsonschema** | 4.x | Schema validation |

---

## 3. LLM Providers

### 3.1 Local Providers (Primary)

#### Ollama (Recommended)

| Attribute | Value |
|-----------|-------|
| **URL** | http://localhost:11434 |
| **API** | OpenAI-compatible |
| **Pros** | Easy setup, model management, GPU support |
| **Cons** | Limited concurrent requests |

**Supported Models:**

| Model | Parameters | Use Case | VRAM Required |
|-------|------------|----------|---------------|
| **qwen2.5-coder:14b** | 14B | Primary coding tasks | 16GB |
| **qwen2.5-coder:7b** | 7B | Lightweight tasks | 8GB |
| **deepseek-coder:6.7b** | 6.7B | Debugging, analysis | 8GB |
| **codellama:13b** | 13B | Code generation | 16GB |
| **codellama:7b** | 7B | Quick completions | 8GB |
| **mistral:7b** | 7B | General reasoning | 8GB |
| **llama3.1:8b** | 8B | Planning, analysis | 10GB |

#### LM Studio (Alternative)

| Attribute | Value |
|-----------|-------|
| **URL** | http://localhost:1234 |
| **API** | OpenAI-compatible |
| **Pros** | GUI management, GGUF support |
| **Cons** | Single model active |

### 3.2 Cloud Providers (Fallback)

#### Anthropic (Recommended)

| Model | Use Case | Context Window | Cost (per 1M tokens) |
|-------|----------|----------------|---------------------|
| **claude-sonnet-4** | Primary cloud | 200K | $3 input / $15 output |
| **claude-3.5-sonnet** | Alternative | 200K | $3 input / $15 output |
| **claude-3.5-haiku** | Fast tasks | 200K | $0.80 input / $4 output |

#### OpenAI (Alternative)

| Model | Use Case | Context Window | Cost (per 1M tokens) |
|-------|----------|----------------|---------------------|
| **gpt-4o** | Complex tasks | 128K | $2.50 input / $10 output |
| **gpt-4o-mini** | Fast tasks | 128K | $0.15 input / $0.60 output |
| **o3-mini** | Reasoning | 200K | $1.10 input / $4.40 output |

#### Azure OpenAI (Enterprise)

| Attribute | Value |
|-----------|-------|
| **Use Case** | Enterprise deployments with compliance requirements |
| **Pros** | Data residency, enterprise SLA |
| **Cons** | Setup complexity, approval process |

### 3.3 Provider Selection Matrix

| Agent Type | Primary | Fallback | Rationale |
|------------|---------|----------|-----------|
| **Workflow Agents** | Local (Ollama) | Cloud (Claude) | Cost efficiency |
| **Industry Experts** | Local (Fine-tuned) | Cloud (Claude) | Domain specialization |
| **Orchestrator** | Cloud (Claude) | Local | Complex reasoning |
| **Analyst/Planner** | Cloud (Claude) | Local | Strategic thinking |

---

## 4. Model Abstraction Layer (MAL)

### 4.1 Router Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MAL ROUTER                               │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Request    │  │   Routing    │  │   Response   │          │
│  │   Analyzer   │──▶│   Engine     │──▶│   Aggregator │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                 │                   │                  │
│         ▼                 ▼                   ▼                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    PROVIDER POOL                          │   │
│  │                                                           │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │   │
│  │  │ Ollama  │  │LM Studio│  │Anthropic│  │ OpenAI  │     │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Implementation Options

| Framework | Language | Pros | Cons |
|-----------|----------|------|------|
| **LiteLLM** | Python | 100+ providers, unified API | Dependency overhead |
| **LangChain** | Python | Ecosystem, tools | Complexity |
| **Custom Router** | Python | Full control, minimal deps | Development effort |

**Recommendation:** **LiteLLM** for multi-provider support with unified OpenAI-compatible API.

### 4.3 Routing Logic

```yaml
routing_rules:
  default: local
  
  triggers:
    use_cloud:
      - complexity_score > 8
      - context_length > 8000
      - local_unavailable: true
      - error_rate > 0.3
      
    use_local:
      - default
      - cost_limit_reached: true
      
  priority:
    1: ollama
    2: lm_studio
    3: anthropic
    4: openai
```

---

## 5. RAG Infrastructure

### 5.1 RAG Framework

| Framework | Version | Use Case | Recommendation |
|-----------|---------|----------|----------------|
| **LangChain** | 0.3+ | Full-featured RAG pipelines | Primary |
| **LlamaIndex** | 0.10+ | Document-centric RAG | Alternative |
| **Haystack** | 2.x | Production pipelines | Enterprise |
| **Custom** | — | Simple retrieval | Minimal setups |

**Recommendation:** **LangChain** for comprehensive ecosystem and tool integration.

### 5.2 Vector Database

| Database | Type | Pros | Cons | Use Case |
|----------|------|------|------|----------|
| **ChromaDB** | Embedded | Easy setup, Python-native | Limited scale | Development, small projects |
| **Qdrant** | Self-hosted/Cloud | Performance, filtering | Setup complexity | Production |
| **Milvus** | Self-hosted | Scale, features | Resource heavy | Enterprise |
| **Pinecone** | Cloud | Managed, reliable | Cost, vendor lock | Quick deployment |
| **Weaviate** | Self-hosted/Cloud | Hybrid search | Complexity | Advanced search |

**Recommendation Matrix:**

| Deployment | Recommended | Rationale |
|------------|-------------|-----------|
| **Development** | ChromaDB | Zero setup, embedded |
| **Production (Small)** | ChromaDB | Simple, sufficient |
| **Production (Medium)** | Qdrant | Performance, self-hosted |
| **Production (Large)** | Milvus/Pinecone | Scale, reliability |

### 5.3 Embedding Models

| Model | Dimensions | Speed | Quality | Use Case |
|-------|------------|-------|---------|----------|
| **all-MiniLM-L6-v2** | 384 | Fast | Good | Development |
| **all-mpnet-base-v2** | 768 | Medium | Better | Production |
| **bge-large-en-v1.5** | 1024 | Slower | Best | High accuracy |
| **nomic-embed-text** | 768 | Fast | Good | Ollama-native |
| **mxbai-embed-large** | 1024 | Medium | Better | Ollama-native |

**Recommendation:** 
- **Development:** `all-MiniLM-L6-v2` (fast, good quality)
- **Production:** `bge-large-en-v1.5` or `nomic-embed-text` (if using Ollama)

### 5.4 RAG Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      EXPERT AGENT RAG                            │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │    Query     │    │   Retriever  │    │   Context    │      │
│  │   Encoder    │───▶│              │───▶│   Builder    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                    │               │
│         ▼                   ▼                    ▼               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    VECTOR DATABASE                          │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │   Domain    │  │   Patterns  │  │   Project   │        │ │
│  │  │ Knowledge   │  │   Library   │  │   Context   │        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 5.5 RAG Configuration

```yaml
rag_config:
  embedding:
    model: "sentence-transformers/all-MiniLM-L6-v2"
    # Alternative: "BAAI/bge-large-en-v1.5"
    # Alternative: "nomic-embed-text" (via Ollama)
    
  vector_db:
    type: "chromadb"  # or "qdrant", "milvus", "pinecone"
    path: "./vector_store"
    
  chunking:
    strategy: "recursive"
    chunk_size: 512
    chunk_overlap: 50
    
  retrieval:
    top_k: 5
    similarity_threshold: 0.7
    reranking: true
    reranker_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
```

---

## 6. Fine-Tuning Stack

### 6.1 Fine-Tuning Methods

| Method | Training Time | Quality | Resource Requirements |
|--------|--------------|---------|----------------------|
| **Prompt Engineering** | None | Good | None |
| **Few-shot Examples** | None | Good | Context window |
| **LoRA** | Hours | Better | 16GB+ VRAM |
| **QLoRA** | Hours | Better | 8GB+ VRAM |
| **Full Fine-tune** | Days | Best | 40GB+ VRAM |

**Recommendation:** **QLoRA** for best quality/resource balance.

### 6.2 Fine-Tuning Tools

| Tool | Pros | Cons | Recommendation |
|------|------|------|----------------|
| **Unsloth** | 2x faster, memory efficient | Limited models | Primary |
| **Axolotl** | Feature-rich, flexible | Complex setup | Alternative |
| **LLaMA-Factory** | GUI, easy setup | Less customizable | Beginners |
| **Hugging Face PEFT** | Standard, well-documented | Slower | Reference |

**Recommendation:** **Unsloth** for efficiency, **Axolotl** for advanced needs.

### 6.3 Fine-Tuning Infrastructure

```yaml
fine_tuning:
  method: "qlora"
  
  base_models:
    - qwen2.5-coder-14b
    - codellama-13b
    
  tools:
    primary: "unsloth"
    alternative: "axolotl"
    
  hardware:
    minimum_vram: 16GB
    recommended_vram: 24GB
    
  training:
    epochs: 3
    learning_rate: 2e-4
    batch_size: 4
    gradient_accumulation: 4
    
  lora:
    rank: 64
    alpha: 128
    dropout: 0.05
    target_modules:
      - q_proj
      - k_proj
      - v_proj
      - o_proj
```

### 6.4 Training Data Format

```yaml
# Alpaca format (recommended)
training_example:
  instruction: "Explain the Home Assistant automation trigger format"
  input: "I want to trigger when motion is detected"
  output: |
    In Home Assistant, motion detection triggers use the state trigger format:
    
    ```yaml
    trigger:
      - platform: state
        entity_id: binary_sensor.motion_sensor
        to: "on"
    ```
    
    Key points:
    - Use `binary_sensor` for motion sensors
    - State changes from "off" to "on" indicate motion detected
    - Add `for` duration to debounce frequent triggers
```

---

## 7. Agent Orchestration

### 7.1 Orchestration Frameworks

| Framework | Language | Pros | Cons | Use Case |
|-----------|----------|------|------|----------|
| **LangGraph** | Python | LangChain ecosystem, stateful | Complexity | Multi-agent workflows |
| **CrewAI** | Python | Simple, role-based | Less flexible | Team-based agents |
| **AutoGen** | Python | Microsoft backing, research | Learning curve | Research, complex flows |
| **Custom** | Python | Full control | Development effort | Specific needs |

**Recommendation:** **LangGraph** for sophisticated orchestration, **Custom** for framework simplicity.

### 7.2 MCP Integration

| Component | Purpose | Technology |
|-----------|---------|------------|
| **MCP Server** | Tool exposure | TypeScript/Python |
| **MCP Client** | Tool consumption | SDK integration |
| **Tool Bridge** | Legacy tools | HTTP adapters |

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLAUDE CODE / IDE                            │
│                                                                  │
│                         ▲                                        │
│                         │ MCP Protocol                           │
│                         ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    MCP SERVER                             │   │
│  │                                                           │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │   │
│  │  │  Agent  │  │   RAG   │  │  Fine-  │  │  Tools  │     │   │
│  │  │ Router  │  │ Query   │  │  Tune   │  │  Bridge │     │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Claude Code Integration

```yaml
# Agent Skill format (SKILL.md)
---
name: implementer
description: Write production-quality code following project patterns
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
model_profile: implementer_profile
---
```

---

## 8. Development Tools

### 8.1 IDE Integration

| IDE | Support Level | Integration Method |
|-----|---------------|-------------------|
| **Cursor** | Primary | Agent Skills, MCP |
| **VS Code** | Secondary | Extensions, MCP |
| **JetBrains** | Planned | Plugin |

### 8.2 Testing & Quality

| Tool | Purpose | Version |
|------|---------|---------|
| **pytest** | Unit testing | 7.x |
| **pytest-asyncio** | Async testing | 0.21+ |
| **mypy** | Type checking | 1.x |
| **ruff** | Linting, formatting | 0.1+ |
| **pre-commit** | Git hooks | 3.x |

### 8.3 Monitoring & Observability

| Tool | Purpose | Use Case |
|------|---------|----------|
| **LangSmith** | LLM tracing | Development, debugging |
| **Langfuse** | LLM observability | Production monitoring |
| **OpenTelemetry** | Distributed tracing | Full-stack observability |
| **Prometheus** | Metrics collection | Infrastructure monitoring |
| **Grafana** | Visualization | Dashboards |

---

## 9. Infrastructure

### 9.1 Containerization

```yaml
# docker-compose.yml structure
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma

  agent-api:
    build: ./services/agent-api
    ports:
      - "8080:8080"
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - CHROMA_HOST=http://chromadb:8000
```

### 9.2 Hardware Requirements

#### Minimum (Development)

| Component | Requirement |
|-----------|-------------|
| **CPU** | 8 cores |
| **RAM** | 16GB |
| **GPU** | 8GB VRAM (RTX 3060/4060) |
| **Storage** | 100GB SSD |

#### Recommended (Production)

| Component | Requirement |
|-----------|-------------|
| **CPU** | 16+ cores |
| **RAM** | 32GB+ |
| **GPU** | 24GB VRAM (RTX 3090/4090) |
| **Storage** | 500GB NVMe |

#### Enterprise (Multi-user)

| Component | Requirement |
|-----------|-------------|
| **CPU** | 32+ cores |
| **RAM** | 64GB+ |
| **GPU** | Multiple 24GB+ GPUs |
| **Storage** | 1TB+ NVMe RAID |

---

## 10. Technology Matrix

### 10.1 Full Stack Summary

| Layer | Primary | Alternative | Enterprise |
|-------|---------|-------------|------------|
| **Language** | Python 3.11+ | TypeScript | Both |
| **Local LLM Host** | Ollama | LM Studio | vLLM |
| **Cloud LLM** | Anthropic | OpenAI | Azure OpenAI |
| **RAG Framework** | LangChain | LlamaIndex | Haystack |
| **Vector DB** | ChromaDB | Qdrant | Milvus |
| **Embeddings** | all-MiniLM-L6-v2 | bge-large-en | Custom |
| **Fine-Tuning** | Unsloth | Axolotl | Custom |
| **Orchestration** | Custom/LangGraph | CrewAI | Custom |
| **MCP** | TypeScript SDK | Python SDK | Both |

### 10.2 Component Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPENDENCY GRAPH                              │
│                                                                  │
│  Agent Skills ──────┬──► MAL Router ──────┬──► Ollama           │
│       │             │          │          └──► Anthropic        │
│       │             │          │                                │
│       ▼             │          ▼                                │
│  Orchestrator ──────┤    LangChain ────────┬──► ChromaDB        │
│       │             │          │           └──► Embeddings      │
│       │             │          │                                │
│       ▼             │          ▼                                │
│  Expert Agents ─────┴──► RAG Pipeline ─────┬──► Knowledge Base  │
│       │                        │           └──► Fine-tuned Model│
│       │                        │                                │
│       ▼                        ▼                                │
│  Workflow Agents ──────► Quality Gates                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. Recommended Configurations

### 11.1 Development Setup

```yaml
# config/development.yaml
environment: development

llm:
  primary_provider: ollama
  primary_model: qwen2.5-coder:7b  # Smaller for dev
  fallback_provider: anthropic
  fallback_model: claude-3.5-haiku  # Cheaper for dev

rag:
  vector_db: chromadb
  embedding_model: all-MiniLM-L6-v2
  persistence: ./data/vectors

fine_tuning:
  enabled: false  # Use base models in dev

monitoring:
  langsmith: true
  tracing: verbose
```

### 11.2 Production Setup

```yaml
# config/production.yaml
environment: production

llm:
  primary_provider: ollama
  primary_model: qwen2.5-coder:14b
  fallback_provider: anthropic
  fallback_model: claude-sonnet-4
  
  rate_limiting:
    local_rpm: 60
    cloud_rpm: 20
    
  retry:
    max_attempts: 3
    backoff_factor: 2

rag:
  vector_db: qdrant
  embedding_model: BAAI/bge-large-en-v1.5
  persistence: /data/vectors
  replication: 2

fine_tuning:
  enabled: true
  adapter_path: /models/adapters

monitoring:
  langfuse: true
  prometheus: true
  tracing: standard
```

### 11.3 Minimal Setup (Quick Start)

```yaml
# config/minimal.yaml
environment: minimal

llm:
  provider: ollama
  model: qwen2.5-coder:7b
  # No cloud fallback

rag:
  vector_db: chromadb
  embedding_model: nomic-embed-text  # Via Ollama
  persistence: ./vectors

fine_tuning:
  enabled: false

monitoring:
  enabled: false
```

---

## 12. Version Compatibility

### 12.1 Python Dependencies

```txt
# requirements.txt

# Core
python>=3.11,<3.13
pydantic>=2.0,<3.0
fastapi>=0.100,<1.0
httpx>=0.25,<1.0
pyyaml>=6.0,<7.0

# LLM
langchain>=0.3,<1.0
litellm>=1.30,<2.0
anthropic>=0.40,<1.0
openai>=1.30,<2.0

# RAG
chromadb>=0.5,<1.0
sentence-transformers>=2.2,<3.0
# qdrant-client>=1.8,<2.0  # Optional

# Fine-Tuning
# unsloth>=2024.1  # Optional, install separately
# peft>=0.10,<1.0  # Optional

# Development
pytest>=7.0,<8.0
mypy>=1.0,<2.0
ruff>=0.1,<1.0
```

### 12.2 Version Lock Strategy

| Category | Strategy | Rationale |
|----------|----------|-----------|
| **Core** | Pin minor | Stability |
| **LLM SDKs** | Pin minor | API compatibility |
| **RAG** | Pin minor | Data compatibility |
| **Dev Tools** | Pin major | Flexibility |

---

## Appendix

### A.1 Glossary

| Term | Definition |
|------|------------|
| **MAL** | Model Abstraction Layer - Routes requests to appropriate LLM providers |
| **RAG** | Retrieval-Augmented Generation - Enhances LLM with external knowledge |
| **LoRA** | Low-Rank Adaptation - Efficient fine-tuning method |
| **QLoRA** | Quantized LoRA - Memory-efficient fine-tuning |
| **MCP** | Model Context Protocol - Anthropic's tool integration standard |
| **VRAM** | Video RAM - GPU memory for model inference |

### A.2 References

| Resource | URL |
|----------|-----|
| Ollama | https://ollama.com |
| LangChain | https://langchain.com |
| ChromaDB | https://trychroma.com |
| Unsloth | https://unsloth.ai |
| Claude Code | https://code.claude.com |
| MCP Protocol | https://modelcontextprotocol.io |

### A.3 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0-draft | Dec 2025 | Initial tech stack document |

---

*End of Document*

