# TappsCodingAgents - Technology Stack Document

**Version:** 2.0.6  
**Date:** January 2026  
**Status:** Implementation Reference

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

### 1.1 Target Environment

> **This framework runs on a developer's local workstation**, not cloud servers or enterprise infrastructure. All recommendations prioritize:
> - Easy local setup (no complex infrastructure)
> - Consumer GPU compatibility (8-24GB VRAM)
> - Embedded databases (no separate services)
> - Cost efficiency (local models over API calls)

### 1.2 Design Philosophy (2025 Patterns)

| Principle | Implementation |
|-----------|----------------|
| **Local-First** | Run LLMs locally via Ollama; cloud only for complex tasks |
| **Agent-Native** | Agents as first-class citizens, not afterthoughts |
| **Embedded Data** | ChromaDB, LanceDB embedded; no external DB services |
| **IDE-Integrated** | Native Claude Code Skills, MCP protocol |
| **Cost-Conscious** | Minimize API costs; local inference preferred |
| **Privacy-Aware** | Code stays local; cloud fallback is opt-in |

### 1.3 Stack Layers (Developer Workstation)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    IDE LAYER                                         │
│   Cursor • VS Code • Claude Code Skills • MCP Protocol              │
├─────────────────────────────────────────────────────────────────────┤
│                    AGENT LAYER                                       │
│   13 Workflow Agents • N Industry Experts • Orchestrator            │
├─────────────────────────────────────────────────────────────────────┤
│                    INTELLIGENCE LAYER                                │
│   RAG (ChromaDB embedded) • Embeddings • Optional Fine-Tuning       │
├─────────────────────────────────────────────────────────────────────┤
│                    MODEL ROUTER (MAL)                                │
│   Local-First (Ollama) → Cloud Fallback (Anthropic/OpenAI)          │
├─────────────────────────────────────────────────────────────────────┤
│                    LOCAL INFRASTRUCTURE                              │
│   Ollama (GPU) • Python venv • ChromaDB (disk) • Config (YAML)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Framework

### 2.1 Primary Language

| Technology | Version | Purpose | Justification |
|------------|---------|---------|---------------|
| **Python** | 3.13+ | Core framework | Latest stable with performance improvements, better typing |
| **TypeScript** | 5.6+ | MCP servers, IDE integration | Type safety, Claude Code compatibility |
| **YAML** | 1.2 | Configuration | Human-readable, agent definitions |
| **JSON Schema** | Draft 2020-12 | Validation | Latest schema standard with improved features |

### 2.2 Core Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| **Pydantic** | 2.12.5+ | Data validation and configuration models |
| **httpx** | 0.28.1+ | HTTP client (sync + async) |
| **aiohttp** | 3.13.2+ | Async HTTP (Ollama integration) |
| **PyYAML** | 6.0.3+ | YAML parsing |
| **psutil** | 5.9.0+ | Resource monitoring (NUC optimization) |
| **radon** | 6.0.1+ | Complexity / maintainability analysis |
| **bandit** | 1.9.2+ | Security static analysis |

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

**Supported Models (2025) - Developer Workstation:**

| Model | Parameters | Use Case | VRAM Required | Recommended |
|-------|------------|----------|---------------|-------------|
| **qwen2.5-coder:7b** | 7B | Primary coding tasks | 6GB | ✅ 8GB GPU |
| **qwen2.5-coder:14b** | 14B | Complex coding | 12GB | ✅ 16GB GPU |
| **qwen2.5-coder:32b** | 32B | Architecture decisions | 24GB | 24GB GPU |
| **deepseek-coder-v2:lite** | 2.4B (active) | Fast completions, MoE | 4GB | ✅ Any GPU |
| **deepseek-coder-v2:16b** | 16B | Advanced debugging | 12GB | 16GB GPU |
| **codellama:7b** | 7B | Code generation | 6GB | ✅ 8GB GPU |
| **codellama:13b** | 13B | Better generation | 12GB | 16GB GPU |
| **llama3.2:3b** | 3B | Fast tasks, low VRAM | 3GB | ✅ Any GPU |
| **llama3.2:8b** | 8B | General reasoning | 8GB | ✅ 12GB GPU |
| **phi-4:14b** | 14B | Reasoning, math | 12GB | 16GB GPU |
| **mistral:7b** | 7B | General purpose | 6GB | ✅ 8GB GPU |

**Developer GPU Tiers:**

| GPU Tier | VRAM | Recommended Models |
|----------|------|-------------------|
| **Entry** (RTX 3060/4060) | 8GB | qwen2.5-coder:7b, deepseek-v2:lite, llama3.2:3b |
| **Mid** (RTX 3070/4070) | 12GB | qwen2.5-coder:14b, deepseek-v2:16b, phi-4 |
| **High** (RTX 3090/4090) | 24GB | qwen2.5-coder:32b, any model |
| **CPU Only** | — | llama3.2:3b (slow), deepseek-v2:lite |

#### LM Studio (Alternative)

| Attribute | Value |
|-----------|-------|
| **URL** | http://localhost:1234 |
| **API** | OpenAI-compatible |
| **Pros** | GUI management, GGUF support |
| **Cons** | Single model active |

### 3.2 Cloud Providers (Fallback for Complex Tasks)

> **Note:** Cloud fallback is used when local models are insufficient for complex reasoning, large context, or when local GPU is unavailable.

#### Anthropic (Recommended)

| Model | Use Case | Context Window | Cost (per 1M tokens) |
|-------|----------|----------------|---------------------|
| **claude-sonnet-4** | Primary cloud (balanced) | 200K | $3 input / $15 output |
| **claude-opus-4** | Most complex tasks | 200K | $15 input / $75 output |
| **claude-3.5-haiku** | Fast/cheap tasks | 200K | $0.80 input / $4 output |

#### OpenAI (Alternative)

| Model | Use Case | Context Window | Cost (per 1M tokens) |
|-------|----------|----------------|---------------------|
| **gpt-4o** | Complex tasks | 128K | $2.50 input / $10 output |
| **gpt-4o-mini** | Fast/cheap tasks | 128K | $0.15 input / $0.60 output |
| **o3-mini** | Deep reasoning | 200K | $1.10 input / $4.40 output |

#### Google (Alternative)

| Model | Use Case | Context Window | Cost (per 1M tokens) |
|-------|----------|----------------|---------------------|
| **gemini-2.0-flash** | Fast, multimodal | 1M | $0.075 input / $0.30 output |
| **gemini-1.5-pro** | Long context | 2M | $1.25 input / $5.00 output |

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

### 5.2 Vector Database (Local/Embedded)

> **Philosophy:** For developer workstations, use embedded databases. No separate services to manage.

| Database | Type | Pros | Cons | Use Case |
|----------|------|------|------|----------|
| **ChromaDB** | Embedded | Zero setup, Python-native, persists to disk | Single process | ✅ Primary choice |
| **LanceDB** | Embedded | Fast, columnar, serverless | Newer | Alternative |
| **SQLite + sqlite-vec** | Embedded | Familiar, lightweight | Basic features | Minimal setups |
| **Qdrant** | Local server | Performance, filtering | Requires service | When scaling |

**Recommendation for Developer Workstation:**

| Scenario | Recommended | Rationale |
|----------|-------------|-----------|
| **Single project** | ChromaDB (embedded) | Zero config, just works |
| **Multiple projects** | ChromaDB (embedded per project) | Isolation, no conflicts |
| **Large knowledge base (10K+ docs)** | Qdrant (local Docker) | Better performance |
| **Minimal dependencies** | LanceDB | Single file, fast |

### 5.3 Embedding Models (Local-First)

> **Philosophy:** Run embeddings locally. Avoid API costs for high-volume embedding tasks.

#### Local Embeddings (via Ollama) - Recommended

| Model | Dimensions | Speed | Quality | Command |
|-------|------------|-------|---------|---------|
| **nomic-embed-text** | 768 | Fast | Good | `ollama pull nomic-embed-text` |
| **mxbai-embed-large** | 1024 | Medium | Better | `ollama pull mxbai-embed-large` |
| **snowflake-arctic-embed** | 1024 | Medium | Best | `ollama pull snowflake-arctic-embed` |

#### Local Embeddings (via sentence-transformers)

| Model | Dimensions | Speed | Quality | Notes |
|-------|------------|-------|---------|-------|
| **all-MiniLM-L6-v2** | 384 | Very Fast | Good | Best for low resources |
| **all-mpnet-base-v2** | 768 | Fast | Better | Good balance |
| **bge-large-en-v1.5** | 1024 | Medium | Best | Highest quality |
| **bge-m3** | 1024 | Medium | Best | Multilingual |

**Recommendation for Developer Workstation:**

| GPU Available | Recommended | Why |
|---------------|-------------|-----|
| **Yes (8GB+)** | nomic-embed-text (Ollama) | Fast, GPU-accelerated |
| **Yes (12GB+)** | mxbai-embed-large (Ollama) | Better quality |
| **No GPU** | all-MiniLM-L6-v2 | CPU-friendly, fast |
| **Low RAM** | all-MiniLM-L6-v2 | Smallest footprint |

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

## 6. Fine-Tuning Stack (Optional)

> **Note:** Fine-tuning is **optional** for most use cases. Start with prompt engineering and RAG. Only fine-tune when you have domain-specific patterns that base models can't learn from context.

### 6.1 When to Fine-Tune vs. Use RAG

| Scenario | Recommendation | Why |
|----------|----------------|-----|
| Domain terminology | RAG | Retrieval handles vocabulary |
| Code patterns/style | RAG | Examples in context work well |
| Consistent behavior | Fine-tune | Bakes in preferences |
| Proprietary APIs | Fine-tune | Not in training data |
| Cost reduction | Fine-tune | Smaller model + adapter |

### 6.2 Fine-Tuning Methods (Developer Workstation)

| Method | Training Time | Quality | VRAM Required | Difficulty |
|--------|--------------|---------|---------------|------------|
| **Prompt Engineering** | None | Good | None | Easy |
| **Few-shot RAG** | None | Good | None | Easy |
| **QLoRA** | 2-4 hours | Better | 8GB+ | Medium |
| **LoRA** | 4-8 hours | Better | 16GB+ | Medium |
| **Full Fine-tune** | Days | Best | 40GB+ | Hard |

**Recommendation for Developer Workstation:** **QLoRA** (8GB VRAM minimum)

### 6.3 Fine-Tuning Tools (2025)

| Tool | Pros | Cons | GPU Requirement |
|------|------|------|-----------------|
| **Unsloth** | 2-5x faster, 60% less VRAM | Limited models | 8GB+ |
| **LLaMA-Factory** | GUI, easy setup | Less customizable | 12GB+ |
| **Axolotl** | Feature-rich, flexible | Complex setup | 16GB+ |
| **MLX (Apple Silicon)** | Native M1/M2/M3 | Mac only | 16GB+ unified |

**Recommendation:** 
- **8GB GPU:** Unsloth + QLoRA + 7B model
- **16GB GPU:** Unsloth + LoRA + 14B model  
- **Apple Silicon:** MLX for native performance

### 6.4 Realistic Fine-Tuning Config (Consumer GPU)

```yaml
fine_tuning:
  method: "qlora"  # 4-bit quantization
  
  base_model: "qwen2.5-coder:7b"  # Start small
  
  tool: "unsloth"  # Memory efficient
    
  hardware:
    target: "consumer_gpu"  # RTX 3060/4060
    minimum_vram: 8GB
    
  training:
    epochs: 3
    learning_rate: 2e-4
    batch_size: 2  # Small for limited VRAM
    gradient_accumulation: 8  # Effective batch = 16
    max_seq_length: 2048
    
  qlora:
    bits: 4
    rank: 16  # Lower rank for 8GB
    alpha: 32
    dropout: 0.05
    
  output:
    adapter_path: "./adapters/domain-expert/"
    merge_and_export: false  # Keep adapter separate
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
| **pytest** | Unit testing | 9.x |
| **pytest-asyncio** | Async testing | 1.x |
| **mypy** | Type checking | 1.19+ |
| **ruff** | Linting, formatting | 0.14+ |
| **black** | Formatting | 25.x |

### 8.3 Monitoring & Observability

| Tool | Purpose | Use Case |
|------|---------|----------|
| **LangSmith** | LLM tracing | Development, debugging |
| **Langfuse** | LLM observability | Production monitoring |
| **OpenTelemetry** | Distributed tracing | Full-stack observability |
| **Prometheus** | Metrics collection | Infrastructure monitoring |
| **Grafana** | Visualization | Dashboards |

---

## 9. Infrastructure (Developer Workstation)

> **Philosophy:** This framework runs on a developer's local machine, not servers. Keep it simple, avoid over-engineering.

### 9.1 Local Setup (No Docker Required)

**Recommended: Native Installation**

```bash
# 1. Install Ollama (manages local LLMs)
# Windows: winget install Ollama.Ollama
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull coding models
ollama pull qwen2.5-coder:7b
ollama pull deepseek-coder-v2:lite

# 3. Python environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# 4. ChromaDB runs embedded (no separate service)
# Vector store persists to ./data/vectors/
```

### 9.2 Optional Docker (for isolation)

```yaml
# docker-compose.yml (optional, for those who prefer containers)
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ~/.ollama:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
```

### 9.3 Hardware Requirements (Developer Workstation)

#### Entry Level (Budget/Laptop)

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **CPU** | 4+ cores | Intel i5/AMD Ryzen 5 or better |
| **RAM** | 16GB | 8GB usable after OS |
| **GPU** | 6-8GB VRAM | RTX 3060/4060, or CPU-only |
| **Storage** | 50GB free | SSD recommended |
| **Models** | qwen2.5-coder:7b, deepseek-v2:lite | 7B models comfortable |

#### Recommended (Desktop Developer)

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **CPU** | 8+ cores | Intel i7/AMD Ryzen 7 |
| **RAM** | 32GB | Room for IDE + models |
| **GPU** | 12-16GB VRAM | RTX 4070/4080 |
| **Storage** | 100GB free | NVMe for fast loading |
| **Models** | qwen2.5-coder:14b, phi-4 | 14B models comfortable |

#### High-End (Power User)

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **CPU** | 12+ cores | Intel i9/AMD Ryzen 9 |
| **RAM** | 64GB | Multiple models loaded |
| **GPU** | 24GB VRAM | RTX 4090 / RTX 3090 |
| **Storage** | 200GB free | Multiple model versions |
| **Models** | qwen2.5-coder:32b, any | 32B+ models possible |

#### CPU-Only (No GPU)

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **CPU** | 8+ cores | More cores = faster inference |
| **RAM** | 32GB+ | Models load to RAM |
| **Storage** | 50GB free | SSD essential |
| **Models** | llama3.2:3b, deepseek-v2:lite | Small models only, 10x slower |

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

## 11. Recommended Configurations (Developer Workstation)

### 11.1 Quick Start (Entry-Level GPU: 8GB)

```yaml
# config/quickstart.yaml
# For: RTX 3060/4060, laptops with dedicated GPU

environment: quickstart

llm:
  primary:
    provider: ollama
    model: qwen2.5-coder:7b
  fallback:
    provider: anthropic
    model: claude-3.5-haiku  # Cheap fallback
    
rag:
  vector_db: chromadb  # Embedded, no setup
  embedding:
    provider: ollama
    model: nomic-embed-text
  persistence: ./data/vectors

fine_tuning:
  enabled: false  # Not needed to start

api_keys:
  anthropic: ${ANTHROPIC_API_KEY}  # Optional fallback
```

### 11.2 Recommended (Mid-Range GPU: 12-16GB)

```yaml
# config/recommended.yaml
# For: RTX 4070/4080, desktop workstations

environment: recommended

llm:
  primary:
    provider: ollama
    model: qwen2.5-coder:14b  # Better model
  secondary:
    provider: ollama
    model: deepseek-coder-v2:lite  # Fast fallback
  cloud_fallback:
    provider: anthropic
    model: claude-sonnet-4
    trigger_on:
      - complexity_score > 8
      - context_length > 12000
      - local_error

rag:
  vector_db: chromadb
  embedding:
    provider: ollama
    model: mxbai-embed-large  # Better embeddings
  chunking:
    size: 512
    overlap: 50
  retrieval:
    top_k: 5
    reranking: true
  persistence: ./data/vectors

fine_tuning:
  enabled: false  # Enable when needed
  
monitoring:
  langsmith: true  # Free tier available
```

### 11.3 Power User (High-End GPU: 24GB)

```yaml
# config/poweruser.yaml
# For: RTX 4090/3090, workstations

environment: poweruser

llm:
  primary:
    provider: ollama
    model: qwen2.5-coder:32b  # Best local model
  fast:
    provider: ollama
    model: deepseek-coder-v2:lite
  cloud_fallback:
    provider: anthropic
    model: claude-sonnet-4
    trigger_on:
      - explicit_request
      - complexity_score > 9

rag:
  vector_db: chromadb
  embedding:
    provider: ollama
    model: snowflake-arctic-embed
  retrieval:
    top_k: 10
    reranking: true
  persistence: ./data/vectors

fine_tuning:
  enabled: true
  method: qlora
  tool: unsloth
  base_model: qwen2.5-coder:14b
  adapter_path: ./adapters/

monitoring:
  langsmith: true
  local_metrics: true
```

### 11.4 CPU-Only (No GPU)

```yaml
# config/cpu-only.yaml
# For: Laptops without GPU, older hardware

environment: cpu_only

llm:
  primary:
    provider: ollama
    model: llama3.2:3b  # Small, CPU-friendly
  cloud_fallback:
    provider: anthropic
    model: claude-3.5-haiku  # Use cloud more often
    trigger_on:
      - always_for_coding  # Local too slow for code
      
rag:
  vector_db: chromadb
  embedding:
    provider: sentence-transformers
    model: all-MiniLM-L6-v2  # CPU-optimized
  persistence: ./data/vectors

fine_tuning:
  enabled: false  # Not practical on CPU

note: "CPU inference is 10x slower. Consider cloud fallback for coding tasks."
```

---

## 12. Version Compatibility (December 2025)

### 12.1 Python Dependencies

```txt
# requirements.txt / pyproject.toml (current)

# Core
python>=3.13
pydantic>=2.12.5
httpx>=0.28.1
pyyaml>=6.0.3
aiohttp>=3.13.2
psutil>=5.9.0

# Code analysis
radon>=6.0.1
bandit>=1.9.2
pylint>=4.0.4
coverage>=7.13.0

# Testing
pytest>=9.0.2
pytest-asyncio>=1.3.0
pytest-cov>=7.0.0
pytest-mock>=3.15.1
pytest-timeout>=2.4.0

# Development / quality tools
black>=25.12.0
ruff>=0.14.8,<1.0
mypy>=1.19.0,<2.0
pip-audit>=2.10.0
pipdeptree>=2.30.0

# Reporting
jinja2>=3.1.6
plotly>=6.5.0
```

### 12.2 Ollama Models (December 2025)

```bash
# Recommended model versions
ollama pull qwen2.5-coder:7b      # 4.7GB
ollama pull qwen2.5-coder:14b     # 9.0GB
ollama pull deepseek-coder-v2:lite # 1.6GB
ollama pull nomic-embed-text       # 274MB
ollama pull mxbai-embed-large      # 670MB
```

### 12.3 Version Lock Strategy

| Category | Strategy | Rationale |
|----------|----------|-----------|
| **Python** | 3.13+ | Performance, typing improvements |
| **Core libs** | Pin minor | Stability |
| **LLM SDKs** | Pin minor | API compatibility |
| **Ollama models** | Latest | Continuous improvement |
| **Dev Tools** | Pin major | Flexibility |

---

## Appendix

### A.1 2025 Architecture Patterns Applied

| Pattern | Implementation in TappsCodingAgents |
|---------|-------------------------------------|
| **Agent-First Development** | 13 workflow agents + N experts as core architecture |
| **Local-First AI** | Ollama local inference, cloud as fallback only |
| **Embedded Data Stores** | ChromaDB embedded, no external database services |
| **MCP Protocol** | Native integration with Claude Code and Cursor |
| **Event-Driven Agents** | Agents respond to events, not polling |
| **Prompt-as-Code** | Agent behaviors defined in version-controlled YAML/MD |
| **RAG over Fine-Tuning** | Prefer retrieval; fine-tune only when necessary |

### A.2 Glossary

| Term | Definition |
|------|------------|
| **MAL** | Model Abstraction Layer - Routes requests to appropriate LLM providers |
| **RAG** | Retrieval-Augmented Generation - Enhances LLM with external knowledge |
| **LoRA** | Low-Rank Adaptation - Efficient fine-tuning method |
| **QLoRA** | Quantized LoRA - Memory-efficient fine-tuning (4-bit) |
| **MCP** | Model Context Protocol - Anthropic's tool integration standard |
| **VRAM** | Video RAM - GPU memory for model inference |
| **Agent Skill** | Claude Code format for defining agent capabilities |
| **Embedded DB** | Database that runs in-process (no separate server) |

### A.3 References

| Resource | URL |
|----------|-----|
| Ollama | https://ollama.com |
| LangChain | https://langchain.com |
| LangGraph | https://langchain-ai.github.io/langgraph |
| ChromaDB | https://trychroma.com |
| Unsloth | https://unsloth.ai |
| Claude Code | https://code.claude.com |
| MCP Protocol | https://modelcontextprotocol.io |
| Cursor IDE | https://cursor.com |
| LiteLLM | https://litellm.ai |

### A.4 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0-draft | Dec 2025 | Initial tech stack document |
| 1.0.1-draft | Dec 2025 | Updated for 2025 patterns, developer workstation focus |

---

*End of Document*

