# Hardware Recommendations for TappsCodingAgents

**Last Updated:** January 2026  
**Project Version:** 2.0.8

## Executive Summary

TappsCodingAgents is designed to work **Cursor-first**:

- **Cursor provides the LLM runtime** (using the developer’s configured model).
- The framework provides the **tooling layer** (workflows, reports, quality tools, caching).
- **No local LLM required** - All LLM operations are handled by Cursor Skills.

To run this project efficiently, optimize for:

1. **Cursor + development workflow** - CPU/RAM for IDE + indexing + tooling
2. **Python tooling** - Ruff, mypy, pytest, report generation
3. **Fast I/O** - SSD for code indexing, caches, and reports

---

## Project Requirements Analysis

### Core Components

| Component | Resource Impact | Notes |
|-----------|----------------|-------|
| **Cursor (LLM runtime)** | Network + CPU/RAM | Uses developer-configured model (Auto or pinned) |
| **Python Runtime** | RAM: 2-4GB | Framework + dependencies |
| **Code Analysis Tools** | CPU: Multi-core | Ruff, mypy, pytest run in parallel |
| **IDE (Cursor/VS Code)** | RAM: 2-4GB | Language servers, extensions |
| **Quality Reports** | Storage: Fast SSD | HTML/JSON report generation |

### LLM Requirements

All LLM operations are handled by Cursor Skills, which use the developer's configured model in Cursor.
No local GPU or VRAM is required for LLM operations - Cursor handles all model execution.

---

## Recommended Hardware Configurations

### 🎯 Tier 1: Budget-Friendly (Minimum Viable)

**Target:** Handle small-medium projects efficiently

| Component | Specification | Rationale |
|-----------|---------------|-----------|
| **CPU** | Intel Core i5-12400 / AMD Ryzen 5 5600 (6 cores) | Sufficient for code analysis tools |
| **GPU** | Integrated graphics or entry-level GPU | No GPU required for LLM operations (handled by Cursor) |
| **RAM** | 16GB DDR4 | Adequate for IDE + framework + analysis tools |
| **Storage** | 512GB NVMe SSD | Fast enough for development workflow |
| **OS** | Windows 11 / Linux / macOS | All supported |

**Estimated Cost:** $600-1,000 (desktop) / $800-1,500 (laptop)

**Performance Expectations:**
- Code review: 2-5 seconds per file
- Quality analysis: 10-30 seconds per service
- All LLM operations handled by Cursor (performance depends on Cursor's configured model)

---

### ⚡ Tier 2: Recommended (Optimal Balance)

**Target:** Handle large projects efficiently, fast development

| Component | Specification | Rationale |
|-----------|---------------|-----------|
| **CPU** | Intel Core i7-13700K / AMD Ryzen 7 7700X (8+ cores) | Excellent for parallel code analysis |
| **GPU** | Integrated graphics or mid-range GPU | No GPU required for LLM operations (handled by Cursor) |
| **RAM** | 32GB DDR5 | Comfortable headroom for multitasking |
| **Storage** | 1TB NVMe SSD (PCIe 4.0) | Fast project loading, quick file operations |
| **OS** | Windows 11 / Linux / macOS | All supported |

**Estimated Cost:** $1,200-2,000 (desktop) / $1,500-2,500 (laptop)

**Performance Expectations:**
- Code review: 1-3 seconds per file
- Quality analysis: 5-15 seconds per service
- All LLM operations handled by Cursor (performance depends on Cursor's configured model)

---

### 🚀 Tier 3: High-End (Maximum Performance)

**Target:** Handle enterprise projects, fastest development

| Component | Specification | Rationale |
|-----------|---------------|-----------|
| **CPU** | Intel Core i9-13900K / AMD Ryzen 9 7900X (12+ cores) | Maximum parallel processing |
| **GPU** | Integrated graphics or mid-range GPU | No GPU required for LLM operations (handled by Cursor) |
| **RAM** | 64GB DDR5 | Run multiple IDEs, large codebases |
| **Storage** | 2TB NVMe SSD (PCIe 4.0/5.0) | Large project storage, fast indexing |
| **OS** | Windows 11 / Linux / macOS | All supported |

**Estimated Cost:** $2,000-3,500 (desktop) / $2,500-4,500 (laptop)

**Performance Expectations:**
- Code review: <1 second per file
- Quality analysis: 3-10 seconds per service
- All LLM operations handled by Cursor (performance depends on Cursor's configured model)

---

## Platform-Specific Recommendations

### 🍎 macOS (Apple Silicon)

**Best Options:**
- **MacBook Pro 16" M3 Max** (14-core CPU, 40-core GPU, 96GB RAM)
  - Excellent for development, unified memory architecture
  - **Pros:** Long battery life, excellent display, native optimization
  - **Cons:** More expensive

- **MacBook Pro 14" M3 Pro** (12-core CPU, 18-core GPU, 36GB RAM)
  - Good balance for most developers
  - Excellent for all development tasks

**Note:** No GPU requirements for LLM operations - all handled by Cursor Skills.

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

## GPU Requirements

**No GPU required for LLM operations** - All LLM operations are handled by Cursor Skills, which use the developer's configured model in Cursor. Any GPU in your system is only used for display and general computing tasks, not for LLM inference.

---

## Performance Optimization Tips

### 1. CPU Optimization

- **Enable multi-core processing** for code analysis:
  - Ruff: Automatically uses all cores
  - pytest: Use `-n auto` with pytest-xdist
  - mypy: Uses multiple cores by default

### 2. RAM Optimization

- **Close unused applications** when running large code analysis tasks
- **Monitor memory usage** with Task Manager / Activity Monitor

### 3. Storage Optimization

- **Use NVMe SSD** for project directory
- **Store caches on fast drive** (Context7 cache, report files)
- **Keep 20% free space** for optimal SSD performance

### 5. Development Environment

- **Use Cursor IDE** - Optimized for AI coding assistants
- **Enable indexing** for faster code navigation
- **Use virtual environments** to isolate dependencies
- **Keep Python updated** (3.13+ recommended)

---

## LLM Operations

All LLM operations are handled by Cursor Skills, which use the developer's configured model in Cursor.
No local GPU, API keys, or model management is required. Cursor handles all model selection and execution automatically.

---

## Real-World Performance Benchmarks

Based on project documentation and typical usage:

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

### Budget Tier ($600-1,000)
- ✅ Handles small-medium projects efficiently
- ✅ Adequate for most development tasks
- ⚠️ Slower for large codebases

### Recommended Tier ($1,200-2,000)
- ✅ **Best value** - Optimal price/performance
- ✅ Fast development workflow
- ✅ Handles large projects
- ✅ **Recommended for most developers**

### High-End Tier ($2,000+)
- ✅ Maximum performance
- ✅ Fastest development experience
- ✅ Best for enterprise-scale projects
- ⚠️ Diminishing returns for most users

---

## Specific Recommendations by Use Case

### Solo Developer / Small Projects
**Recommended:** Tier 1 (Budget-Friendly)
- Integrated graphics or entry-level GPU
- 16GB RAM
- 512GB SSD
- **Total:** ~$800-1,000

### Professional Developer / Medium Projects
**Recommended:** Tier 2 (Optimal Balance) ⭐ **BEST CHOICE**
- Integrated graphics or mid-range GPU
- 32GB RAM
- 1TB NVMe SSD
- **Total:** ~$1,500-2,000

### Enterprise / Large Codebases
**Recommended:** Tier 3 (High-End)
- Integrated graphics or mid-range GPU
- 64GB RAM
- 2TB NVMe SSD
- **Total:** ~$2,500-3,500

### macOS Developer
**Recommended:** MacBook Pro 16" M3 Max or M3 Pro
- 36GB+ unified memory
- Excellent for development
- Native optimization
- **Total:** ~$2,500-4,000

---

## Checklist: Is Your System Ready?

Before starting development, verify:

- [ ] **RAM**: 16GB minimum (32GB recommended)
- [ ] **Storage**: NVMe SSD with 100GB+ free
- [ ] **CPU**: 6+ cores (8+ recommended)
- [ ] **Python**: 3.13+ installed
- [ ] **Cursor IDE**: Installed and configured
- [ ] **Cursor Skills**: Installed via `tapps-agents init`

**Test your setup:**
```bash
# Test TappsCodingAgents
python -m tapps_agents.cli reviewer help

# Verify Cursor Skills are installed
ls .claude/skills/
```

---

## Future-Proofing Considerations

### Future Considerations
- All LLM operations handled by Cursor - no local model management needed
- Cursor handles model selection and optimization automatically
- Focus on CPU/RAM for code analysis tools rather than GPU for LLM inference

### Framework Evolution
- More parallel processing (multi-agent workflows)
- Enhanced code analysis capabilities
- Real-time collaboration features

### Recommendations
- **More RAM is better** (32GB+ for future-proofing)
- **Fast storage** (PCIe 4.0+ NVMe)
- **CPU cores** for parallel code analysis tools

---

## Additional Resources

- **Project Quick Start**: [QUICK_START.md](../guides/QUICK_START.md)
- **Architecture Details**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Cursor Skills Installation**: [CURSOR_SKILLS_INSTALLATION_GUIDE.md](CURSOR_SKILLS_INSTALLATION_GUIDE.md)

---

## Summary

**For most developers, we recommend:**

1. **Desktop**: Custom build with integrated graphics or mid-range GPU, 32GB RAM, 1TB NVMe SSD (~$1,500-2,000)
2. **Laptop**: Any modern laptop with 32GB RAM and fast SSD (~$1,500-2,500)
3. **macOS**: MacBook Pro 14" M3 Pro or 16" M3 Max with 36GB+ RAM (~$2,500-4,000)

**Key Takeaways:**
- No GPU required for LLM operations (all handled by Cursor)
- 32GB RAM provides comfortable headroom for development
- NVMe SSD significantly improves workflow speed
- Tier 2 (Recommended) offers best value for most users

**Remember:** All LLM operations are handled by Cursor Skills. Focus on CPU, RAM, and storage for optimal code analysis performance.

---

**Questions?** Check the [Troubleshooting Guide](TROUBLESHOOTING.md) or open an issue on GitHub.

