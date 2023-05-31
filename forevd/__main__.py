"""
The main entry point for forevd.
"""
import importlib
import logging
import os
import tempfile

import click

from firestone_lib import cli

_DEFAULT_ERRLOG = "/dev/stderr"
_DEFAULT_ACCESSLOG = "/dev/stdout"

_DEFAULT_LISTEN = "127.0.0.1:8080"
_DEFAULT_HOSTNAME = os.environ.get("HOSTNAME", "localhost")

_DEFAULT_VAR_DIR = os.path.join(tempfile.mkdtemp(), "forevd")

_LOGGER = logging.getLogger(__name__)


def _setup_logging(debug):
    cli.init_logging("forevd.resources.logging", "cli.conf")

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("forevd").setLevel(logging.DEBUG)


def _nomalize_locations(
    locations: dict, backend: str, location: str, mtls: bool, http_methods: list
):
    if not locations:
        locations = {}

    loc_struct = locations.get(location, {})
    loc_struct["backend"] = backend
    loc_struct["mtls"] = mtls
    loc_struct["http_methods"] = http_methods

    locations[location] = loc_struct

    return locations


@click.command()
@click.option(
    "--access-log",
    help="Location of the access log",
    type=click.Path(),
    default=_DEFAULT_ACCESSLOG,
    show_default=True,
)
@click.option(
    "--backend-type",
    help="Provide the backend type.",
    default="apache",
    type=click.Choice(["apache"]),
    show_default=True,
)
@click.option(
    "--backend",
    help="The backend of this reverse proxy will front, e.g. http://localhost:8080/foo",
    type=str,
)
@click.option(
    "--ca-cert",
    help="The CA cert to be used",
    type=click.Path(),
)
@click.option(
    "--cert-key",
    help="The key certificate",
    type=click.Path(),
)
@click.option(
    "--cert",
    help="The key certificate",
    type=click.Path(),
)
@click.option(
    "--cmd",
    help="Override the command to execute the appropriate backend; "
    "default depends on the backend, e.g. for apache, it must be in your PATH",
)
@click.option("--debug", help="Turn on debugging", is_flag=True)
@click.option(
    "--exec/--no-exec",
    "do_exec",
    help="Execute the command after generating config",
    is_flag=True,
    default=True,
)
@click.option(
    "--err-log",
    help="Location of the error log",
    type=click.Path(),
    default=_DEFAULT_ERRLOG,
    show_default=True,
)
@click.option(
    "--http-methods",
    help="Restrict HTTP method calls for the supplied list ",
    type=cli.StrList,
)
@click.option(
    "--ldap",
    help="Provide the LDAP config in a JSON or YAML string or file",
    type=cli.FromJsonOrYaml(),
)
@click.option(
    "--listen",
    help="The IP/hostname and port to listen on",
    type=str,
    default=_DEFAULT_LISTEN,
    show_default=True,
)
@click.option(
    "--location",
    help="Provide a json string or file with location details",
    type=str,
)
@click.option(
    "--locations",
    help="Provide the Location config in a JSON or YAML string or file",
    type=cli.FromJsonOrYaml(),
)
@click.option("--mtls", help="Enable mutual TLS", type=click.Choice(["optional", "require"]))
@click.option(
    "--oidc",
    help="Provide the OIDC config in a JSON or YAML string or file",
    type=cli.FromJsonOrYaml(),
)
@click.option(
    "--server-name",
    help="Define the server name, else it uses $HOSTNAME",
    type=str,
    show_default=True,
    default=_DEFAULT_HOSTNAME,
    envvar="FOREVD_HOSTNAME",
)
@click.option(
    "--var-dir",
    help="The backend of this reverse proxy will front, e.g. http://localhost:8080/foo",
    type=click.Path(),
    default=_DEFAULT_VAR_DIR,
    show_default=True,
)
# pylint: disable=too-many-arguments,too-many-locals
def main(
    access_log,
    backend_type,
    backend,
    ca_cert,
    cert,
    cert_key,
    cmd,
    debug,
    err_log,
    do_exec,
    http_methods,
    ldap,
    listen,
    location,
    locations,
    mtls,
    oidc,
    server_name,
    var_dir,
):
    """forevd is a forward/reverse proxy, primarily used as a sidecar for REST or any HTTP/s apps."""
    _setup_logging(debug)

    if not backend and location and not locations:
        raise click.UsageError("You must supply a --backend and --location or --locations")

    config = {
        "err_log": err_log,
        "access_log": access_log,
        "ca_cert": ca_cert,
        "cert": cert,
        "cert_key": cert_key,
        "debug": debug,
        "ldap": ldap,
        "locations": _nomalize_locations(locations, backend, location, mtls, http_methods),
        "listen": listen,
        "oidc": oidc,
        "server_name": server_name,
    }
    _LOGGER.debug(f"config: {config}")

    mod = importlib.import_module(f"forevd.{backend_type}")

    getattr(mod, "run")(var_dir, config, do_exec, cmd)


if __name__ == "main":
    # pylint: disable=no-value-for-parameter
    main()
