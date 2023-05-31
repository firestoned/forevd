# Table of contents
1. [Intro](#intro)
2. [Dependencies](#deps)
3. [Running `forevd`](#running)
    1. [Config Files](#config)
    2. [Mutual TLS](#mtls)

# <a name="intro" />Intro

`forevd` is a forward and reverse proxy that helps deliver authentication and, optionally,
authorization as a sidecar.

This project was created to help eliminate any need to add authentication into your application
code.

# <a name="deps" />Dependencies

At the moment, `forevd`, runs using Apache, so you will need to have httpd or docker image of it
available at runtime.

- Apache
- nginx (TBD)

# <a name="running" />Running `forevd`

The following proivides some details on how to run `forevd`. The way the options work are that
anything provided immediately on the CLI, are "global" defaults; if you then provide config
(optionally files), via the `--locations`, `--ldap` or `--oidc` options, then those will override
the CLI options, of, e.g. `--backend` and `--location`

## <a name="config" />Config Files

You can optionally provide config files for more complicated setups; this section provides soem
examples, which can be found in the `etc` directory.

The config files use Jinja2 templating via environment variables, so, instead of putting values in
directly, you can use the form `{{ ENV_VAR_NAME }}` to have the environment varibale injected at
runtime.

The following command line options support files: `--locations`, `--ldap` or `--oidc`, via the `@`
symbol, similar to `curl`'s command line option `--data`, for example, `--oidc @etc/oidc.yaml`

### Locations Config

This config allows you to provide much more control over each "location" or "endpoint" to your
reverse proxy. For example, using different backends for different URLs or adding authorization. The
format of the file is a dictionary of locations, or endpoints, and their correspondign data.

#### Example

The following adds LDAP group **and** static user authorization to `/`

```yaml
/:
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

### OIDC Config

This is useful for adding any other global OIDC config; there are required fields for the auth to
work, e.g. `ClientID` and `ClientSecret`.

#### Example

```yaml
ProviderMetadataUrl: "https://{{ OIDC_PROVIDER_NAME }}.us.auth0.com/.well-known/openid-configuration"
RedirectURI: "https://erick-pro.jeb.ca:8080/secure/redirect_uri"
ClientId: "{{ OIDC_CLIENT_ID }}"
ClientSecret: "{{ OIDC_CLIENT_SECRET }}"
Scope: '"openid profile"'
PKCEMethod: S256
RemoteUserClaim: nickname
```

### LDAP Config

This is used for global LDAP config, e.g. setting cache information for `mod_ldap`. Note: The `LDAP`
prefix is stripped, as it's redundant and it's added as part of the config generation.

#### Example

```yaml
SharedCacheSize: 500000
CacheEntries: 1024
CacheTTL: 600
OpCacheEntries: 1024
OpCacheTTL: 600
```

## <a name="mtls" />Mutual TLS

The following command provides termination of mTLS on `/` and redirects connections to a backend at
`http://localhost:8081`

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

## <a name="mtls" />Authorization

To add authorization, it's recommended you use a config file for the `--locations` command line.
