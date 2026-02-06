"""Tests for chunk cache functions."""

import os
import time
from unittest.mock import patch

from src.generate_changelog import (
    cleanup_chunk_cache,
    get_chunk_cache_dir,
    get_chunk_cache_key,
    read_chunk_cache,
    write_chunk_cache,
)


class TestGetChunkCacheKey:
    """Tests for get_chunk_cache_key function."""

    def test_deterministic(self):
        """Same inputs produce the same cache key."""
        key1 = get_chunk_cache_key("commits", "technical", "gpt-4", "English")
        key2 = get_chunk_cache_key("commits", "technical", "gpt-4", "English")
        assert key1 == key2
        assert len(key1) == 16

    def test_unique_for_different_inputs(self):
        """Different inputs produce different cache keys."""
        key1 = get_chunk_cache_key("commits-a", "technical", "gpt-4", "English")
        key2 = get_chunk_cache_key("commits-b", "technical", "gpt-4", "English")
        assert key1 != key2


class TestGetChunkCacheDir:
    """Tests for get_chunk_cache_dir function."""

    def test_creates_directory(self, tmp_path):
        """Directory is created if it doesn't exist."""
        cache_dir = os.path.join(str(tmp_path), "changelog_cache", "chunks")
        with patch("src.generate_changelog.tempfile") as mock_tempfile:
            mock_tempfile.gettempdir.return_value = str(tmp_path)
            result = get_chunk_cache_dir()

        assert result == cache_dir
        assert os.path.isdir(cache_dir)


class TestReadChunkCache:
    """Tests for read_chunk_cache function."""

    def test_cache_miss(self, tmp_path):
        """Returns None for non-existent key."""
        with patch(
            "src.generate_changelog.get_chunk_cache_dir", return_value=str(tmp_path)
        ):
            result = read_chunk_cache("nonexistent_key")
        assert result is None

    def test_cache_hit(self, tmp_path):
        """Returns content for cached key."""
        cache_file = tmp_path / "test_key.txt"
        cache_file.write_text("cached content")

        with patch(
            "src.generate_changelog.get_chunk_cache_dir", return_value=str(tmp_path)
        ):
            result = read_chunk_cache("test_key")
        assert result == "cached content"

    def test_empty_file_returns_none(self, tmp_path):
        """Returns None for empty cache file."""
        cache_file = tmp_path / "empty_key.txt"
        cache_file.write_text("   ")

        with patch(
            "src.generate_changelog.get_chunk_cache_dir", return_value=str(tmp_path)
        ):
            result = read_chunk_cache("empty_key")
        assert result is None

    def test_handles_os_error(self, tmp_path, capfd):
        """Logs warning on read failure."""
        with patch(
            "src.generate_changelog.get_chunk_cache_dir", return_value=str(tmp_path)
        ):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", side_effect=OSError("Permission denied")):
                    result = read_chunk_cache("bad_key")

        assert result is None
        captured = capfd.readouterr()
        assert "Warning: Could not read cache file" in captured.out


class TestWriteChunkCache:
    """Tests for write_chunk_cache function."""

    def test_creates_file(self, tmp_path):
        """Writes content to disk."""
        with patch(
            "src.generate_changelog.get_chunk_cache_dir", return_value=str(tmp_path)
        ):
            write_chunk_cache("write_key", "some content")

        cache_file = tmp_path / "write_key.txt"
        assert cache_file.exists()
        assert cache_file.read_text() == "some content"

    def test_handles_os_error(self, tmp_path, capfd):
        """Logs warning on write failure."""
        with patch(
            "src.generate_changelog.get_chunk_cache_dir", return_value=str(tmp_path)
        ):
            with patch("builtins.open", side_effect=OSError("Disk full")):
                write_chunk_cache("bad_key", "content")

        captured = capfd.readouterr()
        assert "Warning: Could not write cache file" in captured.out


class TestCleanupChunkCache:
    """Tests for cleanup_chunk_cache function."""

    def test_removes_old_files(self, tmp_path, capfd):
        """Removes files older than threshold."""
        old_file = tmp_path / "old.txt"
        old_file.write_text("old")
        # Set mtime to 3 days ago
        old_time = time.time() - (72 * 3600)
        os.utime(old_file, (old_time, old_time))

        with patch(
            "src.generate_changelog.get_chunk_cache_dir", return_value=str(tmp_path)
        ):
            cleanup_chunk_cache(max_age_hours=48)

        assert not old_file.exists()
        captured = capfd.readouterr()
        assert "Cleaned up 1 stale chunk cache files" in captured.out

    def test_keeps_recent_files(self, tmp_path):
        """Keeps files within threshold."""
        recent_file = tmp_path / "recent.txt"
        recent_file.write_text("recent")

        with patch(
            "src.generate_changelog.get_chunk_cache_dir", return_value=str(tmp_path)
        ):
            cleanup_chunk_cache(max_age_hours=48)

        assert recent_file.exists()

    def test_handles_missing_dir(self, tmp_path):
        """Handles non-existent directory gracefully."""
        missing = str(tmp_path / "nonexistent")
        with patch("src.generate_changelog.get_chunk_cache_dir", return_value=missing):
            # Should not raise
            cleanup_chunk_cache()
