# pydiscord-mcp-server

A Python MCP server that lets multiple assistants read and manage Discord through
**one shared bot connection per process**. It exposes 88 tools over Streamable HTTP
at `http://localhost:8085/mcp`.

Tools cover messages, search, threads, forums, polls, members, roles, moderation,
channels, permissions, events, integrations, and optional direct messages.
Browse [all available tools](#available-tools), or see the
[detailed catalogue](docs/tools.md) for parameters and limits.

## License

This project is free and open source under the [MIT License](LICENSE). You may
use, modify, and redistribute it, including commercially, provided you retain
the copyright and license notices.

## Quick start with Docker

You need Docker with Compose and a Discord bot invited to your server
([bot setup](#discord-bot-setup)). From the repository root:

```bash
cp .env.example .env
chmod 600 .env
# Edit .env: set DISCORD_TOKEN, allowed guilds, and any required intents.
docker compose up -d --build
curl --fail http://localhost:8085/health/ready
```

Once ready, the health endpoint returns `{"status":"ready"}`. Connect your MCP
client to `http://localhost:8085/mcp` using Streamable HTTP, then try `list_guilds`.
The Discord token stays on the server; clients do not need it.

Compose publishes the service on `127.0.0.1` only. Run **one instance with one
worker** to keep a single bot connection. The `.env` file is excluded from Git and
the Docker build context.

```bash
docker compose logs --tail=100 discord-mcp
docker compose up -d --build           # Apply code changes.
docker compose up -d --force-recreate  # Apply .env changes.
docker compose down
```

## Discord bot setup

1. Create an application in the [Discord Developer Portal](https://discord.com/developers/applications).
2. Get its **bot token** and set `DISCORD_TOKEN` in `.env`. Keep it private; use a
   bot account, never a user token.
3. Enable **Message Content Intent** to read normal message content and
   **Server Members Intent** for member name searches and event subscriber lists.
   Enable the matching `.env` options below as well. Both are off by default.
4. Invite the bot with the OAuth2 `bot` scope and the permissions needed for your
   tools. No slash commands or `applications.commands` scope are required.
5. Enable Discord developer mode to copy guild, channel, member, and message IDs.

Start with **View Channel** and **Read Message History** for reading. Add
**Send Messages** and **Send Messages in Threads** for posting, **Send Polls** for
polls, and the relevant management permissions for administrative tools. Role
hierarchy and channel/thread overrides still apply; avoid granting Administrator
by default.

## Configuration

Environment variables override `.env`. See [.env.example](.env.example) for all
settings, including logging, allowed hosts/origins, and timeouts.

| Variable | Default and purpose |
| --- | --- |
| `DISCORD_TOKEN` | Required bot token |
| `DISCORD_GUILD_ID` | Optional default when a tool omits `guild_id` |
| `DISCORD_ALLOWED_GUILD_IDS` | JSON array of string IDs; unset allows all accessible guilds, `[]` denies all |
| `DISCORD_INTENT_MESSAGE_CONTENT` | `false`; also enable it in the Developer Portal |
| `DISCORD_INTENT_MEMBERS` | `false`; also enable it in the Developer Portal |
| `DISCORD_ENABLE_DMS` | `false`; opt in to private-message operations |
| `MCP_HOST` | `127.0.0.1` locally; Compose sets `0.0.0.0` inside the container |
| `MCP_PORT` | `8085`; in Compose, changes the published host port only |

For example, restrict access to one guild:

```dotenv
DISCORD_GUILD_ID=123456789012345678
DISCORD_ALLOWED_GUILD_IDS='["123456789012345678"]'
DISCORD_INTENT_MESSAGE_CONTENT=true
```

The default guild is a convenience, **not an access restriction**. Use the allowlist
to restrict tools, including calls made with direct channel or thread IDs. Private
tools additionally require an allowed selected guild and a fresh check that the
recipient is a member of it.

## Connection and access

| Endpoint | Purpose |
| --- | --- |
| `/mcp` | Streamable HTTP MCP endpoint with structured JSON tool results |
| `/health/live` | HTTP process is alive: `200` |
| `/health/ready` | Bot is connected: `200`; unavailable: `503` |

Use a Streamable HTTP MCP client; opening `/mcp` in a browser is not an MCP
initialization. From another container on the same Compose network, connect to
`http://discord-mcp:8085/mcp`. Add other hostnames to `MCP_ALLOWED_HOSTS` as needed.

The service has **no built-in MCP authentication**. Anyone who can reach `/mcp`
can use the bot's capabilities within the allowed guilds. Keep it local or on a
controlled private network. Remote access requires an authentication gateway,
HTTPS, and appropriate Host/Origin restrictions. Browser clients also need CORS
configured at the proxy or adapter.

## Available tools

All **88 tools** are listed below, grouped by purpose. See the
[detailed catalogue](docs/tools.md) for required and optional parameters,
pagination, and limits. Availability in the catalogue does not grant permission
to run a tool: guild restrictions, Discord permissions, and configured intents
still apply.

### Guilds

| Tool | Purpose |
| --- | --- |
| `list_guilds` | List allowed guilds. |
| `get_guild_info` | Read guild metadata. |
| `get_server_info` | Read guild metadata (equivalent to `get_guild_info`). |

### Channels and categories

| Tool | Purpose |
| --- | --- |
| `list_channels` | List channels, excluding threads. |
| `get_channel_info` | Read a channel or thread, including uncached archived threads. |
| `create_text_channel` | Create a text channel with validated settings. |
| `edit_text_channel` | Edit the name, topic, NSFW flag, slowmode, category, or position. |
| `delete_channel` | Permanently delete a channel or thread. |
| `find_channel` | Find channels whose names match exactly, ignoring case. |
| `move_channel` | Move a channel to a category in the same guild or change its position. |
| `create_category` | Create a category. |
| `edit_category` | Rename or reposition a category. |
| `delete_category` | Delete a category while keeping its child channels. |
| `find_category` | Find categories with an exact name match. |
| `list_channels_in_category` | List a category's child channels. |
| `create_voice_channel` | Create a voice channel with limits and a region. |
| `create_stage_channel` | Create a Stage channel. |
| `edit_voice_channel` | Edit a voice or Stage channel. |

### Messages and search

| Tool | Purpose |
| --- | --- |
| `read_messages` | Read a history page with at most one boundary. |
| `get_message` | Read a message and its reply reference. |
| `send_message` | Send text, optionally as a reply. |
| `edit_message` | Edit a message owned by the bot. |
| `delete_message` | Delete a message; deleting another author's message requires opt-in and Manage Messages. |
| `add_reaction` | Add a reaction as the bot. |
| `remove_reaction` | Remove a reaction; removing someone else's requires Manage Messages. |
| `search_messages` | Search message bodies and embed text in up to 1000 messages from one channel or thread. |
| `get_message_replies` | Find explicit replies in up to 1000 later messages. |

### Threads and forums

| Tool | Purpose |
| --- | --- |
| `list_threads` | List a parent's active or accessible archived threads. |
| `get_thread_info` | Read thread metadata directly by ID. |
| `list_active_threads` | List a guild's accessible active threads. |
| `create_forum_channel` | Create a forum with default settings. |
| `edit_forum_channel` | Edit a forum or media channel's settings. |
| `list_forum_channels` | List the guild's forum and media channels. |
| `get_forum_channel_info` | Read a forum's metadata, tags, and settings. |
| `list_forum_tags` | List a forum's available tags. |
| `create_forum_post` | Create a post with its first message and valid tags. |
| `list_forum_posts` | List active forum posts; use `list_threads` for archives. |
| `modify_forum_post` | Lock, archive, pin, or replace a post's tags. |

### Polls

| Tool | Purpose |
| --- | --- |
| `create_poll` | Create a native Discord poll with a question and answer options. |
| `get_poll` | Refresh a poll and its counts through REST. |
| `end_poll` | Close a poll created by this bot. |
| `get_poll_answer_voters` | List users who selected a poll answer. |

### Members

| Tool | Purpose |
| --- | --- |
| `get_member` | Read a member from cache, with a REST fallback. |
| `get_member_by_id` | Read a member by stable ID (equivalent to `get_member`). |
| `get_user_id_by_name` | Resolve an exact, unambiguous username within the available search scope. |
| `search_members` | Look up a specific ID or search names in cache and Gateway candidates. |

### Roles

| Tool | Purpose |
| --- | --- |
| `list_roles` | List roles and their permissions. |
| `create_role` | Create a role with permissions, a color, and other settings. |
| `edit_role` | Edit a role's properties or position. |
| `delete_role` | Permanently delete a role. |
| `assign_role` | Add a role without replacing the member's other roles. |
| `remove_role` | Remove a role without replacing the member's other roles. |

### Moderation and voice state

| Tool | Purpose |
| --- | --- |
| `kick_member` | Remove a member from the guild. |
| `ban_member` | Ban a user; optionally delete 0–7 days of messages. |
| `unban_member` | Lift a ban without automatically returning the user to the guild. |
| `timeout_member` | Restrict communication for 1 second to 28 days. |
| `remove_timeout` | Lift a temporary communication restriction. |
| `set_nickname` | Change a nickname; `null` restores the username. |
| `get_bans` | List banned users and ban reasons. |
| `move_member` | Move a member to a voice channel in the same guild. |
| `disconnect_member` | Disconnect a member from their voice channel. |
| `modify_voice_state` | Apply or remove server mute/deafen. |

### Channel permissions

| Tool | Purpose |
| --- | --- |
| `list_channel_permission_overwrites` | List explicit role or member permission overwrites. |
| `upsert_role_channel_permissions` | Create or update a role overwrite, preserving unrelated permissions. |
| `upsert_member_channel_permissions` | Create or update a member overwrite, preserving unrelated permissions. |
| `delete_channel_permission_overwrite` | Delete an entire overwrite to restore inheritance. |

### Webhooks

| Tool | Purpose |
| --- | --- |
| `create_webhook` | Create a webhook and return metadata without secrets. |
| `list_webhooks` | List a channel's webhooks without exposing tokens. |
| `delete_webhook` | Delete a webhook after checking its guild. |
| `send_webhook_message` | Send through an authorized webhook, optionally into one of its threads. |

### Invites

| Tool | Purpose |
| --- | --- |
| `create_invite` | Create an invite with bounded lifetime and usage limits. |
| `list_invites` | List guild invites with statistics. |
| `delete_invite` | Revoke an invite after checking its guild. |
| `get_invite_details` | Read a public invite while enforcing the guild allowlist. |

### Emojis

| Tool | Purpose |
| --- | --- |
| `list_emojis` | List the guild's custom emojis. |
| `get_emoji_details` | Read a custom emoji from cache, with a REST fallback. |
| `create_emoji` | Upload an emoji from a base64 image of up to 256 KiB. |
| `edit_emoji` | Rename an emoji or replace its role restrictions. |
| `delete_emoji` | Permanently delete a custom emoji. |

### Scheduled events

| Tool | Purpose |
| --- | --- |
| `create_guild_scheduled_event` | Create a voice, Stage, or external event with consistent dates and location. |
| `edit_guild_scheduled_event` | Edit an event's details or status. |
| `delete_guild_scheduled_event` | Permanently delete an event. |
| `list_guild_scheduled_events` | List the guild's scheduled and active events. |
| `get_guild_scheduled_event_users` | List interested users; requires Members intent. |

### Private messages

These tools are always listed, but calls require `DISCORD_ENABLE_DMS=true`,
an allowed selected guild, and a fresh check of the recipient's membership.

| Tool | Purpose |
| --- | --- |
| `send_private_message` | Send a DM after opt-in and a REST membership check for the shared guild. |
| `read_private_messages` | Read the bot's DM history after opt-in and authorization. |
| `edit_private_message` | Edit a DM sent by this bot. |
| `delete_private_message` | Delete a DM sent by this bot. |

## Tool behavior and limits

- IDs are decimal **strings**, including in results. Page sizes are 1–100; follow
  `next_cursor` using the parameter identified by `cursor_parameter`.
- Message search and reply lookup scan a bounded history in one channel or thread.
  Member searches depend on available cache and Gateway results. Neither is
  guaranteed to be exhaustive.
- Mentions are disabled by default. `allow_mentions=true` enables all mention
  types. Only the bot's own messages can be edited; deleting another author's
  guild message requires `allow_other_author=true` and Manage Messages.
- Messages include structured embeds, attachments, stickers, components, replies,
  and polls. Empty `content` does not mean a message has no other content.
- Text writes accept 1–2000 characters. File uploads and attachment/embed editing
  are not supported. Use forum tools to create posts in a forum.
- Failed tool calls return MCP errors with stable codes such as `ACCESS_DENIED`,
  `NOT_FOUND`, `INVALID_PARAMETER`, `DISCORD_UNAVAILABLE`, or `TIMEOUT`. A timed-out
  write may already have succeeded: check before retrying.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Startup fails or readiness stays unavailable | Bot token, network access, intents in both the portal and `.env`, and container logs |
| Message content is empty | Message Content intent and the message's structured fields |
| `ACCESS_DENIED` or `NOT_FOUND` | Guild allowlist, bot permissions, channel overrides, private-thread membership |
| HTTP `421` | Request hostname is included in `MCP_ALLOWED_HOSTS` |
| HTTP Origin or Accept error | Allowed origins and a compatible Streamable HTTP client |
| Multiple bot connections | Stop duplicate processes or containers; use one worker |

## Development and documentation

For local development, use Python 3.12+ and uv:

```bash
uv sync --locked
cp .env.example .env
# Set DISCORD_TOKEN and any required options before starting the server.
uv run --locked python -m pydiscord_mcp_server
```

- [Architecture](ARCHITECTURE.md): runtime, request flow, and access policies.
- [Contributing](CONTRIBUTING.md): development checks and adding tools.
- [Agent instructions](AGENTS.md): repository conventions for coding agents.
- [Tool catalogue](docs/tools.md), [poll guide](docs/polls.md), and
  [reference compatibility](docs/parity.md).
- [Release verification record](docs/verification.md): historical checks and limits.
