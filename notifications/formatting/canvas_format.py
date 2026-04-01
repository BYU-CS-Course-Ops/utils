from notifications.formatting.formatting_utils import get_course_style, truncate_error
from notifications.formatting.plain_text_utils import (
    build_bullet_sections,
    build_header_section,
    build_text_section,
    dedupe_remaining_content,
    format_link_items,
    pluralize,
    render_summary_table,
    summarize_names,
)
from notifications.resources import Notification, WebhookMessage


def has_content(data) -> bool:
    return bool(
        data['deployed_content']
        or data['content_to_review']
        or data['error']
    )


def requires_review(data) -> bool:
    return bool(data["content_to_review"] or data["error"])


def _build_canvas_summary(data: dict) -> str:
    deployed_count = len(data["deployed_content"])
    review_count = len(data["content_to_review"])
    error_count = 1 if data["error"] else 0

    summary = (
        f"{deployed_count} {pluralize(deployed_count, 'item')} deployed, "
        f"{review_count} {pluralize(review_count, 'item')} need review, "
        f"{error_count} {pluralize(error_count, 'error')}."
    )

    changed_items = summarize_names(content for _, content, _ in data["deployed_content"])
    if changed_items:
        summary += f" Changed items: {changed_items}."

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
    style = get_course_style("canvas")

    deployed_count = len(data["deployed_content"])
    review_count = len(data["content_to_review"])
    error_count = 1 if data["error"] else 0

    status_header = "Canvas update needs review" if requires_review(data) else "Canvas update posted"
    summary_table = render_summary_table(
        [
            ("Deployed", deployed_count),
            ("Review", review_count),
            ("Errors", error_count),
        ]
    )

    review_items = format_link_items(data["content_to_review"])
    remaining_items = format_link_items(
        dedupe_remaining_content(data["deployed_content"], data["content_to_review"])
    )
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
                        summary_table=summary_table,
                        executive_summary=_build_canvas_summary(data),
                    ),
                    *build_bullet_sections("Content to Review:", review_items),
                    *build_bullet_sections("Remaining Content:", remaining_items),
                    *build_text_section("Error:", error),
                    f"Run: {action_url}",
                ],
                continuation_title="Canvas details (continued)",
            )
        ],
    )
