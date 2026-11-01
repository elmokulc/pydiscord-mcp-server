# Adding an MCP tool

The usual workflow is: service function → typed MCP wrapper → explicit
registration → tests and documentation. No automatic imports, file scanning, or
new Discord client are needed. This guide follows **`get_channel_info`**, an
existing, tested tool that reads an accessible channel or archived thread by ID.

## 1. Choose the domain and model

Put business logic in `src/pydiscord_mcp_server/services/channels.py`, contracts in
`models/`, and the MCP wrapper in `tools/channels.py`. For a new domain, create
matching modules in `services/` and `tools/`.

`ChannelInfo`, in `models/__init__.py`, is a Pydantic model containing string IDs,
`guild_id`, `name`, `type`, `parent_id`, `topic`, `url`, and thread metadata. Reuse
existing contracts instead of returning formatted text. Dates use `datetime` and
are serialized as ISO 8601 by the SDK.

## 2. Access the shared client and discord.py

The existing service function is:

```python
from ..models import ChannelInfo
from .access import DiscordAccess
from .serialization import channel_info


async def get_channel_info(access: DiscordAccess, channel_id: str) -> ChannelInfo:
    return channel_info(await access.channel(channel_id))
```

`access` is created once by `create_application`. It provides the runtime,
settings, and `access.client`. Its `channel` helper follows this lookup path:

```python
ident = int(channel_id)
channel = access.client.get_channel(ident) or await access.client.fetch_channel(ident)
```

`get_channel` checks the cache; `fetch_channel` is discord.py's official REST
coroutine. The helper then checks the channel type and its guild through
`access.check_guild(channel.guild.id)`. It rejects DMs and guilds outside the
allowlist. This also lets callers fetch an uncached archived thread directly,
without first calling `list_threads`.

Reuse `access.guild`, `access.channel`, `access.message_channel`, `access.message`,
and `access.member` as appropriate. Before calling a discord.py method not covered
by these helpers, resolve and authorize the resource. If the method returns
another resource, check its scope as well. Access restrictions must never rely
solely on a caller-supplied `guild_id`.

Do not use `discord.Client()` or `client.run()` inside a tool, or start another
thread or asyncio event loop. Check the signature in the
[stable discord.py API reference](https://discordpy.readthedocs.io/en/stable/api.html)
and use `await` or `async for` according to the method's actual contract.

## 3. Declare MCP parameters and results

In `tools/channels.py`, `register_tools` explicitly registers local functions:

```python
from mcp.server import MCPServer

from ..models import ChannelInfo, Snowflake
from ..services import channels
from ..services.access import DiscordAccess
from .common import READ


def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    @mcp.tool(annotations=READ)
    async def get_channel_info(channel_id: Snowflake) -> ChannelInfo:
        """Get an allowed guild channel or thread, including uncached archived threads, by ID."""
        async with access.operation():
            return await channels.get_channel_info(access, channel_id)
```

This example matches existing code; do not add it a second time. The decorator
runs when the registry calls `register_tools`, not merely when the module is
imported. `access` is a shared dependency captured by the closure, not a parameter
exposed to the model. Request data stays in local variables.

The **MCP v2** SDK used here imports `MCPServer` from `mcp.server`. It derives input
and output schemas from type annotations and the Pydantic model. Results are
available in `structuredContent`; the Python v2 client exposes this as
`result.structured_content`. Do not use FastMCP import paths from v1 examples.

For new parameters:

- Reuse `Snowflake`: a strict, nonzero decimal string within the 64-bit range.
  Convert to `int` only for discord.py; return IDs as `str`.
- Reuse `PageLimit`: a strict integer from 1 to 100. Document the order, exclusive
  boundary, and parameter that accepts `next_cursor`; return `null` at the end.
- Define strings and choices with `Annotated`, `Field`, `Literal`, and bounds.
  For example: `Annotated[str, Field(min_length=1, max_length=100, description="...")]`.
- Document optional parameters and their effects in the signature or docstring.
  Use strict booleans such as `AllowMentions` for sensitive opt-ins.
- Add a dedicated result model if existing models do not fit. Do not return
  discord.py objects, tokens, or internal client data.

Schema validation runs at the MCP boundary. Context-dependent business rules,
such as message ownership or permissions, belong in services and apply even if a
client misrepresents its capabilities.

## 4. Translate errors and bound the operation

`async with access.operation()` handles:

1. A bounded wait for the shared runtime to become ready.
2. An async operation bounded by `DISCORD_OPERATION_TIMEOUT`.
3. Translation of Discord and network exceptions through `errors.py`.

`discord.Forbidden` becomes `ACCESS_DENIED`, `discord.NotFound` becomes `NOT_FOUND`,
an HTTP 400 rejection becomes `INVALID_PARAMETER`, other network/HTTP failures
become `DISCORD_UNAVAILABLE`, and a timeout becomes `TIMEOUT`. Asyncio cancellation
propagates to allow clean shutdown.

Raise an explicit business-rule failure like this:

```python
from ..errors import DiscordToolError

raise DiscordToolError("INVALID_PARAMETER", "Resource is not a thread.")
```

`DiscordToolError` extends the official v2 `ToolError`, so the MCP client receives
an error with `isError=true`. Never use `return {"error": "..."}` in a result
reported as successful. Do not copy HTTP error bodies, tokens, or message content
into logs. Unexpected errors remain SDK failures and should be fixed; do not hide
all bugs behind `except Exception`.

Choose an annotation from `tools/common.py`, or add one that fits:

| Constant | Usage |
| --- | --- |
| `READ` | Read-only, idempotent operation |
| `WRITE` | Non-idempotent addition, such as sending a message |
| `EDIT` | Replacement or partial removal of state, such as editing or removing a reaction |
| `DELETE` | Deletion; another call may fail after the first succeeds |
| `REACTION_ADD` | Idempotent reaction addition |

Annotations inform the client. They grant no permissions and do not replace
guild, ownership, or permission checks.

## 5. Register the domain

`tools/channels.py` is already called from `tools/__init__.py`:

```python
def register_tools(mcp: MCPServer, access: DiscordAccess) -> None:
    guilds.register_tools(mcp, access)
    channels.register_tools(mcp, access)
    messages.register_tools(mcp, access)
    threads.register_tools(mcp, access)
    members.register_tools(mcp, access)
```

The excerpt above shows the original domains. The current registry also explicitly
calls `polls`, `manage_channels`, `roles`, `moderation`, `permissions`,
`integrations`, `events`, `search`, and `private_messages`. Models for these domains
also live in `models/management.py` and `models/polls.py`.

Adding a tool to an existing domain does not require changing the central
registry. A new domain must be imported and explicitly called here. Do not add a
second MCP server instance.

## 6. Test without a token or network access

Fixtures in `tests/conftest.py` provide `access` and objects using discord.py specs.
Async methods use `AsyncMock`, and iterators use real async functions. Network
connections are automatically blocked during all tests.

Example test for `tests/test_access.py` or a new test file:

```python
from conftest import make_channel
from mcp import Client
from mcp.server import MCPServer

from pydiscord_mcp_server.tools.channels import register_tools


async def test_get_channel_info_mcp(access):
    access.client.fetch_channel.return_value = make_channel()
    mcp = MCPServer("test-channel-info")
    register_tools(mcp, access)
    async with Client(mcp) as client:
        result = await client.call_tool("get_channel_info", {"channel_id": "200"})
        assert not result.is_error
        assert result.structured_content["id"] == "200"
        assert result.structured_content["guild_id"] == "100"
    access.client.fetch_channel.assert_awaited_once_with(200)
```

This uses the official client in memory. The bot does not start: the fixture mocks
the readiness wait. Separate lifecycle tests exercise task startup with a mocked
connection.

Also cover relevant cases: invalid IDs, missing resources, Discord refusals,
excluded guilds, cache misses, final pagination pages, and write effects. For
mutations, assert that no mutating method was called after a refusal. For tools
that support mentions, check `AllowedMentions`, including replies. Existing tests
in `test_access.py`, `test_messages.py`, `test_threads.py`, and `test_mcp.py` provide
complete examples.

## 7. Document, verify, and rebuild

Add the tool to `docs/tools.md` with its parameters, permissions, and limits, and
extend the catalogue tests. Update the README if the overview or configuration
changes. See also the [contributing guide](../CONTRIBUTING.md).

The pinned `tests/fixtures/reference_tools.json` describes the reference
repository: do not modify it to add a project-specific tool. Tests list extensions
separately and verify that all 81 reference names remain covered. Do not promise
exhaustive search when the API or cache cannot provide it.

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest -q
docker compose up -d --build
```

Python code is built into the image; restarting the old image is not enough.
Refresh tool discovery in the MCP client after rebuilding. If a dependency changes,
update `pyproject.toml` and `uv.lock` together with uv before rebuilding. Live write
validation requires explicit authorization and a test channel; automated tests
remain offline.
