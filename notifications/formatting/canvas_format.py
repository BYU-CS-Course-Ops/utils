from notifications.formatting.formatting_utils import get_course_style, truncate_error
from notifications.formatting.plain_text_utils import (
    dedupe_remaining_content,
    status_color,
)
from notifications.resources import Notification, WebhookMessage, Embed, Footer


def has_content(data) -> bool:
    return bool(
        data['deployed_content']
        or data['content_to_review']
        or data['error']
    )


def requires_review(data) -> bool:
    return bool(data["content_to_review"] or data["error"])


def _build_plain_text(data, course_name, course_url, author, branch, action_url):
    sections = []

    # --- Status ---
    deployed_count = len(data["deployed_content"])
    review_count = len(data["content_to_review"])

    if data["error"]:
        sections.append(f"A publishing error was reported. {deployed_count} item(s) deployed.")
    elif review_count:
        sections.append(f"{review_count} item(s) need review. {deployed_count} item(s) deployed.")
    else:
        sections.append(f"{deployed_count} item(s) deployed successfully.")

    # --- Needs Review ---
    if data["content_to_review"]:
        lines = [f"- [{name}]({link})" for name, link in data["content_to_review"]]
        sections.append("### Needs Review\n" + "\n".join(lines))

    # --- Published (deduped) ---
    remaining = dedupe_remaining_content(data["deployed_content"], data["content_to_review"])
    if remaining:
        lines = []
        for label, url in remaining:
            if url:
                lines.append(f"- [{label}]({url})")
            else:
                lines.append(f"- {label}")
        sections.append("### Published\n" + "\n".join(lines))

    # --- Errors ---
    if data["error"]:
        truncated = truncate_error(data["error"])
        sections.append(f"### Errors\n{truncated}")

    # --- Metadata footer ---
    sections.append(f"-# {author} | `{branch}` | [{course_name}]({course_url}) | [Action Log]({action_url})")

    return "\n\n".join(sections)


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

    title = "Canvas Deploy"
    if data["error"]:
        title = "Canvas Deploy -- Error"
    elif data["content_to_review"]:
        title = "Canvas Deploy -- Review Needed"

    color = status_color(has_error=bool(data["error"]), needs_review=requires_review(data))
    plain_text = _build_plain_text(data, course_name, course_url, author, branch, action_url)

    return Notification(
        username=style["username"],
        avatar_url=style["avatar_url"],
        messages=[
            WebhookMessage(
                content=plain_text,
                embeds=[
                    Embed(
                        title=f"CS {course_id} | {title}",
                        description="",
                        color=color,
                        fields=[],
                        timestamp="",
                        footer=Footer(text=style["footer_text"], icon_url=style["footer_icon_url"]),
                    )
                ],
            )
        ],
    )
