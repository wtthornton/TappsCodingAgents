# Hardware Recommendations for TappsCodingAgents

**Last Updated:** December 2025  
**Project Version:** 2.0.0

## Executive Summary

TappsCodingAgents is a Python-based AI coding framework that uses local LLM inference (Ollama) for code generation, review, and analysis. To run this project efficiently and make coding fast, you need a system optimized for:

1. **Local LLM Inference** - GPU acceleration for Ollama models (7B-14B parameters)
2. **Python Development** - Fast CPU for code analysis tools (Ruff, mypy, pytest)
3. **Multi-tasking** - Sufficient RAM for running IDE, agents, and analysis tools simultaneously
4. **Fast I/O** - SSD storage for quick file operations and code indexing

---

## Project Requirements Analysis

### Core Components

| Component | Resource Impact | Notes |
|-----------|----------------|-------|
| **Ollama LLM** | GPU VRAM: 8-16GB+ | Primary bottleneck for code generation |
| **Python Runtime** | RAM: 2-4GB | Framework + dependencies |
| **Code Analysis Tools** | CPU: Multi-core | Ruff, mypy, pytest run in parallel |
| **IDE (Cursor/VS Code)** | RAM: 2-4GB | Language servers, extensions |
| **Quality Reports** | Storage: Fast SSD | HTML/JSON report generation |

### Model Requirements

Based on `QUICK_START.md` recommendations:

- **Minimum (7B models)**: 8GB GPU VRAM
  - `qwen2.5-coder:7b` - Good for most tasks
  - `deepseek-coder-v2:lite` - Ultra-lightweight (1.6GB)
  
- **Recommended (14B models)**: 16GB+ GPU VRAM
  - `qwen2.5-coder:14b` - Better code quality
  - Faster inference with larger context windows

---

## Recommended Hardware Configurations

### 🎯 Tier 1: Budget-Friendly (Minimum Viable)

**Target:** Run 7B models efficiently, handle small-medium projects

| Component | Specification | Rationale |
|-----------|---------------|-----------|
| **CPU** | Intel Core i5-12400 / AMD Ryzen 5 5600 (6 cores) | Sufficient for code analysis tools |
| **GPU** | NVIDIA RTX 3060 (12GB VRAM) | Minimum for 7B models, can run 14B with quantization |
| **RAM** | 16GB DDR4 | Adequate for IDE + framework + analysis tools |
| **Storage** | 512GB NVMe SSD | Fast enough for development workflow |
| **OS** | Windows 11 / Linux / macOS | All supported |

**Estimated Cost:** $800-1,200 (desktop) / $1,200-1,800 (laptop)

**Performance Expectations:**
- Code generation: 5-15 tokens/second (7B model)
- Code review: 2-5 seconds per file
- Quality analysis: 10-30 seconds per service

---

### ⚡ Tier 2: Recommended (Optimal Balance)

**Target:** Run 14B models smoothly, handle large projects, fast development

| Component | Specification | Rationale |
|-----------|---------------|-----------|
| **CPU** | Intel Core i7-13700K / AMD Ryzen 7 7700X (8+ cores) | Excellent for parallel code analysis |
| **GPU** | NVIDIA RTX 4070 (12GB) / RTX 4060 Ti 16GB | Ideal for 14B models, fast inference |
| **RAM** | 32GB DDR5 | Comfortable headroom for multitasking |
| **Storage** | 1TB NVMe SSD (PCIe 4.0) | Fast project loading, quick file operations |
| **OS** | Windows 11 / Linux / macOS | All supported |

**Estimated Cost:** $1,500-2,500 (desktop) / $2,000-3,500 (laptop)

**Performance Expectations:**
- Code generation: 15-30 tokens/second (14B model)
- Code review: 1-3 seconds per file
- Quality analysis: 5-15 seconds per service

---

### 🚀 Tier 3: High-End (Maximum Performance)

**Target:** Run multiple models, handle enterprise projects, fastest development

| Component | Specification | Rationale |
|-----------|---------------|-----------|
| **CPU** | Intel Core i9-13900K / AMD Ryzen 9 7900X (12+ cores) | Maximum parallel processing |
| **GPU** | NVIDIA RTX 4080 (16GB) / RTX 4090 (24GB) | Run 14B+ models, multiple instances |
| **RAM** | 64GB DDR5 | Run multiple IDEs, large codebases |
| **Storage** | 2TB NVMe SSD (PCIe 4.0/5.0) | Large project storage, fast indexing |
| **OS** | Windows 11 / Linux / macOS | All supported |

**Estimated Cost:** $2,500-4,000 (desktop) / $3,500-6,000 (laptop)

**Performance Expectations:**
- Code generation: 30-60 tokens/second (14B model)
- Code review: <1 second per file
- Quality analysis: 3-10 seconds per service

---

## Platform-Specific Recommendations

### 🍎 macOS (Apple Silicon)

**Best Options:**
- **MacBook Pro 16" M3 Max** (14-core CPU, 40-core GPU, 96GB RAM)
  - Excellent for development, unified memory architecture
  - GPU performance: Equivalent to RTX 4070 for inference
  - **Pros:** Long battery life, excellent display, native optimization
  - **Cons:** More expensive, limited GPU upgrade path

- **MacBook Pro 14" M3 Pro** (12-core CPU, 18-core GPU, 36GB RAM)
  - Good balance for most developers
  - Can run 7B models efficiently, 14B with some limitations

**Note:** Apple Silicon uses unified memory, so GPU VRAM shares with system RAM. 36GB+ recommended for 14B models.

### 🪟 Windows / Linux (x86-64)

**Desktop Recommendations:**
- **Custom Build** (Tier 2 specs above) - Best value
- **Pre-built:** HP Omen, Dell XPS Desktop, Lenovo ThinkStation

**Laptop Recommendations:**
- **Lenovo ThinkPad P1 Gen 7** - Professional, RTX GPU options
- **Dell XPS 17** - Large display, powerful specs
- **ASUS ROG Zephyrus G14** - Compact, powerful GPU
- **Razer Blade 16** - Premium build, RTX 5090 option

---

## GPU-Specific Guidance

### NVIDIA RTX Series (Recommended)

| GPU Model | VRAM | 7B Models | 14B Models | Notes |
|-----------|------|-----------|------------|-------|
| **RTX 3060** | 12GB | ✅ Excellent | ⚠️ With quantization | Budget option |
| **RTX 4060 Ti** | 16GB | ✅ Excellent | ✅ Good | Best value |
| **RTX 4070** | 12GB | ✅ Excellent | ✅ Good | Fast inference |
| **RTX 4070 Ti** | 12GB | ✅ Excellent | ✅ Good | Faster than 4070 |
| **RTX 4080** | 16GB | ✅ Excellent | ✅ Excellent | High-end |
| **RTX 4090** | 24GB | ✅ Excellent | ✅ Excellent | Run multiple models |

### AMD GPUs

- **RX 6700 XT / 6800 XT** (12-16GB) - Supported but slower than NVIDIA
- Ollama has better NVIDIA CUDA support
- Consider NVIDIA for best performance

### Apple Silicon (M-series)

- **M3 Max** (40-core GPU) - Excellent for 7B, good for 14B
- **M3 Pro** (18-core GPU) - Good for 7B, limited for 14B
- Unified memory architecture is efficient

---

## Performance Optimization Tips

### 1. GPU Optimization

```bash
# Use appropriate model size for your GPU
# 8GB GPU: qwen2.5-coder:7b
# 16GB+ GPU: qwen2.5-coder:14b

# Monitor GPU usage
ollama ps

# Use quantization for larger models on smaller GPUs
ollama pull qwen2.5-coder:14b-q4_K_M  # Quantized 14B model
```

### 2. CPU Optimization

- **Enable multi-core processing** for code analysis:
  - Ruff: Automatically uses all cores
  - pytest: Use `-n auto` with pytest-xdist
  - mypy: Uses multiple cores by default

### 3. RAM Optimization

- **Close unused applications** when running large models
- **Use cloud fallback** for very large models if GPU is insufficient
- **Monitor memory usage** with Task Manager / Activity Monitor

### 4. Storage Optimization

- **Use NVMe SSD** for project directory
- **Store models on fast drive** (Ollama model cache)
- **Keep 20% free space** for optimal SSD performance

### 5. Development Environment

- **Use Cursor IDE** - Optimized for AI coding assistants
- **Enable indexing** for faster code navigation
- **Use virtual environments** to isolate dependencies
- **Keep Python updated** (3.13+ recommended)

---

## Cloud Fallback Strategy

If local GPU is insufficient, configure cloud fallback:

```yaml
# .tapps-agents/config.yaml
mal:
  ollama_url: "http://localhost:11434"
  default_model: "qwen2.5-coder:7b"
  fallback:
    provider: "anthropic"  # or "openai"
    model: "claude-3.5-haiku"
    api_key: "${ANTHROPIC_API_KEY}"
```

**Benefits:**
- Use smaller local model for quick tasks
- Fall back to cloud for complex tasks
- Cost-effective hybrid approach

---

## Real-World Performance Benchmarks

Based on project documentation and typical usage:

### Code Generation (7B Model)
- **RTX 3060 (12GB)**: 8-12 tokens/sec
- **RTX 4070 (12GB)**: 20-25 tokens/sec
- **RTX 4090 (24GB)**: 40-50 tokens/sec
- **M3 Max (40-core GPU)**: 15-20 tokens/sec

### Code Review (Single File)
- **Budget Setup**: 3-8 seconds
- **Recommended Setup**: 1-3 seconds
- **High-End Setup**: <1 second

### Quality Analysis (Multi-file Service)
- **Budget Setup**: 20-45 seconds
- **Recommended Setup**: 8-20 seconds
- **High-End Setup**: 5-12 seconds

---

## Cost-Benefit Analysis

### Budget Tier ($800-1,200)
- ✅ Can run 7B models efficiently
- ✅ Handles small-medium projects
- ⚠️ Slower for large codebases
- ⚠️ May struggle with 14B models

### Recommended Tier ($1,500-2,500)
- ✅ **Best value** - Optimal price/performance
- ✅ Runs 14B models smoothly
- ✅ Fast development workflow
- ✅ Handles large projects
- ✅ **Recommended for most developers**

### High-End Tier ($2,500+)
- ✅ Maximum performance
- ✅ Run multiple models simultaneously
- ✅ Fastest development experience
- ⚠️ Diminishing returns for most users
- ⚠️ Only needed for enterprise-scale projects

---

## Specific Recommendations by Use Case

### Solo Developer / Small Projects
**Recommended:** Tier 1 (Budget-Friendly)
- RTX 3060 or RTX 4060 Ti
- 16GB RAM
- 512GB SSD
- **Total:** ~$1,200

### Professional Developer / Medium Projects
**Recommended:** Tier 2 (Optimal Balance) ⭐ **BEST CHOICE**
- RTX 4070 or RTX 4060 Ti 16GB
- 32GB RAM
- 1TB NVMe SSD
- **Total:** ~$2,000

### Enterprise / Large Codebases
**Recommended:** Tier 3 (High-End)
- RTX 4080 or RTX 4090
- 64GB RAM
- 2TB NVMe SSD
- **Total:** ~$3,500+

### macOS Developer
**Recommended:** MacBook Pro 16" M3 Max
- 36GB+ unified memory
- Excellent for development
- Native optimization
- **Total:** ~$3,500+

---

## Checklist: Is Your System Ready?

Before starting development, verify:

- [ ] **GPU**: 8GB+ VRAM (12GB+ recommended)
- [ ] **RAM**: 16GB minimum (32GB recommended)
- [ ] **Storage**: NVMe SSD with 100GB+ free
- [ ] **CPU**: 6+ cores (8+ recommended)
- [ ] **Python**: 3.10+ installed
- [ ] **Ollama**: Installed and running
- [ ] **Model**: At least one coding model pulled (7B or 14B)

**Test your setup:**
```bash
# Verify Ollama is working
ollama run qwen2.5-coder:7b "Write a hello world function"

# Test TappsCodingAgents
python -m tapps_agents.cli reviewer help
```

---

## Future-Proofing Considerations

### Model Size Trends
- Models are getting larger (70B+ becoming common)
- Consider 16GB+ GPU for future-proofing
- Cloud fallback becomes more important

### Framework Evolution
- More parallel processing (multi-agent workflows)
- Larger context windows (need more VRAM)
- Real-time collaboration features

### Recommendations
- **Invest in GPU VRAM** (16GB+ recommended)
- **More RAM is better** (32GB+ for future-proofing)
- **Fast storage** (PCIe 4.0+ NVMe)

---

## Additional Resources

- **Ollama Model Library**: https://ollama.com/library
- **GPU Benchmarks**: https://www.techpowerup.com/gpu-specs/
- **Project Quick Start**: [QUICK_START.md](../QUICK_START.md)
- **Architecture Details**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Summary

**For most developers, we recommend:**

1. **Desktop**: Custom build with RTX 4070 (12GB), 32GB RAM, 1TB NVMe SSD (~$2,000)
2. **Laptop**: Lenovo ThinkPad P1 Gen 7 or Dell XPS 17 with RTX GPU (~$2,500)
3. **macOS**: MacBook Pro 16" M3 Max with 36GB+ RAM (~$3,500)

**Key Takeaways:**
- GPU VRAM is the primary bottleneck (12GB+ recommended)
- 32GB RAM provides comfortable headroom
- NVMe SSD significantly improves workflow speed
- Tier 2 (Recommended) offers best value for most users

**Remember:** You can always start with a smaller setup and use cloud fallback for larger models. The framework is designed to work efficiently across different hardware configurations.

---

**Questions?** Check the [Troubleshooting Guide](TROUBLESHOOTING.md) or open an issue on GitHub.

