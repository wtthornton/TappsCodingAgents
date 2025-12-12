from pathlib import Path

import pytest

from tapps_agents.agents.reviewer.report_generator import ReportGenerator


pytestmark = pytest.mark.unit


def test_generate_html_report_uses_template_when_available(tmp_path: Path) -> None:
    rg = ReportGenerator(output_dir=tmp_path / "reports")
    
    scores = {
        "overall_score": 88.5,
        "complexity_score": 2.0,
        "security_score": 9.0,
        "maintainability_score": 8.0,
        "test_coverage_score": 7.0,
        "performance_score": 7.5,
        "linting_score": 8.5,
        "type_checking_score": 9.5,
    }
    
    files = [
        {
            "file": "src/app.py",
            "scoring": {
                "overall_score": 80.0,
                "complexity_score": 3.0,
                "security_score": 8.0,
                "maintainability_score": 7.0,
            },
        }
    ]
    
    out = rg.generate_html_report(scores=scores, files=files, metadata={"project_name": "Demo", "version": "0.1.0"})
    html = out.read_text(encoding="utf-8")
    
    assert "Quality Analysis Dashboard" in html
    assert "Demo" in html
    assert "src/app.py" in html


