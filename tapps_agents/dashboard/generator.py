"""
Main dashboard generator — orchestrates data collection, recommendation
analysis, HTML rendering, file writing, and browser launch.
"""

from __future__ import annotations

import logging
import platform
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

from .data_collector import DashboardDataCollector
from .html_renderer import HTMLRenderer

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = ".tapps-agents/dashboard"
DEFAULT_FILENAME = "dashboard.html"


# ── Recommendations Engine ────────────────────────────────────────────

def _generate_recommendations(data: dict[str, Any]) -> list[dict[str, str]]:
    """Analyse collected data and produce actionable recommendations."""
    recs: list[dict[str, str]] = []

    # Agent success rate
    for agent in data.get("agents", {}).get("agents", []):
        rate = agent.get("success_rate", 100)
        if 0 < rate < 80:
            recs.append({
                "tab": "agents",
                "message": (
                    f'Agent "{agent["name"]}" has a {rate:.0f}% success rate. '
                    "Review recent failures for patterns."
                ),
            })

    # Unused agents
    unused = [a["name"] for a in data.get("agents", {}).get("agents", []) if a.get("executions", 0) == 0]
    if unused:
        recs.append({
            "tab": "agents",
            "message": f"{len(unused)} agents have never been used ({', '.join(unused[:5])}). Consider workflow adoption.",
        })

    # Expert confidence
    for expert in data.get("experts", {}).get("experts", []):
        conf = expert.get("avg_confidence", 1)
        if expert.get("consultations", 0) > 0 and conf < 0.6:
            recs.append({
                "tab": "experts",
                "message": (
                    f'Expert "{expert["id"]}" has low confidence ({conf:.2f}). '
                    "Consider enriching its knowledge base."
                ),
            })

    # No expert consultations
    active = data.get("experts", {}).get("summary", {}).get("active", 0)
    if active == 0:
        recs.append({
            "tab": "experts",
            "message": "No expert consultations recorded. Ensure the expert system is enabled.",
        })

    # High fallback rate in expert selection (PRD: fallback_builtin + fallback_all > 30%)
    reason_dist = data.get("experts", {}).get("selection_reason_distribution", {})
    total_sel = sum(reason_dist.values())
    if total_sel > 0:
        fallback_count = reason_dist.get("fallback_builtin", 0) + reason_dist.get("fallback_all", 0)
        if fallback_count / total_sel > 0.30:
            recs.append({
                "tab": "experts",
                "message": (
                    "High fallback rate in expert selection. "
                    "Check domain config and weight matrix."
                ),
            })

    # Cache hit rate
    hit_rate = data.get("cache", {}).get("summary", {}).get("hit_rate", 100)
    if 0 < hit_rate < 50:
        recs.append({
            "tab": "cache",
            "message": (
                f"Cache hit rate is {hit_rate:.0f}%. "
                "Run `tapps-agents init` to pre-populate the Context7 cache."
            ),
        })

    # Zero-hit libraries
    zero_hit_libs = [
        lib["name"]
        for lib in data.get("cache", {}).get("libraries", [])
        if lib.get("hits", 0) == 0
    ]
    if zero_hit_libs:
        recs.append({
            "tab": "cache",
            "message": (
                f"{len(zero_hit_libs)} cached libraries have 0 hits "
                f"({', '.join(zero_hit_libs[:4])}). Consider removing unused entries."
            ),
        })

    # Quality gate failures
    gate_rate = data.get("quality", {}).get("gate_pass_rate", 100)
    if 0 < gate_rate < 70:
        recs.append({
            "tab": "quality",
            "message": (
                f"Quality gates are failing {100 - gate_rate:.0f}% of the time. "
                "Review scoring thresholds or address common failure causes."
            ),
        })

    # Workflow success
    wf_rate = data.get("workflows", {}).get("summary", {}).get("success_rate", 100)
    if 0 < wf_rate < 80:
        recs.append({
            "tab": "workflows",
            "message": (
                f"Overall workflow success rate is {wf_rate:.0f}%. "
                "Check for bottleneck steps or recurring failures."
            ),
        })

    # Health degraded/unhealthy
    for check in data.get("health", {}).get("checks", []):
        if check.get("status") in ("degraded", "unhealthy"):
            recs.append({
                "tab": "health",
                "message": (
                    f'Health check "{check["name"]}" is {check["status"]} '
                    f'(score: {check.get("score", 0):.0f}).'
                    + (f' Fix: {check["remediation"][0]}' if check.get("remediation") else "")
                ),
            })

    return recs


# ── Generator ─────────────────────────────────────────────────────────

class DashboardGenerator:
    """Collect metrics → analyse → render HTML → write → optionally open."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = (project_root or Path.cwd()).resolve()

    def generate(
        self,
        output_path: Path | None = None,
        days: int = 30,
        open_browser: bool = True,
        verbose: bool = False,
    ) -> Path:
        """Generate the dashboard and return the output path.

        Args:
            output_path: Where to write the HTML file.  Defaults to
                ``.tapps-agents/dashboard/dashboard.html``.
            days: Number of days of data to include.
            open_browser: Open the result in the default browser.
            verbose: Include raw event stream data.

        Returns:
            Absolute path to the generated HTML file.
        """
        # 1. Collect
        collector = DashboardDataCollector(self.project_root, days=days)
        data = collector.collect_all()

        if not verbose:
            data["events"] = data.get("events", [])[:100]

        # 2. Recommendations
        data["recommendations"] = _generate_recommendations(data)

        # 3. Render
        renderer = HTMLRenderer()
        html_content = renderer.render(data)

        # 4. Write
        if output_path is None:
            output_path = self.project_root / DEFAULT_OUTPUT_DIR / DEFAULT_FILENAME
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")

        logger.info("Dashboard written to %s", output_path)

        # 5. Open
        if open_browser:
            _open_file(output_path)

        return output_path


def _open_file(path: Path) -> None:
    """Open a local file in the default browser, cross-platform."""
    try:
        url = path.as_uri()
        webbrowser.open(url)
    except Exception:  # noqa: BLE001
        # Fallback for some environments
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["start", "", str(path)], shell=True)  # noqa: S603, S607
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(path)])  # noqa: S603, S607
            else:
                subprocess.Popen(["xdg-open", str(path)])  # noqa: S603, S607
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not open browser: %s", exc)
            print(f"Dashboard generated: {path}", file=sys.stderr)
