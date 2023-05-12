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

The following command provides termination of mTLS on `/` and redirects connections to a backend at
`http://localhost:8081`

```
forevd --debug --listen 0.0.0.0:8080 \
    --ca-cert $PWD/../certs/ca/ca-cert.pem
    --cert $PWD/../certs/server.crt
    --cert-key $PWD/../certs/server.key
    --backend http://localhost:8081
    --location /
    --server-name example.com
    --var-dir /var/tmp/apache
```
