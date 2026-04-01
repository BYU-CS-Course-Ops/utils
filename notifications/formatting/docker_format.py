from notifications.formatting.formatting_utils import get_course_style, truncate_error
from notifications.formatting.plain_text_utils import (
    build_markdown_list_sections,
    build_markdown_text_section,
    build_metadata_embed,
    build_status_section,
    format_name_items,
    pluralize,
    status_color,
)
from notifications.resources import Notification, WebhookMessage


def has_content(data) -> bool:
    return bool(
        data['updated_images']
        or data['failed_images']
        or data['error']
    )


def requires_review(data) -> bool:
    return bool(data["failed_images"] or data["error"])


def _build_docker_summary(data: dict) -> tuple[str, str | None]:
    updated_count = len(data["updated_images"])
    failed_count = len(data["failed_images"])
    error_count = 1 if data["error"] else 0

    if failed_count or error_count:
        summary = (
            f"**Status:** {updated_count} {pluralize(updated_count, 'image')} updated. "
            f"{failed_count} {pluralize(failed_count, 'image')} failed."
        )
    else:
        summary = f"**Status:** {updated_count} {pluralize(updated_count, 'image')} updated."

    if error_count:
        summary += f" {error_count} {pluralize(error_count, 'error')} reported."

    updated_names = ", ".join(format_name_items(data["updated_images"][:3]))
    highlight = f"> Updated images: {updated_names}" if updated_names else None
    return summary, highlight


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

    status_title = "Docker Update Needs Attention" if requires_review(data) else "Docker Update Posted"
    status_description = (
        "A build or publishing error was reported."
        if data["error"]
        else "Some images failed and may need follow-up."
        if data["failed_images"]
        else "Everything published cleanly."
    )
    error = truncate_error(data["error"]) if data["error"] else None
    summary_line, highlight = _build_docker_summary(data)

    return Notification(
        username=style["username"],
        avatar_url=style["avatar_url"],
        messages=[
            WebhookMessage(
                embeds=[
                    build_metadata_embed(
                        title=status_title,
                        description=status_description,
                        course_name=course_name,
                        course_url=course_url,
                        author=author,
                        branch=branch,
                        footer_text=style["footer_text"],
                        footer_icon_url=style["footer_icon_url"],
                        timestamp="",
                        color=status_color(has_error=bool(data["error"]), needs_review=requires_review(data)),
                    )
                ],
                sections=[
                    build_status_section(summary_line, highlight),
                    *build_markdown_list_sections("Updated Images", format_name_items(data["updated_images"])),
                    *build_markdown_list_sections("Failed Images", format_name_items(data["failed_images"])),
                    *build_markdown_text_section("Error", error),
                    f"## Run\n{action_url}",
                ],
                continuation_title="Docker details (continued)",
            )
        ],
    )
