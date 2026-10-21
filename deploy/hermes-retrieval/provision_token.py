"""Copy the existing proxy credential to Hermes without printing it."""

import json
import subprocess
import secrets
from pathlib import Path

info = json.loads(subprocess.check_output(
    ["docker", "inspect", "headroom-headroom-proxy-1"], text=True
))[0]
env = dict(item.split("=", 1) for item in info["Config"]["Env"] if "=" in item)
token = env.get("HEADROOM_RETRIEVE_TOKEN") or secrets.token_hex(32)
p = Path(".env")
lines = p.read_text().splitlines()
lines = [line for line in lines if not line.startswith("HEADROOM_RETRIEVE_TOKEN=")]
lines.append("HEADROOM_RETRIEVE_TOKEN=" + token)
p.write_text("\n".join(lines) + "\n")
p.chmod(0o600)
script = '''
import os, sys
from pathlib import Path
p = Path("/opt/data/.env")
token = sys.stdin.read()
lines = p.read_text().splitlines() if p.exists() else []
lines = [line for line in lines if not line.strip().startswith((
    "HEADROOM_RETRIEVE_TOKEN=", "export HEADROOM_RETRIEVE_TOKEN="
))]
lines.append("HEADROOM_RETRIEVE_TOKEN=" + repr(token))
p.write_text("\\n".join(lines) + "\\n")
os.chmod(p, 0o600)
print("Hermes retrieval token configured; value withheld.")
'''
subprocess.run(
    ["docker", "exec", "-i", "4983540ee4b9", "python", "-c", script],
    input=token, text=True, check=True,
)
