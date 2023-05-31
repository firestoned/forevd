"""
Resources module ot help load templates in
"""
import io
import logging
import os
import shlex
import shutil

import jinja2

_LOGGER = logging.getLogger(__name__)


def run(var_dir: str, config: dict, do_exec: bool, cmd: str = None):
    """Execute Apache given the config."""

    jinja_env = jinja2.Environment(
        loader=jinja2.PackageLoader("forevd", "apache"), autoescape=jinja2.select_autoescape()
    )
    jinja_env.add_extension("jinja2.ext.do")

    template = jinja_env.get_template("httpd.conf")

    apache_config = template.render(**config)
    _LOGGER.debug(f"apache_config: {apache_config}")

    config_file = os.path.join(var_dir, "httpd.conf")
    _LOGGER.debug(f"config_file: {config_file}")

    try:
        os.makedirs(var_dir, mode=0o700)
    except FileExistsError:
        pass

    with io.open(config_file, "w", encoding="utf-8") as fh:
        fh.write(apache_config)

    _LOGGER.debug(f"cmd: {cmd!r}")
    if not cmd:
        httpd = shutil.which("httpd")
        _LOGGER.debug(f"httpd: {httpd}")

        cmd = [
            os.path.basename(httpd),
            "-D",
            "FOREGROUND",
            "-f",
            config_file,
            "-d",
            "/opt/homebrew/Cellar/httpd/2.4.55/lib/httpd",
        ]
    else:
        cmd = shlex.split(cmd)
        httpd = shutil.which(cmd[0])

    if not do_exec:
        _LOGGER.info(f"Not executing command: {shlex.join(cmd)}")
        return

    _LOGGER.info(f"Executing: {httpd} {shlex.join(cmd)}")

    os.execve(httpd, cmd, os.environ)
