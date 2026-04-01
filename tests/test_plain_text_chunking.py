from notifications.resources import WebhookMessage
from notifications.send_notification import _chunk_plain_text_message


def test_chunk_plain_text_message_preserves_prefix_only_on_first_chunk():
    message = WebhookMessage(
        content="<@&123456>",
        sections=[
            "\n".join(
                [
                    "Canvas update needs review",
                    "Course: CS 235 - https://courses.example/cs235",
                    "By: robbykapua",
                    "Branch: main",
                    "",
                    "Executive Summary: 2 items deployed, 3 items need review, 1 error.",
                ]
            ),
            "\n".join(
                [
                    "Content to Review:",
                    "- Week 12 Overview: https://courses.example/week-12",
                    "- Lab 8 Instructions: https://courses.example/lab-8",
                ]
            ),
            "\n".join(
                [
                    "Remaining Content:",
                    "- Project Milestone: https://courses.example/project",
                    "- Syllabus Refresh: https://courses.example/syllabus",
                ]
            ),
        ],
        continuation_title="Canvas details (continued)",
    )

    chunks = _chunk_plain_text_message(message, max_chars=320)

    assert len(chunks) == 2
    assert chunks[0].startswith("<@&123456>\n\nCanvas update needs review")
    assert "Content to Review:" in chunks[0]
    assert chunks[1].startswith("Canvas details (continued)\n\nRemaining Content:")
    assert "<@&123456>" not in chunks[1]


def test_chunk_plain_text_message_keeps_chunks_under_limit_and_in_order():
    message = WebhookMessage(
        sections=[
            "Canvas update posted\nCourse: CS 235 - https://courses.example/cs235",
            "Summary:\n- Deployed: 12\n- Review: 0\n- Errors: 0",
            "Remaining Content:\n" + "\n".join(
                f"- Item {index}: https://courses.example/item-{index}" for index in range(1, 18)
            ),
        ],
        continuation_title="Canvas details (continued)",
    )

    chunks = _chunk_plain_text_message(message, max_chars=180)

    assert len(chunks) >= 2
    assert all(len(chunk) <= 180 for chunk in chunks)
    assert "Canvas update posted" in chunks[0]
    assert "Summary:" in chunks[0]
    assert "Item 1" in chunks[1]
