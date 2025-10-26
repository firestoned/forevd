---
applyTo: '**/*.yaml'
---

# YAML Configuration Guidelines

These rules cover runtime configs under `etc/` and any future YAML surfaced through CLI options (e.g., `--locations`, `--oidc`, `--ldap`, `--ssl`). They mirror how the Apache template consumes data today while layering in broadly accepted YAML practices.

## File Format & Style
- Indent with two spaces; avoid tabs and keep sequence items (`-`) aligned with their parent key.
- Use lowercase booleans (`true`/`false`) and `null` where needed; prefer bare numbers over quoted strings unless leading zeros matter.
- Quote strings only when required (embedded colon, leading `@`, templated values); default to double quotes for consistency with `etc/` samples.
- Preserve key order that reflects execution flow (e.g., `path`, `backend`, then `authc`/`authz` blocks) so diffs stay readable.

## Structure & Typing
- Model locations as lists of maps (`- path: ...`) to match `_nomalize_locations`; avoid mixing scalars and mappings at the same level.
- Keep nested dictionaries compact but readable—break complex structures across lines with sensible indentation.
- When adding new keys consumed by `forevd`, update both `_nomalize_locations` and the Apache Jinja template so generated configs remain synchronized.

## Jinja Templating & Secrets
- Use `{{ ENV_VAR }}` placeholders for secrets or host-specific values; do not commit literal credentials.
- For optional fields, prefer empty strings or omit the key entirely so downstream code can fall back to defaults.
- Document expected environment variables in adjacent comments when they are not self-explanatory.

## Validation & Tooling
- Sanity-check changes with `poetry run python -c "import yaml, sys; yaml.safe_load(sys.stdin)" < file.yaml` or an equivalent safe loader before shipping.
- Keep configs deterministic—do not rely on anchors/aliases unless both the CLI parser and template logic explicitly support them.
- When introducing schema changes, supplement with README notes or inline comments so operators understand the new knobs.

## Security & Robustness
- Treat every YAML file as potentially user-supplied input: guard against unsafe constructs (no `!!python/object` or custom tags).
- Ensure TLS-related paths and credential references align with CLI validation (`--cert`/`--cert-key` must be provided together).
- Preserve logging and header-injection settings that downstream services rely on; call out in commit messages when behavior changes.
