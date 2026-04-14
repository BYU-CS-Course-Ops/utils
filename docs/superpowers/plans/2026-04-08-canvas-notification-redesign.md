# Canvas Notification Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign Canvas deploy notifications with tabulate overview tables, limit-aware formatting via builder classes, and no emojis.

**Architecture:** Extract Discord limit constants and builders into `notifications/discord_limits.py`. Formatters build notifications incrementally using `EmbedBuilder`/`MessageBuilder` to respect character budgets. `send_notification.py` becomes a thin webhook sender.

**Tech Stack:** Python, tabulate (already installed), discord-webhook, pytest

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `notifications/discord_limits.py` | Create | Constants, `EmbedBuilder`, `MessageBuilder`, `validate_notification`, `calc_embed_size`, `split_content` |
| `notifications/send_notification.py` | Modify | Thin webhook sender only — imports limits from `discord_limits` |
| `notifications/formatting/canvas_format.py` | Rewrite | Three-case notification formatter with tabulate overview table |
| `notifications/formatting/formatting_utils.py` | Modify | Remove `chunk_field_lines` and `emoji_for`, keep `get_course_style`, `truncate_error` |
| `notifications/formatting/docker_format.py` | Modify | Use `EmbedBuilder` instead of `chunk_field_lines` |
| `notifications/send_course.py` | Modify | Pass `cicd_role_id` to formatter, remove post-hoc content injection |
| `tests/test_discord_limits.py` | Create | Builder unit tests + limit validation tests |
| `tests/test_embed_chunking.py` | Modify | Update imports, replace `_chunk_embed` tests with builder tests |
| `tests/test_course_text_formatters.py` | Modify | Update canvas tests for new format/signature, fix docker tests |

---

### Task 1: Create `discord_limits.py` — constants and moved functions

**Files:**
- Create: `notifications/discord_limits.py`
- Test: `tests/test_discord_limits.py`

- [ ] **Step 1: Write failing tests for constants and `calc_embed_size`**

Create `tests/test_discord_limits.py`:

```python
from notifications.discord_limits import (
    TITLE_LIMIT,
    DESCRIPTION_LIMIT,
    FIELD_NAME_LIMIT,
    FIELD_VALUE_LIMIT,
    FIELDS_PER_EMBED,
    FOOTER_LIMIT,
    AUTHOR_NAME_LIMIT,
    EMBED_CHAR_LIMIT,
    MAX_EMBEDS_PER_MESSAGE,
    CONTENT_LIMIT,
    calc_embed_size,
    split_content,
)
from notifications.resources import Author, Embed, Field, Footer


class TestConstants:
    def test_embed_char_limit(self):
        assert EMBED_CHAR_LIMIT == 6000

    def test_field_value_limit(self):
        assert FIELD_VALUE_LIMIT == 1024

    def test_fields_per_embed(self):
        assert FIELDS_PER_EMBED == 25

    def test_content_limit(self):
        assert CONTENT_LIMIT == 2000

    def test_max_embeds_per_message(self):
        assert MAX_EMBEDS_PER_MESSAGE == 10


class TestCalcEmbedSize:
    def test_basic_size(self):
        embed = Embed(
            title="Hello",
            description="World",
            color=0xFF0000,
            fields=[Field(name="key", value="val")],
            timestamp="2025-01-01T00:00:00Z",
        )
        assert calc_embed_size(embed) == len("Hello") + len("World") + len("key") + len("val")

    def test_includes_footer_and_author(self):
        embed = Embed(
            title="T",
            description="D",
            color=0,
            fields=[],
            timestamp="",
            author=Author(name="AuthorName"),
            footer=Footer(text="FooterText"),
        )
        assert calc_embed_size(embed) == len("T") + len("D") + len("AuthorName") + len("FooterText")

    def test_empty_embed(self):
        embed = Embed(
            title="",
            description="",
            color=0,
            fields=[],
            timestamp="",
        )
        assert calc_embed_size(embed) == 0


class TestSplitContent:
    def test_short_content_unchanged(self):
        result = split_content("hello", 2000)
        assert result == ["hello"]

    def test_long_content_splits_on_paragraphs(self):
        paragraphs = ["paragraph " + str(i) for i in range(200)]
        content = "\n\n".join(paragraphs)
        result = split_content(content, 100)
        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= 100
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_discord_limits.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'notifications.discord_limits'`

- [ ] **Step 3: Create `discord_limits.py` with constants and functions**

Create `notifications/discord_limits.py`:

```python
from __future__ import annotations

from .resources import Embed

# ── Discord API limits ──────────────────────────────────────────────────────
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


def calc_embed_size(embed: Embed) -> int:
    size = 0
    size += len(embed.title or "")
    size += len(embed.description or "")
    if embed.author:
        size += len(embed.author.name or "")
    if embed.footer:
        size += len(embed.footer.text or "")
    for field in embed.fields:
        size += len(field.name or "")
        size += len(field.value or "")
    return size


def split_content(content: str, max_chars: int = CONTENT_LIMIT) -> list[str]:
    if len(content) <= max_chars:
        return [content]

    paragraphs = content.split("\n\n")
    chunks: list[str] = []
    current_parts: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        needed = len(paragraph) + (2 if current_parts else 0)
        if current_parts and current_length + needed > max_chars:
            chunks.append("\n\n".join(current_parts))
            current_parts = [paragraph]
            current_length = len(paragraph)
            continue
        current_parts.append(paragraph)
        current_length += needed

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return chunks
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_discord_limits.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add notifications/discord_limits.py tests/test_discord_limits.py
git commit -m "Add discord_limits module with constants, calc_embed_size, split_content"
```

---

### Task 2: Add `EmbedBuilder` to `discord_limits.py`

**Files:**
- Modify: `notifications/discord_limits.py`
- Modify: `tests/test_discord_limits.py`

- [ ] **Step 1: Write failing tests for `EmbedBuilder`**

Append to `tests/test_discord_limits.py`:

```python
from notifications.discord_limits import EmbedBuilder


class TestEmbedBuilder:
    def test_build_produces_embed(self):
        b = EmbedBuilder(
            title="Title",
            description="Desc",
            color=0xFF0000,
            timestamp="2025-01-01T00:00:00Z",
            author=Author(name="Bot"),
            footer=Footer(text="Footer"),
        )
        embed = b.build()
        assert embed.title == "Title"
        assert embed.description == "Desc"
        assert embed.color == 0xFF0000
        assert embed.author.name == "Bot"
        assert embed.footer.text == "Footer"
        assert embed.fields == []

    def test_add_field_success(self):
        b = EmbedBuilder(
            title="T", description="D", color=0, timestamp="",
        )
        result = b.add_field("Name", "Value", inline=False)
        assert result is True
        embed = b.build()
        assert len(embed.fields) == 1
        assert embed.fields[0].name == "Name"
        assert embed.fields[0].value == "Value"

    def test_can_add_field_checks_char_limit(self):
        b = EmbedBuilder(
            title="x" * 5000, description="", color=0, timestamp="",
        )
        # Only ~1000 chars left, try to add 1500-char field
        assert b.can_add_field("name", "x" * 1500) is False

    def test_can_add_field_checks_field_count(self):
        b = EmbedBuilder(
            title="T", description="D", color=0, timestamp="",
        )
        for i in range(25):
            b.add_field(f"f{i}", "v")
        assert b.can_add_field("f25", "v") is False

    def test_add_field_returns_false_when_full(self):
        b = EmbedBuilder(
            title="x" * 5900, description="", color=0, timestamp="",
        )
        result = b.add_field("name", "x" * 500)
        assert result is False
        assert len(b.build().fields) == 0

    def test_remaining_chars_decreases(self):
        b = EmbedBuilder(
            title="Hello", description="World", color=0, timestamp="",
        )
        initial = b.remaining_chars()
        b.add_field("Key", "Value")
        assert b.remaining_chars() == initial - len("Key") - len("Value")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_discord_limits.py::TestEmbedBuilder -v`
Expected: FAIL — `ImportError: cannot import name 'EmbedBuilder'`

- [ ] **Step 3: Implement `EmbedBuilder`**

Add to `notifications/discord_limits.py`:

```python
from .resources import Author, Embed, Field, Footer


class EmbedBuilder:
    def __init__(
        self,
        title: str,
        description: str,
        color: int,
        timestamp: str,
        author: Author | None = None,
        footer: Footer | None = None,
    ):
        self._title = title
        self._description = description
        self._color = color
        self._timestamp = timestamp
        self._author = author
        self._footer = footer
        self._fields: list[Field] = []

        self._base_size = len(title or "") + len(description or "")
        if author:
            self._base_size += len(author.name or "")
        if footer:
            self._base_size += len(footer.text or "")
        self._fields_size = 0

    def remaining_chars(self) -> int:
        return EMBED_CHAR_LIMIT - self._base_size - self._fields_size

    def can_add_field(self, name: str, value: str) -> bool:
        if len(self._fields) >= FIELDS_PER_EMBED:
            return False
        field_size = len(name or "") + len(value or "")
        return self._fields_size + field_size <= self.remaining_chars()

    def add_field(self, name: str, value: str, inline: bool = False) -> bool:
        if not self.can_add_field(name, value):
            return False
        self._fields.append(Field(name=name, value=value, inline=inline))
        self._fields_size += len(name or "") + len(value or "")
        return True

    def build(self) -> Embed:
        return Embed(
            title=self._title,
            description=self._description,
            color=self._color,
            fields=list(self._fields),
            timestamp=self._timestamp,
            author=self._author,
            footer=self._footer,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_discord_limits.py::TestEmbedBuilder -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add notifications/discord_limits.py tests/test_discord_limits.py
git commit -m "Add EmbedBuilder with char budget and field count tracking"
```

---

### Task 3: Add `MessageBuilder` to `discord_limits.py`

**Files:**
- Modify: `notifications/discord_limits.py`
- Modify: `tests/test_discord_limits.py`

- [ ] **Step 1: Write failing tests for `MessageBuilder`**

Append to `tests/test_discord_limits.py`:

```python
from notifications.discord_limits import MessageBuilder


class TestMessageBuilder:
    def test_build_single_embed_message(self):
        mb = MessageBuilder(color=0xFF0000, timestamp="2025-01-01T00:00:00Z")
        eb = mb.new_embed(title="Title", description="Desc")
        eb.add_field("Key", "Value")
        message = mb.build()
        assert len(message.embeds) == 1
        assert message.embeds[0].title == "Title"

    def test_new_embed_creates_continuation(self):
        mb = MessageBuilder(color=0xFF0000, timestamp="2025-01-01T00:00:00Z")
        mb.new_embed(title="First", description="Desc")
        mb.new_embed(title="Second", description="")
        message = mb.build()
        assert len(message.embeds) == 2

    def test_set_content(self):
        mb = MessageBuilder(color=0, timestamp="")
        mb.set_content("hello world")
        mb.new_embed(title="T", description="D")
        message = mb.build()
        assert message.content == "hello world"

    def test_current_embed_returns_active_builder(self):
        mb = MessageBuilder(color=0, timestamp="")
        eb = mb.new_embed(title="T", description="D")
        assert mb.current_embed is eb
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_discord_limits.py::TestMessageBuilder -v`
Expected: FAIL — `ImportError: cannot import name 'MessageBuilder'`

- [ ] **Step 3: Implement `MessageBuilder`**

Add to `notifications/discord_limits.py`:

```python
from .resources import WebhookMessage


class MessageBuilder:
    def __init__(self, color: int, timestamp: str):
        self._color = color
        self._timestamp = timestamp
        self._content: str | None = None
        self._embeds: list[EmbedBuilder] = []

    def set_content(self, content: str):
        self._content = content

    @property
    def current_embed(self) -> EmbedBuilder | None:
        return self._embeds[-1] if self._embeds else None

    def new_embed(
        self,
        title: str,
        description: str,
        author: Author | None = None,
        footer: Footer | None = None,
    ) -> EmbedBuilder:
        eb = EmbedBuilder(
            title=title,
            description=description,
            color=self._color,
            timestamp=self._timestamp,
            author=author,
            footer=footer,
        )
        self._embeds.append(eb)
        return eb

    def build(self) -> WebhookMessage:
        return WebhookMessage(
            content=self._content,
            embeds=[eb.build() for eb in self._embeds],
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_discord_limits.py::TestMessageBuilder -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add notifications/discord_limits.py tests/test_discord_limits.py
git commit -m "Add MessageBuilder for multi-embed message construction"
```

---

### Task 4: Add `validate_notification` to `discord_limits.py`

**Files:**
- Modify: `notifications/discord_limits.py`
- Modify: `tests/test_discord_limits.py`

- [ ] **Step 1: Write failing tests for `validate_notification`**

Append to `tests/test_discord_limits.py`:

```python
from notifications.discord_limits import validate_notification
from notifications.resources import Notification, WebhookMessage


class TestValidateNotification:
    def test_valid_notification_returns_empty(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    content=None,
                    embeds=[
                        Embed(
                            title="Title",
                            description="Desc",
                            color=0,
                            fields=[Field(name="k", value="v")],
                            timestamp="",
                        )
                    ],
                )
            ],
        )
        assert validate_notification(notification) == []

    def test_title_too_long(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    embeds=[
                        Embed(
                            title="x" * 257,
                            description="",
                            color=0,
                            fields=[],
                            timestamp="",
                        )
                    ],
                )
            ],
        )
        violations = validate_notification(notification)
        assert any("title" in v.lower() for v in violations)

    def test_field_value_too_long(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    embeds=[
                        Embed(
                            title="T",
                            description="",
                            color=0,
                            fields=[Field(name="k", value="x" * 1025)],
                            timestamp="",
                        )
                    ],
                )
            ],
        )
        violations = validate_notification(notification)
        assert any("field value" in v.lower() for v in violations)

    def test_too_many_fields(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    embeds=[
                        Embed(
                            title="T",
                            description="",
                            color=0,
                            fields=[Field(name="k", value="v") for _ in range(26)],
                            timestamp="",
                        )
                    ],
                )
            ],
        )
        violations = validate_notification(notification)
        assert any("field count" in v.lower() for v in violations)

    def test_embed_total_chars_too_large(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    embeds=[
                        Embed(
                            title="x" * 256,
                            description="x" * 4096,
                            color=0,
                            fields=[Field(name="k", value="x" * 1024) for _ in range(3)],
                            timestamp="",
                        )
                    ],
                )
            ],
        )
        violations = validate_notification(notification)
        assert any("embed char" in v.lower() for v in violations)

    def test_content_too_long(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    content="x" * 2001,
                    embeds=[],
                )
            ],
        )
        violations = validate_notification(notification)
        assert any("content" in v.lower() for v in violations)

    def test_too_many_embeds(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    embeds=[
                        Embed(title="T", description="", color=0, fields=[], timestamp="")
                        for _ in range(11)
                    ],
                )
            ],
        )
        violations = validate_notification(notification)
        assert any("embed count" in v.lower() for v in violations)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_discord_limits.py::TestValidateNotification -v`
Expected: FAIL — `ImportError: cannot import name 'validate_notification'`

- [ ] **Step 3: Implement `validate_notification`**

Add to `notifications/discord_limits.py`:

```python
from .resources import Notification


def validate_notification(notification: Notification) -> list[str]:
    violations: list[str] = []

    for msg_idx, message in enumerate(notification.messages):
        prefix = f"Message {msg_idx}"

        if message.content and len(message.content) > CONTENT_LIMIT:
            violations.append(
                f"{prefix}: Content length {len(message.content)} exceeds {CONTENT_LIMIT}"
            )

        if len(message.embeds) > MAX_EMBEDS_PER_MESSAGE:
            violations.append(
                f"{prefix}: Embed count {len(message.embeds)} exceeds {MAX_EMBEDS_PER_MESSAGE}"
            )

        for emb_idx, embed in enumerate(message.embeds):
            ep = f"{prefix}, Embed {emb_idx}"

            if embed.title and len(embed.title) > TITLE_LIMIT:
                violations.append(
                    f"{ep}: Title length {len(embed.title)} exceeds {TITLE_LIMIT}"
                )

            if embed.description and len(embed.description) > DESCRIPTION_LIMIT:
                violations.append(
                    f"{ep}: Description length {len(embed.description)} exceeds {DESCRIPTION_LIMIT}"
                )

            if embed.footer and len(embed.footer.text or "") > FOOTER_LIMIT:
                violations.append(
                    f"{ep}: Footer length {len(embed.footer.text)} exceeds {FOOTER_LIMIT}"
                )

            if embed.author and len(embed.author.name or "") > AUTHOR_NAME_LIMIT:
                violations.append(
                    f"{ep}: Author name length {len(embed.author.name)} exceeds {AUTHOR_NAME_LIMIT}"
                )

            if len(embed.fields) > FIELDS_PER_EMBED:
                violations.append(
                    f"{ep}: Field count {len(embed.fields)} exceeds {FIELDS_PER_EMBED}"
                )

            for fld_idx, field in enumerate(embed.fields):
                if field.name and len(field.name) > FIELD_NAME_LIMIT:
                    violations.append(
                        f"{ep}, Field {fld_idx}: Field name length {len(field.name)} exceeds {FIELD_NAME_LIMIT}"
                    )
                if field.value and len(field.value) > FIELD_VALUE_LIMIT:
                    violations.append(
                        f"{ep}, Field {fld_idx}: Field value length {len(field.value)} exceeds {FIELD_VALUE_LIMIT}"
                    )

            total = calc_embed_size(embed)
            if total > EMBED_CHAR_LIMIT:
                violations.append(
                    f"{ep}: Embed char total {total} exceeds {EMBED_CHAR_LIMIT}"
                )

    return violations
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_discord_limits.py::TestValidateNotification -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add notifications/discord_limits.py tests/test_discord_limits.py
git commit -m "Add validate_notification for post-build limit checking"
```

---

### Task 5: Refactor `send_notification.py` and update `test_embed_chunking.py`

**Files:**
- Modify: `notifications/send_notification.py`
- Modify: `tests/test_embed_chunking.py`

- [ ] **Step 1: Rewrite `send_notification.py` as thin sender**

Replace the contents of `notifications/send_notification.py` with:

```python
from discord_webhook import DiscordWebhook, DiscordEmbed

from .discord_limits import CONTENT_LIMIT, split_content
from .resources import Embed, Notification


def _build_discord_embed(embed_data: Embed) -> DiscordEmbed:
    embed = DiscordEmbed(
        title=embed_data.title,
        description=embed_data.description,
        color=embed_data.color,
        timestamp=embed_data.timestamp or None,
    )

    if embed_data.author:
        embed.set_author(
            name=embed_data.author.name,
            icon_url=embed_data.author.icon_url,
        )

    if embed_data.footer:
        embed.set_footer(
            text=embed_data.footer.text,
            icon_url=embed_data.footer.icon_url,
        )

    for field in embed_data.fields:
        embed.add_embed_field(
            name=field.name or "\u200b",
            value=field.value or "\u200b",
            inline=field.inline,
        )

    return embed


def _execute_webhook(webhook_url: str, notification: Notification, content: str | None = None, embeds: list[Embed] | None = None):
    webhook = DiscordWebhook(
        url=webhook_url,
        username=notification.username,
        avatar_url=notification.avatar_url,
        content=content,
    )

    for embed_data in embeds or []:
        webhook.add_embed(_build_discord_embed(embed_data))

    return webhook.execute()


def send_notification(webhook_url: str, notification: Notification):
    for message in notification.messages:
        content_chunks = split_content(message.content, CONTENT_LIMIT) if message.content else [None]

        for index, content in enumerate(content_chunks):
            try:
                response = _execute_webhook(
                    webhook_url=webhook_url,
                    notification=notification,
                    content=content,
                    embeds=message.embeds if index == 0 else [],
                )
            except Exception as e:
                print(f"Error sending notification: {e}")
                continue

            if response.status_code >= 400:
                print(f"Discord returned status {response.status_code}: {response.text}")
            else:
                print("Sent message successfully.")
```

- [ ] **Step 2: Rewrite `test_embed_chunking.py` to test builders instead**

Replace `tests/test_embed_chunking.py` with:

```python
from notifications.discord_limits import (
    EMBED_CHAR_LIMIT,
    FIELDS_PER_EMBED,
    EmbedBuilder,
    calc_embed_size,
)
from notifications.resources import Author, Embed, Field, Footer


class TestCalcEmbedSize:
    def test_basic_size(self):
        embed = Embed(
            title="Hello",
            description="World",
            color=0xFF0000,
            fields=[Field(name="key", value="val")],
            timestamp="2025-01-01T00:00:00Z",
        )
        assert calc_embed_size(embed) == len("Hello") + len("World") + len("key") + len("val")

    def test_includes_footer_and_author(self):
        embed = Embed(
            title="T",
            description="D",
            color=0,
            fields=[],
            timestamp="",
            author=Author(name="AuthorName"),
            footer=Footer(text="FooterText"),
        )
        assert calc_embed_size(embed) == len("T") + len("D") + len("AuthorName") + len("FooterText")

    def test_empty_embed(self):
        embed = Embed(
            title="",
            description="",
            color=0,
            fields=[],
            timestamp="",
        )
        assert calc_embed_size(embed) == 0

    def test_spacer_fields(self):
        embed = Embed(
            title="",
            description="",
            color=0,
            fields=[Field(name="\u200b", value="\u200b")],
            timestamp="",
        )
        assert calc_embed_size(embed) == 2


class TestEmbedBuilderLimits:
    def test_builder_never_exceeds_embed_char_limit(self):
        b = EmbedBuilder(
            title="Title",
            description="Description text",
            color=0,
            timestamp="",
            author=Author(name="Bot"),
            footer=Footer(text="Footer"),
        )
        added = 0
        for i in range(100):
            if not b.add_field(f"field-{i}", "x" * 500):
                break
            added += 1
        embed = b.build()
        assert calc_embed_size(embed) <= EMBED_CHAR_LIMIT
        assert added > 0

    def test_builder_respects_field_count_limit(self):
        b = EmbedBuilder(title="T", description="D", color=0, timestamp="")
        for i in range(30):
            b.add_field(f"f{i}", "v")
        embed = b.build()
        assert len(embed.fields) <= FIELDS_PER_EMBED

    def test_all_fields_preserved_when_within_limits(self):
        b = EmbedBuilder(title="T", description="D", color=0, timestamp="")
        for i in range(10):
            b.add_field(f"f{i}", f"v{i}")
        embed = b.build()
        assert len(embed.fields) == 10

    def test_typical_pypi_embed_stays_small(self):
        b = EmbedBuilder(
            title="PyPI Update",
            description="A new version has been published.",
            color=0x3B82F6,
            timestamp="2025-01-01T00:00:00Z",
            author=Author(name="PyPI Bot"),
            footer=Footer(text="BeanLab Dev Utils"),
        )
        b.add_field("Package", "my-package")
        b.add_field("Version", "1.2.3")
        b.add_field("Status", "Published")
        embed = b.build()
        assert calc_embed_size(embed) < EMBED_CHAR_LIMIT
```

- [ ] **Step 3: Run all tests**

Run: `python -m pytest tests/test_embed_chunking.py tests/test_discord_limits.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add notifications/send_notification.py tests/test_embed_chunking.py
git commit -m "Refactor send_notification to thin sender, update chunking tests for builders"
```

---

### Task 6: Clean up `formatting_utils.py`

**Files:**
- Modify: `notifications/formatting/formatting_utils.py`

- [ ] **Step 1: Remove `chunk_field_lines`, `emoji_for`, `RESOURCE_EMOJI`, and `MAX_FIELD_CHARS`**

The file should become:

```python
from markdowndata import load
from pathlib import Path


STYLE_PATH = Path(__file__).parent / "style.md"


def hex_to_int(hex_color: str) -> int:
    return int(hex_color.lstrip('#'), 16)


def _load_styles():
    with open(STYLE_PATH) as f:
        return load(f)


def get_course_style(ntype: str) -> dict[str, str]:
    styles = _load_styles()
    for row in styles.get("Course", []):
        if row.get("type") == ntype:
            return row
    return {}


def get_pypi_style(ntype: str) -> dict[str, str]:
    styles = _load_styles()
    for row in styles.get("PyPi Packages", []):
        if row.get("type") == ntype:
            return row
    return {}


def truncate_error(error: str, max_chars: int = 900) -> str:
    if not error:
        return "```\nNo error output available.\n```"

    lines = error.splitlines()

    traceback_indices = [
        i for i, line in enumerate(lines)
        if line.strip().startswith("Traceback (most recent call last):")
    ]

    if traceback_indices:
        tb_start = traceback_indices[-1]
        relevant = lines[tb_start:]

        MAX_LINES = 12
        if len(relevant) > MAX_LINES:
            relevant = ["... (traceback truncated) ..."] + relevant[-MAX_LINES:]

        message = "\n".join(relevant)
    else:
        message = "\n".join(lines[-15:])

    if len(message) > max_chars:
        message = message[-max_chars:]
        message = "... (truncated) ...\n" + message

    return f"```\n{message}\n```"
```

- [ ] **Step 2: Run existing tests to verify nothing breaks**

Run: `python -m pytest tests/ -v --ignore=tests/test_course_text_formatters.py`
Expected: PASS (formatter tests will be updated later since they test the old format)

- [ ] **Step 3: Commit**

```bash
git add notifications/formatting/formatting_utils.py
git commit -m "Remove chunk_field_lines and emoji_for from formatting_utils"
```

---

### Task 7: Rewrite `canvas_format.py`

**Files:**
- Rewrite: `notifications/formatting/canvas_format.py`

- [ ] **Step 1: Write the new canvas formatter**

Replace `notifications/formatting/canvas_format.py` with:

```python
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from tabulate import tabulate

from notifications.discord_limits import EmbedBuilder, MessageBuilder
from notifications.formatting.formatting_utils import get_course_style, truncate_error
from notifications.formatting.plain_text_utils import (
    dedupe_remaining_content,
    status_color,
)
from notifications.resources import Author, Footer, Notification


def has_content(data) -> bool:
    return bool(
        data["deployed_content"]
        or data["content_to_review"]
        or data["error"]
    )


def requires_review(data) -> bool:
    return bool(data["content_to_review"] or data["error"])


def _build_overview_table(deployed_content: list, content_to_review: list) -> str:
    """Build a tabulate overview table counting distinct items by resource type."""
    seen: set[str] = set()
    type_counts: Counter = Counter()

    for content_type, name, *_ in deployed_content:
        if name not in seen:
            seen.add(name)
            type_counts[content_type] += 1

    for name, *_ in content_to_review:
        if name not in seen:
            seen.add(name)
            type_counts["assignment"] += 1

    rows = sorted(type_counts.items(), key=lambda r: (-r[1], r[0]))
    table = tabulate(rows, headers=["Resource Type", "Count"], tablefmt="pipe")
    return f"```\n{table}\n```"


def _format_item(resource_type: str, name: str, link: str | None) -> str:
    label = f"`{resource_type}`"
    if link:
        return f"{label} [{name}]({link})"
    return f"{label} {name}"


def _add_items_to_builder(
    builder: EmbedBuilder,
    message_builder: MessageBuilder,
    header: str,
    lines: list[str],
    author: Author | None,
    footer: Footer | None,
    continuation_title: str,
):
    """Pack item lines into fields, starting new embeds as needed."""
    current_lines: list[str] = []
    current_len = 0
    is_first_field = True

    def flush_field():
        nonlocal current_lines, current_len, is_first_field, builder
        if not current_lines:
            return
        value = "\n".join(current_lines)
        name = header if is_first_field else "\u200b"

        if not builder.can_add_field(name, value):
            builder = message_builder.new_embed(
                title=continuation_title,
                description="",
                footer=footer,
            )

        builder.add_field(name, value, inline=False)
        is_first_field = False
        current_lines = []
        current_len = 0

    for line in lines:
        needed = len(line) + (1 if current_lines else 0)
        test_value = "\n".join(current_lines + [line])
        test_name = header if is_first_field else "\u200b"

        if current_lines and not builder.can_add_field(test_name, test_value):
            flush_field()

        current_lines.append(line)
        current_len += needed

    flush_field()
    return builder


def format_notification(
    data,
    course_id,
    course_name,
    course_url,
    author,
    author_icon,
    branch,
    action_url,
    cicd_role_id=None,
) -> Notification:
    style = get_course_style("canvas")
    timestamp = datetime.now(timezone.utc).isoformat()
    footer = Footer(text=style["footer_text"], icon_url=style["footer_icon_url"])
    author_obj = Author(name=author, icon_url=author_icon)

    # ── Title ────────────────────────────────────────────────────────────
    if data["error"]:
        title = f"CS {course_id} | {course_name} -- Deploy failed"
    elif data["content_to_review"]:
        title = f"CS {course_id} | {course_name} -- Deploy complete -- items need review"
    else:
        title = f"CS {course_id} | {course_name} -- Deploy complete"

    continuation_title = f"{title} (continued)"

    # ── Color ────────────────────────────────────────────────────────────
    color = status_color(
        has_error=bool(data["error"]),
        needs_review=requires_review(data),
    )

    # ── Content message ──────────────────────────────────────────────────
    content = None
    if data["error"] and cicd_role_id:
        content = f"<@&{cicd_role_id}> ERROR -- MDXCanvas failed to deploy. View [here]({action_url})"
    elif data["content_to_review"] and cicd_role_id:
        content = f"<@&{cicd_role_id}> -- Deployed Resources to Review"

    # ── Description ──────────────────────────────────────────────────────
    description = f"**Branch:** `{branch}`"

    if data["error"]:
        truncated = truncate_error(data["error"])
        description += f"\n\n**Error:**\n{truncated}"

    # ── Build message ────────────────────────────────────────────────────
    mb = MessageBuilder(color=color, timestamp=timestamp)
    if content:
        mb.set_content(content)

    eb = mb.new_embed(
        title=title,
        description=description,
        author=author_obj,
        footer=footer,
    )

    # Error case: no fields, just the error in description
    if data["error"]:
        return Notification(
            username=style["username"],
            avatar_url=style["avatar_url"],
            messages=[mb.build()],
        )

    # ── Overview table ───────────────────────────────────────────────────
    if data["deployed_content"] or data["content_to_review"]:
        table = _build_overview_table(data["deployed_content"], data["content_to_review"])
        eb.add_field("Over View:", table, inline=False)

    # ── Needs review items ───────────────────────────────────────────────
    if data["content_to_review"]:
        lines = [
            _format_item("assignment", name, link)
            for name, link in data["content_to_review"]
        ]
        header = f"Needs review ({len(data['content_to_review'])})"
        eb = _add_items_to_builder(
            eb, mb, header, lines, author_obj, footer, continuation_title,
        )

    # ── Remaining resources ──────────────────────────────────────────────
    remaining = dedupe_remaining_content(
        data["deployed_content"], data["content_to_review"]
    )
    if remaining:
        lines = [
            _format_item(content_type, name, url)
            for content_type, name, url in remaining
        ]
        header = f"Remaining Resources ({len(remaining)})"
        eb = _add_items_to_builder(
            eb, mb, header, lines, author_obj, footer, continuation_title,
        )

    return Notification(
        username=style["username"],
        avatar_url=style["avatar_url"],
        messages=[mb.build()],
    )
```

- [ ] **Step 2: Smoke-test the formatter with the test payload**

Run: `python -c "
import json
from notifications.formatting.canvas_format import format_notification
from notifications.discord_limits import validate_notification

with open('tests/test-mdxcanvas-payload.json') as f:
    data = json.load(f)

n = format_notification(
    data=data, course_id='110', course_name='CS 110 Course Updates',
    course_url='https://byu.instructure.com/courses/20736',
    author='robbykap', author_icon='', branch='main',
    action_url='https://github.com/actions/runs/1',
)
violations = validate_notification(n)
print(f'Messages: {len(n.messages)}')
for msg in n.messages:
    print(f'  Embeds: {len(msg.embeds)}')
    for emb in msg.embeds:
        print(f'    Fields: {len(emb.fields)}, Title: {emb.title[:60]}')
print(f'Violations: {violations}')
"
`
Expected: No violations, at least 1 message with fields

- [ ] **Step 3: Commit**

```bash
git add notifications/formatting/canvas_format.py
git commit -m "Rewrite canvas_format with tabulate overview and limit-aware builders"
```

---

### Task 8: Update `send_course.py` and `docker_format.py`

**Files:**
- Modify: `notifications/send_course.py`
- Modify: `notifications/formatting/docker_format.py`

- [ ] **Step 1: Update `send_course.py` to pass `cicd_role_id` to formatter**

In `notifications/send_course.py`, change the `main()` function. The `format_notification` call should pass `cicd_role_id`, and remove the post-hoc content injection:

Replace lines 32-44:

```python
    notification = format_notification(
        data=data,
        course_id=course_id,
        course_name=course_name,
        course_url=course_url,
        author=author,
        author_icon=author_icon or "",
        branch=branch_name,
        action_url=action_url,
        cicd_role_id=cicd_role_id,
    )

    send_notification(webhook_url, notification)
```

(Remove the `if requires_review(data) and cicd_role_id...` block entirely.)

- [ ] **Step 2: Update `docker_format.py` to use `EmbedBuilder` and accept `cicd_role_id`**

Replace `notifications/formatting/docker_format.py` with:

```python
from datetime import datetime, timezone

from notifications.discord_limits import EmbedBuilder, MessageBuilder
from notifications.formatting.formatting_utils import get_course_style, truncate_error
from notifications.formatting.plain_text_utils import status_color
from notifications.resources import Author, Footer, Notification


def has_content(data) -> bool:
    return bool(
        data["updated_images"]
        or data["failed_images"]
        or data["error"]
    )


def requires_review(data) -> bool:
    return bool(data["failed_images"] or data["error"])


def format_notification(
    data,
    course_id,
    course_name,
    course_url,
    author,
    author_icon,
    branch,
    action_url,
    cicd_role_id=None,
) -> Notification:
    style = get_course_style("docker")
    timestamp = datetime.now(timezone.utc).isoformat()
    footer = Footer(text=style["footer_text"], icon_url=style["footer_icon_url"])
    author_obj = Author(name=author, icon_url=author_icon)

    # ── Title ────────────────────────────────────────────────────────────
    if data["error"]:
        title = f"CS {course_id} | {course_name} -- Build failed"
    elif data["failed_images"]:
        title = f"CS {course_id} | {course_name} -- Build complete -- failures"
    else:
        title = f"CS {course_id} | {course_name} -- Build complete"

    # ── Color ────────────────────────────────────────────────────────────
    color = status_color(
        has_error=bool(data["error"]),
        needs_review=requires_review(data),
    )

    # ── Description ──────────────────────────────────────────────────────
    description = f"**Branch:** `{branch}`"
    if data["error"]:
        truncated = truncate_error(data["error"])
        description += f"\n\n{truncated}"

    # ── Build message ────────────────────────────────────────────────────
    mb = MessageBuilder(color=color, timestamp=timestamp)
    eb = mb.new_embed(
        title=title,
        description=description,
        author=author_obj,
        footer=footer,
    )

    if data["failed_images"]:
        lines = [f"`{image}`" for image in data["failed_images"]]
        value = "\n".join(lines)
        eb.add_field(f"Failed ({len(data['failed_images'])})", value, inline=False)

    if data["updated_images"]:
        lines = [f"`{image}`" for image in data["updated_images"]]
        value = "\n".join(lines)
        eb.add_field(f"Built ({len(data['updated_images'])})", value, inline=False)

    return Notification(
        username=style["username"],
        avatar_url=style["avatar_url"],
        messages=[mb.build()],
    )
```

- [ ] **Step 3: Run all tests except formatter tests (which need updating next)**

Run: `python -m pytest tests/test_embed_chunking.py tests/test_discord_limits.py tests/test_workflow_wiring.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add notifications/send_course.py notifications/formatting/docker_format.py
git commit -m "Update send_course and docker_format for new builder pattern and cicd_role_id"
```

---

### Task 9: Update formatter tests

**Files:**
- Modify: `tests/test_course_text_formatters.py`

- [ ] **Step 1: Rewrite canvas formatter tests for new format**

Replace `tests/test_course_text_formatters.py` with:

```python
from notifications.formatting.canvas_format import format_notification as format_canvas_notification
from notifications.formatting.docker_format import format_notification as format_docker_notification
from notifications.discord_limits import validate_notification


class TestCanvasNotificationSuccess:
    def test_success_has_overview_table(self):
        notification = format_canvas_notification(
            data={
                "deployed_content": [
                    ("page", "Week 12 Overview", "https://courses.example/week-12"),
                    ("page", "Lab 8 Instructions", "https://courses.example/lab-8"),
                    ("assignment", "Project Milestone", "https://courses.example/project"),
                ],
                "content_to_review": [],
                "error": "",
            },
            course_id="235",
            course_name="CS 235 Spring 2026",
            course_url="https://courses.example/cs235",
            author="robbykapua",
            author_icon="https://github.com/robbykapua.png",
            branch="main",
            action_url="https://github.com/actions/runs/123",
        )
        message = notification.messages[0]
        embed = message.embeds[0]

        assert message.content is None
        assert "Deploy complete" in embed.title
        assert "`main`" in embed.description
        assert embed.author is not None
        assert embed.footer is not None

        # First field is overview table
        overview = embed.fields[0]
        assert "Over View" in overview.name
        assert "page" in overview.value
        assert "assignment" in overview.value

        # Remaining resources field follows
        remaining = embed.fields[1]
        assert "Remaining Resources" in remaining.name
        assert "Week 12 Overview" in remaining.value

        assert validate_notification(notification) == []


class TestCanvasNotificationReview:
    def test_review_has_content_ping_and_review_section(self):
        notification = format_canvas_notification(
            data={
                "deployed_content": [
                    ("page", "Week 12 Overview", "https://courses.example/week-12"),
                    ("assignment", "Needs Review", "https://courses.example/review-me"),
                ],
                "content_to_review": [
                    ("Needs Review", "https://courses.example/review-me"),
                    ("Professor Approval", "https://courses.example/professor"),
                ],
                "error": "",
            },
            course_id="235",
            course_name="CS 235 Spring 2026",
            course_url="https://courses.example/cs235",
            author="robbykapua",
            author_icon="https://github.com/robbykapua.png",
            branch="main",
            action_url="https://github.com/actions/runs/123",
            cicd_role_id="123456",
        )
        message = notification.messages[0]
        embed = message.embeds[0]

        assert "<@&123456>" in message.content
        assert "review" in embed.title.lower()

        # Has overview, needs review, and remaining fields
        field_names = [f.name for f in embed.fields]
        assert any("Over View" in n for n in field_names)
        assert any("Needs review" in n for n in field_names)
        assert any("Remaining Resources" in n for n in field_names)

        # Review items present
        review_field = next(f for f in embed.fields if "Needs review" in f.name)
        assert "Needs Review" in review_field.value
        assert "Professor Approval" in review_field.value

        # Deduplication: review item not in remaining
        remaining_field = next(f for f in embed.fields if "Remaining Resources" in f.name)
        assert "https://courses.example/review-me" not in remaining_field.value
        assert "Week 12 Overview" in remaining_field.value

        assert validate_notification(notification) == []


class TestCanvasNotificationError:
    def test_error_has_content_ping_and_error_in_description(self):
        notification = format_canvas_notification(
            data={
                "deployed_content": [],
                "content_to_review": [],
                "error": "\n".join([
                    "prefix noise",
                    "Traceback (most recent call last):",
                    '  File "runner.py", line 1, in <module>',
                    "    raise RuntimeError('boom')",
                    "RuntimeError: boom",
                ]),
            },
            course_id="235",
            course_name="CS 235 Spring 2026",
            course_url="https://courses.example/cs235",
            author="robbykapua",
            author_icon="",
            branch="main",
            action_url="https://github.com/actions/runs/123",
            cicd_role_id="123456",
        )
        message = notification.messages[0]
        embed = message.embeds[0]

        assert "failed" in embed.title.lower()
        assert "RuntimeError: boom" in embed.description
        assert "<@&123456>" in message.content
        assert "ERROR" in message.content
        assert embed.fields == []

        assert validate_notification(notification) == []


class TestDockerNotificationFailures:
    def test_docker_with_failures(self):
        notification = format_docker_notification(
            data={
                "updated_images": ["lab-1", "lab-2"],
                "failed_images": ["project-base"],
                "error": "",
            },
            course_id="235",
            course_name="CS 235 Spring 2026",
            course_url="https://courses.example/cs235",
            author="robbykapua",
            author_icon="",
            branch="main",
            action_url="https://github.com/actions/runs/123",
        )
        message = notification.messages[0]
        embed = message.embeds[0]

        assert message.content is None
        assert "failures" in embed.title.lower()
        assert len(embed.fields) == 2

        failed_field = embed.fields[0]
        assert "Failed" in failed_field.name
        assert "`project-base`" in failed_field.value

        built_field = embed.fields[1]
        assert "Built" in built_field.name
        assert "`lab-1`" in built_field.value
        assert "`lab-2`" in built_field.value

        assert validate_notification(notification) == []


class TestDockerNotificationError:
    def test_docker_with_error(self):
        notification = format_docker_notification(
            data={
                "updated_images": [],
                "failed_images": ["project-base"],
                "error": "\n".join([
                    "build logs",
                    "Traceback (most recent call last):",
                    '  File "docker.py", line 10, in <module>',
                    "    raise ValueError('bad image')",
                    "ValueError: bad image",
                ]),
            },
            course_id="235",
            course_name="CS 235 Spring 2026",
            course_url="https://courses.example/cs235",
            author="robbykapua",
            author_icon="",
            branch="main",
            action_url="https://github.com/actions/runs/123",
        )
        message = notification.messages[0]
        embed = message.embeds[0]

        assert "failed" in embed.title.lower()
        assert "ValueError: bad image" in embed.description
        assert message.content is None

        assert validate_notification(notification) == []
```

- [ ] **Step 2: Run formatter tests**

Run: `python -m pytest tests/test_course_text_formatters.py -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_course_text_formatters.py
git commit -m "Update formatter tests for new canvas/docker format with limit validation"
```

---

### Task 10: Integration tests with real payload

**Files:**
- Modify: `tests/test_discord_limits.py`

- [ ] **Step 1: Add integration tests using the test payload**

Append to `tests/test_discord_limits.py`:

```python
import json
from pathlib import Path

from notifications.formatting.canvas_format import format_notification
from notifications.discord_limits import validate_notification


class TestIntegrationWithRealPayload:
    @staticmethod
    def _load_payload():
        path = Path(__file__).parent / "test-mdxcanvas-payload.json"
        with open(path) as f:
            return json.load(f)

    def test_success_case_passes_all_limits(self):
        data = self._load_payload()
        notification = format_notification(
            data=data,
            course_id="110",
            course_name="CS 110 Course Updates",
            course_url="https://byu.instructure.com/courses/20736",
            author="robbykap",
            author_icon="https://github.com/robbykap.png",
            branch="main",
            action_url="https://github.com/actions/runs/1",
        )
        violations = validate_notification(notification)
        assert violations == [], f"Limit violations: {violations}"

    def test_review_case_passes_all_limits(self):
        data = self._load_payload()
        data["content_to_review"] = [
            ("lab-notebook-week1", "https://byu.instructure.com/courses/20736/assignments/1332409"),
            ("group-presentation", "https://byu.instructure.com/courses/20736/assignments/1332413"),
        ]
        notification = format_notification(
            data=data,
            course_id="110",
            course_name="CS 110 Course Updates",
            course_url="https://byu.instructure.com/courses/20736",
            author="robbykap",
            author_icon="https://github.com/robbykap.png",
            branch="main",
            action_url="https://github.com/actions/runs/1",
            cicd_role_id="999888777",
        )
        violations = validate_notification(notification)
        assert violations == [], f"Limit violations: {violations}"

    def test_error_case_passes_all_limits(self):
        data = {
            "deployed_content": [],
            "content_to_review": [],
            "error": "SONDecodeError: Expecting value: line 1 column 1 (char 0)",
        }
        notification = format_notification(
            data=data,
            course_id="110",
            course_name="CS 110 Course Updates",
            course_url="https://byu.instructure.com/courses/20736",
            author="robbykap",
            author_icon="",
            branch="main",
            action_url="https://github.com/actions/runs/1",
            cicd_role_id="999888777",
        )
        violations = validate_notification(notification)
        assert violations == [], f"Limit violations: {violations}"

    def test_overview_table_has_correct_type_count(self):
        data = self._load_payload()
        notification = format_notification(
            data=data,
            course_id="110",
            course_name="CS 110 Course Updates",
            course_url="https://byu.instructure.com/courses/20736",
            author="robbykap",
            author_icon="",
            branch="main",
            action_url="https://github.com/actions/runs/1",
        )
        overview_field = notification.messages[0].embeds[0].fields[0]
        # The test payload has these types: module, module_item, assignment, quiz,
        # page, quiz_question, quiz_question_order, syllabus, announcement
        for resource_type in ["module", "assignment", "quiz", "page"]:
            assert resource_type in overview_field.value

    def test_massive_payload_passes_all_limits(self):
        data = {
            "deployed_content": [
                ("page", f"page-{i}", f"https://example.com/pages/{i}")
                for i in range(500)
            ],
            "content_to_review": [],
            "error": "",
        }
        notification = format_notification(
            data=data,
            course_id="110",
            course_name="CS 110 Course Updates",
            course_url="https://byu.instructure.com/courses/20736",
            author="robbykap",
            author_icon="",
            branch="main",
            action_url="https://github.com/actions/runs/1",
        )
        violations = validate_notification(notification)
        assert violations == [], f"Limit violations: {violations}"

    def test_empty_payload_has_no_content(self):
        from notifications.formatting.canvas_format import has_content
        data = {
            "deployed_content": [],
            "content_to_review": [],
            "error": "",
        }
        assert has_content(data) is False
```

- [ ] **Step 2: Run integration tests**

Run: `python -m pytest tests/test_discord_limits.py::TestIntegrationWithRealPayload -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_discord_limits.py
git commit -m "Add integration tests with real payload and edge cases"
```

---

### Task 11: Full test suite verification

- [ ] **Step 1: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS with no collection errors

- [ ] **Step 2: Final commit if any fixups needed**

```bash
git add -A
git commit -m "Fix any remaining test issues"
```
