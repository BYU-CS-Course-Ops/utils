from __future__ import annotations

SUCCESS_COLOR = 0x57F287  # Green
REVIEW_COLOR = 0xFEE75C   # Yellow
ERROR_COLOR = 0xED4245    # Red


def status_color(*, has_error: bool, needs_review: bool) -> int:
    if has_error:
        return ERROR_COLOR
    if needs_review:
        return REVIEW_COLOR
    return SUCCESS_COLOR


def dedupe_remaining_content(
    deployed_content: list[tuple[str, str, str | None]],
    review_items: list[tuple[str, str]],
) -> list[tuple[str, str, str | None]]:
    review_urls = {url for _, url in review_items if url}
    review_labels = {label for label, _ in review_items}

    seen_urls: set[str] = set()
    seen_labels: set[str] = set()
    remaining = []

    for content_type, label, url in deployed_content:
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
        remaining.append((content_type, label, url))

    return remaining
