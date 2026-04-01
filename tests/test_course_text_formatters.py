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
        author_icon="https://github.com/robbykapua.png",
        branch="main",
        action_url="https://github.com/testkapua/testing-repo/actions/runs/123",
    )

    message = notification.messages[0]
    embed = message.embeds[0]

    # Content is None (reserved for role mentions only)
    assert message.content is None

    # Embed metadata
    assert "Review" in embed.title or "review" in embed.title
    assert embed.author is not None
    assert embed.author.name == "robbykapua"
    assert embed.footer is not None
    assert embed.timestamp

    # Description has branch info
    assert "`main`" in embed.description

    # Fields: review items + deployed items
    assert len(embed.fields) == 2

    review_field = embed.fields[0]
    assert "Needs review" in review_field.name
    assert "(2)" in review_field.name
    assert "Needs Review" in review_field.value
    assert "Professor Approval" in review_field.value

    deployed_field = embed.fields[1]
    assert "Deployed" in deployed_field.name
    # Review items deduped from deployed
    assert "https://courses.example/review-me" not in deployed_field.value
    assert "Week 12 Overview" in deployed_field.value
    assert "Lab 8 Instructions" in deployed_field.value


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
    embed = message.embeds[0]

    assert "failed" in embed.title
    assert "RuntimeError: boom" in embed.description
    assert message.content is None


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

    assert message.content is None
    assert "failures" in embed.title.lower()

    # Failed field first, then built
    assert len(embed.fields) == 2

    failed_field = embed.fields[0]
    assert "Failed" in failed_field.name
    assert "`project-base`" in failed_field.value

    built_field = embed.fields[1]
    assert "Built" in built_field.name
    assert "`lab-1`" in built_field.value
    assert "`lab-2`" in built_field.value


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
    embed = message.embeds[0]

    assert "failed" in embed.title.lower()
    assert "ValueError: bad image" in embed.description
    assert message.content is None
