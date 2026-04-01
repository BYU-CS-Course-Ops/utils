from datetime import datetime, timezone

from notifications.formatting.formatting_utils import chunk_field_lines, get_course_style, truncate_error
from notifications.formatting.plain_text_utils import status_color
from notifications.resources import (
    Author,
    Embed,
    Field,
    Footer,
    Notification,
    WebhookMessage,
)


def has_content(data) -> bool:
    return bool(
        data['updated_images']
        or data['failed_images']
        or data['error']
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
) -> Notification:
    style = get_course_style("docker")
    timestamp = datetime.now(timezone.utc).isoformat()

    # ── Title ────────────────────────────────────────────────────────────
    if data["error"]:
        title = f"{course_name} — Build failed"
    elif data["failed_images"]:
        title = f"{course_name} — Build complete — failures"
    else:
        title = f"{course_name} — Build complete"

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

    # ── Fields ───────────────────────────────────────────────────────────
    SPACER = Field(name="\u200b", value="\u200b", inline=False)
    fields = []

    if data["failed_images"]:
        lines = [f"> ❌ `{image}`" for image in data["failed_images"]]
        chunks = chunk_field_lines(lines)
        header = f"❌  Failed ({len(data['failed_images'])})"
        if fields:
            fields.append(SPACER)
        for i, chunk in enumerate(chunks):
            fields.append(Field(
                name=header if i == 0 else "\u200b",
                value=chunk,
                inline=False,
            ))

    if data["updated_images"]:
        lines = [f"> 📦 `{image}`" for image in data["updated_images"]]
        chunks = chunk_field_lines(lines)
        header = f"✅  Built ({len(data['updated_images'])})"
        if fields:
            fields.append(SPACER)
        for i, chunk in enumerate(chunks):
            fields.append(Field(
                name=header if i == 0 else "\u200b",
                value=chunk,
                inline=False,
            ))

    # ── Build notification ───────────────────────────────────────────────
    return Notification(
        username=style["username"],
        avatar_url=style["avatar_url"],
        messages=[
            WebhookMessage(
                content=None,
                embeds=[
                    Embed(
                        title=f"CS {course_id} | {title}",
                        description=description,
                        color=color,
                        fields=fields,
                        timestamp=timestamp,
                        author=Author(name=author, icon_url=author_icon),
                        footer=Footer(
                            text=style["footer_text"],
                            icon_url=style["footer_icon_url"],
                        ),
                    )
                ],
            )
        ],
    )
