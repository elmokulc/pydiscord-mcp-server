# Repository instructions

## Orientation

- Read `README.md` for setup, `ARCHITECTURE.md` for design, and `CONTRIBUTING.md`
  for the development workflow.
- Write documentation, public tool descriptions, and examples in English.
- Keep changes scoped to the task. Do not edit generated caches or unrelated files.

## Implementation conventions

- Target Python 3.12+, strict mypy, and Ruff's configured 100-character line limit.
- Use the official MCP SDK v2 (`mcp.server.MCPServer`), not v1 FastMCP APIs.
- Keep MCP wrappers in `tools/`, business logic in `services/`, and Pydantic
  contracts in `models/`. Register new domains explicitly in `tools/__init__.py`.
- Preserve one shared `DiscordRuntime` per process and one Uvicorn worker. Never
  create a bot client, event loop, or connection inside a tool.
- Wrap tool operations in `access.operation()`. Use `DiscordAccess` helpers and
  check the guild of resolved resources, including direct IDs, before operations.
- Keep IDs as validated decimal strings at MCP boundaries. Reuse `Snowflake`,
  `PageLimit`, and existing serialization helpers.
- Preserve omitted-versus-null semantics for edit settings, bounded reads, and
  documented cursor order. Do not imply exhaustive results from cache or scans.
- Preserve default-disabled mentions, DM opt-in and fresh guild membership checks,
  message ownership rules, and explicit opt-ins for deleting others' messages.
- Raise `DiscordToolError` for expected business failures. Do not return error
  text as successful data, expose raw Discord error bodies, or swallow cancellation.
- Tool annotations describe effects; authorization belongs in service logic.

## Verification

For Python changes, run the relevant tests and the configured checks:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest -q
```

- Keep tests offline. Use fixtures from `tests/conftest.py`, `AsyncMock`, and
  in-memory MCP/ASGI clients; do not weaken the network-blocking fixture.
- Cover affected access policies and assert that rejected writes do not mutate
  Discord. Update tool catalogue tests and `docs/tools.md` when contracts change.
- Keep `tests/fixtures/reference_tools.json` pinned to upstream; list local
  extensions separately in tests.
- Update dependencies with uv and keep `pyproject.toml` consistent with `uv.lock`.
- For Docker changes, build the image and validate Compose as described in
  `CONTRIBUTING.md`. For documentation-only work, check links and factual accuracy.
- Report checks actually run and any gaps; do not present historical verification
  results as new results.

## Credentials and live operations

- Do not read or print the real `.env` or tokens during routine development. Use
  `.env.example` and fake test credentials.
- Do not log tokens, message content, raw HTTP error bodies, or webhook secrets.
- Starting the real bot or making live Discord calls requires task authorization.
  Live writes require explicit authorization and a dedicated test channel.
- Keep loopback/private deployment defaults and existing Host/Origin validation.
  Remote deployment needs an authentication gateway and HTTPS.
