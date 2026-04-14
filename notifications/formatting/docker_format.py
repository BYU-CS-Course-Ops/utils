from datetime import datetime, timezone

from notifications.discord_limits import FIELD_VALUE_LIMIT, EmbedBuilder, MessageBuilder
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
    style = get_course_style("docker")
    timestamp = datetime.now(timezone.utc).isoformat()
    footer = Footer(text=style["footer_text"], icon_url=style["footer_icon_url"])
    author_obj = Author(name=author, icon_url=author_icon)

    # -- Title ----------------------------------------------------------------
    if data["error"]:
        title = f"CS {course_id} | {course_name} -- Build failed"
    elif data["failed_images"]:
        title = f"CS {course_id} | {course_name} -- Build complete -- failures"
    else:
        title = f"CS {course_id} | {course_name} -- Build complete"

    continuation_title = f"{title} (continued)"

    # -- Color ----------------------------------------------------------------
    color = status_color(
        has_error=bool(data["error"]),
        needs_review=requires_review(data),
    )

    # -- Content message ------------------------------------------------------
    content = None
    if data["error"] and cicd_role_id:
        content = f"<@&{cicd_role_id}> ERROR -- Docker failed build(s). View [here]({action_url})"
    elif data["failed_images"] and cicd_role_id:
        content = f"<@&{cicd_role_id}> -- Docker build complete with failures -- review failed images"

    # -- Description ----------------------------------------------------------
    description = f"**Branch:** `{branch}`"

    if data["error"]:
        truncated = truncate_error(data["error"])
        description += f"\n\n**Error:**\n{truncated}"

    # -- Build message --------------------------------------------------------
    mb = MessageBuilder(color=color, timestamp=timestamp)
    eb = mb.new_embed(
        title=title,
        description=description,
        author=author_obj,
        footer=footer,
    )

    if data["failed_images"]:
        lines = [f"`{image}`" for image in data["failed_images"]]
        header = f"Build(s) Failed ({len(data['failed_images'])})"
        _add_items_to_builder(
            eb, mb, header, lines, author_obj, footer, continuation_title,
        )

    if data["updated_images"]:
        lines = [f"`{image}`" for image in data["updated_images"]]
        header = f"Successfully Built ({len(data['updated_images'])})"
        _add_items_to_builder(
            eb, mb, header, lines, author_obj, footer, continuation_title,
        )

    return Notification(
        username=style["username"],
        avatar_url=style["avatar_url"],
        messages=mb.build(),
    )
