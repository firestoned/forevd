"""Tests for the forevd CLI — --timeout flag, env var, and httpd_include precedence.

Precedence (highest → lowest):
  1. httpd_include file containing a Timeout directive  (Apache last-directive-wins)
  2. --timeout CLI flag
  3. FOREVD_TIMEOUT environment variable
  4. Built-in default (10 s)
"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from forevd.__main__ import main


@pytest.fixture
def runner():
    return CliRunner()


def _invoke(runner, extra_args=None, env=None):
    """Invoke main with minimum required args plus extras, mocking apache.run.

    Uses sys.modules injection rather than a global importlib.import_module mock
    so that importlib.resources (used internally by firestone_lib's init_logging)
    still receives real module objects and does not break on Python 3.13+.
    """
    base_args = [
        "--backend",
        "http://localhost:8080",
        "--location",
        "/",
        "--no-exec",
    ]
    args = base_args + (extra_args or [])

    mock_apache = MagicMock()
    with (
        patch("forevd.__main__._setup_logging"),
        patch.dict("sys.modules", {"forevd.apache": mock_apache}),
    ):
        result = runner.invoke(main, args, env=env, catch_exceptions=False)

    return result, mock_apache


def _config(mock_module):
    """Extract the config dict passed to the mocked apache run call."""
    return mock_module.run.call_args[0][1]


# ---------------------------------------------------------------------------
# Default
# ---------------------------------------------------------------------------


class TestTimeoutDefault:
    def test_default_is_10(self, runner):
        result, mock_module = _invoke(runner)
        assert result.exit_code == 0
        assert _config(mock_module)["timeout"] == 10


# ---------------------------------------------------------------------------
# --timeout flag
# ---------------------------------------------------------------------------


class TestTimeoutFlag:
    def test_flag_sets_timeout(self, runner):
        result, mock_module = _invoke(runner, ["--timeout", "30"])
        assert result.exit_code == 0
        assert _config(mock_module)["timeout"] == 30

    def test_flag_overrides_default(self, runner):
        result, mock_module = _invoke(runner, ["--timeout", "1"])
        assert result.exit_code == 0
        assert _config(mock_module)["timeout"] == 1

    def test_flag_accepts_large_value(self, runner):
        result, mock_module = _invoke(runner, ["--timeout", "300"])
        assert result.exit_code == 0
        assert _config(mock_module)["timeout"] == 300

    def test_flag_value_in_config_dict(self, runner):
        """timeout must be present in the config passed to the backend."""
        result, mock_module = _invoke(runner, ["--timeout", "45"])
        assert result.exit_code == 0
        assert "timeout" in _config(mock_module)


# ---------------------------------------------------------------------------
# FOREVD_TIMEOUT environment variable (middle precedence tier)
# ---------------------------------------------------------------------------


class TestTimeoutEnvVar:
    def test_env_var_sets_timeout(self, runner):
        result, mock_module = _invoke(runner, env={"FOREVD_TIMEOUT": "45"})
        assert result.exit_code == 0
        assert _config(mock_module)["timeout"] == 45

    def test_env_var_overrides_default(self, runner):
        """FOREVD_TIMEOUT must override the built-in default of 10."""
        result, mock_module = _invoke(runner, env={"FOREVD_TIMEOUT": "20"})
        assert result.exit_code == 0
        assert _config(mock_module)["timeout"] == 20

    def test_flag_overrides_env_var(self, runner):
        """--timeout flag must take precedence over FOREVD_TIMEOUT."""
        result, mock_module = _invoke(runner, ["--timeout", "60"], env={"FOREVD_TIMEOUT": "45"})
        assert result.exit_code == 0
        assert _config(mock_module)["timeout"] == 60


# ---------------------------------------------------------------------------
# httpd_include file-based override (highest precedence at Apache level)
#
# Apache uses the last occurrence of a repeated global directive.  Because
# httpd_include is rendered *after* Timeout {{ timeout }}, a Timeout directive
# inside the include file will shadow the flag value at runtime.
# These tests verify that the config dict preserves both values correctly so
# the template can render them in the right order.
# ---------------------------------------------------------------------------


class TestHttpdIncludeOverride:
    def test_httpd_include_forwarded_in_config(self, runner):
        """httpd_include content must be present in the config dict."""
        include = "Timeout 120"
        result, mock_module = _invoke(runner, ["--httpd-include", include])
        assert result.exit_code == 0
        assert _config(mock_module)["httpd_include"] == include

    def test_timeout_flag_and_include_coexist(self, runner):
        """Both timeout and httpd_include are passed through together."""
        include = "Timeout 120"
        result, mock_module = _invoke(runner, ["--timeout", "30", "--httpd-include", include])
        assert result.exit_code == 0
        cfg = _config(mock_module)
        assert cfg["timeout"] == 30
        assert cfg["httpd_include"] == include

    def test_no_include_leaves_timeout_alone(self, runner):
        """When no httpd_include is provided httpd_include is None in config."""
        result, mock_module = _invoke(runner, ["--timeout", "30"])
        assert result.exit_code == 0
        cfg = _config(mock_module)
        assert cfg["timeout"] == 30
        assert cfg["httpd_include"] is None
