"""Verify one real CCR retrieval from Hermes without showing secrets or prompts."""

import subprocess

seed = '''
from headroom.cache.compression_store import get_compression_store
print(get_compression_store().store(
    "Headroom Hermes retrieval connectivity check", "connectivity check",
    original_tokens=8, compressed_tokens=2, tool_name="hermes-connectivity-check",
))
'''
key = subprocess.check_output([
    "docker", "compose", "exec", "-T", "headroom-proxy", "python", "-c", seed
], text=True).strip()
script = '''
import sys, httpx
from dotenv import dotenv_values
token = dotenv_values("/opt/data/.env")["HEADROOM_RETRIEVE_TOKEN"]
base = "http://host.docker.internal:8787"
headers = {"Authorization": "Bearer " + token}
with httpx.Client(timeout=20) as client:
    path = base + "/v1/retrieve/stats"
    assert client.get(path).status_code in (401, 404)
    assert client.get(path, headers={"Authorization": "Bearer incorrect"}).status_code in (401, 404)
    before = client.get(path, headers=headers)
    before.raise_for_status()
    n = before.json()["store"]["total_retrievals"]
    result = client.post(base + "/v1/retrieve", json={"hash": sys.argv[1]}, headers=headers)
    result.raise_for_status()
    assert result.json()["original_content"] == "Headroom Hermes retrieval connectivity check"
    after = client.get(path, headers=headers)
    after.raise_for_status()
    assert after.json()["store"]["total_retrievals"] == n + 1
    assert client.get(base + "/debug/memory", headers=headers).status_code == 404
    health = client.get(base + "/health").json()
    assert health["ready"] and not health["checks"]["memory"]["enabled"]
print("PASS: Hermes-to-Headroom retrieval; counter +1; missing/wrong tokens blocked; memory off; proxy healthy.")
'''
subprocess.run([
    "docker", "exec", "4983540ee4b9", "python", "-c", script, key
], check=True)
