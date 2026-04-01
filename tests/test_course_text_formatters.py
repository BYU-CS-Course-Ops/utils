from notifications.formatting.canvas_format import format_notification as format_canvas_notification
from notifications.formatting.docker_format import format_notification as format_docker_notification


def test_canvas_notification_with_review_items():
    notification = format_canvas_notification(
        data={
            "deployed_content": [
                ("Page", "Week 12 Overview", "https://courses.example/week-12"),
                ("Page", "Lab 8 Instructions", "https://courses.example/lab-8"),
                ("Assignment", "Project Milestone", "https://courses.example/project"),
                ("Page", "Needs Review", "https://courses.example/review-me"),
            ],
            "content_to_review": [
                ("Needs Review", "https://courses.example/review-me"),
                ("Professor Approval", "https://courses.example/professor"),
            ],
            "error": "",
        },
        course_id="235",
        course_name="CS 235 Spring 2026",
        course_url="https://courses.example/cs235",
        author="robbykapua",
        author_icon="",
        branch="main",
        action_url="https://github.com/testkapua/testing-repo/actions/runs/123",
    )

    message = notification.messages[0]
    embed = message.embeds[0]
    text = message.content

    # Embed is the header
    assert "Review Needed" in embed.title
    assert embed.footer is not None

    # Content is plain text
    assert "### Needs Review" in text
    assert "[Needs Review](https://courses.example/review-me)" in text
    assert "[Professor Approval](https://courses.example/professor)" in text
    assert "### Published" in text
    # Review items deduped from published
    assert text.count("https://courses.example/review-me") == 1
    assert "Action Log" in text


def test_canvas_notification_with_error():
    notification = format_canvas_notification(
        data={
            "deployed_content": [],
            "content_to_review": [],
            "error": "\n".join([
                "prefix noise",
                "Traceback (most recent call last):",
                '  File "runner.py", line 1, in <module>',
                "    raise RuntimeError('boom')",
                "RuntimeError: boom",
            ]),
        },
        course_id="235",
        course_name="CS 235 Spring 2026",
        course_url="https://courses.example/cs235",
        author="robbykapua",
        author_icon="",
        branch="main",
        action_url="https://github.com/testkapua/testing-repo/actions/runs/123",
    )

    message = notification.messages[0]
    assert "Error" in message.embeds[0].title
    assert "### Errors" in message.content
    assert "RuntimeError: boom" in message.content


def test_docker_notification_with_failures():
    notification = format_docker_notification(
        data={
            "updated_images": ["lab-1", "lab-2"],
            "failed_images": ["project-base"],
            "error": "",
        },
        course_id="235",
        course_name="CS 235 Spring 2026",
        course_url="https://courses.example/cs235",
        author="robbykapua",
        author_icon="",
        branch="main",
        action_url="https://github.com/testkapua/testing-repo/actions/runs/123",
    )

    message = notification.messages[0]
    embed = message.embeds[0]
    text = message.content

    assert "Failures" in embed.title
    assert "### Built" in text
    assert "`lab-1`" in text
    assert "`lab-2`" in text
    assert "### Failed" in text
    assert "`project-base`" in text


def test_docker_notification_with_error():
    notification = format_docker_notification(
        data={
            "updated_images": [],
            "failed_images": ["project-base"],
            "error": "\n".join([
                "build logs",
                "Traceback (most recent call last):",
                '  File "docker.py", line 10, in <module>',
                "    raise ValueError('bad image')",
                "ValueError: bad image",
            ]),
        },
        course_id="235",
        course_name="CS 235 Spring 2026",
        course_url="https://courses.example/cs235",
        author="robbykapua",
        author_icon="",
        branch="main",
        action_url="https://github.com/testkapua/testing-repo/actions/runs/123",
    )

    message = notification.messages[0]
    assert "Error" in message.embeds[0].title
    assert "### Errors" in message.content
    assert "ValueError: bad image" in message.content
