# Hermes CCR retrieval deployment

This local v0.41.0 patch permits remote callers on the four `/v1/retrieve`
routes when they present `HEADROOM_RETRIEVE_TOKEN` as a bearer credential.
The existing authenticated proxy-token path also works. Without either
credential, the original loopback guard applies. Other local-only routes
and the existing POST origin checks retain their guards. Persistent memory
is independent and remains disabled.

`docker-compose.override.yml` selects the local patched image and passes the
retrieval-only token from the host `.env`. The same token is in the Hermes
container's `/opt/data/.env`. Credentials are not committed to this directory.
This is a local patch, not an upstream Headroom release.

Build using the saved exact original image:

```sh
docker build --build-arg BASE_IMAGE=headroom-local:0.41.0-base \
  -t headroom-local:0.41.0-hermes-retrieval deploy/hermes-retrieval
docker compose up -d --no-deps --no-build --wait headroom-proxy
```

`check_access.py` exercises the real ASGI authentication and route guards
against the installed dependencies. `verify_live.py` verifies one synthetic
retrieval from the Hermes container and checks the counter increases by one.
The latter assumes the current Hermes container ID; adjust it on replacement.

Hermes activation remains a separate step: enable the plugin and platform
toolset, ensure `.env` is loaded, then restart Hermes and test the actual tool.

To roll back the proxy while preserving its volume, explicitly select only
the original Compose file (skipping the override):

```sh
docker compose -f docker-compose.yml up -d --no-deps --no-build --wait headroom-proxy
```

Disable or rename the override before subsequent normal Compose operations
if retaining the rollback. Do not reapply this version-specific patch to a
new upstream image without reviewing and repeating the access tests.
