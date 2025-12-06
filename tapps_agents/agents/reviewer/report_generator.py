"""
Report Generator - Generate quality analysis reports in multiple formats

Phase 6.3: Comprehensive Reporting Infrastructure
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import json

try:
    from jinja2 import Environment, FileSystemLoader, Template
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


class ReportGenerator:
    """
    Generate quality analysis reports in multiple formats.
    
    Phase 6.3: Comprehensive Reporting Infrastructure
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize report generator.
        
        Args:
            output_dir: Base directory for reports (default: reports/quality/)
        """
        if output_dir is None:
            output_dir = Path("reports/quality")
        self.output_dir = Path(output_dir)
        self.quality_dir = self.output_dir
        self.historical_dir = self.quality_dir / "historical"
        
        # Create directories if they don't exist
        self.quality_dir.mkdir(parents=True, exist_ok=True)
        self.historical_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_json_report(
        self,
        scores: Dict[str, Any],
        files: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate JSON report for CI/CD integration.
        
        Phase 6.3: Comprehensive Reporting Infrastructure
        
        Args:
            scores: Quality scores dictionary
            files: List of file-level scores (optional)
            metadata: Additional metadata (timestamp, project name, etc.)
            
        Returns:
            Path to generated JSON report
        """
        if metadata is None:
            metadata = {}
        
        report_data = {
            "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
            "project_name": metadata.get("project_name", "Unknown"),
            "version": metadata.get("version", "Unknown"),
            "summary": {
                "overall_score": scores.get("overall_score", 0.0),
                "complexity_score": scores.get("complexity_score", 0.0),
                "security_score": scores.get("security_score", 0.0),
                "maintainability_score": scores.get("maintainability_score", 0.0),
                "test_coverage_score": scores.get("test_coverage_score", 0.0),
                "performance_score": scores.get("performance_score", 0.0),
                "linting_score": scores.get("linting_score", 0.0),
                "type_checking_score": scores.get("type_checking_score", 0.0)
            },
            "metrics": scores.get("metrics", {}),
            "files": files or [],
            "thresholds": metadata.get("thresholds", {
                "overall": 70.0,
                "complexity": 5.0,
                "security": 8.0,
                "maintainability": 7.0
            }),
            "passed": scores.get("overall_score", 0.0) >= metadata.get("thresholds", {}).get("overall", 70.0)
        }
        
        report_path = self.quality_dir / "quality-report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        return report_path
    
    def generate_summary_report(
        self,
        scores: Dict[str, Any],
        files: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate Markdown summary report.
        
        Phase 6.3: Comprehensive Reporting Infrastructure
        
        Args:
            scores: Quality scores dictionary
            files: List of file-level scores (optional)
            metadata: Additional metadata
            
        Returns:
            Path to generated Markdown report
        """
        if metadata is None:
            metadata = {}
        
        timestamp = metadata.get("timestamp", datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        thresholds = metadata.get("thresholds", {
            "overall": 70.0,
            "complexity": 5.0,
            "security": 8.0,
            "maintainability": 7.0
        })
        
        overall_score = scores.get("overall_score", 0.0)
        passed = overall_score >= thresholds.get("overall", 70.0)
        
        # Build markdown content
        markdown_lines = [
            "# Quality Analysis Report",
            "",
            f"**Generated**: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Project**: {metadata.get('project_name', 'Unknown')}",
            f"**Version**: {metadata.get('version', 'Unknown')}",
            "",
            "## Summary",
            "",
            f"**Overall Score**: {overall_score:.2f}/100",
            f"**Status**: {'✅ PASSED' if passed else '❌ FAILED'}",
            f"**Threshold**: {thresholds.get('overall', 70.0)}",
            "",
            "## Quality Metrics",
            "",
            "| Metric | Score | Threshold | Status |",
            "|--------|-------|-----------|--------|",
            f"| Complexity | {scores.get('complexity_score', 0.0):.2f}/10 | {thresholds.get('complexity', 5.0)} | {'✅' if scores.get('complexity_score', 0.0) <= thresholds.get('complexity', 5.0) else '❌'} |",
            f"| Security | {scores.get('security_score', 0.0):.2f}/10 | {thresholds.get('security', 8.0)} | {'✅' if scores.get('security_score', 0.0) >= thresholds.get('security', 8.0) else '❌'} |",
            f"| Maintainability | {scores.get('maintainability_score', 0.0):.2f}/10 | {thresholds.get('maintainability', 7.0)} | {'✅' if scores.get('maintainability_score', 0.0) >= thresholds.get('maintainability', 7.0) else '❌'} |",
            f"| Test Coverage | {scores.get('test_coverage_score', 0.0):.2f}/10 | N/A | - |",
            f"| Performance | {scores.get('performance_score', 0.0):.2f}/10 | N/A | - |",
            f"| Linting | {scores.get('linting_score', 0.0):.2f}/10 | N/A | - |",
            f"| Type Checking | {scores.get('type_checking_score', 0.0):.2f}/10 | N/A | - |",
            "",
        ]
        
        # Add file-level details if provided
        if files and len(files) > 0:
            markdown_lines.extend([
                "## File-Level Analysis",
                "",
                f"**Total Files**: {len(files)}",
                "",
                "| File | Overall Score | Complexity | Security | Maintainability |",
                "|------|---------------|------------|----------|-----------------|",
            ])
            
            for file_data in files[:20]:  # Limit to top 20 files
                file_scores = file_data.get("scoring", {})
                file_path = file_data.get("file", "Unknown")
                # Truncate long paths
                display_path = file_path if len(file_path) <= 50 else "..." + file_path[-47:]
                
                markdown_lines.append(
                    f"| {display_path} | "
                    f"{file_scores.get('overall_score', 0.0):.2f} | "
                    f"{file_scores.get('complexity_score', 0.0):.2f} | "
                    f"{file_scores.get('security_score', 0.0):.2f} | "
                    f"{file_scores.get('maintainability_score', 0.0):.2f} |"
                )
            
            if len(files) > 20:
                markdown_lines.append(f"\n*Showing top 20 of {len(files)} files*")
        
        markdown_lines.extend([
            "",
            "---",
            f"*Generated by TappsCodingAgents Quality Analysis System*"
        ])
        
        report_path = self.quality_dir / "SUMMARY.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_lines))
        
        return report_path
    
    def generate_html_report(
        self,
        scores: Dict[str, Any],
        files: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate interactive HTML dashboard.
        
        Phase 6.3: Comprehensive Reporting Infrastructure
        
        Args:
            scores: Quality scores dictionary
            files: List of file-level scores (optional)
            metadata: Additional metadata
            
        Returns:
            Path to generated HTML report
        """
        if metadata is None:
            metadata = {}
        
        timestamp = metadata.get("timestamp", datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        thresholds = metadata.get("thresholds", {
            "overall": 70.0,
            "complexity": 5.0,
            "security": 8.0,
            "maintainability": 7.0
        })
        
        overall_score = scores.get("overall_score", 0.0)
        passed = overall_score >= thresholds.get("overall", 70.0)
        
        # Generate HTML using Jinja2 if available, otherwise use simple template
        if HAS_JINJA2:
            # Try to use Jinja2 template (would need to create templates directory)
            html_content = self._generate_html_with_jinja2(scores, files, metadata, timestamp, thresholds, passed)
        else:
            # Fallback to simple HTML
            html_content = self._generate_simple_html(scores, files, metadata, timestamp, thresholds, passed)
        
        report_path = self.quality_dir / "quality-dashboard.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path
    
    def _generate_simple_html(
        self,
        scores: Dict[str, Any],
        files: Optional[List[Dict[str, Any]]],
        metadata: Dict[str, Any],
        timestamp: datetime,
        thresholds: Dict[str, float],
        passed: bool
    ) -> str:
        """Generate simple HTML without Jinja2."""
        status_color = "#28a745" if passed else "#dc3545"
        status_text = "PASSED" if passed else "FAILED"
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quality Analysis Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .status {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
            background-color: {status_color};
            margin: 10px 0;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Quality Analysis Dashboard</h1>
        <p><strong>Generated:</strong> {timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Project:</strong> {metadata.get('project_name', 'Unknown')}</p>
        <p><strong>Version:</strong> {metadata.get('version', 'Unknown')}</p>
        <div class="status">{status_text}</div>
        <p><strong>Overall Score:</strong> {overall_score:.2f}/100 (Threshold: {thresholds.get('overall', 70.0)})</p>
    </div>
    
    <div class="metrics">
        <div class="metric-card">
            <div class="metric-label">Complexity</div>
            <div class="metric-value">{scores.get('complexity_score', 0.0):.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Security</div>
            <div class="metric-value">{scores.get('security_score', 0.0):.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Maintainability</div>
            <div class="metric-value">{scores.get('maintainability_score', 0.0):.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Test Coverage</div>
            <div class="metric-value">{scores.get('test_coverage_score', 0.0):.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Performance</div>
            <div class="metric-value">{scores.get('performance_score', 0.0):.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Linting</div>
            <div class="metric-value">{scores.get('linting_score', 0.0):.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Type Checking</div>
            <div class="metric-value">{scores.get('type_checking_score', 0.0):.2f}</div>
        </div>
    </div>
"""
        
        if files and len(files) > 0:
            html += """
    <h2>File-Level Analysis</h2>
    <table>
        <thead>
            <tr>
                <th>File</th>
                <th>Overall Score</th>
                <th>Complexity</th>
                <th>Security</th>
                <th>Maintainability</th>
            </tr>
        </thead>
        <tbody>
"""
            for file_data in files[:50]:  # Limit to 50 files
                file_scores = file_data.get("scoring", {})
                file_path = file_data.get("file", "Unknown")
                html += f"""
            <tr>
                <td>{file_path}</td>
                <td>{file_scores.get('overall_score', 0.0):.2f}</td>
                <td>{file_scores.get('complexity_score', 0.0):.2f}</td>
                <td>{file_scores.get('security_score', 0.0):.2f}</td>
                <td>{file_scores.get('maintainability_score', 0.0):.2f}</td>
            </tr>
"""
            html += """
        </tbody>
    </table>
"""
        
        html += f"""
    <div class="footer">
        Generated by TappsCodingAgents Quality Analysis System
    </div>
</body>
</html>
"""
        return html
    
    def _generate_html_with_jinja2(
        self,
        scores: Dict[str, Any],
        files: Optional[List[Dict[str, Any]]],
        metadata: Dict[str, Any],
        timestamp: datetime,
        thresholds: Dict[str, float],
        passed: bool
    ) -> str:
        """Generate HTML using Jinja2 (future enhancement)."""
        # For now, use simple HTML
        # TODO: Create Jinja2 templates directory and implement template rendering
        return self._generate_simple_html(scores, files, metadata, timestamp, thresholds, passed)
    
    def save_historical_data(
        self,
        scores: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Save historical data for trend analysis.
        
        Phase 6.3: Comprehensive Reporting Infrastructure
        
        Args:
            scores: Quality scores dictionary
            metadata: Additional metadata
            
        Returns:
            Path to saved historical data file
        """
        if metadata is None:
            metadata = {}
        
        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H%M%S')
        
        historical_data = {
            "timestamp": timestamp.isoformat(),
            "project_name": metadata.get("project_name", "Unknown"),
            "version": metadata.get("version", "Unknown"),
            "scores": scores,
            "metrics": scores.get("metrics", {})
        }
        
        # Save to date-based file
        historical_file = self.historical_dir / f"{date_str}-{time_str}.json"
        with open(historical_file, 'w', encoding='utf-8') as f:
            json.dump(historical_data, f, indent=2)
        
        return historical_file
    
    def generate_all_reports(
        self,
        scores: Dict[str, Any],
        files: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Path]:
        """
        Generate all report formats.
        
        Phase 6.3: Comprehensive Reporting Infrastructure
        
        Args:
            scores: Quality scores dictionary
            files: List of file-level scores (optional)
            metadata: Additional metadata
            
        Returns:
            Dictionary mapping report type to file path
        """
        if metadata is None:
            metadata = {}
        
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now()
        
        reports = {}
        
        # Generate all formats
        reports["json"] = self.generate_json_report(scores, files, metadata)
        reports["markdown"] = self.generate_summary_report(scores, files, metadata)
        reports["html"] = self.generate_html_report(scores, files, metadata)
        
        # Save historical data
        reports["historical"] = self.save_historical_data(scores, metadata)
        
        return reports

