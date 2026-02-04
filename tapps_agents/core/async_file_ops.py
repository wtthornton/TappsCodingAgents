"""
Async File Operations - Async file I/O utilities using aiofiles.

2025 Performance Pattern: Async file operations for better concurrency.
Python 3.13+ supports native async file I/O, but aiofiles provides a more
convenient API and better cross-platform compatibility.

References:
- docs/PERFORMANCE_OPTIMIZATION_RECOMMENDATIONS_2025.md
- docs/PERFORMANCE_PATTERNS_QUICK_REFERENCE.md
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import AsyncIterator
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import aiofiles, fall back to sync operations if not available
try:
    import aiofiles
    import aiofiles.os
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    logger.warning(
        "aiofiles not installed. Async file operations will use synchronous fallback. "
        "Install with: pip install aiofiles"
    )


class AsyncFileOps:
    """
    Async file operations using aiofiles.
    
    Provides async versions of common file operations for better concurrency
    in async applications. Falls back to synchronous operations if aiofiles
    is not installed.
    
    Features:
    - Async read/write operations
    - File hashing
    - Line-by-line iteration
    - Atomic writes
    
    Example:
        # Read file asynchronously
        content = await AsyncFileOps.read_file(Path("file.txt"))
        
        # Write file asynchronously
        await AsyncFileOps.write_file(Path("file.txt"), "content")
        
        # Compute file hash
        hash = await AsyncFileOps.file_hash(Path("file.txt"))
    """
    
    @staticmethod
    async def read_file(file_path: Path, encoding: str = "utf-8") -> str:
        """
        Read file asynchronously.
        
        Args:
            file_path: Path to the file
            encoding: File encoding (default: utf-8)
            
        Returns:
            File contents as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            OSError: If file cannot be read
        """
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(file_path, encoding=encoding) as f:
                return await f.read()
        else:
            # Synchronous fallback
            return file_path.read_text(encoding=encoding)
    
    @staticmethod
    async def read_bytes(file_path: Path) -> bytes:
        """
        Read file as bytes asynchronously.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File contents as bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
            OSError: If file cannot be read
        """
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()
        else:
            # Synchronous fallback
            return file_path.read_bytes()
    
    @staticmethod
    async def write_file(
        file_path: Path,
        content: str,
        encoding: str = "utf-8",
        create_parents: bool = True,
    ) -> None:
        """
        Write file asynchronously.
        
        Args:
            file_path: Path to the file
            content: Content to write
            encoding: File encoding (default: utf-8)
            create_parents: Create parent directories if they don't exist
            
        Raises:
            OSError: If file cannot be written
        """
        if create_parents:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(file_path, "w", encoding=encoding) as f:
                await f.write(content)
        else:
            # Synchronous fallback
            file_path.write_text(content, encoding=encoding)
    
    @staticmethod
    async def write_bytes(
        file_path: Path,
        content: bytes,
        create_parents: bool = True,
    ) -> None:
        """
        Write bytes to file asynchronously.
        
        Args:
            file_path: Path to the file
            content: Content to write
            create_parents: Create parent directories if they don't exist
            
        Raises:
            OSError: If file cannot be written
        """
        if create_parents:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
        else:
            # Synchronous fallback
            file_path.write_bytes(content)
    
    @staticmethod
    async def write_atomic(
        file_path: Path,
        content: str,
        encoding: str = "utf-8",
        create_parents: bool = True,
    ) -> None:
        """
        Write file atomically (write to temp, then rename).
        
        This ensures the file is never in a partially written state.
        
        Args:
            file_path: Path to the file
            content: Content to write
            encoding: File encoding (default: utf-8)
            create_parents: Create parent directories if they don't exist
            
        Raises:
            OSError: If file cannot be written
        """
        if create_parents:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        
        try:
            if AIOFILES_AVAILABLE:
                async with aiofiles.open(temp_path, "w", encoding=encoding) as f:
                    await f.write(content)
                # Rename (atomic on most systems)
                temp_path.replace(file_path)
            else:
                # Synchronous fallback
                temp_path.write_text(content, encoding=encoding)
                temp_path.replace(file_path)
        except Exception:
            # Clean up temp file on error
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
    
    @staticmethod
    async def file_hash(file_path: Path, algorithm: str = "sha256") -> str:
        """
        Compute file hash asynchronously.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm (default: sha256)
            
        Returns:
            Hex digest of file hash (truncated to 16 characters)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            OSError: If file cannot be read
        """
        content = await AsyncFileOps.read_bytes(file_path)
        hasher = hashlib.new(algorithm)
        hasher.update(content)
        return hasher.hexdigest()[:16]
    
    @staticmethod
    async def file_exists(file_path: Path) -> bool:
        """
        Check if file exists asynchronously.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        if AIOFILES_AVAILABLE:
            try:
                await aiofiles.os.stat(file_path)
                return True
            except FileNotFoundError:
                return False
        else:
            # Synchronous fallback
            return file_path.exists()
    
    @staticmethod
    async def file_size(file_path: Path) -> int:
        """
        Get file size asynchronously.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if AIOFILES_AVAILABLE:
            stat = await aiofiles.os.stat(file_path)
            return stat.st_size
        else:
            # Synchronous fallback
            return file_path.stat().st_size
    
    @staticmethod
    async def iter_lines(
        file_path: Path,
        encoding: str = "utf-8",
    ) -> AsyncIterator[str]:
        """
        Iterate over file lines asynchronously.
        
        Args:
            file_path: Path to the file
            encoding: File encoding (default: utf-8)
            
        Yields:
            Lines from the file (with newlines stripped)
        """
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(file_path, encoding=encoding) as f:
                async for line in f:
                    yield line.rstrip("\n\r")
        else:
            # Synchronous fallback
            with open(file_path, encoding=encoding) as f:
                for line in f:
                    yield line.rstrip("\n\r")
    
    @staticmethod
    async def append_file(
        file_path: Path,
        content: str,
        encoding: str = "utf-8",
        create_parents: bool = True,
    ) -> None:
        """
        Append content to file asynchronously.
        
        Args:
            file_path: Path to the file
            content: Content to append
            encoding: File encoding (default: utf-8)
            create_parents: Create parent directories if they don't exist
            
        Raises:
            OSError: If file cannot be written
        """
        if create_parents:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if AIOFILES_AVAILABLE:
            async with aiofiles.open(file_path, "a", encoding=encoding) as f:
                await f.write(content)
        else:
            # Synchronous fallback
            with open(file_path, "a", encoding=encoding) as f:
                f.write(content)
    
    @staticmethod
    async def delete_file(file_path: Path, missing_ok: bool = True) -> bool:
        """
        Delete file asynchronously.
        
        Args:
            file_path: Path to the file
            missing_ok: If True, don't raise error if file doesn't exist
            
        Returns:
            True if file was deleted, False if it didn't exist
            
        Raises:
            FileNotFoundError: If file doesn't exist and missing_ok is False
            OSError: If file cannot be deleted
        """
        if AIOFILES_AVAILABLE:
            try:
                await aiofiles.os.remove(file_path)
                return True
            except FileNotFoundError:
                if not missing_ok:
                    raise
                return False
        else:
            # Synchronous fallback
            try:
                file_path.unlink()
                return True
            except FileNotFoundError:
                if not missing_ok:
                    raise
                return False
    
    @staticmethod
    async def copy_file(
        source: Path,
        destination: Path,
        create_parents: bool = True,
    ) -> None:
        """
        Copy file asynchronously.
        
        Args:
            source: Source file path
            destination: Destination file path
            create_parents: Create parent directories if they don't exist
            
        Raises:
            FileNotFoundError: If source doesn't exist
            OSError: If file cannot be copied
        """
        content = await AsyncFileOps.read_bytes(source)
        await AsyncFileOps.write_bytes(destination, content, create_parents=create_parents)
    
    @staticmethod
    def is_async_available() -> bool:
        """
        Check if async file operations are available.
        
        Returns:
            True if aiofiles is installed, False otherwise
        """
        return AIOFILES_AVAILABLE


# Convenience functions for common operations
async def read_file(file_path: Path, encoding: str = "utf-8") -> str:
    """Read file asynchronously (convenience function)."""
    return await AsyncFileOps.read_file(file_path, encoding)


async def write_file(file_path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write file asynchronously (convenience function)."""
    await AsyncFileOps.write_file(file_path, content, encoding)


async def file_hash(file_path: Path) -> str:
    """Compute file hash asynchronously (convenience function)."""
    return await AsyncFileOps.file_hash(file_path)
