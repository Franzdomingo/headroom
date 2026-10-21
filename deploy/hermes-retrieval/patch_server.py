"""Allow token-authenticated remote CCR clients without relaxing other routes."""

import sys
from pathlib import Path


def patch(source: str) -> str:
    anchor = "    def _is_host_of_loopback_published_container(request: Request) -> bool:\n"
    helper = '''    def _require_ccr_client(request: Request) -> None:
        """Allow local callers or remote callers verified by the token gate."""
        if _authenticated_at_gate(request):
            return
        token = os.environ.get("HEADROOM_RETRIEVE_TOKEN")
        provided = read_proxy_token(request.headers)
        if token and provided and hmac.compare_digest(
            token.encode("utf-8"), provided.encode("utf-8", "replace")
        ):
            return
        _require_loopback(request)

'''
    assert source.count(anchor) == 1
    source = source.replace(anchor, helper + anchor)
    for route in (
        '"/v1/retrieve",',
        '"/v1/retrieve/stats",',
        '"/v1/retrieve/{hash_key}",',
        '"/v1/retrieve/tool_call",',
    ):
        start = source.index(route)
        end = source.index("\n    async def", start)
        block = source[start:end]
        assert block.count("Depends(_require_loopback)") == 1, route
        source = source[:start] + block.replace(
            "Depends(_require_loopback)", "Depends(_require_ccr_client)"
        ) + source[end:]
    return source


if __name__ == "__main__":
    path = Path(sys.argv[1])
    path.write_text(patch(path.read_text()))
