from notifications.resources import WebhookMessage
from notifications.resources import Embed
from notifications.send_notification import _chunk_plain_text_message, send_notification


def test_chunk_plain_text_message_preserves_prefix_only_on_first_chunk():
    message = WebhookMessage(
        content="<@&123456>",
        embeds=[],
        sections=[
            "\n".join(
                [
                    "## Status",
                    "**Action needed:** 2 items need review. 3 items were published.",
                    "> Updated content: Week 12 Overview, Lab 8 Instructions",
                ]
            ),
            "\n".join(
                [
                    "## Needs Review",
                    "- Week 12 Overview: https://courses.example/week-12",
                    "- Lab 8 Instructions: https://courses.example/lab-8",
                ]
            ),
            "\n".join(
                [
                    "## Published",
                    "- Project Milestone: https://courses.example/project",
                    "- Syllabus Refresh: https://courses.example/syllabus",
                ]
            ),
        ],
        continuation_title="Canvas details (continued)",
    )

    chunks = _chunk_plain_text_message(message, max_chars=320)

    assert len(chunks) == 2
    assert chunks[0].startswith("<@&123456>\n\n## Status")
    assert "## Needs Review" in chunks[0]
    assert chunks[1].startswith("Canvas details (continued)\n\n## Published")
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


def test_send_notification_keeps_embed_on_first_plain_text_chunk(monkeypatch):
    delivered = []

    def fake_execute_webhook(webhook_url, notification, content=None, embeds=None):
        delivered.append((content, embeds or []))

        class Response:
            status_code = 200
            text = "ok"

        return Response()

    monkeypatch.setattr("notifications.send_notification._execute_webhook", fake_execute_webhook)

    send_notification(
        "https://discord.invalid/webhook",
        type(
            "NotificationStub",
            (),
            {
                "username": "Canvas Notifications",
                "avatar_url": None,
                "messages": [
                    WebhookMessage(
                        content="<@&123456>",
                        embeds=[
                            Embed(
                                title="Canvas Update Posted",
                                description="Everything published cleanly.",
                                color=0x00AA55,
                                fields=[],
                                timestamp="2026-04-01T00:00:00Z",
                            )
                        ],
                        sections=[
                            "## Status\n**Status:** 5 items were published.",
                            "## Published\n- Week 12 Overview: https://courses.example/week-12",
                        ],
                        continuation_title="Canvas details (continued)",
                    )
                ],
            },
        )(),
    )

    assert len(delivered) == 1
    assert delivered[0][0].startswith("<@&123456>\n\n## Status")
    assert len(delivered[0][1]) == 1
    assert delivered[0][1][0].title == "Canvas Update Posted"
