# Forevd Copilot Instructions

## Intent & Scope
- `forevd` ships a sidecar-style forward/reverse proxy that externalizes authn/authz so application services stay unaware of identity plumbing.
- Current focus is Apache HTTPD; nginx support is aspirational/TBD and should be treated as future work.
- CLI tooling targets automation scenarios (containers, CI) where configs may be provided inline or as files with Jinja2-based env substitution.

## Ecosystem Awareness
- `firestone_lib` supplies the CLI parameter types, logging config bootstrap, and schema loaders used here—keep imports aligned with its public API and coordinate on breaking changes.
- `firestone` leans on the same shared library; if you extend templating or resource semantics, check whether the generators might need equivalent updates.
- Note cross-repo impacts in PR descriptions and, when necessary, link to the companion changes so the Firestone suite can version bump together.

## Core Components
- CLI entry point: `forevd.__main__.main` wires `click` + `firestone_lib.cli` helpers, validates option combos, and prepares a normalized config dict for the backend.
- Location normalization: `_nomalize_locations` merges single `--backend/--location` values with multi-location payloads and fills default authc/authz/http method settings so the template has everything it needs.
- Apache backend: `forevd.apache.run` loads `apache/httpd.conf` via Jinja2, writes it under `var_dir/httpd.conf`, and, when `--exec` is left on (default), `execve`s the resolved `httpd` binary.
- Templates & resources live under `forevd/apache` and `forevd/resources` (logging config consumed through `firestone_lib.cli.init_logging`).
- `forevd/app.py` is a minimal FastAPI sample that echoes incoming headers—useful for manual or automated smoke tests of the proxy pipeline.

## Configuration Lifecycle
- CLI accepts JSON/YAML payloads directly or via `@file` syntax for `--locations`, `--ldap`, `--oidc`, and `--ssl`; the helper types already handle parsing and slurping files.
- Example configs in `etc/` demonstrate common scenarios (multiple backends, LDAP groups, allow-all, static users, SSL hardening) and rely on Jinja templating for secrets and host-specific values.
- Location records expect `path`, optional `match`, `backend`, `authc` (keys: `mtls`, `oidc`), `authz` (join semantics + LDAP/users/allow_all), `http_methods`, and `set_access_token`; keep `_nomalize_locations` and the Apache template in sync when adding new keys.
- Authn features (mTLS, OIDC) enable derived headers (`X-Remote-User`, `Authorization`, certificate data) in the emitted config—ensure downstream expectations stay aligned when changing defaults.

## When Extending
- Prefer augmenting `forevd/__main__.py` for new CLI switches and feed them through the config dict; update the Jinja template alongside any new surface area.
- If additional backends are introduced, follow the Apache module pattern (`run(var_dir, config, do_exec, cmd)`) so the CLI can dynamically import by `--backend-type`.
- Maintain compatibility with existing option workflows: guard against missing `--backend/--location` when `--locations` is absent, and keep helpful `click.UsageError` messages.
- Logging defaults come from `forevd.resources.logging.cli.conf`; extend via that config or by exposing CLI overrides rather than ad-hoc logging setup.

## Operational Notes
- Default paths: listen on `127.0.0.1:8080`, server name from `$HOSTNAME`, logs to stdout/stderr, temporary config written under a generated `var_dir` unless overridden.
- `--cmd` lets operators supply a custom launch command (e.g., containerized httpd); remember to honour it when adjusting exec logic.
- Mutual TLS requires both `--cert` and `--cert-key`; the CLI enforces this—mirror the pattern if new coupled options are added.
- Debug mode raises log verbosity globally and for `forevd` namespaced loggers; keep debug branches lightweight to avoid leaking secrets or large configs.
