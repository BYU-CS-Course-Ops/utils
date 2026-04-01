from discord_webhook import DiscordWebhook, DiscordEmbed

from .resources import Embed, Notification, WebhookMessage

MAX_CONTENT_CHARS = 2000
MAX_EMBED_CHARS = 5900  # 100-char safety margin below Discord's 6000


def _calc_embed_size(embed: Embed) -> int:
    """Sum all character-counted fields Discord uses for embed size limits."""
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


def _build_chunk(original: Embed, fields: list, is_first: bool, continuation_title: str) -> Embed:
    """Construct one embed from the original's metadata + a subset of fields."""
    if is_first:
        return Embed(
            title=original.title,
            description=original.description,
            color=original.color,
            fields=fields,
            timestamp=original.timestamp,
            author=original.author,
            footer=original.footer,
        )
    else:
        return Embed(
            title=continuation_title,
            description="",
            color=original.color,
            fields=fields,
            timestamp=original.timestamp,
            author=None,
            footer=original.footer,
        )


def _chunk_embed(embed: Embed, max_chars: int = MAX_EMBED_CHARS) -> list[Embed]:
    """Split an oversized embed into multiple embeds by fields.

    Fields are the unit of splitting — a single field is never split.
    Returns [embed] unchanged if already under the limit.
    """
    if _calc_embed_size(embed) <= max_chars:
        return [embed]

    continuation_title = f"{embed.title} (continued)"
    chunks = []
    current_fields = []

    # Base size for first chunk (title + description + author + footer)
    first_base = len(embed.title or "") + len(embed.description or "")
    if embed.author:
        first_base += len(embed.author.name or "")
    if embed.footer:
        first_base += len(embed.footer.text or "")

    # Base size for continuation chunks (continuation title + footer)
    cont_base = len(continuation_title)
    if embed.footer:
        cont_base += len(embed.footer.text or "")

    is_first = True
    current_size = first_base

    for field in embed.fields:
        field_size = len(field.name or "") + len(field.value or "")

        if current_fields and (current_size + field_size) > max_chars:
            chunks.append(_build_chunk(embed, current_fields, is_first, continuation_title))
            is_first = False
            current_fields = []
            current_size = cont_base

        current_fields.append(field)
        current_size += field_size

    if current_fields:
        chunks.append(_build_chunk(embed, current_fields, is_first, continuation_title))

    return chunks


def _split_plain_text_content(content: str, max_chars: int) -> list[str]:
    if len(content) <= max_chars:
        return [content]

    paragraphs = content.split("\n\n")
    chunks = []
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


def _split_large_section(section: str, max_chars: int) -> list[str]:
    if len(section) <= max_chars:
        return [section]

    lines = section.splitlines()
    if len(lines) <= 1:
        return _split_plain_text_content(section, max_chars)

    heading = lines[0]
    body_lines = lines[1:]
    sections = []
    current_lines: list[str] = []
    current_length = len(heading) + 1

    for line in body_lines:
        needed = len(line) + (1 if current_lines else 0)
        if current_lines and current_length + needed > max_chars:
            sections.append(heading + "\n" + "\n".join(current_lines))
            current_lines = [line]
            current_length = len(heading) + 1 + len(line)
            continue
        current_lines.append(line)
        current_length += needed

    if current_lines:
        sections.append(heading + "\n" + "\n".join(current_lines))

    return sections


def _chunk_plain_text_message(message: WebhookMessage, max_chars: int = MAX_CONTENT_CHARS) -> list[str]:
    if not message.sections:
        return _split_plain_text_content(message.content or "", max_chars) if message.content else []

    first_prefix = message.content
    continuation_prefix = message.continuation_title
    chunked_sections = []

    for section in message.sections:
        prefix_length = len(continuation_prefix or "") + 2 if continuation_prefix else 0
        chunked_sections.extend(_split_large_section(section, max_chars - prefix_length))

    chunks = []
    current_sections: list[str] = []
    current_prefix = first_prefix
    current_length = len(current_prefix) + 2 if current_prefix else 0

    for section in chunked_sections:
        needed = len(section) + (2 if current_sections or current_prefix else 0)
        if current_sections and current_length + needed > max_chars:
            chunks.append("\n\n".join(([current_prefix] if current_prefix else []) + current_sections))
            current_sections = []
            current_prefix = continuation_prefix
            current_length = len(current_prefix) + 2 if current_prefix else 0

        current_sections.append(section)
        current_length += len(section) + (2 if current_sections[:-1] or current_prefix else 0)

    if current_sections:
        chunks.append("\n\n".join(([current_prefix] if current_prefix else []) + current_sections))

    return chunks


def _build_discord_embed(embed_data: Embed) -> DiscordEmbed:
    embed = DiscordEmbed(
        title=embed_data.title,
        description=embed_data.description,
        color=embed_data.color,
        timestamp=embed_data.timestamp,
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
        field_name = field.name or "\u200b"
        field_value = field.value or "\u200b"

        if not field_name.strip():
            field_name = "\u200b"
        if not field_value.strip():
            field_value = "\u200b"

        embed.add_embed_field(
            name=field_name,
            value=field_value,
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
    outbound_messages: list[tuple[str | None, list[Embed]]] = []

    for message in notification.messages:
        if message.sections:
            plain_text_chunks = _chunk_plain_text_message(message)
            for index, chunk_content in enumerate(plain_text_chunks):
                outbound_messages.append((chunk_content, message.embeds if index == 0 else []))
            continue

        if message.embeds:
            embed_chunks = []
            for embed_data in message.embeds:
                embed_chunks.extend(_chunk_embed(embed_data))

            for index, embed_data in enumerate(embed_chunks):
                outbound_messages.append((message.content if index == 0 else None, [embed_data]))
            continue

        if message.content:
            for chunk_content in _split_plain_text_content(message.content, MAX_CONTENT_CHARS):
                outbound_messages.append((chunk_content, []))

    for index, (content, embeds) in enumerate(outbound_messages, start=1):
        try:
            response = _execute_webhook(
                webhook_url=webhook_url,
                notification=notification,
                content=content,
                embeds=embeds,
            )
        except Exception as e:
            print(f"\u274c Error sending chunk {index}/{len(outbound_messages)}: {e}")
            continue

        if response.status_code >= 400:
            print(f"\u274c Discord returned status {response.status_code} on chunk {index}/{len(outbound_messages)}: {response.text}")
        else:
            print(f"\u2705 Sent chunk {index}/{len(outbound_messages)} successfully.")
