# nightbot-mcp

An MCP (Model Context Protocol) server for [Nightbot](https://nightbot.tv):
manage custom chat commands, timers, regulars, and spam-protection filters —
including the **blacklist** (banned words/phrases for live chat) — through
the official [Nightbot API](https://api-docs.nightbot.tv).

- Every mutating tool accepts `dry_run=true` and returns a preview.
- `add_banned_phrases` appends to the blacklist without clobbering it
  (fetch → merge → update).
- No secrets in this repo or logged at runtime.

## Quick start

1. Create an app at [nightbot.tv/account/applications](https://nightbot.tv/account/applications)
   and generate an access token (scopes: `channel commands timers regulars
   spam_protection channel_send`).
2. Provide the token:

```bash
export NIGHTBOT_ACCESS_TOKEN=...     # or NIGHTBOT_MCP_SECRETS=vaultproxy
```

3. Add to your MCP client:

```bash
# Claude Code
claude mcp add nightbot -s user -- uvx nightbot-mcp
```

## Tools

| Area | Tools |
|---|---|
| Channel | `channel_info`, `join_channel`, `part_channel`, `send_chat_message` |
| Commands | `list_commands`, `add_command`, `update_command`, `delete_command` |
| Timers | `list_timers`, `add_timer`, `toggle_timer`, `delete_timer` |
| Regulars | `list_regulars`, `add_regular`, `remove_regular` |
| Spam protection | `get_spam_filter`, `update_spam_filter`, `add_banned_phrases` |
| Meta | `health_check` |

Filters: `blacklist`, `links`, `caps`, `symbols`, `repetitions`, `emotes`.
Blacklist entries support Nightbot's `*` wildcards.

## Development

```bash
pip install -e '.[dev]'
ruff check src tests && pytest
```

Tests are fully offline (fake HTTP opener).

## License

MIT
