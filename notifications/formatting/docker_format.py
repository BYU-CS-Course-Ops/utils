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

    # -- Title ----------------------------------------------------------------
    if data["error"]:
        title = f"CS {course_id} | {course_name} -- Build failed"
    elif data["failed_images"]:
        title = f"CS {course_id} | {course_name} -- Build complete -- failures"
    else:
        title = f"CS {course_id} | {course_name} -- Build complete"

    # -- Color ----------------------------------------------------------------
    color = status_color(
        has_error=bool(data["error"]),
        needs_review=requires_review(data),
    )

    # -- Description ----------------------------------------------------------
    description = f"**Branch:** `{branch}`"
    if data["error"]:
        truncated = truncate_error(data["error"])
        description += f"\n\n{truncated}"

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
