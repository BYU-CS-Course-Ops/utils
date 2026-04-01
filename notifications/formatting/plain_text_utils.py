from __future__ import annotations

from collections.abc import Iterable

from notifications.resources import Embed, Field, Footer

MAX_SECTION_CHARS = 1100
SUCCESS_COLOR = 0x2E8B57
REVIEW_COLOR = 0xD97706
ERROR_COLOR = 0xDC2626


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    if count == 1:
        return singular
    return plural or f"{singular}s"


def summarize_names(names: Iterable[str], limit: int = 3) -> str:
    seen: set[str] = set()
    ordered = []
    for name in names:
        if name and name not in seen:
            ordered.append(name)
            seen.add(name)

    if not ordered:
        return ""

    shown = ordered[:limit]
    remainder = len(ordered) - len(shown)
    summary = ", ".join(shown)
    if remainder > 0:
        summary += f" (+{remainder} more)"
    return summary


def build_metadata_embed(
    *,
    title: str,
    description: str,
    course_name: str,
    course_url: str,
    author: str,
    branch: str,
    footer_text: str,
    footer_icon_url: str,
    timestamp: str,
    color: int,
) -> Embed:
    return Embed(
        title=title,
        description=description,
        color=color,
        fields=[
            Field(name="Course", value=f"{course_name}\n{course_url}", inline=True),
            Field(name="By", value=author, inline=True),
            Field(name="Branch", value=branch, inline=True),
        ],
        timestamp=timestamp,
        footer=Footer(text=footer_text, icon_url=footer_icon_url),
    )


def status_color(*, has_error: bool, needs_review: bool) -> int:
    if has_error:
        return ERROR_COLOR
    if needs_review:
        return REVIEW_COLOR
    return SUCCESS_COLOR


def build_status_section(summary_line: str, highlight: str | None = None) -> str:
    lines = ["## Status", summary_line]
    if highlight:
        lines.append(highlight)
    return "\n".join(lines)


def build_markdown_list_sections(title: str, items: list[str], max_chars: int = MAX_SECTION_CHARS) -> list[str]:
    if not items:
        return []

    sections = []
    current_lines: list[str] = []
    heading = f"## {title}"
    current_length = len(heading) + 1

    for item in items:
        line = f"- {item}"
        needed = len(line) + (1 if current_lines else 0)
        if current_lines and current_length + needed > max_chars:
            sections.append(f"{heading}\n" + "\n".join(current_lines))
            current_lines = [line]
            current_length = len(heading) + 1 + len(line)
            continue

        current_lines.append(line)
        current_length += needed

    if current_lines:
        sections.append(f"{heading}\n" + "\n".join(current_lines))

    return sections


def build_markdown_text_section(title: str, body: str | None) -> list[str]:
    if not body:
        return []
    return [f"## {title}\n{body}"]


def dedupe_remaining_content(
    deployed_content: list[tuple[str, str, str | None]],
    review_items: list[tuple[str, str]],
) -> list[tuple[str, str | None]]:
    review_urls = {url for _, url in review_items if url}
    review_labels = {label for label, _ in review_items}

    seen_urls: set[str] = set()
    seen_labels: set[str] = set()
    remaining = []

    for _, label, url in deployed_content:
        if url and url in review_urls:
            continue
        if label in review_labels:
            continue
        if url and url in seen_urls:
            continue
        if label in seen_labels:
            continue

        if url:
            seen_urls.add(url)
        seen_labels.add(label)
        remaining.append((label, url))

    return remaining


def format_link_items(items: Iterable[tuple[str, str | None]]) -> list[str]:
    formatted = []
    for label, url in items:
        if url:
            formatted.append(f"**{label}**: {url}")
        else:
            formatted.append(f"**{label}**")
    return formatted


def format_name_items(items: Iterable[str]) -> list[str]:
    return [f"`{item}`" for item in items if item]
