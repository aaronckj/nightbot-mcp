"""FastMCP app: Nightbot commands, timers, regulars, spam protection."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .client import get_nb, preview

SPAM_FILTERS = ("blacklist", "links", "caps", "symbols", "repetitions", "emotes")


def build_app() -> FastMCP:
    mcp = FastMCP(
        "nightbot",
        instructions=(
            "Manage Nightbot for the connected channel: custom chat commands, "
            "timers, regulars, and spam-protection filters. The blacklist filter "
            "is the banned-words/phrases list for live chat. Every mutating tool "
            "accepts dry_run=True."
        ),
    )

    @mcp.tool()
    def channel_info() -> dict:
        """The Nightbot channel this token controls, and whether the bot has joined."""
        nb = get_nb()
        ch = nb.request("GET", "/channel").get("channel", {})
        return {
            "name": ch.get("name"),
            "display_name": ch.get("displayName"),
            "joined": ch.get("joined"),
            "platform": ch.get("provider"),
        }

    @mcp.tool()
    def join_channel(dry_run: bool = False) -> dict:
        """Make Nightbot join the channel's chat."""
        if dry_run:
            return preview("join_channel", {})
        get_nb().request("POST", "/channel/join")
        return {"joined": True}

    @mcp.tool()
    def part_channel(dry_run: bool = False) -> dict:
        """Make Nightbot leave the channel's chat."""
        if dry_run:
            return preview("part_channel", {})
        get_nb().request("POST", "/channel/part")
        return {"joined": False}

    @mcp.tool()
    def list_commands() -> list[dict]:
        """List custom chat commands."""
        nb = get_nb()
        res = nb.request("GET", "/commands")
        return [
            {
                "id": c["_id"],
                "name": c["name"],
                "message": c["message"],
                "user_level": c.get("userLevel"),
                "cooldown": c.get("coolDown"),
                "count": c.get("count"),
            }
            for c in res.get("commands", [])
        ]

    @mcp.tool()
    def add_command(
        name: str,
        message: str,
        user_level: str = "everyone",
        cooldown: int = 30,
        dry_run: bool = False,
    ) -> dict:
        """Add a custom command (name like !rules). user_level:
        everyone|subscriber|regular|moderator|owner. cooldown in seconds (5-300)."""
        if dry_run:
            return preview(
                "add_command",
                {"name": name, "message": message, "user_level": user_level},
            )
        nb = get_nb()
        res = nb.request(
            "POST",
            "/commands",
            {"name": name, "message": message, "userLevel": user_level, "coolDown": cooldown},
        )
        return {"created": res.get("command", {}).get("_id"), "name": name}

    @mcp.tool()
    def update_command(
        command_id: str,
        message: str | None = None,
        user_level: str | None = None,
        cooldown: int | None = None,
        dry_run: bool = False,
    ) -> dict:
        """Update a custom command's message, user level, or cooldown."""
        body = {}
        if message is not None:
            body["message"] = message
        if user_level is not None:
            body["userLevel"] = user_level
        if cooldown is not None:
            body["coolDown"] = cooldown
        if dry_run:
            return preview("update_command", {"command_id": command_id, **body})
        get_nb().request("PUT", f"/commands/{command_id}", body)
        return {"updated": command_id, "changes": body}

    @mcp.tool()
    def delete_command(command_id: str, dry_run: bool = False) -> dict:
        """Delete a custom command."""
        if dry_run:
            return preview("delete_command", {"command_id": command_id})
        get_nb().request("DELETE", f"/commands/{command_id}")
        return {"deleted": command_id}

    @mcp.tool()
    def list_timers() -> list[dict]:
        """List timers (scheduled recurring chat messages)."""
        res = get_nb().request("GET", "/timers")
        return [
            {
                "id": t["_id"],
                "name": t["name"],
                "message": t["message"],
                "interval": t.get("interval"),
                "lines": t.get("lines"),
                "enabled": t.get("enabled"),
            }
            for t in res.get("timers", [])
        ]

    @mcp.tool()
    def add_timer(
        name: str,
        message: str,
        interval_minutes: int = 30,
        chat_lines: int = 2,
        dry_run: bool = False,
    ) -> dict:
        """Add a timer that posts a message every interval_minutes (5-60) once
        chat_lines messages have passed (spam guard)."""
        if dry_run:
            return preview(
                "add_timer", {"name": name, "message": message, "interval": interval_minutes}
            )
        nb = get_nb()
        res = nb.request(
            "POST",
            "/timers",
            {
                "name": name,
                "message": message,
                "interval": f"*/{interval_minutes} * * * *",
                "lines": chat_lines,
            },
        )
        return {"created": res.get("timer", {}).get("_id"), "name": name}

    @mcp.tool()
    def toggle_timer(timer_id: str, enabled: bool, dry_run: bool = False) -> dict:
        """Enable or disable a timer."""
        if dry_run:
            return preview("toggle_timer", {"timer_id": timer_id, "enabled": enabled})
        get_nb().request("PUT", f"/timers/{timer_id}", {"enabled": "true" if enabled else "false"})
        return {"timer": timer_id, "enabled": enabled}

    @mcp.tool()
    def delete_timer(timer_id: str, dry_run: bool = False) -> dict:
        """Delete a timer."""
        if dry_run:
            return preview("delete_timer", {"timer_id": timer_id})
        get_nb().request("DELETE", f"/timers/{timer_id}")
        return {"deleted": timer_id}

    @mcp.tool()
    def list_regulars() -> list[dict]:
        """List regulars (trusted users exempt from spam filters)."""
        res = get_nb().request("GET", "/regulars")
        return [
            {"id": r["_id"], "name": r.get("displayName", r.get("name"))}
            for r in res.get("regulars", [])
        ]

    @mcp.tool()
    def add_regular(name: str, dry_run: bool = False) -> dict:
        """Add a user to regulars by username."""
        if dry_run:
            return preview("add_regular", {"name": name})
        res = get_nb().request("POST", "/regulars", {"name": name})
        return {"added": res.get("regular", {}).get("_id"), "name": name}

    @mcp.tool()
    def remove_regular(regular_id: str, dry_run: bool = False) -> dict:
        """Remove a regular by id (from list_regulars)."""
        if dry_run:
            return preview("remove_regular", {"regular_id": regular_id})
        get_nb().request("DELETE", f"/regulars/{regular_id}")
        return {"removed": regular_id}

    @mcp.tool()
    def get_spam_filter(filter_name: str) -> dict:
        """Get a spam-protection filter's settings.
        filter_name: blacklist|links|caps|symbols|repetitions|emotes.
        blacklist = the banned words/phrases list for live chat."""
        if filter_name not in SPAM_FILTERS:
            return {"error": f"filter_name must be one of {SPAM_FILTERS}"}
        return get_nb().request("GET", f"/spam_protection/{filter_name}")

    @mcp.tool()
    def update_spam_filter(
        filter_name: str,
        enabled: bool | None = None,
        blacklist: list[str] | None = None,
        exempt_user_level: str | None = None,
        timeout_length: int | None = None,
        silent: bool | None = None,
        dry_run: bool = False,
    ) -> dict:
        """Update a spam filter. For filter_name=blacklist, `blacklist` replaces
        the banned words/phrases list (supports * wildcards per Nightbot docs)."""
        if filter_name not in SPAM_FILTERS:
            return {"error": f"filter_name must be one of {SPAM_FILTERS}"}
        body: dict = {}
        if enabled is not None:
            body["enabled"] = "true" if enabled else "false"
        if blacklist is not None:
            body["blacklist"] = "\n".join(blacklist)
        if exempt_user_level is not None:
            body["exemptUserLevel"] = exempt_user_level
        if timeout_length is not None:
            body["length"] = timeout_length
        if silent is not None:
            body["silent"] = "true" if silent else "false"
        if dry_run:
            return preview("update_spam_filter", {"filter": filter_name, **body})
        get_nb().request("PUT", f"/spam_protection/{filter_name}", body)
        return {"updated": filter_name, "changes": list(body)}

    @mcp.tool()
    def add_banned_phrases(phrases: list[str], dry_run: bool = False) -> dict:
        """Append phrases to the chat blacklist (fetch-merge-update; no duplicates)."""
        nb = get_nb()
        current = nb.request("GET", "/spam_protection/blacklist")
        existing = current.get("blacklist", "")
        lines = [ln for ln in existing.splitlines() if ln.strip()] if isinstance(existing, str) \
            else list(existing or [])
        merged = lines + [p for p in phrases if p not in lines]
        if dry_run:
            return preview("add_banned_phrases", {"added": phrases, "total": len(merged)})
        nb.request("PUT", "/spam_protection/blacklist", {"blacklist": "\n".join(merged)})
        return {"added": [p for p in phrases if p not in lines], "total": len(merged)}

    @mcp.tool()
    def send_chat_message(message: str, dry_run: bool = False) -> dict:
        """Send a chat message as Nightbot."""
        if dry_run:
            return preview("send_chat_message", {"message": message})
        get_nb().request("POST", "/channel/send", {"message": message})
        return {"sent": True}

    @mcp.tool()
    def health_check() -> dict:
        """Verify the Nightbot token and report the connected channel."""
        try:
            nb = get_nb()
            ch = nb.request("GET", "/channel").get("channel", {})
            return {"status": "ok", "channel": ch.get("displayName"), "joined": ch.get("joined")}
        except Exception as exc:  # noqa: BLE001 - health check reports, never raises
            return {"status": f"error: {exc}"}

    return mcp
