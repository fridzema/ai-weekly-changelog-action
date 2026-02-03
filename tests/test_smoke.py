"""Smoke test to verify pytest setup and module import."""


def test_pytest_runs():
    """Verify pytest is working."""
    assert True


def test_module_imports(setup_test_environment):
    """Verify generate_changelog can be imported after env setup."""
    import src.generate_changelog

    assert hasattr(src.generate_changelog, "retry_api_call")
    assert hasattr(src.generate_changelog, "redact_api_key")
