from datetime import datetime, timezone

from notifications.formatting.formatting_utils import (
    emoji_for,
    get_course_style,
    truncate_error,
)
from notifications.formatting.plain_text_utils import (
    dedupe_remaining_content,
    status_color,
)
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
        data['deployed_content']
        or data['content_to_review']
        or data['error']
    )


def requires_review(data) -> bool:
    return bool(data["content_to_review"] or data["error"])


def _format_item(resource_type: str, name: str, link: str | None) -> str:
    emoji = emoji_for(resource_type)
    label = f"`{resource_type}`"
    if link:
        return f"{emoji} {label} [{name}]({link})"
    return f"{emoji} {label} {name}"


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
    style = get_course_style("canvas")
    timestamp = datetime.now(timezone.utc).isoformat()

    # ── Title ────────────────────────────────────────────────────────────
    if data["error"]:
        title = f"{course_name} — Deploy failed"
    elif data["content_to_review"]:
        title = f"{course_name} — Deploy complete — items need review"
    else:
        title = f"{course_name} — Deploy complete"

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
    fields = []

    if data["content_to_review"]:
        review_lines = "\n".join(
            _format_item("Assignment", name, link)
            for name, link in data["content_to_review"]
        )
        fields.append(Field(
            name=f"⚠️  Needs review ({len(data['content_to_review'])})",
            value=review_lines,
            inline=False,
        ))

    remaining = dedupe_remaining_content(
        data["deployed_content"], data["content_to_review"]
    )
    if remaining:
        deployed_lines = "\n".join(
            _format_item(content_type, name, url)
            for content_type, name, url in remaining
        )
        fields.append(Field(
            name=f"✅  Deployed ({len(remaining)})",
            value=deployed_lines,
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
