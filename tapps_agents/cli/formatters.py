"""
Output formatters for CLI commands.

Provides functions to convert command results to various output formats:
- JSON: Structured data format
- Markdown: Human-readable markdown format
- HTML: Interactive HTML reports with charts
"""
import json
from typing import Any


def _format_library_recommendations_markdown(recommendations: dict[str, Any]) -> list[str]:
    """
    Format library recommendations as markdown.
    
    Args:
        recommendations: Dictionary of library recommendations
        
    Returns:
        List of markdown lines
    """
    lines = []
    
    if not recommendations:
        return lines
    
    lines.append("## Library Recommendations")
    lines.append("")
    
    for lib_name, rec in recommendations.items():
        lines.append(f"### {lib_name}")
        lines.append("")
        
        if isinstance(rec, dict):
            # Best practices
            best_practices = rec.get("best_practices", [])
            if best_practices:
                lines.append("**Best Practices:**")
                for practice in best_practices:
                    lines.append(f"- {practice}")
                lines.append("")
            
            # Common mistakes
            common_mistakes = rec.get("common_mistakes", [])
            if common_mistakes:
                lines.append("**Common Mistakes:**")
                for mistake in common_mistakes:
                    lines.append(f"- {mistake}")
                lines.append("")
            
            # Usage examples
            usage_examples = rec.get("usage_examples", [])
            if usage_examples:
                lines.append("**Usage Examples:**")
                for example in usage_examples:
                    lines.append("```python")
                    lines.append(example)
                    lines.append("```")
                    lines.append("")
        else:
            # Fallback for simple string recommendations
            lines.append(f"- {rec}")
            lines.append("")
    
    return lines


def _format_pattern_guidance_markdown(guidance: dict[str, Any]) -> list[str]:
    """
    Format pattern guidance as markdown.
    
    Args:
        guidance: Dictionary of pattern guidance
        
    Returns:
        List of markdown lines
    """
    lines = []
    
    if not guidance:
        return lines
    
    lines.append("## Pattern Guidance")
    lines.append("")
    
    for pattern_name, pattern_info in guidance.items():
        lines.append(f"### {pattern_name.replace('_', ' ').title()}")
        lines.append("")
        
        if isinstance(pattern_info, dict):
            # Confidence score
            confidence = pattern_info.get("confidence", pattern_info.get("detected"))
            if confidence is not None:
                if isinstance(confidence, bool):
                    lines.append(f"**Detected:** {'Yes' if confidence else 'No'}")
                else:
                    lines.append(f"**Confidence:** {confidence:.2f}")
                lines.append("")
            
            # Recommendations
            recommendations = pattern_info.get("recommendations", [])
            if recommendations:
                lines.append("**Recommendations:**")
                for rec in recommendations:
                    lines.append(f"- {rec}")
                lines.append("")
            
            # Best practices
            best_practices = pattern_info.get("best_practices", [])
            if best_practices:
                lines.append("**Best Practices:**")
                for practice in best_practices:
                    lines.append(f"- {practice}")
                lines.append("")
        else:
            # Fallback for simple string guidance
            lines.append(f"- {pattern_info}")
            lines.append("")
    
    return lines


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
            
            # NEW: Library Recommendations section
            if "library_recommendations" in item:
                lines.extend(_format_library_recommendations_markdown(item["library_recommendations"]))
            
            # NEW: Pattern Guidance section
            if "pattern_guidance" in item:
                lines.extend(_format_pattern_guidance_markdown(item["pattern_guidance"]))
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
            lines.append("## Error")
            lines.append(data["error"])
            lines.append("")
        
        # NEW: Library Recommendations section
        if "library_recommendations" in data:
            lines.extend(_format_library_recommendations_markdown(data["library_recommendations"]))
        
        # NEW: Pattern Guidance section
        if "pattern_guidance" in data:
            lines.extend(_format_pattern_guidance_markdown(data["pattern_guidance"]))
    
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
                
                html_parts.append("<tr>")
                html_parts.append(f"<td>{file_path}</td>")
                html_parts.append(f"<td><strong>{overall:.1f}</strong></td>")
                html_parts.append(f"<td>{complexity:.1f}</td>")
                html_parts.append(f"<td>{security:.1f}</td>")
                html_parts.append(f"<td>{maintainability:.1f}</td>")
                html_parts.append(f"<td style='color: {status_color}'><strong>{status}</strong></td>")
                html_parts.append("</tr>")
            elif "error" in item:
                html_parts.append("<tr>")
                html_parts.append(f"<td>{file_path}</td>")
                html_parts.append(f"<td colspan='5' class='error'>{item['error']}</td>")
                html_parts.append("</tr>")
        
        html_parts.append("</tbody>")
        html_parts.append("</table>")
        
        # Add detailed sections for each file
        for item in data:
            file_path = item.get('file', 'unknown')
            html_parts.append("<div class='file-result'>")
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
            
            # NEW: Library Recommendations section
            if "library_recommendations" in item:
                html_parts.extend(_format_library_recommendations_html(item["library_recommendations"]))
            
            # NEW: Pattern Guidance section
            if "pattern_guidance" in item:
                html_parts.extend(_format_pattern_guidance_html(item["pattern_guidance"]))
            
            html_parts.append("</div>")
    else:
        # Single result
        file_path = data.get('file', 'unknown')
        html_parts.append("<div class='file-result'>")
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
        
        # NEW: Library Recommendations section
        if "library_recommendations" in data:
            html_parts.extend(_format_library_recommendations_html(data["library_recommendations"]))
        
        # NEW: Pattern Guidance section
        if "pattern_guidance" in data:
            html_parts.extend(_format_pattern_guidance_html(data["pattern_guidance"]))
    
    html_parts.extend([
        "</body>",
        "</html>",
    ])
    
    return "\n".join(html_parts)


def _format_library_recommendations_html(recommendations: dict[str, Any]) -> list[str]:
    """
    Format library recommendations as HTML.
    
    Args:
        recommendations: Dictionary of library recommendations
        
    Returns:
        List of HTML lines
    """
    html_parts = []
    
    if not recommendations:
        return html_parts
    
    html_parts.append("<div class='file-result'>")
    html_parts.append("<h2>Library Recommendations</h2>")
    
    for lib_name, rec in recommendations.items():
        html_parts.append(f"<h3>{lib_name}</h3>")
        
        if isinstance(rec, dict):
            # Best practices
            best_practices = rec.get("best_practices", [])
            if best_practices:
                html_parts.append("<h4>Best Practices</h4>")
                html_parts.append("<ul>")
                for practice in best_practices:
                    html_parts.append(f"<li>{practice}</li>")
                html_parts.append("</ul>")
            
            # Common mistakes
            common_mistakes = rec.get("common_mistakes", [])
            if common_mistakes:
                html_parts.append("<h4>Common Mistakes</h4>")
                html_parts.append("<ul>")
                for mistake in common_mistakes:
                    html_parts.append(f"<li>{mistake}</li>")
                html_parts.append("</ul>")
            
            # Usage examples
            usage_examples = rec.get("usage_examples", [])
            if usage_examples:
                html_parts.append("<h4>Usage Examples</h4>")
                for example in usage_examples:
                    html_parts.append("<pre><code>")
                    html_parts.append(example)
                    html_parts.append("</code></pre>")
        else:
            html_parts.append(f"<p>{rec}</p>")
    
    html_parts.append("</div>")
    
    return html_parts


def _format_pattern_guidance_html(guidance: dict[str, Any]) -> list[str]:
    """
    Format pattern guidance as HTML.
    
    Args:
        guidance: Dictionary of pattern guidance
        
    Returns:
        List of HTML lines
    """
    html_parts = []
    
    if not guidance:
        return html_parts
    
    html_parts.append("<div class='file-result'>")
    html_parts.append("<h2>Pattern Guidance</h2>")
    
    for pattern_name, pattern_info in guidance.items():
        display_name = pattern_name.replace('_', ' ').title()
        html_parts.append(f"<h3>{display_name}</h3>")
        
        if isinstance(pattern_info, dict):
            # Confidence score
            confidence = pattern_info.get("confidence", pattern_info.get("detected"))
            if confidence is not None:
                if isinstance(confidence, bool):
                    html_parts.append(f"<p><strong>Detected:</strong> {'Yes' if confidence else 'No'}</p>")
                else:
                    html_parts.append(f"<p><strong>Confidence:</strong> {confidence:.2f}</p>")
            
            # Recommendations
            recommendations = pattern_info.get("recommendations", [])
            if recommendations:
                html_parts.append("<h4>Recommendations</h4>")
                html_parts.append("<ul>")
                for rec in recommendations:
                    html_parts.append(f"<li>{rec}</li>")
                html_parts.append("</ul>")
            
            # Best practices
            best_practices = pattern_info.get("best_practices", [])
            if best_practices:
                html_parts.append("<h4>Best Practices</h4>")
                html_parts.append("<ul>")
                for practice in best_practices:
                    html_parts.append(f"<li>{practice}</li>")
                html_parts.append("</ul>")
        else:
            html_parts.append(f"<p>{pattern_info}</p>")
    
    html_parts.append("</div>")
    
    return html_parts

