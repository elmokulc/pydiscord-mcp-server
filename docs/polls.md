# Native Discord polls

`create_poll` creates a message containing a **native Discord poll**, the same
kind of object offered by **“+” → Poll** in the app. Members vote through the
usual Discord interface. The server uses `discord.Poll` and
`channel.send(poll=...)`; it does not simulate voting with reactions.

## Create a poll

Call the `create_poll` MCP tool with:

```json
{
  "channel_id": "123456789012345678",
  "question": "Which day should we meet?",
  "answers": [
    {"text": "Monday", "emoji": "📅"},
    {"text": "Tuesday", "emoji": "📅"},
    {"text": "Wednesday"}
  ],
  "duration_hours": 24,
  "allow_multiselect": false
}
```

Replace the ID with an allowed channel or thread that supports messages.
A forum cannot receive a poll directly: use the thread ID of its post.
A custom emoji can use the form `<:name:ID>` if the bot can access it.
Mentions are disabled when creating polls.

The bot needs **View Channel**, **Send Messages**, and **Send Polls**. In a thread,
also check **Send Messages in Threads** and thread access. Grant **Read Message
History** to read the poll again. Message Content intent may be required to read
poll data created by other members, subject to Discord's exceptions. Results for
the bot's own polls are available through REST without listening for Gateway
vote events.

Limits validated before sending:

| Parameter | Contract |
| --- | --- |
| `question` | 1–300 characters; cannot be whitespace-only |
| `answers` | 2–10 objects, each with `text` and optional `emoji` |
| `answers[].text` | 1–55 characters; cannot be whitespace-only |
| `duration_hours` | Integer from 1 to 768 hours (32 days); default 24 |
| `allow_multiselect` | Strict boolean; default `false` |

Durations follow the API's capabilities; they are not restricted to the few
preset durations shown in Discord's interface.

## Read and end a poll

Creation returns a `MessageInfo` containing its `id`, `channel_id`, Discord link,
and a `poll` field. Keep these IDs.

| Tool | Parameters |
| --- | --- |
| `get_poll` | `channel_id`, `message_id`; refreshes votes through REST |
| `end_poll` | `channel_id`, `message_id`; ends a poll created by this bot early |
| `get_poll_answer_voters` | `channel_id`, `message_id`, `answer_id`, `limit=25`, `after?` |

`poll` contains `question`, `answers` (numeric answer ID, text, emoji, votes),
`allow_multiselect`, `expires_at`, `finalized`, and `total_votes`. The same data is
included in `read_messages` and `get_message` when Discord supplies it. Missing
counts remain `null`, rather than being converted to zero. Counts for an ongoing
poll may be approximate; wait for `finalized=true` for the final tally. With
multiple selections enabled, the sum of votes is not the number of distinct
voters.

To list voters for an answer, use the ID returned in `answers[].id`, not an
assumed index. Pass `next_cursor` as `after` to continue listing users. User IDs
remain strings; poll answer IDs are small integers local to the poll.

Discord does not allow applications to vote or the poll message to be edited
after creation. No tool is provided for voting or editing questions/answers.
To correct a poll, create a new one and optionally delete the old one with
`delete_message`, subject to the usual checks. This bot cannot end another
author's poll.

## Live validation

The included tests use doubles only and do not publish polls. After configuring
your bot, explicitly authorize a poll to be posted in a test channel. Check its
native appearance and vote manually in Discord, then use `get_poll` to inspect
the results. Test `end_poll` only on a disposable poll created by the bot.
See [manual Discord validation](../CONTRIBUTING.md#manual-discord-validation)
for the general setup.

Official references consulted:
[Discord Poll Resource](https://docs.discord.com/developers/resources/poll),
[discord.py Poll](https://discordpy.readthedocs.io/en/stable/api.html#discord.Poll).
