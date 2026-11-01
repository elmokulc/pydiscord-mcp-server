# Catalogue of 88 tools

Every tool is registered explicitly and has an input schema, a structured output
schema, and MCP annotations. The server shares one bot client. Mutating tools
remain subject to Discord permissions.

Parameter names use `snake_case`. Omitting `guild_id` selects `DISCORD_GUILD_ID`;
it is still required if no default is configured. Every Discord ID must be a
string. `limit` ranges from 1 to 100. `reason` is an optional reason recorded in
the Discord audit log.

| Tool | Required parameters | Optional parameters | Operation |
| --- | --- | --- | --- |
| `list_guilds` | — | `limit`, `after` | List allowed guilds. |
| `get_guild_info` | — | `guild_id` | Read guild metadata. |
| `get_server_info` | — | `guild_id` | Read guild metadata (equivalent to get_guild_info). |
| `list_channels` | — | `guild_id`, `limit`, `after` | List channels, excluding threads. |
| `get_channel_info` | `channel_id` | — | Read a channel or thread, including uncached archived threads. |
| `read_messages` | `channel_id` | `limit`, `before`, `after`, `around` | Read a history page with at most one boundary. |
| `get_message` | `channel_id`, `message_id` | — | Read a message and its reply reference. |
| `send_message` | `channel_id`, `content` | `reply_to_message_id`, `allow_mentions` | Send text, optionally as a reply. |
| `edit_message` | `channel_id`, `message_id`, `content` | `allow_mentions` | Edit a message owned by the bot. |
| `delete_message` | `channel_id`, `message_id` | `allow_other_author` | Delete a message; deleting another author's message requires opt-in and Manage Messages. |
| `add_reaction` | `channel_id`, `message_id`, `emoji` | — | Add a reaction as the bot. |
| `remove_reaction` | `channel_id`, `message_id`, `emoji` | `member_id` | Remove a reaction; removing someone else's requires Manage Messages. |
| `list_threads` | `channel_id` | `mode`, `limit`, `cursor` | List a parent's active or accessible archived threads. |
| `get_thread_info` | `thread_id` | — | Read thread metadata directly by ID. |
| `get_member` | `member_id` | `guild_id` | Read a member from cache, with a REST fallback. |
| `search_members` | `query` | `guild_id`, `limit` | Look up a specific ID or search names in cache and Gateway candidates. |
| `get_member_by_id` | `user_id` | `guild_id` | Read a member by stable ID (equivalent to get_member). |
| `get_user_id_by_name` | `username` | `guild_id` | Resolve an exact, unambiguous username within the available search scope. |
| `create_poll` | `channel_id`, `question`, `answers` | `duration_hours`, `allow_multiselect` | Create a native Discord poll with a question and answer options. |
| `get_poll` | `channel_id`, `message_id` | — | Refresh a poll and its counts through REST. |
| `end_poll` | `channel_id`, `message_id` | — | Close a poll created by this bot. |
| `get_poll_answer_voters` | `channel_id`, `message_id`, `answer_id` | `limit`, `after` | List users who selected a poll answer. |
| `create_text_channel` | `name` | `guild_id`, `settings`, `reason` | Create a text channel with validated settings. |
| `edit_text_channel` | `channel_id`, `settings` | `reason` | Edit the name, topic, NSFW flag, slowmode, category, or position. |
| `delete_channel` | `channel_id` | `reason` | Permanently delete a channel or thread. |
| `find_channel` | `name` | `guild_id`, `limit`, `after` | Find channels whose names match exactly, ignoring case. |
| `move_channel` | `channel_id` | `category_id`, `position`, `remove_category`, `reason` | Move a channel to a category in the same guild or change its position. |
| `create_category` | `name` | `guild_id`, `position`, `reason` | Create a category. |
| `edit_category` | `category_id`, `settings` | `reason` | Rename or reposition a category. |
| `delete_category` | `category_id` | `reason` | Delete a category while keeping its child channels. |
| `find_category` | `name` | `guild_id`, `limit`, `after` | Find categories with an exact name match. |
| `list_channels_in_category` | `category_id` | `limit`, `after` | List a category's child channels. |
| `create_voice_channel` | `name` | `guild_id`, `settings`, `reason` | Create a voice channel with limits and a region. |
| `create_stage_channel` | `name` | `guild_id`, `settings`, `reason` | Create a Stage channel. |
| `edit_voice_channel` | `channel_id`, `settings` | `reason` | Edit a voice or Stage channel. |
| `create_forum_channel` | `name` | `guild_id`, `settings`, `reason` | Create a forum with default settings. |
| `edit_forum_channel` | `channel_id`, `settings` | `reason` | Edit a forum or media channel's settings. |
| `list_forum_channels` | — | `guild_id`, `limit`, `after` | List the guild's forum and media channels. |
| `get_forum_channel_info` | `channel_id` | — | Read a forum's metadata, tags, and settings. |
| `list_forum_tags` | `channel_id` | — | List a forum's available tags. |
| `create_forum_post` | `channel_id`, `title`, `content` | `tag_ids`, `allow_mentions`, `reason` | Create a post with its first message and valid tags. |
| `list_forum_posts` | `channel_id` | `limit`, `cursor` | List active forum posts; use list_threads for archives. |
| `modify_forum_post` | `post_id`, `settings` | `reason` | Lock, archive, pin, or replace a post's tags. |
| `list_active_threads` | — | `guild_id`, `limit`, `after` | List a guild's accessible active threads. |
| `list_roles` | — | `guild_id`, `limit`, `after` | List roles and their permissions. |
| `create_role` | `name` | `guild_id`, `settings`, `reason` | Create a role with permissions, a color, and other settings. |
| `edit_role` | `role_id`, `settings` | `guild_id`, `reason` | Edit a role's properties or position. |
| `delete_role` | `role_id` | `guild_id`, `reason` | Permanently delete a role. |
| `assign_role` | `member_id`, `role_id` | `guild_id`, `reason` | Add a role without replacing the member's other roles. |
| `remove_role` | `member_id`, `role_id` | `guild_id`, `reason` | Remove a role without replacing the member's other roles. |
| `kick_member` | `member_id` | `guild_id`, `reason` | Remove a member from the guild. |
| `ban_member` | `member_id` | `guild_id`, `delete_message_seconds`, `reason` | Ban a user; optionally delete 0–7 days of messages. |
| `unban_member` | `member_id` | `guild_id`, `reason` | Lift a ban without automatically returning the user to the guild. |
| `timeout_member` | `member_id`, `duration_seconds` | `guild_id`, `reason` | Restrict communication for 1 second to 28 days. |
| `remove_timeout` | `member_id` | `guild_id`, `reason` | Lift a temporary communication restriction. |
| `set_nickname` | `member_id`, `nickname` | `guild_id`, `reason` | Change a nickname; null restores the username. |
| `get_bans` | — | `guild_id`, `limit`, `after` | List banned users and ban reasons. |
| `move_member` | `member_id`, `channel_id` | `guild_id`, `reason` | Move a member to a voice channel in the same guild. |
| `disconnect_member` | `member_id` | `guild_id`, `reason` | Disconnect a member from their voice channel. |
| `modify_voice_state` | `member_id` | `guild_id`, `mute`, `deafen`, `reason` | Apply or remove server mute/deafen. |
| `list_channel_permission_overwrites` | `channel_id` | `limit`, `after` | List explicit role or member permission overwrites. |
| `upsert_role_channel_permissions` | `channel_id`, `role_id`, `changes` | `reason` | Merge role permissions into an existing overwrite. |
| `upsert_member_channel_permissions` | `channel_id`, `member_id`, `changes` | `reason` | Merge member permissions into an existing overwrite. |
| `delete_channel_permission_overwrite` | `channel_id`, `target_id`, `target_type` | `reason` | Delete an entire overwrite to restore inheritance. |
| `create_webhook` | `channel_id`, `name` | `reason` | Create a webhook and return metadata without secrets. |
| `list_webhooks` | `channel_id` | `limit`, `after` | List a channel's webhooks without exposing tokens. |
| `delete_webhook` | `webhook_id` | `reason` | Delete a webhook after checking its guild. |
| `send_webhook_message` | `webhook_id`, `content` | `allow_mentions`, `thread_id` | Send through an authorized webhook, optionally into one of its threads. |
| `create_invite` | `channel_id` | `max_age`, `max_uses`, `temporary`, `unique`, `reason` | Create an invite with bounded lifetime and usage limits. |
| `list_invites` | — | `guild_id`, `limit`, `after` | List guild invites with statistics. |
| `delete_invite` | `code` | `reason` | Revoke an invite after checking its guild. |
| `get_invite_details` | `code` | — | Read a public invite while enforcing the guild allowlist. |
| `list_emojis` | — | `guild_id`, `limit`, `after` | List the guild's custom emojis. |
| `get_emoji_details` | `emoji_id` | `guild_id` | Read a custom emoji from cache, with a REST fallback. |
| `create_emoji` | `name`, `image_base64` | `guild_id`, `role_ids`, `reason` | Upload an emoji from a base64 image of up to 256 KiB. |
| `edit_emoji` | `emoji_id` | `guild_id`, `name`, `role_ids`, `reason` | Rename an emoji or replace its role restrictions. |
| `delete_emoji` | `emoji_id` | `guild_id`, `reason` | Permanently delete a custom emoji. |
| `create_guild_scheduled_event` | `name`, `start_time`, `entity_type` | `guild_id`, `channel_id`, `end_time`, `location`, `description`, `reason` | Create a voice, Stage, or external event with consistent dates and location. |
| `edit_guild_scheduled_event` | `event_id`, `settings` | `guild_id`, `reason` | Edit an event's details or status. |
| `delete_guild_scheduled_event` | `event_id` | `guild_id`, `reason` | Permanently delete an event. |
| `list_guild_scheduled_events` | — | `guild_id`, `with_user_count`, `limit`, `after` | List the guild's scheduled and active events. |
| `get_guild_scheduled_event_users` | `event_id` | `guild_id`, `limit`, `after` | List interested users; requires Members intent. |
| `search_messages` | `channel_id`, `query` | `limit`, `scan_limit`, `before` | Search text in up to 1000 messages from one channel or thread. |
| `get_message_replies` | `channel_id`, `message_id` | `limit`, `scan_limit`, `after` | Find explicit replies in up to 1000 later messages. |
| `send_private_message` | `user_id`, `content` | `guild_id`, `reply_to_message_id`, `allow_mentions` | Send a DM after opt-in and a REST membership check for the shared guild. |
| `read_private_messages` | `user_id` | `guild_id`, `limit`, `before`, `after`, `around` | Read the bot's DM history after opt-in and authorization. |
| `edit_private_message` | `user_id`, `message_id`, `content` | `guild_id`, `allow_mentions` | Edit a DM sent by this bot. |
| `delete_private_message` | `user_id`, `message_id` | `guild_id` | Delete a DM sent by this bot. |

## Edit objects

`settings` objects reject unknown fields. Omitting a field preserves its value.
The exceptions below describe explicit resets.

| Object | Fields |
| --- | --- |
| Text channel | `name`, `topic` (up to 1024 characters), `nsfw`, `slowmode_delay` (0–21600 s), `category_id` (null removes the category), `position` |
| Category | `name`, `position` |
| Voice / Stage | `name`, `bitrate` (8000–384000, also limited by Discord), `user_limit` (0–99), `rtc_region` (null = automatic), `category_id`, `position` |
| Forum | `name`, `topic` (up to 4096 characters), `nsfw`, `slowmode_delay`, `default_thread_slowmode_delay`, `category_id`, `position`, `default_sort_order` (`latest_activity`/`creation_date`), `default_layout` (`not_set`/`list_view`/`gallery_view`) |
| Forum post | `locked`, `archived`, `pinned`, `tag_ids` (0–5 IDs from the forum; [] clears the tags) |
| Role | `name`, `permissions` (decimal bitset as a string), `colour` (RGB integer 0–16777215), `hoist`, `mentionable`, `position` (editing only) |
| Event | `name`, `description`, `start_time`, `end_time`, `location` (external), `status` (`scheduled`/`active`/`completed`/`cancelled`) |

Permission overwrites use `changes={"permissions":{"send_messages":false}}`:
`true` allows, `false` denies, and `null` restores inheritance for that field.
Other overwrite fields are preserved. Valid names come from `discord.Permissions`;
discord.py may return their canonical names, such as `read_messages` for the
`view_channel` alias. Threads inherit their parent's permissions and do not have
independent overwrites.

## Pagination, scope, and effects

- Lists sorted by ID generally use `after=next_cursor`; invites use their code in
  `after`. Tag lists are bounded by Discord and do not need a cursor.
- `list_threads` and `list_forum_posts` use an opaque `cursor`; keep the same parent
  and mode. `list_forum_posts` covers active posts; use
  `list_threads(mode="archived_public")` for archived forum posts.
- History accepts at most one of `before`, `after`, or `around`. The
  `cursor_parameter` field identifies the direction to reuse; `around` provides no
  continuation. Searches are limited to 1000 messages per call.
- Channel, role, and emoji lists and member searches may read from cache. Some
  Discord endpoints return a full collection before local pagination; the MCP
  response size remains bounded.
- `allow_mentions=false` is the default everywhere, including replies, forums,
  DMs, and webhooks. Explicitly enabling it allows all mention categories.
- State changes depend on Discord permissions and role hierarchy, even when their
  MCP annotation describes them as idempotent.
- Private tools require `DISCORD_ENABLE_DMS=true`, an allowed selected guild, and a
  REST check of the recipient's current membership in that guild.
- Webhook tokens never appear in results; sending uses a webhook ID resolved by
  the bot account. Emoji images are supplied as base64; the server does not
  download arbitrary URLs.

See [native polls](polls.md), [reference compatibility](parity.md),
[permissions and intents](../README.md#discord-bot-setup), and
[the tool development guide](adding-tools.md).
