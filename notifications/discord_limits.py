from __future__ import annotations

from .resources import Embed

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
