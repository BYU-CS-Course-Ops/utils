from notifications.formatting.canvas_format import format_notification as format_canvas_notification
from notifications.formatting.docker_format import format_notification as format_docker_notification


def test_canvas_notification_formats_plain_text_sections_with_summary_table_and_links():
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
        action_url="https://github.com/testkapua/testni-repo/actions/runs/123",
    )

    message = notification.messages[0]
    text = "\n\n".join(message.sections)
    embed = message.embeds[0]

    assert embed.title == "Canvas Update Needs Review"
    assert embed.description == "Review required before everything is fully published."
    assert embed.color != 0
    assert [field.name for field in embed.fields] == ["Course", "By", "Branch"]
    assert embed.fields[0].value == "CS 235 Spring 2026\nhttps://courses.example/cs235"
    assert embed.fields[1].value == "robbykapua"
    assert embed.fields[2].value == "main"
    assert embed.footer is not None
    assert "Canvas" in embed.footer.text

    assert "## Status" in text
    assert "**Action needed:** 2 items need review. 4 items were published." in text
    assert "> Updated content: Week 12 Overview, Lab 8 Instructions, Project Milestone (+1 more)" in text
    assert "## Needs Review" in text
    assert "- **Needs Review**: https://courses.example/review-me" in text
    assert "- **Professor Approval**: https://courses.example/professor" in text
    assert "## Published" in text
    assert text.count("https://courses.example/review-me") == 1
    assert "## Run" in text
    assert "https://github.com/testkapua/testni-repo/actions/runs/123" in text


def test_canvas_notification_includes_truncated_error_section_when_present():
    notification = format_canvas_notification(
        data={
            "deployed_content": [],
            "content_to_review": [],
            "error": "\n".join(
                [
                    "prefix noise",
                    "Traceback (most recent call last):",
                    '  File "runner.py", line 1, in <module>',
                    "    raise RuntimeError('boom')",
                    "RuntimeError: boom",
                ]
            ),
        },
        course_id="235",
        course_name="CS 235 Spring 2026",
        course_url="https://courses.example/cs235",
        author="robbykapua",
        author_icon="",
        branch="main",
        action_url="https://github.com/testkapua/testni-repo/actions/runs/123",
    )

    message = notification.messages[0]
    text = "\n\n".join(message.sections)

    assert message.embeds[0].title == "Canvas Update Needs Review"
    assert "## Error" in text
    assert "Traceback (most recent call last):" in text
    assert "RuntimeError: boom" in text


def test_docker_notification_formats_plain_text_sections_without_links_or_canvas_table():
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
        action_url="https://github.com/testkapua/testni-repo/actions/runs/123",
    )

    message = notification.messages[0]
    text = "\n\n".join(message.sections)
    embed = message.embeds[0]

    assert embed.title == "Docker Update Needs Attention"
    assert embed.description == "Some images failed and may need follow-up."
    assert [field.name for field in embed.fields] == ["Course", "By", "Branch"]
    assert "## Status" in text
    assert "**Status:** 2 images updated. 1 image failed." in text
    assert "> Updated images: `lab-1`, `lab-2`" in text
    assert "## Updated Images" in text
    assert "- `lab-1`" in text
    assert "- `lab-2`" in text
    assert "## Failed Images" in text
    assert "- `project-base`" in text
    assert "Type" not in text
    assert "https://courses.example/lab-1" not in text


def test_docker_notification_includes_error_section_for_failures():
    notification = format_docker_notification(
        data={
            "updated_images": [],
            "failed_images": ["project-base"],
            "error": "\n".join(
                [
                    "build logs",
                    "Traceback (most recent call last):",
                    '  File "docker.py", line 10, in <module>',
                    "    raise ValueError('bad image')",
                    "ValueError: bad image",
                ]
            ),
        },
        course_id="235",
        course_name="CS 235 Spring 2026",
        course_url="https://courses.example/cs235",
        author="robbykapua",
        author_icon="",
        branch="main",
        action_url="https://github.com/testkapua/testni-repo/actions/runs/123",
    )

    message = notification.messages[0]
    text = "\n\n".join(message.sections)

    assert message.embeds[0].title == "Docker Update Needs Attention"
    assert "## Error" in text
    assert "ValueError: bad image" in text
