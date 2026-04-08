from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from tabulate import tabulate

from notifications.discord_limits import FIELD_VALUE_LIMIT, EmbedBuilder, MessageBuilder
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
    table = tabulate(rows, headers=["Resource Type", "Count"], tablefmt="presto")
    return f"```\n{table}\n```"


def _format_item(resource_type: str, name: str, link: str | None) -> str:
    label = f"`{resource_type}`"
    if link:
        return f"{label:<3} [{name}]({link})"
    return f"{label:<3} {name}"


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
    is_first_field = True

    def flush_field():
        nonlocal current_lines, is_first_field, builder
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

    for line in lines:
        test_value = "\n".join(current_lines + [line])
        test_name = header if is_first_field else "\u200b"

        would_exceed_field = len(test_value) > FIELD_VALUE_LIMIT
        would_exceed_embed = not builder.can_add_field(test_name, test_value)

        if current_lines and (would_exceed_field or would_exceed_embed):
            flush_field()

        current_lines.append(line)

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

    # -- Title ----------------------------------------------------------------
    if data["error"]:
        title = f"CS {course_id} | {course_name} -- Deploy failed"
    elif data["content_to_review"]:
        title = f"CS {course_id} | {course_name} -- Deploy complete -- items need review"
    else:
        title = f"CS {course_id} | {course_name} -- Deploy complete"

    continuation_title = f"{title} (continued)"

    # -- Color ----------------------------------------------------------------
    color = status_color(
        has_error=bool(data["error"]),
        needs_review=requires_review(data),
    )

    # -- Content message ------------------------------------------------------
    content = None
    if data["error"] and cicd_role_id:
        content = f"<@&{cicd_role_id}> ERROR -- MDXCanvas failed to deploy. View [here]({action_url})"
    elif data["content_to_review"] and cicd_role_id:
        content = f"<@&{cicd_role_id}> -- Deployed Resources to Review"

    # -- Description ----------------------------------------------------------
    description = f"**Branch:** `{branch}`"

    if data["error"]:
        truncated = truncate_error(data["error"])
        description += f"\n\n**Error:**\n{truncated}"

    # -- Build message --------------------------------------------------------
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

    # -- Overview table -------------------------------------------------------
    if data["deployed_content"] or data["content_to_review"]:
        table = _build_overview_table(data["deployed_content"], data["content_to_review"])
        eb.add_field("Over View:", table, inline=False)

    # -- Needs review items ---------------------------------------------------
    if data["content_to_review"]:
        lines = [
            _format_item("assignment", name, link)
            for name, link in data["content_to_review"]
        ]
        header = f"Needs review ({len(data['content_to_review'])})"
        eb = _add_items_to_builder(
            eb, mb, header, lines, author_obj, footer, continuation_title,
        )

    # -- Remaining resources --------------------------------------------------
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
