# forevd

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

## Mutual TLS

The following command provides termination of mTLS on `/`
