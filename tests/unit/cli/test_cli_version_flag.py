"""
Unit tests for CLI --version flag.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


class TestCliVersionFlag:
    def test_cli_version_flag_prints_version_and_exits(self, capsys):
        from tapps_agents.cli import main

        with patch("sys.argv", ["tapps_agents", "--version"]):
            with pytest.raises(SystemExit) as exc:
                main()

        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "2.0.3" in captured.out


