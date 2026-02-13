from discord_webhook import DiscordWebhook, DiscordEmbed

from .resources import Embed, Notification

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


def send_notification(webhook_url: str, notification: Notification):
    # Chunk all embeds
    all_chunks = []
    for embed_data in notification.embeds:
        all_chunks.extend(_chunk_embed(embed_data))

    for i, embed_data in enumerate(all_chunks):
        is_first = (i == 0)

        webhook = DiscordWebhook(
            url=webhook_url,
            username=notification.username,
            avatar_url=notification.avatar_url,
            content=notification.content if is_first else None,
        )

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
            field_name = field.name
            field_value = field.value

            if not field_name or not field_name.strip():
                field_name = "\u200b"
            if not field_value or not field_value.strip():
                field_value = "\u200b"

            embed.add_embed_field(
                name=field_name,
                value=field_value,
                inline=field.inline,
            )

        webhook.add_embed(embed)

        try:
            response = webhook.execute()
        except Exception as e:
            print(f"\u274c Error sending chunk {i + 1}/{len(all_chunks)}: {e}")
            continue

        # TODO: Check for Discord's specific character-limit error code
        if response.status_code >= 400:
            print(f"\u274c Discord returned status {response.status_code} on chunk {i + 1}/{len(all_chunks)}: {response.text}")
        else:
            print(f"\u2705 Sent chunk {i + 1}/{len(all_chunks)} successfully.")
