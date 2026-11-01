# Contributing

Read the [README](README.md) for setup and [architecture](ARCHITECTURE.md) for the
runtime and access model. Keep changes focused and document user-visible behavior.

## Set up

Install Python 3.12+ and uv, then run from the repository root:

```bash
uv sync --locked
```

Tests use fake credentials and Discord doubles; no bot token or `.env` is needed.
To run the actual service locally, copy `.env.example` to `.env`, configure your
bot, and run `uv run --locked python -m pydiscord_mcp_server`.
Keep `.env` private and out of commits.

## Checks

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest -q
```

Ruff targets Python 3.12 with a 100-character line limit. Mypy checks `src/` in
strict mode. Pytest runs async tests automatically. Use
`uv run --locked ruff format .` to format changed Python files.

Tests block outbound socket connections in `tests/conftest.py`. Use `AsyncMock`
for async Discord methods and async iterators for paginated responses. Integration
tests exercise the official MCP client and HTTP through in-memory ASGI transports.

For packaging or deployment changes, also check:

```bash
docker build -t pydiscord-mcp-server:local .
docker compose --env-file .env.example config --no-env-resolution --quiet
```

The image build needs no Discord credentials. Rebuild the image to apply code
changes; restarting an existing container does not update its code.

## Add or change a tool

1. Define or reuse Pydantic contracts in `models/`. Use `Snowflake` for IDs,
   `PageLimit` for page sizes, and explicit bounds for other inputs.
2. Put Discord logic in the relevant `services/` module. Resolve and authorize
   resources through `DiscordAccess` before reading or mutating them. Reuse the
   shared runtime and keep request data local.
3. Add a typed wrapper in the corresponding `tools/` module. Enter
   `async with access.operation()` and choose an annotation from `tools/common.py`
   matching the tool's actual effects.
4. For a new domain, import and register it explicitly in `tools/__init__.py`.
5. Test successful results and relevant failure boundaries: invalid inputs,
   excluded guilds, missing cache entries, Discord refusals, ownership, mentions,
   and pagination. Assert that denied writes never reach the mutating method.
6. Update [docs/tools.md](docs/tools.md) and catalogue coverage in
   `tests/test_catalogue.py` and `tests/test_mcp.py` when names or contracts change.
   Update the README only if the overview or setup changes.

The [detailed walkthrough](docs/adding-tools.md) follows the existing
`get_channel_info` tool. The project uses **MCP SDK v2** and
`from mcp.server import MCPServer`; v1 FastMCP examples do not match this codebase.

Keep `tests/fixtures/reference_tools.json` pinned to its upstream reference. Add
project-specific extensions separately in catalogue tests. Do not change the
reference fixture simply to make a new tool pass.

## Dependencies

Update `pyproject.toml` bounds if needed, then refresh the lockfile deliberately:

```bash
uv lock --upgrade-package PACKAGE_NAME
```

Commit `pyproject.toml` and `uv.lock` together when both change. Run the checks and
rebuild the image after dependency updates.

## Manual Discord validation

Automated tests do not prove real bot permissions or connectivity. If live
validation is needed, use a dedicated test guild with a restrictive allowlist:

1. Configure the bot's permissions and intents in the portal and `.env`.
2. Start the service and wait for `/health/ready` to return `200`.
3. Try `list_guilds`, `list_channels`, `get_channel_info`, and `read_messages`.
4. Check expected content, cursors, and access to a known archived thread.
5. Verify that resources outside the allowed guild are refused.
6. Stop the service and check that it shuts down cleanly.

Live writes require explicit authorization and a dedicated test channel. Never
put a real token in tests, logs, documentation, or a pull request.

## Before submitting

Explain what changed, why, and how it was verified. Include relevant limitations
and distinguish automated checks from live validation. Update affected docs and
avoid unrelated formatting or dependency changes. Documentation-only edits need
link and content checks; Python and Docker checks apply when those areas change.
