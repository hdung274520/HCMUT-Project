import os

os.environ["ALLOWED_ORIGINS"] = "https://hdung274520.github.io"  # must be set before importing server

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import server

client = TestClient(server.app)  # no `with`: skips the startup model loading


def test_origin_ok():
    assert server.origin_ok("https://hdung274520.github.io")
    assert not server.origin_ok("http://evil.com")
    assert not server.origin_ok(None)


def test_ws_rejects_unknown_origin():
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws", headers={"origin": "http://evil.com"}):
            pass


def test_config_cors_only_for_pages():
    ok = client.get("/api/config", headers={"origin": "https://hdung274520.github.io"})
    bad = client.get("/api/config", headers={"origin": "http://evil.com"})
    assert ok.headers.get("access-control-allow-origin") == "https://hdung274520.github.io"
    assert "access-control-allow-origin" not in bad.headers
