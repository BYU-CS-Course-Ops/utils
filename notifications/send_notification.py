from discord_webhook import DiscordWebhook, DiscordEmbed

from .resources import Embed, Notification

MAX_CONTENT_CHARS = 2000
MAX_EMBED_CHARS = 5900  # 100-char safety margin below Discord's 6000


def _calc_embed_size(embed: Embed) -> int:
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
    if _calc_embed_size(embed) <= max_chars:
        return [embed]

    continuation_title = f"{embed.title} (continued)"
    chunks = []
    current_fields = []

    first_base = len(embed.title or "") + len(embed.description or "")
    if embed.author:
        first_base += len(embed.author.name or "")
    if embed.footer:
        first_base += len(embed.footer.text or "")

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


def _split_content(content: str, max_chars: int = MAX_CONTENT_CHARS) -> list[str]:
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
        # Split plain text content if it exceeds Discord's limit
        content_chunks = _split_content(message.content, MAX_CONTENT_CHARS) if message.content else [None]

        # Chunk embeds if they exceed size limit
        embed_chunks = []
        for embed_data in message.embeds:
            embed_chunks.extend(_chunk_embed(embed_data))

        # First chunk gets both content and embeds; subsequent chunks get content only
        for index, content in enumerate(content_chunks):
            try:
                response = _execute_webhook(
                    webhook_url=webhook_url,
                    notification=notification,
                    content=content,
                    embeds=embed_chunks if index == 0 else [],
                )
            except Exception as e:
                print(f"Error sending notification: {e}")
                continue

            if response.status_code >= 400:
                print(f"Discord returned status {response.status_code}: {response.text}")
            else:
                print("Sent message successfully.")
