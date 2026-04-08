from __future__ import annotations

from .resources import Author, Embed, Field, Footer, Notification, WebhookMessage

# -- Discord API limits -------------------------------------------------------
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


# -- EmbedBuilder -------------------------------------------------------------

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


# -- MessageBuilder -----------------------------------------------------------

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


# -- validate_notification ----------------------------------------------------

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
