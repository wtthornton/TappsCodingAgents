"""
Tests that enforce Cursor-first policy:
- MAL must be disabled when running under Cursor/Background Agents.
"""

import pytest
from unittest.mock import AsyncMock, patch

from tapps_agents.core.exceptions import MALDisabledInCursorModeError
from tapps_agents.core.mal import MAL


pytestmark = pytest.mark.unit


class TestCursorFirstMALGuard:
    @pytest.mark.asyncio
    async def test_mal_generate_raises_in_cursor_mode(self, monkeypatch):
        monkeypatch.setenv("TAPPS_AGENTS_MODE", "cursor")
        mal = MAL()
        with pytest.raises(MALDisabledInCursorModeError):
            await mal.generate("hello")

    @pytest.mark.asyncio
    async def test_mal_generate_allowed_in_headless_mode(self, monkeypatch):
        monkeypatch.setenv("TAPPS_AGENTS_MODE", "headless")
        mal = MAL()
        with patch.object(mal, "_ollama_generate", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = "OK"
            result = await mal.generate("hello", provider="ollama", enable_fallback=False)
            assert result == "OK"


