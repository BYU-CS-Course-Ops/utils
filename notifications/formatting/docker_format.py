from notifications.formatting.formatting_utils import get_course_style, truncate_error
from notifications.formatting.plain_text_utils import status_color
from notifications.resources import Notification, WebhookMessage, Embed, Footer


def has_content(data) -> bool:
    return bool(
        data['updated_images']
        or data['failed_images']
        or data['error']
    )


def requires_review(data) -> bool:
    return bool(data["failed_images"] or data["error"])


def _build_plain_text(data, course_name, course_url, author, branch, action_url):
    sections = []

    # --- Status ---
    updated_count = len(data["updated_images"])
    failed_count = len(data["failed_images"])

    if data["error"]:
        sections.append(f"A build error was reported. {updated_count} image(s) built, {failed_count} failed.")
    elif failed_count:
        sections.append(f"{updated_count} image(s) built. {failed_count} image(s) failed.")
    else:
        sections.append(f"{updated_count} image(s) built successfully.")

    # --- Built ---
    if data["updated_images"]:
        lines = [f"- `{image}`" for image in data["updated_images"]]
        sections.append("### Built\n" + "\n".join(lines))

    # --- Failed ---
    if data["failed_images"]:
        lines = [f"- `{image}`" for image in data["failed_images"]]
        sections.append("### Failed\n" + "\n".join(lines))

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
    style = get_course_style("docker")

    title = "Docker Build"
    if data["error"]:
        title = "Docker Build -- Error"
    elif data["failed_images"]:
        title = "Docker Build -- Failures"

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
