from notifications.formatting.formatting_utils import get_course_style, truncate_error
from notifications.formatting.plain_text_utils import (
    build_bullet_sections,
    build_header_section,
    build_text_section,
    format_name_items,
    pluralize,
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


def _build_docker_summary(data: dict) -> str:
    updated_count = len(data["updated_images"])
    failed_count = len(data["failed_images"])
    error_count = 1 if data["error"] else 0

    summary = (
        f"{updated_count} {pluralize(updated_count, 'image')} updated, "
        f"{failed_count} {pluralize(failed_count, 'image')} failed."
    )
    if error_count:
        summary += f" {error_count} {pluralize(error_count, 'error')} reported."
    return summary


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

    status_header = "Docker update needs attention" if requires_review(data) else "Docker update posted"
    error = truncate_error(data["error"]) if data["error"] else None

    return Notification(
        username=style["username"],
        avatar_url=style["avatar_url"],
        messages=[
            WebhookMessage(
                sections=[
                    build_header_section(
                        status_header=status_header,
                        course_name=course_name,
                        course_url=course_url,
                        author=author,
                        branch=branch,
                        executive_summary=_build_docker_summary(data),
                    ),
                    *build_bullet_sections("Updated Images:", format_name_items(data["updated_images"])),
                    *build_bullet_sections("Failed Images:", format_name_items(data["failed_images"])),
                    *build_text_section("Error:", error),
                    f"Run: {action_url}",
                ],
                continuation_title="Docker details (continued)",
            )
        ],
    )
