# Release 0.2.0 verification — October 30, 2026

This is a historical record of checks performed for the October 30 release.
It does not describe the results of subsequent changes or reruns.

## Passed

| Check | Result |
| --- | --- |
| Resolution: `uv lock --check --offline` | Lockfile consistent with `pyproject.toml` |
| Installation: `uv sync --locked --offline` | Passed with Python 3.12.3 on the host |
| `uv run --locked ruff check .` | Passed |
| `uv run --locked ruff format --check .` | Passed |
| `uv run --locked mypy` | Strict mode; 43 source files; no errors |
| `uv run --locked pytest -q` | 220 tests passed; network connections blocked in tests |
| Reference catalogue | 81 names pinned to commit `e134c03714cfadf786b686e3045b92537042a240`, all covered among 88 tools |
| Catalogue MCP calls | All 88 tools called with the official client and Discord doubles; structured results checked |
| Polls | `discord.Poll` payload, bounds and mentions, REST freshness, ending restricted to the bot's own polls, unknown counts, and paginated voters |
| Administration | Excluded guilds and foreign categories rejected, permission merging, opt-in DMs with REST membership checks, message ownership, and event/image validation |
| `docker build -t pydiscord-mcp-server:local .` | Passed using `uv sync --locked --no-dev --no-editable` |
| Compose validation | `docker compose --env-file .env.example config --no-env-resolution --quiet` passed without creating `.env` |
| Non-root execution | UID 10001 confirmed in the container; `.env` absent from the image |
| HTTP in Docker | Two simultaneous official SDK clients, discovery of all 88 tools, `list_guilds` call, poll schema validation, and rejection of an invalid poll |
| HTTP health | `/health/live` and `/health/ready` returned 200 in the isolated container |
| Image healthcheck | `healthy` status confirmed at runtime |
| SIGTERM in Docker | Fake client closure observed, clean ASGI shutdown, exit code 0 |
| Missing token | Required-token validation tested; CLI rejection without a secret had already been checked for the initial release |

The uv commands used a temporary uv 0.13.6 installation and the dependency cache,
outside the project source. The image used Python 3.12.16 and uv 0.13.6; its
measured local size was approximately 254 MiB (265,848,098 bytes).

The Docker HTTP and SIGTERM checks replaced **only the Discord connection** with
a double and used `--network none`, a read-only filesystem, and temporary `/tmp`.
HTTP requests used the container's loopback interface. Temporary containers were
stopped and removed. These checks verified packaging, Uvicorn, the MCP SDK,
routing, and shutdown; they did not validate Discord authentication.

Automated tests also covered a fatal bot-task failure after startup: supervision
requested HTTP shutdown and returned a failure code. Two in-memory SDK clients
shared a single Discord task. Streamable HTTP requests were exercised through
in-memory ASGI, including initialization, structured calls, absence of an HTTP
session, rejected Host headers, and degraded health.

One upstream warning remained: discord.py imports `audioop`, deprecated in
Python 3.12. It did not fail any check; the project manages voice channels and
states without establishing an audio connection.

## Not performed

- Authentication and reconnection with a **real Discord bot**: no real token was
  used. Follow the [manual validation procedure](../CONTRIBUTING.md#manual-discord-validation).
- Verification of actual portal permissions and intents, real channel content,
  access to real private/archived threads, and searches for real members.
- Live writes: no message, poll, edit, deletion, role change, permission change,
  reaction, or other resource change was performed. Explicit authorization and a
  test guild/channel are required.
- Remote deployment with authentication/HTTPS: outside the scope of that local
  release; requirements are documented in the [README](../README.md#connection-and-access).
- Git commits: none were requested or created for that extension. The local
  repository had been initialized between releases; the initial release's note
  about an unusable `.git` directory no longer described its state.

## Blocked checks

No lint, type-checking, test, or Docker build check remained blocked at the time
of this record. A real connection still needed validation with the user's bot.
The older `discord-mcp` project was not modified.
