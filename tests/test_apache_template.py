"""Tests for Apache httpd.conf Jinja2 template rendering, focusing on Timeout."""

import jinja2
import pytest


def _get_template():
    jinja_env = jinja2.Environment(
        loader=jinja2.PackageLoader("forevd", "apache"),
        autoescape=jinja2.select_autoescape(),
    )
    jinja_env.add_extension("jinja2.ext.do")
    return jinja_env.get_template("httpd.conf")


def _base_config(**overrides):
    config = {
        "server_name": "test.example.com",
        "listen": "127.0.0.1:8080",
        "err_log": "/dev/stderr",
        "access_log": "/dev/stdout",
        "timeout": 10,
        "debug": False,
        "cert": None,
        "ca_cert": None,
        "cert_key": None,
        "oidc": None,
        "ldap": None,
        "ssl": None,
        "httpd_include": None,
        "locations": [
            {
                "path": "/",
                "backend": "http://localhost:8080",
                "authc": {},
                "authz": {},
                "http_methods": None,
                "set_access_token": True,
            }
        ],
    }
    config.update(overrides)
    return config


# ---------------------------------------------------------------------------
# Timeout directive value
# ---------------------------------------------------------------------------


def test_default_timeout_renders():
    rendered = _get_template().render(**_base_config())
    assert "Timeout 10" in rendered


def test_custom_timeout_renders():
    rendered = _get_template().render(**_base_config(timeout=30))
    assert "Timeout 30" in rendered


def test_timeout_is_not_hardcoded():
    """Changing the timeout value must change the rendered output."""
    rendered = _get_template().render(**_base_config(timeout=60))
    assert "Timeout 60" in rendered
    assert "Timeout 10" not in rendered


@pytest.mark.parametrize("timeout", [1, 10, 30, 120, 300])
def test_timeout_parametrized(timeout):
    rendered = _get_template().render(**_base_config(timeout=timeout))
    assert f"Timeout {timeout}" in rendered


# ---------------------------------------------------------------------------
# httpd_include ordering — file-based override
# ---------------------------------------------------------------------------


def test_httpd_include_rendered_after_timeout():
    """httpd_include block must appear after the Timeout directive so that
    a Timeout directive in the include file can override the flag value."""
    sentinel = "SENTINEL_INCLUDE_CONTENT"
    rendered = _get_template().render(**_base_config(httpd_include=sentinel))

    timeout_pos = rendered.index("Timeout 10")
    include_pos = rendered.index(sentinel)
    assert (
        include_pos > timeout_pos
    ), "httpd_include must be rendered after Timeout so it can override it"


def test_httpd_include_timeout_override_ordering():
    """When the include file contains its own Timeout directive, it appears
    after the template-generated one — Apache uses the last occurrence."""
    include_content = "Timeout 120"
    rendered = _get_template().render(**_base_config(timeout=10, httpd_include=include_content))

    # Both directives present; the file-supplied one must come last
    first = rendered.index("Timeout 10")
    second = rendered.index("Timeout 120")
    assert (
        second > first
    ), "File-supplied Timeout must appear after the flag-set Timeout so Apache honours it"


def test_httpd_include_absent_does_not_affect_timeout():
    """When no httpd_include is provided the Timeout directive is present exactly once."""
    rendered = _get_template().render(**_base_config(timeout=10))
    assert rendered.count("Timeout 10") == 1


def test_httpd_include_without_timeout_directive():
    """An include file that does not set Timeout leaves the flag value in effect."""
    rendered = _get_template().render(
        **_base_config(timeout=30, httpd_include="Header set X-Powered-By forevd")
    )
    # Only one Timeout line (from the flag), no second occurrence
    assert rendered.count("Timeout") == 1
    assert "Timeout 30" in rendered
