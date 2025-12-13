"""
Unit tests for non-interactive expert setup wizard behavior.
"""

from pathlib import Path

import pytest

from tapps_agents.experts.setup_wizard import (
    ExpertSetupWizard,
    NonInteractiveInputRequired,
)

pytestmark = pytest.mark.unit


class TestExpertSetupWizardNonInteractive:
    def test_init_project_non_interactive_skips_expert_creation(self, tmp_path: Path):
        wizard = ExpertSetupWizard(
            project_root=tmp_path,
            assume_yes=True,
            non_interactive=True,
        )

        wizard.init_project()

        # Core project config structure
        assert (tmp_path / ".tapps-agents").exists()
        assert (tmp_path / ".tapps-agents" / "domains.md").exists()

        # Cursor rules + workflow presets should be installed by init_project()
        assert (tmp_path / ".cursor" / "rules").exists()
        assert (tmp_path / "workflows" / "presets").exists()

        # In non-interactive mode, we intentionally skip expert creation.
        assert not (tmp_path / ".tapps-agents" / "experts.yaml").exists()

    def test_add_expert_non_interactive_requires_input(self, tmp_path: Path):
        wizard = ExpertSetupWizard(project_root=tmp_path, non_interactive=True)

        with pytest.raises(NonInteractiveInputRequired):
            wizard.add_expert()


