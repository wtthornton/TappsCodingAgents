# Feedback and Session Notes

Session feedback, completion summaries, and improvement plans have been moved to the **[Documentation Archive](../archive/README.md)** under `archive/feedback/`.

For current behavior and guides, see the [Documentation Index](../README.md).

## Including health metrics in feedback reports

**When writing feedback on how well tapps-agents helps (e.g. "feedback on how well tapps-agents helps you as an LLM"), include health metrics in the report or document.**

1. Run: `tapps-agents health overview` (or `tapps-agents health usage dashboard`).
2. Run: `tapps-agents dashboard --no-open` to generate the Performance Insight Dashboard HTML (`.tapps-agents/dashboard/dashboard.html`).
3. Include the health overview output or a short summary in your feedback (e.g. overall health, subsystem status, usage at a glance). Reference or attach the dashboard HTML for detailed visual metrics.
4. This makes feedback actionable and comparable across sessions. Place feedback docs in `docs/feedback/` or `docs/archive/feedback/` per [docs/archive/README.md](../archive/README.md).
