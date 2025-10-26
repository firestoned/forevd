# forevd

`forevd` is a forward and reverse proxy sidecar that centralizes authentication (mTLS, OIDC) and optional authorization so application services can stay auth-agnostic.

## Table of contents
1. [Firestone Ecosystem](#firestone-ecosystem)
1. [Intro](#intro)
1. [Requirements](#requirements)
1. [Quick Start](#quick-start)
1. [Running `forevd`](#running-forevd)
1. [Config Files](#config-files)
    1. [Locations Config](#locations-config)
    1. [OIDC Config](#oidc-config)
    1. [LDAP Config](#ldap-config)
1. [Mutual TLS](#mutual-tls)
1. [Authorization](#authorization)
1. [Logging & Debugging](#logging--debugging)
1. [Project Structure](#project-structure)
1. [Contributing & Testing](#contributing--testing)
1. [License](#license)

## Firestone Ecosystem

Forevd shares a codebase lineage with sibling projects maintained under the Firestone umbrella:

- [`firestone`](https://github.com/firestoned/firestone) is the spec generator that turns JSON Schema resources into OpenAPI/AsyncAPI documents and templated CLIs.
- [`firestone-lib`](https://github.com/firestoned/firestone-lib) provides the Click parameter types, schema loaders, and logging helpers that both Firestone and Forevd build on.

## Intro

`forevd` runs Apache HTTPD on your behalf, renders the necessary config from structured input, and launches it in the foreground. You supply backends, authentication knobs, and authorization rules via CLI flags or YAML files; `forevd` turns that into a working proxy that injects the right headers for downstream apps.

## Requirements

- Python **3.9 – <4.0** (as declared in `pyproject.toml`)
- [Poetry](https://python-poetry.org/) for dependency management
- Apache HTTP Server **2.4+** available in `$PATH` or provided via `--cmd`
- (Optional) Docker image of httpd if you prefer containerized execution
- FastAPI/uvicorn only power the sample echo app used for smoke tests
- nginx support is planned but not yet implemented

## Quick Start

1. Install dependencies: `poetry install`
2. Export any secrets used by templated configs (for example `export LDAP_BINDID_PASSWORD=secret` and `export OIDC_CLIENT_SECRET=secret`)
3. Launch the sample backend so you can see proxied requests: `poetry run uvicorn forevd.app:APP --host 0.0.0.0 --port 8081`
4. In another shell, run `forevd` against the bundled configs:

   ```bash
   poetry run forevd \
     --debug \
     --locations @etc/locations.yaml \
     --ldap @etc/ldap.yaml \
     --oidc @etc/oidc.yaml \
     --ssl @etc/ssl.yaml \
     --var-dir "$(mktemp -d)"
   ```

   Replace the templated values and TLS material with your environment-specific data before pushing to production.

5. Hit the proxy (default `127.0.0.1:8080`) and inspect headers echoed by the FastAPI app to confirm OIDC/mTLS state.

## Running `forevd`

CLI arguments provided directly (for example `--backend` and `--location`) act as global defaults. Any structured payload supplied to `--locations`, `--ldap`, `--oidc`, or `--ssl` overrides those defaults for the targeted sections. Use `@file.yaml` to point an option at the configs in `etc/` or your own managed files—`forevd` relies on `firestone_lib.cli` helpers to load JSON or YAML transparently.

## Config Files

The example files in `etc/` cover common scenarios. They rely on Jinja2 templating so you can inject secrets or host-specific values through environment variables at runtime.

### Locations Config

This config controls how each endpoint behaves—backends, authentication, authorization, and HTTP method restrictions. `_nomalize_locations` in `forevd/__main__.py` keeps the data structure consistent before it reaches the Apache template.

| Key | Required | Notes |
| --- | --- | --- |
| `path` | Yes | Literal location or regex when combined with `match` |
| `match` | No | Use `"Match"` to drive `<LocationMatch>` blocks |
| `backend` | No | Falls back to `--backend` when omitted |
| `authc` | No | Dict of authn controls (`mtls`, `oidc`) |
| `authz` | No | Dict of authz controls (LDAP, users, `allow_all`, `join_type`) |
| `http_methods` | No | List of verbs to protect with `<Limit>` |
| `set_access_token` | No | Defaults to `true`; controls `Authorization` header injection |
| `include` | No | Free-form Apache snippet inserted inside the `<Location>` block |

Remember to explicitly disable global auth when a route should opt out:

```yaml
- path: /api
  authc:
    oidc: false
```

#### Example

```yaml
- path: /
  backend: "http://host.docker.internal:8081/"
  authz:
    join_type: "any"
    ldap:
      url: "ldaps://127.0.0.1/DC=foo,DC=example,DC=com"
      bind-dn: "foo"
      bind-pw: "{{ LDAP_BINDID_PASSWORD }}"
      groups:
        - "CN=foobar,OU=groups,DC=example,DC=com"
    users:
      - erick.bourgeois
```

- Top-level list items define individual endpoints.
- `join_type` tells Apache whether any or all authz checks must pass.
- Environment variables in `{{ ... }}` are resolved at render time.

### OIDC Config

Provide client metadata and behavior overrides for `mod_auth_openidc`. Required keys include `ClientId` and `ClientSecret`; optional fields such as `Scope` or `RemoteUserClaim` influence header injection.

```yaml
ProviderMetadataUrl: "https://{{ OIDC_PROVIDER_NAME }}.us.auth0.com/.well-known/openid-configuration"
RedirectURI: "https://example.org:8080/secure/redirect_uri"
ClientId: "{{ OIDC_CLIENT_ID }}"
ClientSecret: "{{ OIDC_CLIENT_SECRET }}"
Scope: '"openid profile"'
PKCEMethod: S256
RemoteUserClaim: nickname
```

Set the following environment variables (or adjust the file) before running:

- `OIDC_PROVIDER_NAME`
- `OIDC_CLIENT_ID`
- `OIDC_CLIENT_SECRET`

### LDAP Config

Configure global LDAP caching and connection details consumed by `mod_ldap`. The loader strips the leading `LDAP` prefix automatically.

```yaml
SharedCacheSize: 500000
CacheEntries: 1024
CacheTTL: 600
OpCacheEntries: 1024
OpCacheTTL: 600
```

### SSL Config

`etc/ssl.yaml` demonstrates how to fine-tune TLS without embedding long directives inside the `locations` file. Pass it with `--ssl @etc/ssl.yaml` to override the default Apache cipher settings.

## Mutual TLS

Mutual TLS requires a certificate/key pair and (optionally) a CA bundle. The CLI enforces that `--cert` and `--cert-key` are provided together. You can supply additional SSL settings via `--ssl` as shown below:

```bash
poetry run forevd \
  --listen 0.0.0.0:8443 \
  --backend http://localhost:8081 \
  --location / \
  --mtls require \
  --cert /path/to/server.crt \
  --cert-key /path/to/server.key \
  --ca-cert /path/to/ca.pem \
  --ssl @etc/ssl.yaml \
  --server-name example.com
```

Inside the generated Apache config, mTLS surfaces headers like `X-Remote-User` and `X-SSL-certificate` that your upstream service can consume.

## Authorization

Authorization rules combine LDAP group membership, explicit user allow-lists, and an `allow_all` escape hatch for trusted endpoints. Use `join_type` to control how the checks interact:

```yaml
authz:
  join_type: "all"        # require both LDAP and static user match
  ldap:
    url: "ldaps://ldap.example.com/DC=example,DC=com"
    bind-dn: "cn=ldap,dc=example,dc=com"
    bind-pw: "{{ LDAP_BINDID_PASSWORD }}"
    groups:
      - "CN=proxy-users,OU=groups,DC=example,DC=com"
  users:
    - alice
    - bob
```

- `allow_all: true` lets any authenticated user through.
- Omit the `authz` block entirely for public endpoints (still subject to whatever authn you configured).
- Keep the structure aligned with the Apache template in `forevd/apache/httpd.conf` when adding new attributes.

## Logging & Debugging

- `--debug` raises the root logger and `forevd` namespace to `DEBUG`, and enables verbose tracing for OIDC when configured.
- Logging defaults originate from `forevd/resources/logging/cli.conf`; extend it there rather than creating ad hoc handlers.
- Apache access/error logs point to stdout/stderr by default (`--access-log`, `--err-log` override these).
- Inspect the generated config under `--var-dir` if Apache fails to start; `forevd` will log the path before exec.

## Project Structure

- `forevd/__main__.py` – CLI entry point, option validation, location normalization, backend dispatch.
- `forevd/apache/` – Jinja2 template and backend launcher that writes `httpd.conf` and `execve`s `httpd`.
- `forevd/app.py` – Minimal FastAPI app that echoes request headers for smoke testing.
- `etc/` – Sample configs demonstrating multi-location setups, LDAP/SSL/OIDC tuning.
- `forevd/resources/logging/` – Logging configuration consumed during CLI initialization.

## Contributing & Testing

- Format and lint with the configured toolchain (`black`, `pylint`, `pycodestyle`) as needed.
- Run unit tests via `poetry run pytest`; add coverage when modifying behavior or templates.
- Keep `pyproject.toml` and `poetry.lock` in sync if you change dependencies.
- Align coding style with `.github/instructions/` (Python and YAML guidelines).

## License

`forevd` is released under the terms of the [LICENSE](LICENSE) file in this repository.
