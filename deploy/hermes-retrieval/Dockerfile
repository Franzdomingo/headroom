ARG BASE_IMAGE=ghcr.io/headroomlabs-ai/headroom:v0.41.0
FROM ${BASE_IMAGE}
COPY patch_server.py /tmp/patch_ccr_server.py
RUN ["/usr/local/bin/python", "/tmp/patch_ccr_server.py", "/usr/local/lib/python3.13/site-packages/headroom/proxy/server.py"]
