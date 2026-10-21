"""Exercise the real ASGI token gate and CCR route dependencies."""

import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import headroom.proxy.server as server
from headroom.cache.backends import InMemoryBackend
from headroom.cache.compression_store import get_compression_store, reset_compression_store

if len(sys.argv) > 1:
    exec(compile(Path(sys.argv[1]).read_text(), server.__file__, "exec"), server.__dict__)

os.environ.pop("HEADROOM_PROXY_TOKEN", None)
os.environ.pop("HEADROOM_RETRIEVE_TOKEN", None)
os.environ["HEADROOM_ALLOW_UNAUTHENTICATED_BIND"] = "1"


def app(token):
    return server.create_app(server.ProxyConfig(
        optimize=False, image_optimize=False, cache_enabled=False,
        rate_limit_enabled=False, cost_tracking_enabled=False, log_requests=False,
        ccr_inject_tool=False, ccr_handle_responses=False, ccr_context_tracking=False,
        proxy_token=token,
    ))


reset_compression_store()
store = get_compression_store(backend=InMemoryBackend())
key = store.store("retrieval-access-check", "compressed", original_tokens=5,
                  compressed_tokens=1, tool_name="access-check")
remote = TestClient(app("test-only-token"), base_url="http://headroom:8787",
                    client=("172.20.0.5", 12345))
headers = {"Authorization": "Bearer test-only-token"}
for method, path, body, expected in (
    ("GET", "/v1/retrieve/stats", None, 200),
    ("GET", f"/v1/retrieve/{key}", None, 200),
    ("POST", "/v1/retrieve", {"hash": key}, 200),
    ("POST", "/v1/retrieve/tool_call", {}, 400),
):
    for auth in ({}, {"Authorization": "Bearer wrong"}):
        response = remote.request(method, path, json=body, headers=auth)
        assert response.status_code == 401, (path, response.status_code)
    response = remote.request(method, path, json=body, headers=headers)
    assert response.status_code == expected, (path, response.status_code, response.text)

for path in ("/debug/memory", "/v1/telemetry"):
    assert remote.get(path, headers=headers).status_code == 404, path
assert remote.post("/v1/retrieve", json={"hash": key}, headers={
    **headers, "Origin": "http://untrusted.example"
}).status_code == 403
no_token = TestClient(app(None), client=("172.20.0.5", 12345))
assert no_token.get("/v1/retrieve/stats").status_code == 404
os.environ["HEADROOM_RETRIEVE_TOKEN"] = "retrieval-only-test-token"
assert no_token.get("/v1/retrieve/stats", headers={
    "Authorization": "Bearer retrieval-only-test-token"
}).status_code == 200
assert no_token.get("/v1/retrieve/stats", headers={
    "Authorization": "Bearer wrong"
}).status_code == 404
assert no_token.get("/debug/memory", headers={
    "Authorization": "Bearer retrieval-only-test-token"
}).status_code == 404
local = TestClient(app("test-only-token"), base_url="http://127.0.0.1",
                   client=("127.0.0.1", 12345))
assert local.get("/v1/retrieve/stats").status_code == 200
print("PASS: CCR token access, rejection cases, local access, origin checks, and unrelated guards")
