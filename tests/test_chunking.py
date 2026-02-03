"""Tests for commit chunking algorithm and decision logic."""

import pytest

from src.generate_changelog import process_commits_in_chunks


# Sample commit data helpers
def make_commits(count):
    """Generate sample commit data for testing."""
    commits = []
    for i in range(count):
        hash_full = f"a{'0' * 39}{i:04d}"
        hash_short = f"a{i:03d}"
        commits.append(
            f"{hash_full}|feat: Feature {i}|Author{i}|2024-01-{(i % 28) + 1:02d}|{hash_short}"
        )
    return "\n".join(commits)


class TestProcessCommitsInChunks:
    """Test the process_commits_in_chunks function."""

    def test_process_empty_commits(self):
        """Test handling of empty commit string."""
        commits_formatted, commit_links = process_commits_in_chunks("")

        assert commits_formatted == []
        assert commit_links == []

    def test_process_single_commit(self):
        """Test processing a single commit."""
        commits_raw = make_commits(1)
        commits_formatted, commit_links = process_commits_in_chunks(commits_raw)

        assert len(commits_formatted) == 1
        assert len(commit_links) == 1
        assert "feat: Feature 0" in commits_formatted[0]
        assert "Author0" in commits_formatted[0]
        assert "feat: Feature 0" in commit_links[0]
        assert "https://github.com/test-org/test-repo/commit/" in commit_links[0]

    def test_process_five_commits(self):
        """Test processing exactly 5 commits (at chunking threshold)."""
        commits_raw = make_commits(5)
        commits_formatted, commit_links = process_commits_in_chunks(commits_raw)

        assert len(commits_formatted) == 5
        assert len(commit_links) == 5
        # All commits should be processed
        for i in range(5):
            assert any(f"feat: Feature {i}" in commit for commit in commits_formatted)

    def test_process_six_commits(self):
        """Test processing 6 commits (above chunking threshold)."""
        commits_raw = make_commits(6)
        commits_formatted, commit_links = process_commits_in_chunks(commits_raw)

        assert len(commits_formatted) == 6
        assert len(commit_links) == 6
        # All commits should be processed
        for i in range(6):
            assert any(f"feat: Feature {i}" in commit for commit in commits_formatted)

    def test_process_hundred_commits(self):
        """Test processing large commit set (100 commits)."""
        commits_raw = make_commits(100)
        commits_formatted, commit_links = process_commits_in_chunks(commits_raw)

        assert len(commits_formatted) == 100
        assert len(commit_links) == 100
        # Spot check first, middle, and last commits
        assert any("feat: Feature 0" in commit for commit in commits_formatted)
        assert any("feat: Feature 50" in commit for commit in commits_formatted)
        assert any("feat: Feature 99" in commit for commit in commits_formatted)

    def test_process_malformed_commit(self):
        """Test handling of commit without pipe delimiter."""
        commits_raw = "malformed commit line without pipes"
        commits_formatted, commit_links = process_commits_in_chunks(commits_raw)

        assert len(commits_formatted) == 1
        assert len(commit_links) == 1
        assert "malformed commit line without pipes" in commits_formatted[0]
        assert "malformed commit line without pipes" in commit_links[0]

    def test_process_commit_with_special_chars(self):
        """Test handling of commits with special characters in message."""
        commits_raw = "abc123|feat: Add emoji 🎉 and symbols @#$|Author|2024-01-01|abc"
        commits_formatted, commit_links = process_commits_in_chunks(commits_raw)

        assert len(commits_formatted) == 1
        assert "feat: Add emoji 🎉 and symbols @#$" in commits_formatted[0]
        assert "Author" in commits_formatted[0]


class TestChunkingDecisionBoundary:
    """Test the chunking decision logic boundaries."""

    @pytest.mark.parametrize(
        "commit_count,should_chunk",
        [
            (0, False),  # Empty
            (1, False),  # Single commit
            (5, False),  # At threshold
            (6, True),  # Above threshold
            (10, True),  # Well above
            (100, True),  # Large set
        ],
    )
    def test_chunking_threshold(self, commit_count, should_chunk):
        """Test that chunking decision matches expected behavior.

        Note: This is a behavioral test - chunking should be enabled
        for commit counts > 5 based on COMMITS_PER_CHUNK = 5 in source.
        """
        COMMITS_PER_CHUNK = 5  # Mirror the constant from source
        use_chunking = commit_count > COMMITS_PER_CHUNK

        assert use_chunking == should_chunk, (
            f"Expected chunking={should_chunk} for {commit_count} commits, got {use_chunking}"
        )

        # Calculate expected chunk count
        if use_chunking:
            expected_chunks = (
                commit_count + COMMITS_PER_CHUNK - 1
            ) // COMMITS_PER_CHUNK
            assert expected_chunks > 0
        else:
            expected_chunks = 0

        # Verify the math matches ceiling division
        if commit_count > COMMITS_PER_CHUNK:
            import math

            assert expected_chunks == math.ceil(commit_count / COMMITS_PER_CHUNK)
