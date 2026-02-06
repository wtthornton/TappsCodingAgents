"""
Collects metrics from all tapps-agents subsystems into a unified
JSON-serializable dict suitable for embedding in the HTML dashboard.

Every ``collect_*`` method is fault-tolerant: if a subsystem is not
configured or has no data, it returns sensible defaults so the
dashboard always renders.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────

def _safe(fn, default: Any = None):
    """Call *fn* and swallow exceptions, returning *default* on failure."""
    try:
        return fn()
    except Exception as exc:
        logger.debug("Dashboard data collection error: %s", exc)
        return default


def _ts() -> str:
    return datetime.now(tz=UTC).isoformat()


def _read_jsonl(path: Path, limit: int = 1000) -> list[dict]:
    """Read up to *limit* lines from a JSONL file."""
    entries: list[dict] = []
    if not path.exists():
        return entries
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
                    if len(entries) >= limit:
                        break
    except Exception:
        pass
    return entries


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# ── Main Collector ────────────────────────────────────────────────────

class DashboardDataCollector:
    """Gathers metrics from every subsystem into one dict."""

    def __init__(self, project_root: Path, days: int = 30):
        self.project_root = project_root
        self.days = days
        self.tapps_dir = project_root / ".tapps-agents"

    # ── public entry point ────────────────────────────────────────────

    def collect_all(self) -> dict[str, Any]:
        """Return the full dashboard payload."""
        return {
            "meta": self._meta(),
            "health": self.collect_health(),
            "agents": self.collect_agents(),
            "experts": self.collect_experts(),
            "cache": self.collect_cache(),
            "quality": self.collect_quality(),
            "workflows": self.collect_workflows(),
            "learning": self.collect_learning(),
            "events": self.collect_events(),
            "recommendations": [],  # filled by generator after analysis
        }

    # ── meta ──────────────────────────────────────────────────────────

    def _meta(self) -> dict:
        version = "unknown"
        try:
            from tapps_agents import __version__
            version = __version__
        except Exception:
            pass
        return {
            "project_name": self.project_root.name,
            "generated_at": _ts(),
            "days": self.days,
            "tapps_agents_version": version,
        }

    # ── health ────────────────────────────────────────────────────────

    def collect_health(self) -> dict[str, Any]:
        default = {"overall_score": 0, "checks": [], "trends": {}}

        def _do():
            from tapps_agents.health.collector import HealthMetricsCollector

            hmc = HealthMetricsCollector(project_root=self.project_root)
            summary = hmc.get_summary(days=self.days)

            # HealthMetricsCollector returns "by_check" (dict keyed by check name),
            # not "checks" (list). Adapt to list format for dashboard rendering.
            checks = []
            by_check = summary.get("by_check", {})
            for check_name, info in by_check.items():
                checks.append({
                    "name": check_name,
                    "status": info.get("latest_status", "unknown"),
                    "score": info.get("latest_score", info.get("average_score", 0)),
                    "details": {"count": info.get("count", 0), "avg_score": info.get("average_score", 0)},
                    "remediation": [],
                })

            overall = summary.get("average_score", summary.get("overall_score", 0))
            if not overall and checks:
                scores = [c["score"] for c in checks if c["score"]]
                overall = sum(scores) / len(scores) if scores else 0

            trends: dict[str, list] = {}
            for check in checks:
                name = check["name"]
                trend_data = _safe(lambda n=name: hmc.get_trends(n, days=self.days))
                if trend_data:
                    trends[name] = trend_data if isinstance(trend_data, list) else [trend_data]

            return {"overall_score": overall, "checks": checks, "trends": trends}

        return _safe(_do, default)

    # ── agents ────────────────────────────────────────────────────────

    def collect_agents(self) -> dict[str, Any]:
        default = {"summary": {"total": 14, "active": 0, "avg_success_rate": 0}, "agents": []}

        def _do():
            from tapps_agents.core.analytics_dashboard import AnalyticsDashboard

            ad = AnalyticsDashboard(analytics_dir=self.tapps_dir / "analytics")
            agent_perf = ad.get_agent_performance()

            agents = []
            for ap in agent_perf:
                # success_rate from AnalyticsDashboard is 0.0-1.0; convert to percentage
                raw_rate = ap.get("success_rate", 0)
                # average_duration from AnalyticsDashboard is in seconds; convert to ms
                raw_dur = ap.get("average_duration", 0)
                agents.append({
                    "name": ap.get("agent_name", ap.get("agent_id", "unknown")),
                    "executions": ap.get("total_executions", 0),
                    "success_rate": round(raw_rate * 100, 1),
                    "avg_duration_ms": round(raw_dur * 1000, 1),
                    "last_run": ap.get("last_execution", ""),
                    "trend": ap.get("trend", []),
                })

            active = sum(1 for a in agents if a["executions"] > 0)
            rates = [a["success_rate"] for a in agents if a["executions"] > 0]
            avg_rate = sum(rates) / len(rates) if rates else 0

            return {
                "summary": {"total": 14, "active": active, "avg_success_rate": round(avg_rate, 1)},
                "agents": agents,
            }

        return _safe(_do, default)

    # ── experts ───────────────────────────────────────────────────────

    def collect_experts(self) -> dict[str, Any]:
        default = {
            "summary": {"total": 0, "active": 0, "avg_confidence": 0},
            "experts": [],
            "confidence_distribution": {"low": 0, "medium": 0, "high": 0, "very_high": 0},
            "roi": {"time_saved_hours": 0, "bugs_prevented": 0, "roi_percentage": 0},
        }

        def _do():
            from tapps_agents.experts.performance_tracker import ExpertPerformanceTracker

            ept = ExpertPerformanceTracker(project_root=self.project_root)
            all_perf = ept.get_all_performance(days=self.days)

            experts = []
            confidences: list[float] = []
            for eid, perf in all_perf.items():
                experts.append({
                    "id": eid,
                    "consultations": perf.consultations,
                    "avg_confidence": round(perf.avg_confidence, 3),
                    "first_pass_rate": round(perf.first_pass_success_rate, 1),
                    "quality_impact": round(perf.code_quality_improvement, 2),
                    "domains": perf.domain_coverage,
                })
                if perf.consultations > 0:
                    confidences.append(perf.avg_confidence)

            active = sum(1 for e in experts if e["consultations"] > 0)
            avg_conf = sum(confidences) / len(confidences) if confidences else 0

            # Confidence distribution (all consulted experts)
            dist = {"low": 0, "medium": 0, "high": 0, "very_high": 0}
            for c in confidences:
                if c < 0.5:
                    dist["low"] += 1
                elif c < 0.7:
                    dist["medium"] += 1
                elif c < 0.85:
                    dist["high"] += 1
                else:
                    dist["very_high"] += 1

            # ROI from business metrics
            roi = {"time_saved_hours": 0, "bugs_prevented": 0, "roi_percentage": 0}
            bm_path = self.tapps_dir / "metrics" / "business_metrics.json"
            bm_data = _read_json(bm_path)
            if bm_data:
                roi_data = bm_data.get("roi_metrics", {})
                roi = {
                    "time_saved_hours": roi_data.get("estimated_time_saved_hours", 0),
                    "bugs_prevented": bm_data.get("effectiveness_metrics", {}).get("total_bugs_prevented", 0),
                    "roi_percentage": roi_data.get("roi_percentage", 0),
                }

            return {
                "summary": {"total": len(experts), "active": active, "avg_confidence": round(avg_conf, 3)},
                "experts": experts,
                "confidence_distribution": dist,
                "roi": roi,
            }

        return _safe(_do, default)

    # ── cache & RAG ───────────────────────────────────────────────────

    def collect_cache(self) -> dict[str, Any]:
        default = {
            "summary": {"total_entries": 0, "hit_rate": 0, "total_tokens": 0, "total_size_bytes": 0},
            "libraries": [],
            "skill_usage": [],
            "rag_quality_score": 0,
        }

        def _do():
            cache_root = self.tapps_dir / "kb" / "context7-cache"
            if not cache_root.exists():
                return default

            from tapps_agents.context7.cache_structure import CacheStructure
            from tapps_agents.context7.metadata import MetadataManager

            cs = CacheStructure(cache_root)
            mm = MetadataManager(cs)

            # Try to get cache metrics via Analytics
            summary = {"total_entries": 0, "hit_rate": 0, "total_tokens": 0, "total_size_bytes": 0}
            try:
                from tapps_agents.context7.analytics import Analytics
                analytics = Analytics(cs, mm)
                cm = analytics.get_cache_metrics()
                summary = {
                    "total_entries": cm.total_entries,
                    "hit_rate": round(cm.hit_rate, 1),
                    "total_tokens": cm.total_tokens,
                    "total_size_bytes": cm.total_size_bytes,
                }
            except Exception:
                pass

            # Per-library breakdown
            libraries = []
            idx = mm.load_cache_index()
            for lib_name in idx.libraries:
                meta = mm.load_library_metadata(lib_name)
                if meta:
                    libraries.append({
                        "name": lib_name,
                        "topics": len(meta.topics),
                        "hits": meta.cache_hits,
                        "tokens": meta.total_tokens,
                        "size_bytes": meta.total_size_bytes,
                        "last_accessed": meta.last_accessed or "",
                        "last_updated": meta.last_updated or "",
                    })

            # Skill usage
            skill_usage: list[dict] = []
            su_path = cache_root / "dashboard" / "skill-usage.json"
            su_raw = _read_json(su_path)
            if isinstance(su_raw, list):
                skill_usage = su_raw

            # RAG quality from business metrics
            rag_score = 0
            bm_path = self.tapps_dir / "metrics" / "business_metrics.json"
            bm_data = _read_json(bm_path)
            if bm_data:
                rag_score = bm_data.get("quality_metrics", {}).get("rag_quality_score", 0)

            return {
                "summary": summary,
                "libraries": libraries,
                "skill_usage": skill_usage,
                "rag_quality_score": rag_score,
            }

        return _safe(_do, default)

    # ── quality gates ─────────────────────────────────────────────────

    def collect_quality(self) -> dict[str, Any]:
        default = {
            "gate_pass_rate": 0,
            "avg_score": 0,
            "dimensions": {},
            "score_trend": [],
            "recent_failures": [],
        }

        def _do():
            from tapps_agents.workflow.execution_metrics import ExecutionMetricsCollector

            emc = ExecutionMetricsCollector(project_root=self.project_root)
            metrics = emc.get_metrics(limit=500)

            gate_total = 0
            gate_pass = 0
            scores: list[float] = []
            failures: list[dict] = []

            for m in metrics:
                if m.gate_pass is not None:
                    gate_total += 1
                    if m.gate_pass:
                        gate_pass += 1
                    else:
                        failures.append({
                            "workflow": m.workflow_id,
                            "step": m.step_id,
                            "skill": m.skill or "",
                            "date": m.started_at,
                            "error": (m.error_message or "")[:120],
                        })

            pass_rate = (gate_pass / gate_total * 100) if gate_total else 0

            # Compute dimension averages from execution skill summary
            skill_summary = emc.get_summary_by_skill()
            for _skill, info in skill_summary.items():
                if info.get("average_duration_ms"):
                    scores.append(info.get("gate_pass_rate", 0))

            avg_score = sum(scores) / len(scores) if scores else 0

            # Quality dimensions — read from recent reviewer outputs
            dimensions = {
                "complexity": 0, "security": 0, "maintainability": 0,
                "test_coverage": 0, "performance": 0, "structure": 0, "devex": 0,
            }
            review_dir = self.tapps_dir / "workflow-state"
            if review_dir.exists():
                dim_sums: dict[str, float] = {k: 0.0 for k in dimensions}
                dim_counts: dict[str, int] = {k: 0 for k in dimensions}
                review_files = sorted(review_dir.glob("**/review*.json"), reverse=True)[:50]
                for rf in review_files:
                    rd = _read_json(rf)
                    if not rd:
                        continue
                    dim_scores = rd.get("scores", rd.get("dimensions", {}))
                    for dim in dimensions:
                        # Try both "complexity" and "complexity_score" keys
                        val = dim_scores.get(dim, dim_scores.get(f"{dim}_score", 0))
                        if val and isinstance(val, (int, float)):
                            if val <= 10:
                                val = val * 10  # Normalize 0-10 to 0-100
                            dim_sums[dim] += val
                            dim_counts[dim] += 1
                for dim in dimensions:
                    if dim_counts[dim] > 0:
                        dimensions[dim] = round(dim_sums[dim] / dim_counts[dim], 1)

            return {
                "gate_pass_rate": round(pass_rate, 1),
                "avg_score": round(avg_score, 1),
                "dimensions": dimensions,
                "score_trend": [],
                "recent_failures": failures[:20],
            }

        return _safe(_do, default)

    # ── workflows ─────────────────────────────────────────────────────

    def collect_workflows(self) -> dict[str, Any]:
        default = {
            "summary": {"total": 0, "success_rate": 0, "avg_duration_ms": 0},
            "workflows": [],
            "preset_distribution": {"minimal": 0, "standard": 0, "comprehensive": 0, "full_sdlc": 0},
            "epics": [],
        }

        def _do():
            from tapps_agents.core.analytics_dashboard import AnalyticsDashboard

            ad = AnalyticsDashboard(analytics_dir=self.tapps_dir / "analytics")
            wf_perf = ad.get_workflow_performance()

            # Aggregate workflows by name so duplicate IDs are merged
            by_name: dict[str, dict] = {}
            for wp in wf_perf:
                name = wp.get("workflow_name", wp.get("workflow_id", "unknown"))
                # success_rate from AnalyticsDashboard is 0.0-1.0; convert to %
                raw_rate = wp.get("success_rate", 0)
                # average_duration is in seconds; convert to ms
                raw_dur = wp.get("average_duration", 0)
                execs = wp.get("total_executions", 0)
                if name not in by_name:
                    by_name[name] = {
                        "name": name,
                        "executions": 0,
                        "success_sum": 0.0,
                        "dur_sum": 0.0,
                        "dur_count": 0,
                        "steps_sum": 0.0,
                        "steps_count": 0,
                        "last_run": "",
                    }
                entry = by_name[name]
                entry["executions"] += execs
                entry["success_sum"] += raw_rate * execs
                if raw_dur > 0:
                    entry["dur_sum"] += raw_dur * 1000 * execs
                    entry["dur_count"] += execs
                steps = wp.get("average_steps", 0)
                if steps > 0:
                    entry["steps_sum"] += steps * execs
                    entry["steps_count"] += execs
                lr = wp.get("last_execution", "")
                if lr > entry["last_run"]:
                    entry["last_run"] = lr

            workflows = []
            for entry in by_name.values():
                execs = entry["executions"]
                workflows.append({
                    "name": entry["name"],
                    "executions": execs,
                    "success_rate": round(entry["success_sum"] / execs * 100, 1) if execs else 0,
                    "avg_duration_ms": round(entry["dur_sum"] / entry["dur_count"], 1) if entry["dur_count"] else 0,
                    "avg_steps": round(entry["steps_sum"] / entry["steps_count"], 1) if entry["steps_count"] else 0,
                    "last_run": entry["last_run"],
                })

            total = sum(w["executions"] for w in workflows)
            rates = [w["success_rate"] for w in workflows if w["executions"] > 0]
            avg_rate = sum(rates) / len(rates) if rates else 0
            durations = [w["avg_duration_ms"] for w in workflows if w["avg_duration_ms"] > 0]
            avg_dur = sum(durations) / len(durations) if durations else 0

            # Epic state
            epics = []
            try:
                from tapps_agents.epic.state_manager import EpicStateManager
                esm = EpicStateManager(project_root=self.project_root)
                for epic_info in esm.list_epic_states():
                    epic_id = epic_info.get("epic_id", "")
                    state = esm.load_state(epic_id)
                    if state:
                        stories = state.get("stories", [])
                        done = sum(1 for s in stories if s.get("status") == "done")
                        epics.append({
                            "id": epic_id,
                            "title": state.get("epic_title", epic_id),
                            "stories_total": len(stories),
                            "stories_done": done,
                            "updated_at": state.get("updated_at", ""),
                        })
            except Exception:
                pass

            # Infer preset distribution from workflow names
            preset_dist = {"minimal": 0, "standard": 0, "comprehensive": 0, "full_sdlc": 0}
            for w in workflows:
                wname = w["name"].lower()
                execs = w["executions"]
                if "full" in wname or "sdlc" in wname:
                    preset_dist["full_sdlc"] += execs
                elif "comprehensive" in wname:
                    preset_dist["comprehensive"] += execs
                elif "minimal" in wname or "fix" in wname:
                    preset_dist["minimal"] += execs
                else:
                    preset_dist["standard"] += execs

            return {
                "summary": {
                    "total": total,
                    "success_rate": round(avg_rate, 1),
                    "avg_duration_ms": round(avg_dur, 1),
                },
                "workflows": workflows,
                "preset_distribution": preset_dist,
                "epics": epics,
            }

        return _safe(_do, default)

    # ── adaptive learning ─────────────────────────────────────────────

    def collect_learning(self) -> dict[str, Any]:
        default = {
            "first_pass_trend": [],
            "auto_generated_experts": [],
            "weight_adjustments": [],
            "kb_growth": [],
        }

        def _do():
            learning_dir = self.tapps_dir / "learning"
            if not learning_dir.exists():
                return default

            # Expert performance history
            perf_entries = _read_jsonl(learning_dir / "expert_performance.jsonl", limit=200)
            first_pass: list[dict] = []
            for entry in perf_entries:
                if "first_pass_success_rate" in entry:
                    first_pass.append({
                        "date": entry.get("last_updated", entry.get("timestamp", "")),
                        "rate": entry.get("first_pass_success_rate", 0),
                    })

            # Weight adjustments
            adjustments: list[dict] = []
            adj_path = learning_dir / "weight_adjustments.jsonl"
            for entry in _read_jsonl(adj_path, limit=100):
                adjustments.append({
                    "expert": entry.get("expert_id", ""),
                    "old_weight": entry.get("old_weight", 0),
                    "new_weight": entry.get("new_weight", 0),
                    "reason": entry.get("reason", ""),
                    "date": entry.get("timestamp", ""),
                })

            # Auto-generated experts from experts.yaml
            auto_experts: list[dict] = []
            experts_yaml = self.tapps_dir / "experts.yaml"
            if experts_yaml.exists():
                try:
                    import yaml
                    with experts_yaml.open(encoding="utf-8") as ef:
                        experts_data = yaml.safe_load(ef) or {}
                    for eid, einfo in experts_data.get("experts", {}).items():
                        if isinstance(einfo, dict) and einfo.get("auto_generated"):
                            auto_experts.append({
                                "id": eid,
                                "domain": einfo.get("domain", ""),
                                "created_at": einfo.get("created_at", ""),
                            })
                except Exception:
                    pass

            # KB growth — count files per date from kb/ directory
            kb_growth: list[dict] = []
            kb_dir = self.tapps_dir / "kb"
            if kb_dir.exists():
                from collections import Counter
                date_counts: Counter[str] = Counter()
                for kf in kb_dir.rglob("*.json"):
                    try:
                        mtime = datetime.fromtimestamp(kf.stat().st_mtime, tz=UTC)
                        date_counts[mtime.strftime("%Y-%m-%d")] += 1
                    except OSError:
                        pass
                for d in sorted(date_counts):
                    kb_growth.append({"date": d, "entries": date_counts[d]})

            return {
                "first_pass_trend": first_pass,
                "auto_generated_experts": auto_experts,
                "weight_adjustments": adjustments,
                "kb_growth": kb_growth,
            }

        return _safe(_do, default)

    # ── events ────────────────────────────────────────────────────────

    def collect_events(self, limit: int = 100) -> list[dict]:
        def _do():
            events_dir = self.tapps_dir / "events"
            if not events_dir.exists():
                return []

            event_files = sorted(events_dir.glob("*.json"), reverse=True)[:limit]
            events = []
            for ef in event_files:
                data = _read_json(ef)
                if data:
                    events.append({
                        "timestamp": data.get("timestamp", ""),
                        "event_type": data.get("event_type", ""),
                        "workflow_id": data.get("workflow_id", ""),
                        "step_id": data.get("step_id", ""),
                        "status": data.get("status", ""),
                        "details": str(data.get("data", ""))[:200],
                    })
            return events

        return _safe(_do, [])
