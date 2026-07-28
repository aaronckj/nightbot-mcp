import asyncio
import io
import json
import urllib.parse

import nightbot_mcp.client as client_mod
from nightbot_mcp.client import Nightbot
from nightbot_mcp.server import build_app

EXPECTED = {
    "channel_info", "join_channel", "part_channel",
    "list_commands", "add_command", "update_command", "delete_command",
    "list_timers", "add_timer", "toggle_timer", "delete_timer",
    "list_regulars", "add_regular", "remove_regular",
    "get_spam_filter", "update_spam_filter", "add_banned_phrases",
    "send_chat_message", "health_check",
}


class FakeOpener:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, req, timeout=15):
        body = req.data.decode() if req.data else None
        self.calls.append((req.get_method(), req.full_url, body))
        payload = self.responses.get(req.full_url.split("/1")[-1], {})

        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return Resp(json.dumps(payload).encode())


def make_app(responses):
    opener = FakeOpener(responses)
    client_mod._nb = Nightbot(token="tok", opener=opener)
    return build_app(), opener


def teardown_function():
    client_mod._nb = None


def call_tool(app, name, args=None):
    res = asyncio.run(app.call_tool(name, args or {}))
    if isinstance(res, tuple):
        blocks, structured = res
        if isinstance(structured, dict) and set(structured) == {"result"}:
            return structured["result"]
        if structured is not None:
            return structured
    else:
        blocks = res
    parsed = [json.loads(b.text) for b in blocks]
    return parsed[0] if len(parsed) == 1 else parsed


def test_all_tools_registered():
    app, _ = make_app({})
    tools = asyncio.run(app.list_tools())
    assert {t.name for t in tools} == EXPECTED


def test_list_commands_shapes():
    app, _ = make_app(
        {"/commands": {"commands": [
            {"_id": "x1", "name": "!rules", "message": "Be kind", "userLevel": "everyone",
             "coolDown": 30, "count": 7}
        ]}}
    )
    out = call_tool(app, "list_commands")
    assert out[0]["name"] == "!rules"
    assert out[0]["id"] == "x1"


def test_add_command_posts_form():
    app, opener = make_app({"/commands": {"command": {"_id": "new1"}}})
    out = call_tool(app, "add_command", {"name": "!discord", "message": "soon"})
    assert out["created"] == "new1"
    method, url, body = opener.calls[-1]
    assert method == "POST"
    parsed = urllib.parse.parse_qs(body)
    assert parsed["name"] == ["!discord"]


def test_dry_run_no_call():
    app, opener = make_app({})
    out = call_tool(app, "add_command", {"name": "!x", "message": "y", "dry_run": True})
    assert out["preview"] is True
    assert opener.calls == []


def test_add_banned_phrases_merges():
    app, opener = make_app(
        {"/spam_protection/blacklist": {"blacklist": "spamword\nscamsite"}}
    )
    out = call_tool(app, "add_banned_phrases", {"phrases": ["acme", "scamsite"]})
    assert out["added"] == ["acme"]
    assert out["total"] == 3
    method, url, body = opener.calls[-1]
    assert method == "PUT"
    parsed = urllib.parse.parse_qs(body)
    assert parsed["blacklist"] == ["spamword\nscamsite\nacme"]


def test_spam_filter_validation():
    app, _ = make_app({})
    out = call_tool(app, "get_spam_filter", {"filter_name": "bogus"})
    assert "error" in out
