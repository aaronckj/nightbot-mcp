"""Nightbot API client (https://api-docs.nightbot.tv), stdlib HTTP only."""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger("nightbot_mcp")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

API = "https://api.nightbot.tv/1"


class NightbotError(RuntimeError):
    pass


def _get_token() -> str:
    token = os.environ.get("NIGHTBOT_ACCESS_TOKEN")
    if token:
        return token
    backend = os.environ.get("NIGHTBOT_MCP_SECRETS")
    if backend == "vaultproxy":
        base = os.environ.get("VAULTPROXY_URL", "http://127.0.0.1:8199").rstrip("/")
        req = Request(f"{base}/items/nightbot-mcp%2Faccess_token")
        try:
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read()).get("value", "")
        except URLError as exc:
            raise NightbotError(f"vaultproxy unreachable: {exc.reason}") from exc
    raise NightbotError(
        "no Nightbot token: set NIGHTBOT_ACCESS_TOKEN or NIGHTBOT_MCP_SECRETS=vaultproxy"
    )


class Nightbot:
    def __init__(self, token: str | None = None, opener: Any = None):
        self._token = token
        self._opener = opener or urlopen

    @property
    def token(self) -> str:
        if self._token is None:
            self._token = _get_token()
        return self._token

    def request(
        self, method: str, path: str, body: dict | None = None, form: bool = True
    ) -> dict:
        data = None
        headers = {"authorization": f"Bearer {self.token}"}
        if body is not None:
            if form:
                data = urllib.parse.urlencode(body).encode()
                headers["content-type"] = "application/x-www-form-urlencoded"
            else:
                data = json.dumps(body).encode()
                headers["content-type"] = "application/json"
        req = Request(f"{API}{path}", method=method, data=data, headers=headers)
        try:
            with self._opener(req, timeout=15) as resp:
                raw = resp.read()
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            logger.error("nightbot %s %s -> %s %s", method, path, exc.code, detail)
            if exc.code == 401:
                raise NightbotError(
                    "Nightbot token invalid/expired (401); mint a new access token"
                ) from exc
            raise NightbotError(f"{method} {path} failed ({exc.code}): {detail}") from exc
        except URLError as exc:
            raise NightbotError(f"Nightbot API unreachable: {exc.reason}") from exc
        logger.info("nightbot %s %s ok", method, path)
        return json.loads(raw) if raw else {}


def preview(action: str, would: dict) -> dict:
    return {"preview": True, "action": action, "would": would}


_nb: Nightbot | None = None


def get_nb() -> Nightbot:
    global _nb
    if _nb is None:
        _nb = Nightbot()
    return _nb
