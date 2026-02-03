"""Tests for language configuration lookup and fallback."""

import pytest

from src.generate_changelog import get_language_config


class TestLanguageConfigurations:
    """Test language-specific configurations."""

    @pytest.mark.parametrize(
        "language,week_label,tech_label",
        [
            ("English", "Week", "🔧 Technical Changes"),
            ("Dutch", "Week", "🔧 Technische wijzigingen"),
            ("German", "Woche", "🔧 Technische Änderungen"),
            ("French", "Semaine", "🔧 Modifications techniques"),
            ("Spanish", "Semana", "🔧 Cambios técnicos"),
        ],
    )
    def test_supported_languages(self, language, week_label, tech_label):
        """Test that each supported language returns correct configuration."""
        config = get_language_config(language)

        assert config is not None
        assert config["week_label"] == week_label
        assert config["tech_changes"] == tech_label
        # Verify it has all required keys
        assert "generated_on" in config
        assert "commits_label" in config
        assert "user_impact" in config
        assert "all_commits" in config

    def test_all_languages_have_required_keys(self):
        """Test that all languages have the complete set of required configuration keys."""
        required_keys = {
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
        }

        supported_languages = ["English", "Dutch", "German", "French", "Spanish"]

        for language in supported_languages:
            config = get_language_config(language)
            config_keys = set(config.keys())

            # Check all required keys are present
            missing_keys = required_keys - config_keys
            assert not missing_keys, (
                f"Language '{language}' is missing keys: {missing_keys}"
            )

            # Verify all values are non-empty strings
            for key, value in config.items():
                assert isinstance(value, str), (
                    f"Language '{language}' key '{key}' is not a string: {type(value)}"
                )
                assert value.strip(), f"Language '{language}' key '{key}' is empty"

    def test_unsupported_language_fallback(self, capsys):
        """Test that unsupported language falls back to English with warning."""
        config = get_language_config("Klingon")

        # Should return English configuration
        assert config["week_label"] == "Week"
        assert config["tech_changes"] == "🔧 Technical Changes"

        # Should print warning to stdout
        captured = capsys.readouterr()
        assert "Warning: Language 'Klingon' not supported" in captured.out
        assert "Falling back to English" in captured.out
        assert "Supported languages:" in captured.out

    def test_case_sensitive_language_lookup(self, capsys):
        """Test that language lookup is case-sensitive."""
        # "english" (lowercase) should trigger fallback
        config = get_language_config("english")

        # Should fall back to English
        assert config["week_label"] == "Week"

        # Should show warning
        captured = capsys.readouterr()
        assert "Warning: Language 'english' not supported" in captured.out

    def test_empty_language_fallback(self, capsys):
        """Test handling of empty language string."""
        config = get_language_config("")

        # Should fall back to English
        assert config["week_label"] == "Week"

        # Should show warning
        captured = capsys.readouterr()
        assert "Warning: Language '' not supported" in captured.out

    def test_none_language_fallback(self, capsys):
        """Test handling of None as language."""
        config = get_language_config(None)

        # Should fall back to English
        assert config["week_label"] == "Week"

        # Should show warning
        captured = capsys.readouterr()
        assert "Warning: Language 'None' not supported" in captured.out

    def test_language_specific_statistics_labels(self):
        """Test that statistical terms are properly translated."""
        # English
        english = get_language_config("English")
        assert english["lines_added"] == "lines added"
        assert english["lines_deleted"] == "lines deleted"
        assert english["files_changed"] == "files changed"

        # Dutch
        dutch = get_language_config("Dutch")
        assert dutch["lines_added"] == "regels toegevoegd"
        assert dutch["lines_deleted"] == "regels verwijderd"
        assert dutch["files_changed"] == "bestanden gewijzigd"

        # German
        german = get_language_config("German")
        assert german["lines_added"] == "Zeilen hinzugefügt"
        assert german["lines_deleted"] == "Zeilen gelöscht"
        assert german["files_changed"] == "Dateien geändert"

    def test_fallback_messages_exist(self):
        """Test that fallback messages exist for all languages."""
        supported_languages = ["English", "Dutch", "German", "French", "Spanish"]

        for language in supported_languages:
            config = get_language_config(language)

            # Technical fallback
            assert config["fallback_tech"]
            assert len(config["fallback_tech"]) > 20, (
                f"Language '{language}' fallback_tech is too short"
            )

            # Business fallback
            assert config["fallback_business"]
            assert len(config["fallback_business"]) > 20, (
                f"Language '{language}' fallback_business is too short"
            )
