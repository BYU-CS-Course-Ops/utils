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

    assert "Course: CS 235 Spring 2026 - https://courses.example/cs235" in text
    assert "By: robbykapua" in text
    assert "Branch: main" in text
    assert "Type" in text
    assert "Deployed" in text
    assert "Review" in text
    assert "Errors" in text
    assert "Executive Summary:" in text
    assert "Week 12 Overview" in text
    assert "Lab 8 Instructions" in text
    assert "Project Milestone" in text
    assert "(+1 more)" in text
    assert "Content to Review:" in text
    assert "- Needs Review: https://courses.example/review-me" in text
    assert "- Professor Approval: https://courses.example/professor" in text
    assert "Remaining Content:" in text
    assert text.count("https://courses.example/review-me") == 1
    assert "Run: https://github.com/testkapua/testni-repo/actions/runs/123" in text


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

    text = "\n\n".join(notification.messages[0].sections)

    assert "Error:" in text
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

    text = "\n\n".join(notification.messages[0].sections)

    assert "Course: CS 235 Spring 2026 - https://courses.example/cs235" in text
    assert "Updated Images:" in text
    assert "- lab-1" in text
    assert "- lab-2" in text
    assert "Failed Images:" in text
    assert "- project-base" in text
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

    text = "\n\n".join(notification.messages[0].sections)

    assert "Error:" in text
    assert "ValueError: bad image" in text
