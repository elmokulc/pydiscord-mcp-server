# Compatibility with SaseQ/discord-mcp

This comparison uses the tool catalogue and signatures from
[SaseQ/discord-mcp](https://github.com/SaseQ/discord-mcp), commit
[`e134c03714cfadf786b686e3045b92537042a240`](https://github.com/SaseQ/discord-mcp/tree/e134c03714cfadf786b686e3045b92537042a240).
The reference catalogue contains **81 tool names**. All are present in this Python
version; parameters and contracts remain specific to this project.
`tests/fixtures/reference_tools.json` records the inventory and reference commit.
A test prevents any of these names from being dropped. Each tool is also called
through the official MCP SDK with offline Discord doubles.

**Total: 88 tools.** The seven additional names are `list_guilds`,
`get_guild_info`, `get_member`, and the four poll tools: `create_poll`, `get_poll`,
`end_poll`, and `get_poll_answer_voters`. The first three predate this extension;
the equivalent `get_server_info` and `get_member_by_id` tools are retained to
cover the reference repository's names.

See the [88-tool catalogue](tools.md) for each name and its parameters.

## Explicit contract differences

| Area | This Python server's contract |
| --- | --- |
| Parameters | `snake_case`, string IDs, strict numeric bounds, and `settings` objects for complex edits. Matching tool names does not imply automatic compatibility with Java/camelCase arguments. |
| Results | Pydantic objects and `structuredContent`; MCP errors use `isError=true`. |
| Sessions | One discord.py client per HTTP process; stateless HTTP mode. |
| Authorization | The guild allowlist also applies to direct resource access, webhooks, and invites. Public invites to excluded guilds are still rejected. |
| Private messages | All four tools are present but disabled by default. Setting `DISCORD_ENABLE_DMS=true` also requires an allowed selected guild and a fresh REST check of the recipient's membership. Guild channel tools continue to reject DMs. |
| Mentions | Disabled by default in messages, replies, forums, webhooks, and DMs; enabling them requires an explicit, typed option. |
| Webhooks | Sending takes a `webhook_id`, not a token-bearing URL. The bot fetches the webhook, checks its guild and channel, then uses it. No token or secret URL is returned. The required Discord permissions must be granted. |
| Emojis | Base64 images (or image data URIs), at most 256 KiB, with validated image types. Arbitrary image URLs are not downloaded; provide base64-encoded bytes. |
| History | Only one of `before`, `after`, or `around`. Direction and continuation are explicit; `around` is a window without a continuation cursor. |
| Message search | An explicit scan of 1–1000 messages in one channel/thread; no global search engine is promised. The cursor resumes after the last scanned message. |
| Message replies | Explicit references are searched in at most 1000 later messages per call; results expose the scan budget and an `after` cursor. A resolved referenced message is included one level deep in `reply_to`. |
| Member search | Targeted IDs use cache/REST; names use the available cache and a Gateway query by username/nickname prefix. Uncached global names and nicknames may be missed; results are not guaranteed to be exhaustive. |
| List pagination | Responses contain at most 100 items; some Discord endpoints fetch an entire collection before local pagination. |
| Archived threads | Direct ID access with REST fetching, without prior discovery; pagination supports public, private, and joined private archives. |
| Forums | Active posts through `list_forum_posts`; archives through `list_threads`. Tags must belong to the forum; an empty list removes tags. |
| Permissions | Only supplied permissions are merged; `null` means inheritance. Deleting an overwrite removes the whole overwrite. Threads inherit from their parent. |
| Moderation and roles | Optional audit reasons; Discord enforces permissions and role hierarchy. Message deletion during a ban defaults to zero and is capped at seven days when requested. |
| Events | Timezone-aware dates, consistent start/end times, and validated channel types. External events require a location and end time; listing subscribers requires Members intent and returns user identities. |
| Polls | A project extension using native Discord polls: creation, refreshed results, ending the bot's own polls, and voter pagination. No automated bot voting. |

This reimplementation uses discord.py's public APIs; it does not reuse the Java
code or its dependencies. The pinned catalogue documents a comparison at a given
point in time, not automatic synchronization with future upstream additions.
