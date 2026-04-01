from __future__ import annotations

from collections.abc import Iterable


MAX_SECTION_CHARS = 1100


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


def render_summary_table(rows: list[tuple[str, int]]) -> str:
    type_width = max(len("Type"), *(len(label) for label, _ in rows))
    count_width = max(len("Count"), *(len(str(count)) for _, count in rows))

    lines = [
        f"{'Type':<{type_width}} | {'Count':>{count_width}}",
        f"{'-' * type_width}-+-{'-' * count_width}",
    ]
    lines.extend(f"{label:<{type_width}} | {count:>{count_width}}" for label, count in rows)
    return "```\n" + "\n".join(lines) + "\n```"


def build_header_section(
    status_header: str,
    course_name: str,
    course_url: str,
    author: str,
    branch: str,
    executive_summary: str,
    summary_table: str | None = None,
) -> str:
    lines = [
        status_header,
        f"Course: {course_name} - {course_url}",
        f"By: {author}",
        f"Branch: {branch}",
    ]

    if summary_table:
        lines.extend(["", summary_table])

    lines.extend(["", f"Executive Summary: {executive_summary}"])
    return "\n".join(lines)


def build_bullet_sections(title: str, items: list[str], max_chars: int = MAX_SECTION_CHARS) -> list[str]:
    if not items:
        return []

    sections = []
    current_lines: list[str] = []
    current_length = len(title) + 1

    for item in items:
        line = f"- {item}"
        needed = len(line) + (1 if current_lines else 0)
        if current_lines and current_length + needed > max_chars:
            sections.append(f"{title}\n" + "\n".join(current_lines))
            current_lines = [line]
            current_length = len(title) + 1 + len(line)
            continue

        current_lines.append(line)
        current_length += needed

    if current_lines:
        sections.append(f"{title}\n" + "\n".join(current_lines))

    return sections


def build_text_section(title: str, body: str | None) -> list[str]:
    if not body:
        return []
    return [f"{title}\n{body}"]


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
            formatted.append(f"{label}: {url}")
        else:
            formatted.append(label)
    return formatted


def format_name_items(items: Iterable[str]) -> list[str]:
    return [item for item in items if item]
