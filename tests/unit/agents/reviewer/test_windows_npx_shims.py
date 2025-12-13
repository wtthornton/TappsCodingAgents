"""
Unit tests ensuring reviewer tooling wraps Windows .CMD/.BAT shims via cmd /c.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.agents.reviewer.scoring import CodeScorer
from tapps_agents.agents.reviewer.typescript_scorer import TypeScriptScorer

pytestmark = pytest.mark.unit


class TestReviewerWindowsNpxShims:
    def test_typescript_scorer_wraps_npx_cmd_for_version_checks(self):
        with patch(
            "tapps_agents.agents.reviewer.typescript_scorer.shutil.which"
        ) as mock_which, patch(
            "tapps_agents.agents.reviewer.typescript_scorer.subprocess.run"
        ) as mock_run, patch(
            "tapps_agents.core.subprocess_utils.platform.system", return_value="Windows"
        ):
            # tsc/eslint not directly available; npx is a .CMD shim
            def which_side_effect(name: str):
                if name in {"tsc", "eslint"}:
                    return None
                if name == "npx":
                    return r"C:\tools\npx.CMD"
                return None

            mock_which.side_effect = which_side_effect
            mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

            scorer = TypeScriptScorer()
            assert scorer.has_tsc is True
            assert scorer.has_eslint is True

            # Ensure subprocess was invoked with cmd /c wrapper at least once
            called_argvs = [c.args[0] for c in mock_run.call_args_list]
            assert any(argv[:2] == ["cmd", "/c"] for argv in called_argvs)

    def test_code_scorer_wraps_npx_cmd_for_jscpd(self, tmp_path: Path):
        # Force has_jscpd True and exercise the duplication report path which runs jscpd.
        scorer = CodeScorer(jscpd_enabled=True)
        scorer.has_jscpd = True

        target_file = tmp_path / "a.py"
        target_file.write_text("print('hi')\n", encoding="utf-8")

        with patch(
            "tapps_agents.agents.reviewer.scoring.shutil.which"
        ) as mock_which, patch(
            "tapps_agents.agents.reviewer.scoring.subprocess.run"
        ) as mock_run, patch(
            "tapps_agents.core.subprocess_utils.platform.system", return_value="Windows"
        ):
            def which_side_effect(name: str):
                if name == "jscpd":
                    return None
                if name == "npx":
                    return r"C:\tools\npx.CMD"
                return None

            mock_which.side_effect = which_side_effect
            mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

            scorer.get_duplication_report(target_file)

            called_argv = mock_run.call_args[0][0]
            assert called_argv[:2] == ["cmd", "/c"]


