"""
Unit tests for Windows doctor behavior with .CMD/.BAT shims (npm/npx).
"""

from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.core import doctor

pytestmark = pytest.mark.unit


class TestDoctorWindowsCmdShims:
    def test_run_version_cmd_wraps_cmd_for_cmd_shim(self):
        with patch("tapps_agents.core.doctor.platform.system", return_value="Windows"), patch(
            "tapps_agents.core.doctor.shutil.which", return_value=r"C:\tools\npm.CMD"
        ), patch("tapps_agents.core.doctor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="9.9.9\n", stderr="")

            out = doctor._run_version_cmd(["npm", "--version"])

            called_argv = mock_run.call_args[0][0]
            assert called_argv == ["cmd", "/c", "npm", "--version"]
            assert out == "9.9.9"

    def test_run_version_cmd_does_not_wrap_non_cmd_exe(self):
        with patch("tapps_agents.core.doctor.platform.system", return_value="Windows"), patch(
            "tapps_agents.core.doctor.shutil.which", return_value=r"C:\tools\node.exe"
        ), patch("tapps_agents.core.doctor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="v20.0.0\n", stderr="")

            out = doctor._run_version_cmd(["node", "--version"])

            called_argv = mock_run.call_args[0][0]
            assert called_argv == ["node", "--version"]
            assert out == "v20.0.0"


