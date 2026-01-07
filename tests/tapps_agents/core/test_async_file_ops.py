"""
Tests for AsyncFileOps - async_file_ops.py

Tests for async file I/O utilities using aiofiles.
"""

import tempfile
from pathlib import Path

import pytest

from tapps_agents.core.async_file_ops import (
    AsyncFileOps,
    AIOFILES_AVAILABLE,
    read_file,
    write_file,
    file_hash,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir):
    """Create a temporary file with content."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Hello, World!\n", encoding="utf-8")
    return file_path


class TestAsyncFileOps:
    """Tests for AsyncFileOps class."""

    @pytest.mark.asyncio
    async def test_read_file(self, temp_file):
        """Test reading file asynchronously."""
        content = await AsyncFileOps.read_file(temp_file)
        assert content == "Hello, World!\n"

    @pytest.mark.asyncio
    async def test_read_file_with_encoding(self, temp_dir):
        """Test reading file with specific encoding."""
        file_path = temp_dir / "utf8_file.txt"
        file_path.write_text("Hello, 世界!\n", encoding="utf-8")
        
        content = await AsyncFileOps.read_file(file_path, encoding="utf-8")
        assert content == "Hello, 世界!\n"

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, temp_dir):
        """Test reading non-existent file raises error."""
        nonexistent = temp_dir / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            await AsyncFileOps.read_file(nonexistent)

    @pytest.mark.asyncio
    async def test_read_bytes(self, temp_file):
        """Test reading file as bytes."""
        content = await AsyncFileOps.read_bytes(temp_file)
        # Normalize line endings for cross-platform compatibility
        assert content.replace(b"\r\n", b"\n") == b"Hello, World!\n"

    @pytest.mark.asyncio
    async def test_write_file(self, temp_dir):
        """Test writing file asynchronously."""
        file_path = temp_dir / "output.txt"
        await AsyncFileOps.write_file(file_path, "Test content\n")
        
        assert file_path.exists()
        assert file_path.read_text() == "Test content\n"

    @pytest.mark.asyncio
    async def test_write_file_creates_parents(self, temp_dir):
        """Test that write_file creates parent directories."""
        file_path = temp_dir / "subdir" / "nested" / "output.txt"
        await AsyncFileOps.write_file(file_path, "Nested content\n")
        
        assert file_path.exists()
        assert file_path.read_text() == "Nested content\n"

    @pytest.mark.asyncio
    async def test_write_file_no_create_parents(self, temp_dir):
        """Test that write_file fails without parent creation."""
        file_path = temp_dir / "nonexistent" / "output.txt"
        with pytest.raises(FileNotFoundError):
            await AsyncFileOps.write_file(file_path, "content", create_parents=False)

    @pytest.mark.asyncio
    async def test_write_bytes(self, temp_dir):
        """Test writing bytes to file."""
        file_path = temp_dir / "binary.bin"
        await AsyncFileOps.write_bytes(file_path, b"\x00\x01\x02\x03")
        
        assert file_path.exists()
        assert file_path.read_bytes() == b"\x00\x01\x02\x03"

    @pytest.mark.asyncio
    async def test_write_atomic(self, temp_dir):
        """Test atomic file writing."""
        file_path = temp_dir / "atomic.txt"
        await AsyncFileOps.write_atomic(file_path, "Atomic content\n")
        
        assert file_path.exists()
        assert file_path.read_text() == "Atomic content\n"
        # Temp file should be cleaned up
        assert not file_path.with_suffix(".txt.tmp").exists()

    @pytest.mark.asyncio
    async def test_file_hash(self, temp_file):
        """Test computing file hash."""
        hash1 = await AsyncFileOps.file_hash(temp_file)
        hash2 = await AsyncFileOps.file_hash(temp_file)
        
        assert hash1 == hash2
        assert len(hash1) == 16  # Truncated to 16 chars

    @pytest.mark.asyncio
    async def test_file_hash_changes_with_content(self, temp_file):
        """Test that hash changes when content changes."""
        hash1 = await AsyncFileOps.file_hash(temp_file)
        temp_file.write_text("Different content\n")
        hash2 = await AsyncFileOps.file_hash(temp_file)
        
        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_file_exists(self, temp_file, temp_dir):
        """Test checking file existence."""
        assert await AsyncFileOps.file_exists(temp_file) is True
        assert await AsyncFileOps.file_exists(temp_dir / "nonexistent.txt") is False

    @pytest.mark.asyncio
    async def test_file_size(self, temp_file):
        """Test getting file size."""
        size = await AsyncFileOps.file_size(temp_file)
        # Size may vary due to line endings on different platforms
        # Windows: 15 bytes (CRLF), Unix: 14 bytes (LF)
        assert size >= len("Hello, World!\n")

    @pytest.mark.asyncio
    async def test_iter_lines(self, temp_dir):
        """Test iterating over file lines."""
        file_path = temp_dir / "lines.txt"
        file_path.write_text("Line 1\nLine 2\nLine 3\n")
        
        lines = []
        async for line in AsyncFileOps.iter_lines(file_path):
            lines.append(line)
        
        assert lines == ["Line 1", "Line 2", "Line 3"]

    @pytest.mark.asyncio
    async def test_append_file(self, temp_file):
        """Test appending to file."""
        await AsyncFileOps.append_file(temp_file, "Appended content\n")
        
        content = temp_file.read_text()
        assert "Hello, World!" in content
        assert "Appended content" in content

    @pytest.mark.asyncio
    async def test_delete_file(self, temp_file):
        """Test deleting file."""
        assert temp_file.exists()
        result = await AsyncFileOps.delete_file(temp_file)
        assert result is True
        assert not temp_file.exists()

    @pytest.mark.asyncio
    async def test_delete_file_missing_ok(self, temp_dir):
        """Test deleting non-existent file with missing_ok."""
        nonexistent = temp_dir / "nonexistent.txt"
        result = await AsyncFileOps.delete_file(nonexistent, missing_ok=True)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_file_raises_on_missing(self, temp_dir):
        """Test deleting non-existent file raises error."""
        nonexistent = temp_dir / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            await AsyncFileOps.delete_file(nonexistent, missing_ok=False)

    @pytest.mark.asyncio
    async def test_copy_file(self, temp_file, temp_dir):
        """Test copying file."""
        dest = temp_dir / "copy.txt"
        await AsyncFileOps.copy_file(temp_file, dest)
        
        assert dest.exists()
        assert dest.read_text() == temp_file.read_text()

    def test_is_async_available(self):
        """Test checking if aiofiles is available."""
        result = AsyncFileOps.is_async_available()
        assert result == AIOFILES_AVAILABLE


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.mark.asyncio
    async def test_read_file_function(self, temp_file):
        """Test read_file convenience function."""
        content = await read_file(temp_file)
        assert content == "Hello, World!\n"

    @pytest.mark.asyncio
    async def test_write_file_function(self, temp_dir):
        """Test write_file convenience function."""
        file_path = temp_dir / "output.txt"
        await write_file(file_path, "Test content\n")
        assert file_path.read_text() == "Test content\n"

    @pytest.mark.asyncio
    async def test_file_hash_function(self, temp_file):
        """Test file_hash convenience function."""
        hash_value = await file_hash(temp_file)
        assert len(hash_value) == 16
