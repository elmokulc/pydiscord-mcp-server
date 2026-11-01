# Architecture

The server connects multiple MCP clients to one Discord bot connection per
process. It uses Python 3.12+, discord.py 2.x, the official MCP Python SDK v2,
Pydantic v2, Starlette, and Uvicorn. Dependency versions are pinned in `uv.lock`.

## Project layout

```text
src/pydiscord_mcp_server/
  __main__.py        CLI, Uvicorn, and fatal connection supervision
  config.py          Environment settings and secret validation
  discord_client.py  Bot intents, shared connection, readiness, shutdown
  server.py          Application factory, ASGI lifespan, MCP, health routes
  errors.py          Safe Discord-to-MCP error translation
  models/            Validated inputs and structured output contracts
  services/          Resource access, domain logic, serialization
  tools/             Typed MCP wrappers and explicit domain registration
tests/               Discord doubles and in-memory MCP/HTTP tests
docs/                Tool catalogue, examples, and reference comparisons
```

## Application lifecycle

`__main__.serve()` loads a single application from `create_application(settings)`
and runs Uvicorn with one worker. The application owns:

- One `DiscordRuntime` and its `BotClient`.
- One `DiscordAccess` shared by tool closures.
- One `MCPServer` with explicitly registered tool domains.
- One Starlette application mounting MCP and health endpoints.

The Starlette lifespan starts the Discord task and waits for readiness before
entering the MCP session manager and accepting HTTP traffic. Startup fails if the
bot cannot become ready within `DISCORD_READY_TIMEOUT`.

discord.py handles reconnection and rate limits. A Gateway disconnect makes
readiness false; calls wait for readiness within the configured timeout. If the
Discord task terminates unexpectedly, the runtime signals failure and the CLI
stops HTTP with a nonzero exit code. Compose can then restart the container.
A Docker `unhealthy` status alone does not trigger a Compose restart.

On shutdown, Uvicorn drains requests within its graceful shutdown timeout. The
lifespan closes the Discord client, then cancels and awaits the connection task
with bounded waits. Use the provided CLI to retain fatal-failure supervision.

## Request flow

```text
MCP client -> /mcp -> typed tool wrapper -> DiscordAccess.operation()
           -> domain service -> authorized resource -> discord.py cache / REST
           -> Pydantic result -> MCP structuredContent
```

`tools/__init__.py` explicitly registers each domain. Importing a module does not
register tools. Tool wrappers define validated parameters, output types, and
annotations; services implement Discord operations. Models and serialization
helpers keep SDK objects out of public results.

Each wrapper enters `access.operation()`, which waits for readiness, applies
`DISCORD_OPERATION_TIMEOUT`, and translates expected Discord/network failures.
Request-specific values stay local; tools never create their own bot clients.

The HTTP transport uses `stateless_http=True` and JSON responses. Clients share
the runtime without sharing an HTTP session or per-call context. There is no
database, stdio transport, elicitation, subscription, or client notification stream.

## Resource access and permissions

`services/access.py` centralizes guild, channel, member, and message resolution.
Most lookups try the cache, then targeted REST fetching. Direct IDs can therefore
resolve uncached channels and archived threads. Cache entries may be stale, and
Discord permissions remain the final authority.

`DISCORD_GUILD_ID` selects a default. `DISCORD_ALLOWED_GUILD_IDS` restricts access:
unset allows all accessible guilds, while an empty list denies all. Channel and
thread resolution checks the resolved resource's guild before domain operations;
caller-supplied guild IDs alone are not sufficient authorization.

Guild message tools reject DMs. Private tools remain registered but fail unless
`DISCORD_ENABLE_DMS=true`. They resolve an allowed selected guild and refresh the
recipient's membership through REST before opening or using a private channel.

Writes apply additional policies in services: edits require bot ownership,
deleting another author's guild message requires explicit opt-in and Manage
Messages, and removing another member's reaction requires Manage Messages.
Mentions are disabled by default, including reply mentions. Tool annotations
describe behavior to clients; they do not enforce authorization.

## Data contracts and bounded reads

- `Snowflake` validates nonzero decimal string IDs within the unsigned 64-bit
  range. Convert to integers only when calling discord.py and return strings.
- `PageLimit` is a strict integer from 1 to 100. Page models expose continuation
  cursors and, where applicable, the parameter to use for the next request.
- Edit models distinguish omitted fields from explicit `null`; only supplied
  settings are applied.
- Message serialization retains rich content and a single resolved reply level.
  Poll reads refresh through REST rather than relying on cached counts.
- History search and reply lookup scan one channel/thread with a bounded budget.
  Member searches use cache and bounded Gateway queries; no full member chunking
  runs at startup. Results must not promise completeness.
- Thread cursors are scoped to a parent and mode. Pages are not snapshots;
  concurrent changes and timestamp boundaries can affect continuation.

## Errors and sensitive data

`DiscordToolError` extends the SDK's `ToolError`, producing `isError=true` with a
stable code: `ACCESS_DENIED`, `NOT_FOUND`, `INVALID_PARAMETER`,
`DISCORD_UNAVAILABLE`, or `TIMEOUT`. Schema validation can reject input before the
service runs. Async cancellation propagates so shutdown can complete.

Raw Discord error bodies are not returned. Settings use `SecretStr` and suppress
input values in validation errors. The CLI limits detailed Discord HTTP, Gateway,
webhook, and MCP server logging, even at application DEBUG level. MCP results
contain requested data and may be retained by clients. A write timeout does not
prove that Discord rejected the action; check state before retrying.

## Deployment boundary

The Docker image installs locked production dependencies in a separate build
stage, runs as UID 10001, and checks readiness. Compose adds a read-only filesystem,
temporary `/tmp`, dropped capabilities, and loopback-only port publication. It
fixes the internal port at 8085; `.env`'s `MCP_PORT` selects the published host port.

Host/Origin validation protects the HTTP transport but does not authenticate
clients. The service has no built-in MCP identity layer. Keep it local/private or
put an MCP-compatible authentication gateway and HTTPS in front of it. See the
[README](README.md#connection-and-access) for connection details and
[contributing guide](CONTRIBUTING.md) for offline validation.
