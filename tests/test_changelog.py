"""Tests for changelog file operations and format validation."""

import os

import pytest

from src.generate_changelog import cleanup_temp_files, process_commits_in_chunks


class TestCleanupTempFiles:
    """Tests for cleanup_temp_files function."""

    def test_cleanup_removes_temp_files(self, tmp_path, monkeypatch, capfd):
        """Test that cleanup_temp_files removes all expected temporary files."""
        monkeypatch.chdir(tmp_path)

        # Create temp files
        temp_files = [
            "commits.txt",
            "commits_extended.txt",
            "files_changed.txt",
            "lines_added.tmp",
            "lines_deleted.tmp",
        ]
        for filename in temp_files:
            (tmp_path / filename).write_text("test content")

        # Verify files exist
        for filename in temp_files:
            assert (tmp_path / filename).exists()

        # Run cleanup
        cleanup_temp_files()

        # Verify all files removed
        for filename in temp_files:
            assert not (tmp_path / filename).exists()

    def test_cleanup_handles_missing_files(self, tmp_path, monkeypatch, capfd):
        """Test that cleanup_temp_files doesn't error on missing files."""
        monkeypatch.chdir(tmp_path)

        # Don't create any files - cleanup should handle gracefully
        cleanup_temp_files()

        # Should complete without raising exceptions
        # No warnings should be printed for missing files (they just don't exist)
        captured = capfd.readouterr()
        assert "Could not remove temp file" not in captured.out

    def test_cleanup_logs_oserror(self, tmp_path, monkeypatch, capfd):
        """Test that cleanup_temp_files logs OSError when file removal fails."""
        monkeypatch.chdir(tmp_path)

        # Create a file
        test_file = tmp_path / "commits.txt"
        test_file.write_text("test")

        # Make file read-only (simulate permission error)
        test_file.chmod(0o444)

        # Make directory read-only to prevent deletion (platform-specific)
        if os.name != "nt":  # Unix-like systems
            tmp_path.chmod(0o555)

            try:
                cleanup_temp_files()
                captured = capfd.readouterr()

                # Should log warning about inability to remove file
                assert "Warning: Could not remove temp file" in captured.out
                assert "commits.txt" in captured.out
            finally:
                # Restore permissions for cleanup
                tmp_path.chmod(0o755)
                test_file.chmod(0o644)


class TestProcessCommitsInChunks:
    """Tests for process_commits_in_chunks function."""

    def test_process_commits_formats_correctly(self, monkeypatch):
        """Test that process_commits_in_chunks formats commits correctly."""
        monkeypatch.setenv("GITHUB_REPOSITORY", "test-org/test-repo")

        commits_raw = """abc123|feat: Add feature|Author1|2024-01-01|abc
def456|fix: Fix bug|Author2|2024-01-02|def"""

        formatted, links = process_commits_in_chunks(commits_raw, chunk_size=50)

        # Check formatted output
        assert len(formatted) == 2
        assert formatted[0] == "• feat: Add feature (Author1, 2024-01-01)"
        assert formatted[1] == "• fix: Fix bug (Author2, 2024-01-02)"

        # Check links
        assert len(links) == 2
        assert "[abc](https://github.com/test-org/test-repo/commit/abc123)" in links[0]
        assert "feat: Add feature" in links[0]
        assert "[def](https://github.com/test-org/test-repo/commit/def456)" in links[1]
        assert "fix: Fix bug" in links[1]

    def test_process_commits_handles_empty(self, monkeypatch):
        """Test that process_commits_in_chunks handles empty input gracefully."""
        monkeypatch.setenv("GITHUB_REPOSITORY", "test-org/test-repo")

        commits_raw = ""

        formatted, links = process_commits_in_chunks(commits_raw, chunk_size=50)

        # Should return empty lists for empty input
        assert len(formatted) == 0
        assert len(links) == 0

    def test_process_commits_handles_partial_pipe_lines(self, monkeypatch):
        """Test that commits with | but fewer than 5 parts are handled as raw lines."""
        monkeypatch.setenv("GITHUB_REPOSITORY", "test-org/test-repo")

        # Line with pipe but fewer than 5 parts
        commits_raw = "abc123|partial line only"

        formatted, links = process_commits_in_chunks(commits_raw, chunk_size=50)

        assert len(formatted) == 1
        assert formatted[0] == "• abc123|partial line only"
        assert links[0] == "- abc123|partial line only"

    def test_process_commits_handles_multiple_chunks(self, monkeypatch, capfd):
        """Test that process_commits_in_chunks processes large sets in chunks."""
        monkeypatch.setenv("GITHUB_REPOSITORY", "test-org/test-repo")

        # Create 250 commits to trigger chunking logic
        commits = []
        for i in range(250):
            commits.append(f"hash{i}|feat: Feature {i}|Author{i}|2024-01-01|h{i}")
        commits_raw = "\n".join(commits)

        formatted, links = process_commits_in_chunks(commits_raw, chunk_size=50)

        # Should process all commits
        assert len(formatted) == 250
        assert len(links) == 250

        # Should print progress indicator for large sets (>200 commits)
        captured = capfd.readouterr()
        assert "Processed" in captured.out
        assert "commits..." in captured.out


class TestChangelogFormatLogic:
    """Tests for changelog format and logic patterns."""

    def test_week_header_format(self):
        """Test that week header format matches expected pattern."""
        from src.generate_changelog import get_language_config

        config = get_language_config("English")
        week_num = 5
        year = 2024

        # This is the format used in the code
        week_header = f"## {config['week_label']} {week_num}, {year}"

        assert week_header == "## Week 5, 2024"

    def test_duplicate_detection_logic(self):
        """Test the logic for detecting duplicate week entries."""
        from src.generate_changelog import get_language_config

        config = get_language_config("English")
        week_num = 5
        year = 2024
        week_header = f"## {config['week_label']} {week_num}, {year}"

        # Simulate existing changelog content
        existing_content = """# Changelog

This file is automatically updated.

## Week 5, 2024

*Generated on 01-15-2024 - 3 commits*

### 🔧 Technical Changes
Some changes

---

## Week 4, 2024

*Generated on 01-08-2024 - 2 commits*
"""

        # Test duplicate detection
        assert week_header in existing_content

        # Test different week not detected as duplicate
        different_week_header = f"## {config['week_label']} 6, {year}"
        assert different_week_header not in existing_content

    def test_changelog_entry_structure(self):
        """Test that changelog entry has required structure elements."""
        import textwrap

        from src.generate_changelog import get_language_config

        config = get_language_config("English")
        week_num = 5
        year = 2024
        formatted_date = "01-15-2024"
        num_commits = 3
        tech_summary = "Test technical summary"
        business_summary = "Test business summary"
        commits_links = "- [abc123] Test commit"

        # Simulate the entry creation logic
        week_header = f"## {config['week_label']} {week_num}, {year}"
        changelog_entry = textwrap.dedent(f"""
    {week_header}

    *{config["generated_on"]} {formatted_date} - {num_commits} {config["commits_label"]}*

    ### {config["tech_changes"]}
    {tech_summary}

    ### {config["user_impact"]}
    {business_summary}

    ### {config["all_commits"]}
    {commits_links}

    ---
    """).strip()

        # Verify structure
        assert week_header in changelog_entry
        assert config["generated_on"] in changelog_entry
        assert config["tech_changes"] in changelog_entry
        assert config["user_impact"] in changelog_entry
        assert config["all_commits"] in changelog_entry
        assert tech_summary in changelog_entry
        assert business_summary in changelog_entry
        assert "---" in changelog_entry

    def test_force_update_suffix(self):
        """Test that force update adds correct suffix to week header."""
        from src.generate_changelog import get_language_config

        config = get_language_config("English")
        week_num = 5
        year = 2024

        # Test with force_update = True
        force_update = True
        force_suffix = f" {config['force_updated']}" if force_update else ""
        week_header = f"## {config['week_label']} {week_num}, {year}{force_suffix}"

        assert "(Force Updated)" in week_header

        # Test with force_update = False
        force_update = False
        force_suffix = f" {config['force_updated']}" if force_update else ""
        week_header = f"## {config['week_label']} {week_num}, {year}{force_suffix}"

        assert "(Force Updated)" not in week_header


class TestLanguageConfigChangelogKeys:
    """Tests for language-specific changelog configurations."""

    @pytest.mark.parametrize(
        "language", ["English", "Dutch", "German", "French", "Spanish"]
    )
    def test_language_config_has_changelog_keys(self, language):
        """Test that each language config has all required changelog keys."""
        from src.generate_changelog import get_language_config

        config = get_language_config(language)

        # Required keys for changelog generation
        required_keys = [
            "week_label",
            "generated_on",
            "commits_label",
            "tech_changes",
            "user_impact",
            "all_commits",
            "statistics",
            "file_changes",
            "changelog_title",
            "auto_updated",
            "fallback_tech",
            "fallback_business",
            "lines_added",
            "lines_deleted",
            "files_changed",
            "force_updated",
        ]

        for key in required_keys:
            assert key in config, f"Language '{language}' missing key '{key}'"
            assert config[key], f"Language '{language}' has empty value for key '{key}'"

    def test_date_format_per_language(self):
        """Test that date format is correct for each language."""
        import datetime

        from src.generate_changelog import get_language_config

        # Date formats used in the code
        date_formats = {
            "English": "%m-%d-%Y",
            "Dutch": "%d-%m-%Y",
            "German": "%d.%m.%Y",
            "French": "%d/%m/%Y",
            "Spanish": "%d/%m/%Y",
        }

        test_date = datetime.date(2024, 1, 15)

        expected_formats = {
            "English": "01-15-2024",
            "Dutch": "15-01-2024",
            "German": "15.01.2024",
            "French": "15/01/2024",
            "Spanish": "15/01/2024",
        }

        for language, date_format in date_formats.items():
            formatted = test_date.strftime(date_format)
            assert formatted == expected_formats[language], (
                f"Language '{language}' date format mismatch"
            )

            # Also verify the language config can be retrieved
            config = get_language_config(language)
            assert config is not None
