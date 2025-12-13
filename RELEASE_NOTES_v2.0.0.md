# Release Notes - TappsCodingAgents v2.0.0

**Release Date:** December 13, 2025  
**Version:** 2.0.0  
**Tag:** v2.0.0

## 🚀 Highlights

- **Built-in Expert System (16 experts)** with a large curated technical knowledge base (83 files, ~320k+ words)
- **Dual-layer expert architecture**: framework-controlled built-in experts + user-controlled customer experts
- **Priority-based consultation** with automatic technical vs business domain routing
- **New agent integration patterns** via `ExpertSupportMixin`
- **Comprehensive docs + tests** for the expert system

## ✨ Added

### Built-in Expert System (Framework-Controlled)

Built-in experts are technical-domain specialists shipped with the framework (immutable, versioned with the repo).

- **Security Expert** (`expert-security`)
- **Performance Expert** (`expert-performance`)
- **Testing Expert** (`expert-testing`)
- **Data Privacy Expert** (`expert-data-privacy`)
- **Accessibility Expert** (`expert-accessibility`)
- **User Experience Expert** (`expert-user-experience`)
- **Code Quality Expert** (`expert-code-quality`)
- **Software Architecture Expert** (`expert-software-architecture`)
- **Development Workflow Expert** (`expert-devops`)
- **Documentation Expert** (`expert-documentation`)
- **AI Agent Framework Expert** (`expert-ai-frameworks`)
- **Agent Learning Expert** (`expert-agent-learning`)

### Phase 5: High-Priority Production Experts

- **Observability & Monitoring Expert** (`expert-observability`)
- **API Design & Integration Expert** (`expert-api-design`)
- **Cloud & Infrastructure Expert** (`expert-cloud-infrastructure`)
- **Database & Data Management Expert** (`expert-database`)

### Dual-Layer Expert Architecture

- Built-in experts (framework-controlled, technical domains)
- Customer experts (user-controlled, business domains)
- Automatic priority system with **51% primary authority** weighting
- `prioritize_builtin` support for consultation flows

### Enhanced Expert Registry + Agent Support

- `BuiltinExpertRegistry` for managing built-in experts
- Auto-loading built-in experts on initialization (`load_builtin=True`)
- Automatic domain classification (technical vs business)
- `ExpertSupportMixin` for easy agent integration
  - `_consult_builtin_expert()` convenience method
  - `_consult_customer_expert()` convenience method

### Documentation & Examples

- Built-in experts guide: `docs/BUILTIN_EXPERTS_GUIDE.md`
- Expert knowledge base guide: `docs/EXPERT_KNOWLEDGE_BASE_GUIDE.md`
- Migration guide: `docs/MIGRATION_GUIDE_2.0.md`
- Updated API docs: `docs/API.md`

## 🔄 Changed

- **Expert Registry**: now auto-loads built-in experts by default (`load_builtin=True`)
- **BaseExpert**: supports built-in knowledge bases via `_builtin_knowledge_path`
- **Consultation API**: enhanced with `prioritize_builtin` and automatic domain detection
- **Expert selection**: automatic technical-domain priority (built-in) vs business-domain priority (customer)
- Added technical domains:
  - `observability-monitoring`
  - `api-design-integration`
  - `cloud-infrastructure`
  - `database-data-management`

## 🧪 Testing

- Added **15 tests** covering dual-layer expert behavior (domain classification, priority system, consultation flow)

## ⚠️ Breaking Changes

- **None**: existing expert configurations continue to work
- Legacy consultation API remains functional (with deprecation warnings where applicable)

## 🔧 Technical Notes

- Built-in knowledge bases: `tapps_agents/experts/knowledge/`
- Customer knowledge bases remain: `.tapps-agents/knowledge/`

## 📦 Installation

```bash
pip install tapps-agents==2.0.0
```

## 📝 Full Changelog

See `CHANGELOG.md` for complete details.


