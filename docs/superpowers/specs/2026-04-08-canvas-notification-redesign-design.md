# Canvas Notification Redesign

## Overview

Redesign the Canvas deploy notification system to produce cleaner Discord messages with tabulate-generated overview tables, aligned resource listings, and limit-aware formatting that prevents Discord API errors.

## Decisions

- **Approach:** Limit-aware formatting (Approach B) — formatters build content incrementally, tracking character budget via builder classes
- **Resource listings:** Plain markdown with alignment, keeping links clickable—wrap resource types in backticks for fixed-width font
- **Item display:** Every item listed fully, including quiz_question and quiz_question_order
- **Overview table counts:** Deduplicated union across both `deployed_content` and `content_to_review`
- **Content message:** Built inside `canvas_format.py` (formatter owns full message shape), role ID passed in
- **Refactor:** Extract limits/chunking into `discord_limits.py`, keep `send_notification.py` as webhook sender name

## Architecture

### New module: `notifications/discord_limits.py`

Constants:

```
TITLE_LIMIT = 256
DESCRIPTION_LIMIT = 4096
FIELD_NAME_LIMIT = 256
FIELD_VALUE_LIMIT = 1024
FIELDS_PER_EMBED = 25
FOOTER_LIMIT = 2048
AUTHOR_NAME_LIMIT = 256
EMBED_CHAR_LIMIT = 6000
MAX_EMBEDS_PER_MESSAGE = 10
CONTENT_LIMIT = 2000
```

Classes:

- **`EmbedBuilder`** — stateful builder tracking character budget
  - `__init__(title, description, color, timestamp, author, footer)` — sets base metadata, calculates initial char usage
  - `remaining_chars() -> int`
  - `can_add_field(name, value) -> bool` — checks char limit and 25-field limit
  - `add_field(name, value, inline) -> bool` — adds if fits, returns False otherwise
  - `build() -> Embed`

- **`MessageBuilder`** — manages multiple embeds per message
  - Tracks embed count against `MAX_EMBEDS_PER_MESSAGE`
  - `new_embed(...)` — starts new embed when current fills up
  - `build() -> WebhookMessage`

Functions:

- `calc_embed_size(embed: Embed) -> int` — moved from `send_notification.py`
- `split_content(content: str, max_chars: int) -> list[str]` — moved from `send_notification.py`
- `validate_notification(notification: Notification) -> list[str]` — returns limit violations

### Refactored: `notifications/send_notification.py`

Keeps only webhook-sending logic:
- `_build_discord_embed(embed_data)` — converts `Embed` dataclass to `DiscordEmbed`
- `_execute_webhook(webhook_url, notification, content, embeds)` — sends via `discord_webhook`
- `send_notification(webhook_url, notification)` — iterates messages, splits content if needed via `split_content()`, sends

Removed: all constants, `_calc_embed_size`, `_chunk_embed`, `_build_chunk`, `_split_content`.

### Rewritten: `notifications/formatting/canvas_format.py`

Three notification cases:

**Case 1: Error (red)**
- Content: `@CICD ERROR—MDXCanvas failed to deploy. View [here]({action_url})`
- Embed: title, branch in description, error in code block. No fields, no table.

**Case 2: Needs Review (yellow)**
- Content: `<@&{role_id}>—Deployed Resources to Review`
- Embed fields:
  1. Overview table (tabulate `pipe` format in code block) — resource type x count
  2. Needs Review items — `assignment\` [name](link)` per line
  3. Remaining Resources — `type\` [name](link)` per line

**Case 3: Success (green)**
- Content: None
- Embed fields:
  1. Overview table
  2. Remaining Resources

Overview table built with `tabulate(rows, headers=["Resource Type", "Count"], tablefmt="pipe")` wrapped in a code block. Count is from deduplicated union of both lists.

Resource lines packed into field values using `EmbedBuilder.can_add_field()`. When a field fills, a new field or embed is started.

`format_notification()` signature adds `cicd_role_id` parameter so the formatter can build the content message.

### Modified: `notifications/formatting/formatting_utils.py`

- Remove `chunk_field_lines()` (replaced by `EmbedBuilder`)
- Keep `get_course_style()`, `truncate_error()`

### Modified: `notifications/formatting/docker_format.py`

- Replace `chunk_field_lines` usage with `EmbedBuilder` for consistency with canvas_format

### Modified: `notifications/send_course.py`

- Pass `cicd_role_id` into `format_notification()` instead of applying it after the fact
- Remove post-hoc content message injection

### Dependency

NO PROJECT DEPENDENCIES — this is not a pypi package or anything similar just an internal module

## Test Strategy

### New: `tests/test_discord_limits.py`

**Limit validation tests** — verify every generated component respects Discord limits:
- Title ≤ 256, Description ≤ 4096, Field name ≤ 256, Field value ≤ 1024
- Fields per embed ≤ 25, Embed total chars ≤ 6000
- Embeds per message ≤ 10, Content ≤ 2000

**Integration tests** using `test-mdxcanvas-payload.json`:
- Load payload, run `format_notification()` for all 3 cases
- Run `validate_notification()` — assert zero violations
- Verify overview table row count matches distinct resource type count
- Verify all `content_to_review` items appear in needs-review fields
- Verify no item in both needs-review and remaining sections

**EmbedBuilder unit tests:**
- Refuses field when char budget exhausted
- Refuses field when 25-field limit hit
- `remaining_chars()` decreases correctly
- `build()` produces valid `Embed`

**Edge cases:**
- Empty payload — `has_content()` returns False
- Error-only payload
- Massive payload (500+ items) — still valid notifications

### Modified: `tests/test_embed_chunking.py`

- Update imports from `discord_limits`
- Replace `_chunk_embed` tests with `EmbedBuilder` tests

## File Change Summary

| File | Action |
|---|---|
| `notifications/discord_limits.py` | New |
| `notifications/send_notification.py` | Modify — remove constants/chunking |
| `notifications/formatting/canvas_format.py` | Rewrite |
| `notifications/formatting/formatting_utils.py` | Modify — remove `chunk_field_lines` |
| `notifications/formatting/docker_format.py` | Modify — update imports |
| `notifications/send_course.py` | Modify — pass role ID to formatter |
| `tests/test_discord_limits.py` | New |
| `tests/test_embed_chunking.py` | Modify — update imports/tests |

## Not Changed

- `notifications/resources.py` — dataclasses unchanged
- `notifications/formatting/plain_text_utils.py` — `status_color()` and `dedupe_remaining_content()` unchanged

## DO NOT ADD EMOJIS — we want to keep the tone professional and clear, especially for error notifications.