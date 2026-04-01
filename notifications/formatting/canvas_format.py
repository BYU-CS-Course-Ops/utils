from notifications.formatting.formatting_utils import get_course_style, truncate_error
from notifications.formatting.plain_text_utils import (
    build_markdown_list_sections,
    build_markdown_text_section,
    build_metadata_embed,
    build_status_section,
    dedupe_remaining_content,
    format_link_items,
    pluralize,
    status_color,
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

    if review_count:
        summary = (
            f"**Action needed:** {review_count} {pluralize(review_count, 'item')} need review. "
            f"{deployed_count} {pluralize(deployed_count, 'item')} were published."
        )
    elif error_count:
        summary = (
            f"**Action needed:** {error_count} {pluralize(error_count, 'error')} was reported. "
            f"{deployed_count} {pluralize(deployed_count, 'item')} were published."
        )
    else:
        summary = f"**Status:** {deployed_count} {pluralize(deployed_count, 'item')} were published."

    changed_items = summarize_names(content for _, content, _ in data["deployed_content"])
    if changed_items:
        return summary, f"> Updated content: {changed_items}"
    return summary, None


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

    embed_title = "Canvas Update Needs Review" if requires_review(data) else "Canvas Update Posted"
    embed_description = (
        "A publishing error was reported."
        if data["error"]
        else "Review required before everything is fully published."
        if review_count
        else "Everything published cleanly."
    )
    summary_line, highlight = _build_canvas_summary(data)

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
                embeds=[
                    build_metadata_embed(
                        title=embed_title,
                        description=embed_description,
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
                    *build_markdown_list_sections("Needs Review", review_items),
                    *build_markdown_list_sections("Published", remaining_items),
                    *build_markdown_text_section("Error", error),
                    f"## Run\n{action_url}",
                ],
                continuation_title="Canvas details (continued)",
            )
        ],
    )
