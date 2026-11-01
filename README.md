# pydiscord-mcp-server

A Python MCP server that lets multiple assistants read and manage Discord through
**one shared bot connection per process**. It exposes 88 tools over Streamable HTTP
at `http://localhost:8085/mcp`.

Tools cover messages, search, threads, forums, polls, members, roles, moderation,
channels, permissions, events, integrations, and optional direct messages.
See the [tool catalogue](docs/tools.md) for parameters and limits.

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
