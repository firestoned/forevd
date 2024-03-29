# Table of contents
1. [Intro](#intro)
1. [Dependencies](#dependencies)
1. [Running `forevd`](#running-forevd)
1. [Config Files](#config-files)
    1. [OIDC Config](#oidc-config)
    1. [LDAP](#ldap-config)
1. [Mutual TLS](#mutual-tls)
1. [Authorization](#authorization)

# Intro

`forevd` is a forward and reverse proxy that helps deliver authentication and, optionally,
authorization as a sidecar.

This project was created to help eliminate any need to add authentication into your application
code.

# Dependencies

At the moment, `forevd`, runs using Apache, so you will need to have httpd or docker image of it
available at runtime.

- Apache
- nginx (TBD)

# Running `forevd`

The following proivides some details on how to run `forevd`. The way the options work is that
anything provided immediately on the CLI, are "global" defaults; if you then provide config
(optionally files), via the `--locations`, `--ldap` or `--oidc` options, then those will override
the CLI options, of, e.g. `--backend` and `--location`.

# Config Files

You can optionally provide config files for more complicated setups; this section provides soem
examples, which can be found in the `etc` directory.

The config files use Jinja2 templating via environment variables, so, instead of putting values in
directly, you can use the form `{{ ENV_VAR_NAME }}` to have the environment varibale injected at
runtime.

The following command line options support files: `--locations`, `--ldap` or `--oidc`, via the `@`
symbol, similar to `curl`'s command line option `--data`, for example, `--oidc @etc/oidc.yaml`

## Locations Config

This config allows you to provide much more control over each "location" or "endpoint" to your
reverse proxy. For example, using different backends for different URLs or adding authorization. The
format of the file is a dictionary of locations, or endpoints, and their correspondign data.

### Keys

There are 5 key config options for each location:

1. `path`: the path, location or endpoint of what to protect or unprotect
1. `match`: whether the path value is a regex or *match*
1. `authc`: this is the authentication (aka `authc`) key, representing what authc to enable; this is
   dictionary with keys being either `mtls` or `oidc`.
1. `authz`: this is the authorization (aka `authz`) key, representing what authz to enable; this is
   dictionary with keys, see below example and details at the [Authorization](#authorization)
    section.

Note: remember that global authentication options `--oidc` and `mtls`, so if you want to set OIDC
across all endpoints, except, say, `/api`, you would need to disable it explicitly with:

```yaml
- path: /api
  authc:
    oidc: false
```

### Example

The following adds LDAP group **and** static user authorization to `/`

```yaml
- path: /
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

Let's break this down a bit:

- the high level keys are endpoints
- the next level is authorization config
- the `join_type` key word tells `forevd` how to "combine" or join the two different authorizations,
  values are:
  - `any`: if any of the authorization types match, allow connection through
  - `all`: all of the authorization types **must** match to allow connection through

## OIDC Config

This is useful for adding any other global OIDC config; there are required fields for the auth to
work, e.g. `ClientID` and `ClientSecret`.

### Example

```yaml
ProviderMetadataUrl: "https://{{ OIDC_PROVIDER_NAME }}.us.auth0.com/.well-known/openid-configuration"
RedirectURI: "https://erick-pro.jeb.ca:8080/secure/redirect_uri"
ClientId: "{{ OIDC_CLIENT_ID }}"
ClientSecret: "{{ OIDC_CLIENT_SECRET }}"
Scope: '"openid profile"'
PKCEMethod: S256
RemoteUserClaim: nickname
```

## LDAP Config

This is used for global LDAP config, e.g. setting cache information for `mod_ldap`. Note: The `LDAP`
prefix is stripped, as it's redundant and it's added as part of the config generation.

### Example

```yaml
SharedCacheSize: 500000
CacheEntries: 1024
CacheTTL: 600
OpCacheEntries: 1024
OpCacheTTL: 600
```

# Mutual TLS

The following command provides termination of mTLS on `/` and passes connections to a backend at
`http://0.0.0.0:8080`

```
forevd --debug --listen 0.0.0.0:8080 \
    --ca-cert $PWD/../certs/ca/ca-cert.pem
    --cert $PWD/../certs/server.crt
    --cert-key $PWD/../certs/server.key
    --backend http://localhost:8081
    --location /
    --mtls require
    --server-name example.com
    --var-dir /var/tmp/apache
```

# Authorization

To add authorization, it's recommended you use a config file for the `--locations` command line.

There is currently support for LDAP group lookups, static user names, or allow all valid users. Here
are the keys supported:

1. `allow_all`: this key let's `forevd` know to allow all valid users through
1. `join_type`: this is the "join" type between all authorizations setup
  - `any`: if any of the authorization types match, allow connection through
  - `all`: all of the authorization types **must** match to allow connection through
1. `ldap`: this is the LDAP configuration for group lookups, keys are:
   - `url`: LDAP URL, e.g. `ldaps://127.0.0.1/DC=foo,DC=example,DC=com`
   - `bind-dn`: the DN for bind operation
   - `bind-pw`: the password for bind operation
   - `groups`: a list of groups DNs
1. `users`: a list of user names to verify against

See [Locations Example](#example) for more detail.
