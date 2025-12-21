"""
Output formatters for CLI commands.

Provides functions to convert command results to various output formats:
- JSON: Structured data format
- Markdown: Human-readable markdown format
- HTML: Interactive HTML reports with charts
"""
import json
from typing import Any


def format_json(data: dict[str, Any] | list[dict[str, Any]], indent: int = 2) -> str:
    """
    Format data as JSON string.
    
    Args:
        data: Data to format (dict or list of dicts)
        indent: JSON indentation level
        
    Returns:
        JSON string
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)


def format_markdown(data: dict[str, Any] | list[dict[str, Any]]) -> str:
    """
    Format data as Markdown string.
    
    Args:
        data: Data to format (dict or list of dicts)
        
    Returns:
        Markdown string
    """
    lines = []
    
    if isinstance(data, list):
        # Batch results
        lines.append("# Batch Results")
        lines.append("")
        lines.append(f"Total files: {len(data)}")
        lines.append("")
        
        for i, item in enumerate(data, 1):
            lines.append(f"## File {i}: {item.get('file', 'unknown')}")
            lines.append("")
            
            if "scoring" in item:
                scores = item["scoring"]
                lines.append("### Scores")
                lines.append(f"- **Overall**: {scores.get('overall_score', 0):.1f}/100")
                lines.append(f"- **Complexity**: {scores.get('complexity_score', 0):.1f}/10")
                lines.append(f"- **Security**: {scores.get('security_score', 0):.1f}/10")
                lines.append(f"- **Maintainability**: {scores.get('maintainability_score', 0):.1f}/10")
                lines.append("")
            
            if "issues" in item:
                issues = item["issues"]
                lines.append(f"### Linting Issues ({len(issues)})")
                for issue in issues:
                    code = issue.get('code', '')
                    message = issue.get('message', '')
                    line = issue.get('line', '?')
                    lines.append(f"- **Line {line}** [{code}]: {message}")
                lines.append("")
            
            if "errors" in item:
                errors = item["errors"]
                lines.append(f"### Type Check Errors ({len(errors)})")
                for error in errors:
                    message = error.get('message', '')
                    line = error.get('line', '?')
                    lines.append(f"- **Line {line}**: {message}")
                lines.append("")
            
            if "error" in item:
                lines.append(f"**Error**: {item['error']}")
                lines.append("")
    else:
        # Single result
        if "file" in data:
            lines.append(f"# Results for: {data['file']}")
            lines.append("")
        
        if "scoring" in data:
            scores = data["scoring"]
            lines.append("## Scores")
            lines.append(f"- **Overall**: {scores.get('overall_score', 0):.1f}/100")
            lines.append(f"- **Complexity**: {scores.get('complexity_score', 0):.1f}/10")
            lines.append(f"- **Security**: {scores.get('security_score', 0):.1f}/10")
            lines.append(f"- **Maintainability**: {scores.get('maintainability_score', 0):.1f}/10")
            lines.append("")
        
        if "issues" in data:
            issues = data["issues"]
            lines.append(f"## Linting Issues ({len(issues)})")
            for issue in issues:
                code = issue.get('code', '')
                message = issue.get('message', '')
                line = issue.get('line', '?')
                lines.append(f"- **Line {line}** [{code}]: {message}")
            lines.append("")
        
        if "errors" in data:
            errors = data["errors"]
            lines.append(f"## Type Check Errors ({len(errors)})")
            for error in errors:
                message = error.get('message', '')
                line = error.get('line', '?')
                lines.append(f"- **Line {line}**: {message}")
            lines.append("")
        
        if "error" in data:
            lines.append(f"## Error")
            lines.append(data["error"])
            lines.append("")
    
    return "\n".join(lines)


def format_html(data: dict[str, Any] | list[dict[str, Any]], title: str = "Quality Report") -> str:
    """
    Format data as HTML report.
    
    Args:
        data: Data to format (dict or list of dicts)
        title: Report title
        
    Returns:
        HTML string
    """
    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        f"<title>{title}</title>",
        "<style>",
        """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007acc;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
        }
        .file-result {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .scores {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .score-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .score-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        .score-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .error {
            background: #fee;
            border-left: 4px solid #f00;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .issue, .type-error {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
        }
        .issue-code {
            font-weight: bold;
            color: #856404;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #007acc;
            color: white;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        """,
        "</style>",
        "</head>",
        "<body>",
        f"<h1>{title}</h1>",
    ]
    
    if isinstance(data, list):
        # Batch results
        html_parts.append(f"<p><strong>Total files:</strong> {len(data)}</p>")
        html_parts.append("<table>")
        html_parts.append("<thead><tr><th>File</th><th>Overall Score</th><th>Complexity</th><th>Security</th><th>Maintainability</th><th>Status</th></tr></thead>")
        html_parts.append("<tbody>")
        
        for item in data:
            file_path = item.get('file', 'unknown')
            if "scoring" in item:
                scores = item["scoring"]
                overall = scores.get('overall_score', 0)
                complexity = scores.get('complexity_score', 0)
                security = scores.get('security_score', 0)
                maintainability = scores.get('maintainability_score', 0)
                status = "Pass" if overall >= 70 else "Fail"
                status_color = "#0a0" if overall >= 70 else "#a00"
                
                html_parts.append(f"<tr>")
                html_parts.append(f"<td>{file_path}</td>")
                html_parts.append(f"<td><strong>{overall:.1f}</strong></td>")
                html_parts.append(f"<td>{complexity:.1f}</td>")
                html_parts.append(f"<td>{security:.1f}</td>")
                html_parts.append(f"<td>{maintainability:.1f}</td>")
                html_parts.append(f"<td style='color: {status_color}'><strong>{status}</strong></td>")
                html_parts.append(f"</tr>")
            elif "error" in item:
                html_parts.append(f"<tr>")
                html_parts.append(f"<td>{file_path}</td>")
                html_parts.append(f"<td colspan='5' class='error'>{item['error']}</td>")
                html_parts.append(f"</tr>")
        
        html_parts.append("</tbody>")
        html_parts.append("</table>")
        
        # Add detailed sections for each file
        for item in data:
            file_path = item.get('file', 'unknown')
            html_parts.append(f"<div class='file-result'>")
            html_parts.append(f"<h2>{file_path}</h2>")
            
            if "scoring" in item:
                scores = item["scoring"]
                html_parts.append("<div class='scores'>")
                
                overall = scores.get('overall_score', 0)
                complexity = scores.get('complexity_score', 0)
                security = scores.get('security_score', 0)
                maintainability = scores.get('maintainability_score', 0)
                
                html_parts.append(f"<div class='score-card'><div class='score-label'>Overall</div><div class='score-value'>{overall:.1f}</div></div>")
                html_parts.append(f"<div class='score-card'><div class='score-label'>Complexity</div><div class='score-value'>{complexity:.1f}</div></div>")
                html_parts.append(f"<div class='score-card'><div class='score-label'>Security</div><div class='score-value'>{security:.1f}</div></div>")
                html_parts.append(f"<div class='score-card'><div class='score-label'>Maintainability</div><div class='score-value'>{maintainability:.1f}</div></div>")
                
                html_parts.append("</div>")
            
            if "issues" in item:
                issues = item["issues"]
                html_parts.append(f"<h3>Linting Issues ({len(issues)})</h3>")
                for issue in issues:
                    code = issue.get('code', '')
                    message = issue.get('message', '')
                    line = issue.get('line', '?')
                    html_parts.append(f"<div class='issue'><span class='issue-code'>{code}</span> - Line {line}: {message}</div>")
            
            if "errors" in item:
                errors = item["errors"]
                html_parts.append(f"<h3>Type Check Errors ({len(errors)})</h3>")
                for error in errors:
                    message = error.get('message', '')
                    line = error.get('line', '?')
                    html_parts.append(f"<div class='type-error'>Line {line}: {message}</div>")
            
            html_parts.append("</div>")
    else:
        # Single result
        file_path = data.get('file', 'unknown')
        html_parts.append(f"<div class='file-result'>")
        html_parts.append(f"<h2>{file_path}</h2>")
        
        if "scoring" in data:
            scores = data["scoring"]
            html_parts.append("<div class='scores'>")
            
            overall = scores.get('overall_score', 0)
            complexity = scores.get('complexity_score', 0)
            security = scores.get('security_score', 0)
            maintainability = scores.get('maintainability_score', 0)
            
            html_parts.append(f"<div class='score-card'><div class='score-label'>Overall</div><div class='score-value'>{overall:.1f}</div></div>")
            html_parts.append(f"<div class='score-card'><div class='score-label'>Complexity</div><div class='score-value'>{complexity:.1f}</div></div>")
            html_parts.append(f"<div class='score-card'><div class='score-label'>Security</div><div class='score-value'>{security:.1f}</div></div>")
            html_parts.append(f"<div class='score-card'><div class='score-label'>Maintainability</div><div class='score-value'>{maintainability:.1f}</div></div>")
            
            html_parts.append("</div>")
        
        if "issues" in data:
            issues = data["issues"]
            html_parts.append(f"<h3>Linting Issues ({len(issues)})</h3>")
            for issue in issues:
                code = issue.get('code', '')
                message = issue.get('message', '')
                line = issue.get('line', '?')
                html_parts.append(f"<div class='issue'><span class='issue-code'>{code}</span> - Line {line}: {message}</div>")
        
        if "errors" in data:
            errors = data["errors"]
            html_parts.append(f"<h3>Type Check Errors ({len(errors)})</h3>")
            for error in errors:
                message = error.get('message', '')
                line = error.get('line', '?')
                html_parts.append(f"<div class='type-error'>Line {line}: {message}</div>")
        
        html_parts.append("</div>")
        
        if "error" in data:
            html_parts.append(f"<div class='error'>{data['error']}</div>")
    
    html_parts.extend([
        "</body>",
        "</html>",
    ])
    
    return "\n".join(html_parts)

