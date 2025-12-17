# Epic 15: Analytics Dashboard Integration

## Epic Goal

Integrate analytics and reporting capabilities into Cursor, providing visibility into workflow performance, agent usage, quality trends, and project metrics. This enables data-driven decisions and continuous improvement.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Analytics exist via CLI (`python -m tapps_agents.cli analytics dashboard`), but not integrated into Cursor. Analytics data is collected but may not be easily accessible in Cursor interface. Reporting exists but requires CLI access
- **Technology stack**: Python 3.13+, analytics system, reporting engine, Cursor chat interface
- **Integration points**: 
  - `tapps_agents/cli/commands/analytics.py` - Analytics commands
  - Analytics data collection system
  - Reporting engine
  - Cursor chat interface

### Enhancement Details

- **What's being added/changed**: 
  - Create Cursor-integrated analytics display
  - Implement dashboard rendering in Cursor chat
  - Add real-time analytics updates
  - Create analytics query system (ask questions about data)
  - Implement analytics visualization (charts, graphs, trends)
  - Add analytics alerts (notify on trends, thresholds)
  - Create analytics export (share reports)

- **How it integrates**: 
  - Analytics displayed in Cursor chat
  - Dashboard accessible via natural language or commands
  - Works with existing analytics data collection
  - Integrates with reporting engine
  - Uses Cursor chat for visualization

- **Success criteria**: 
  - Analytics accessible in Cursor
  - Dashboard displays key metrics
  - Real-time updates work
  - Analytics queries return useful information
  - Visualizations are clear and helpful

## Stories

1. **Story 15.1: Analytics Data Access**
   - Create analytics data access layer for Cursor
   - Implement data query system (fetch analytics data)
   - Add data aggregation (summarize metrics)
   - Create data caching (performance optimization)
   - Acceptance criteria: Data accessible, queries work, aggregation accurate, caching effective

2. **Story 15.2: Dashboard Rendering in Cursor**
   - Implement dashboard rendering in Cursor chat
   - Create dashboard layout (key metrics, charts)
   - Add dashboard formatting (markdown, tables)
   - Implement dashboard update mechanism
   - Acceptance criteria: Dashboard renders, layout clear, formatting readable, updates work

3. **Story 15.3: Analytics Visualization**
   - Create visualization system (charts, graphs, trends)
   - Implement text-based charts (ASCII, markdown)
   - Add trend visualization (improvements, regressions)
   - Create metric comparison (before/after, period comparison)
   - Acceptance criteria: Visualizations render, charts readable, trends clear, comparisons accurate

4. **Story 15.4: Analytics Queries and Natural Language**
   - Implement natural language analytics queries
   - Create query parser (understand user questions)
   - Add query execution (fetch and format results)
   - Implement query suggestions (help users ask questions)
   - Acceptance criteria: Queries parsed, execution works, results formatted, suggestions helpful

5. **Story 15.5: Analytics Alerts and Export**
   - Create alert system (notify on trends, thresholds)
   - Implement alert configuration (what to alert on)
   - Add analytics export (share reports, export data)
   - Create alert formatting for Cursor chat
   - Acceptance criteria: Alerts triggered, configuration works, export functions, formatting clear

## Compatibility Requirements

- [ ] Analytics integration is optional (can be disabled)
- [ ] CLI analytics continue to work
- [ ] No breaking changes to analytics system
- [ ] Works with existing data collection
- [ ] Backward compatible with current analytics

## Risk Mitigation

- **Primary Risk**: Analytics queries may be slow
  - **Mitigation**: Caching, data aggregation, performance optimization, timeout limits
- **Primary Risk**: Visualizations may not render well in Cursor
  - **Mitigation**: Text fallback, markdown compatibility, graceful degradation, simple formats
- **Primary Risk**: Analytics data may be large
  - **Mitigation**: Data pagination, summary views, aggregation, size limits
- **Rollback Plan**: 
  - Disable Cursor analytics integration
  - Fall back to CLI analytics only
  - Remove integration without breaking analytics

## Definition of Done

- [x] All stories completed with acceptance criteria met
- [x] Analytics accessible in Cursor chat
- [x] Dashboard displays key metrics
- [x] Visualizations render correctly
- [x] Analytics queries work
- [x] Alerts and export functional
- [x] Comprehensive test coverage
- [x] Documentation complete (analytics, dashboard, queries)
- [x] No regression in CLI analytics
- [x] Analytics enhance user experience

## Implementation Status

**Last Updated:** 2025-01-27

**Overall Status:** ✅ Completed

**Story Status:**
- Story 15.1 (Data Access): ✅ Completed
- Story 15.2 (Dashboard Rendering): ✅ Completed
- Story 15.3 (Visualization): ✅ Completed
- Story 15.4 (Queries): ✅ Completed
- Story 15.5 (Alerts): ✅ Completed

## Implementation Summary

### Files Created:
- `tapps_agents/workflow/analytics_accessor.py` - Analytics data access layer with caching
- `tapps_agents/workflow/analytics_visualizer.py` - Text-based chart and visualization system
- `tapps_agents/workflow/analytics_dashboard_cursor.py` - Cursor chat dashboard rendering
- `tapps_agents/workflow/analytics_query_parser.py` - Natural language query parser
- `tapps_agents/workflow/analytics_alerts.py` - Alert management and export system
- `tapps_agents/workflow/analytics_integration.py` - Integration helper functions
- `docs/stories/15.1.analytics-data-access.md` - Story documentation
- `docs/stories/15.2.dashboard-rendering.md` - Story documentation
- `docs/stories/15.3.analytics-visualization.md` - Story documentation
- `docs/stories/15.4.analytics-queries.md` - Story documentation
- `docs/stories/15.5.analytics-alerts-export.md` - Story documentation

### Key Features Implemented:

1. **Analytics Data Access** (Story 15.1):
   - `CursorAnalyticsAccessor` class with unified interface
   - Data caching with configurable TTL (default: 60 seconds)
   - Query methods for agents, workflows, system metrics, and trends
   - Data aggregation (summary, totals, averages)
   - Cache invalidation support

2. **Dashboard Rendering** (Story 15.2):
   - `CursorAnalyticsDashboard` class for Cursor chat display
   - Formatted dashboard with system metrics, agent performance, workflow performance
   - Markdown formatting for readability
   - Integration with ChatUpdateSender for display
   - Support for agent and workflow summaries

3. **Analytics Visualization** (Story 15.3):
   - `AnalyticsVisualizer` class for text-based charts
   - ASCII bar charts and line charts
   - Trend visualization with emoji indicators (📈 improving, 📉 declining)
   - Period comparison (before/after, current vs previous)
   - Metric table formatting

4. **Analytics Queries** (Story 15.4):
   - `AnalyticsQueryParser` class for natural language parsing
   - Support for common query patterns ("show analytics", "agent performance", etc.)
   - Query execution with filtering (agent_id, workflow_id, time range)
   - Query suggestions for ambiguous queries
   - Integration with analytics accessor

5. **Analytics Alerts and Export** (Story 15.5):
   - `AnalyticsAlertManager` class for threshold-based alerts
   - Alert configuration with severity levels (info, warning, critical)
   - Alert conditions (above, below thresholds)
   - `AnalyticsExporter` class for data export
   - Export formats: JSON, Markdown, Text
   - Alert notifications in Cursor chat

### Configuration:

Analytics can be controlled via environment variable:
- `TAPPS_AGENTS_ANALYTICS_ENABLED=true` (default) - Enable analytics
- `TAPPS_AGENTS_ANALYTICS_ENABLED=false` - Disable analytics

### Usage:

```python
from tapps_agents.workflow.analytics_integration import (
    handle_analytics_query,
    show_analytics_dashboard,
    check_analytics_alerts,
    export_analytics,
)

# Display dashboard
show_analytics_dashboard(days=30)

# Handle natural language query
response = handle_analytics_query("show agent performance last 7 days")
print(response)

# Check alerts
check_analytics_alerts()

# Export analytics
export_path = export_analytics(format="markdown")
print(f"Exported to: {export_path}")
```

### Backward Compatibility:

- Analytics integration is optional (can be disabled)
- CLI analytics continue to work
- No breaking changes to analytics system
- Works with existing data collection
- Backward compatible with current analytics

