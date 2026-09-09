from notifications.formatting.canvas_format import format_notification as format_canvas_notification
from notifications.formatting.docker_format import format_notification as format_docker_notification
from notifications.discord_limits import validate_notification


class TestCanvasNotificationSuccess:
    def test_success_has_overview_table(self):
        notification = format_canvas_notification(
            data={
                "deployed_content": [
                    ("page", "Week 12 Overview", "https://courses.example/week-12"),
                    ("page", "Lab 8 Instructions", "https://courses.example/lab-8"),
                    ("assignment", "Project Milestone", "https://courses.example/project"),
                ],
                "content_to_review": [],
                "error": "",
            },
            course_id="235",
            course_name="CS 235 Spring 2026",
            course_url="https://courses.example/cs235",
            author="robbykapua",
            author_icon="https://github.com/robbykapua.png",
            branch="main",
            action_url="https://github.com/actions/runs/123",
        )
        message = notification.messages[0]
        embed = message.embeds[0]

        assert message.content is None
        assert "Deploy complete" in embed.title
        assert "`main`" in embed.description
        assert embed.author is not None
        assert embed.footer is not None

        # First field is overview table
        overview = embed.fields[0]
        assert "Overview" in overview.name
        assert "page" in overview.value
        assert "assignment" in overview.value

        # Deployed resources field follows
        remaining = embed.fields[1]
        assert "Deployed Resources" in remaining.name
        assert "Week 12 Overview" in remaining.value

        assert validate_notification(notification) == []


class TestCanvasNotificationReview:
    def test_review_has_content_ping_and_review_section(self):
        notification = format_canvas_notification(
            data={
                "deployed_content": [
                    ("page", "Week 12 Overview", "https://courses.example/week-12"),
                    ("assignment", "Needs Review", "https://courses.example/review-me"),
                ],
                "content_to_review": [
                    ("assignment", "Needs Review", "https://courses.example/review-me"),
                    ("assignment", "Professor Approval", "https://courses.example/professor"),
                ],
                "error": "",
            },
            course_id="235",
            course_name="CS 235 Spring 2026",
            course_url="https://courses.example/cs235",
            author="robbykapua",
            author_icon="https://github.com/robbykapua.png",
            branch="main",
            action_url="https://github.com/actions/runs/123",
            cicd_role_id="123456",
        )
        message = notification.messages[0]
        embed = message.embeds[0]

        assert "<@&123456>" in message.content
        assert "review" in embed.title.lower()

        # Has overview, needs review, and remaining fields
        field_names = [f.name for f in embed.fields]
        assert any("Overview" in n for n in field_names)
        assert any("Needs Review" in n for n in field_names)
        assert any("Deployed Resources" in n for n in field_names)

        # Review items present
        review_field = next(f for f in embed.fields if "Needs Review" in f.name)
        assert "Needs Review" in review_field.value
        assert "Professor Approval" in review_field.value

        # Deduplication: review item not in the deployed list
        remaining_field = next(f for f in embed.fields if "Deployed Resources" in f.name)
        assert "https://courses.example/review-me" not in remaining_field.value
        assert "Week 12 Overview" in remaining_field.value

        assert validate_notification(notification) == []


class TestCanvasNotificationError:
    def test_error_has_content_ping_and_error_in_description(self):
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
            action_url="https://github.com/actions/runs/123",
            cicd_role_id="123456",
        )
        message = notification.messages[0]
        embed = message.embeds[0]

        assert "failed" in embed.title.lower()
        assert "RuntimeError: boom" in embed.description
        assert "<@&123456>" in message.content
        assert "ERROR" in message.content
        assert embed.fields == []

        assert validate_notification(notification) == []


class TestDockerNotificationFailures:
    def test_docker_with_failures(self):
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
            action_url="https://github.com/actions/runs/123",
        )
        message = notification.messages[0]
        embed = message.embeds[0]

        assert message.content is None
        assert "failures" in embed.title.lower()
        assert len(embed.fields) == 2

        failed_field = embed.fields[0]
        assert "Failed" in failed_field.name
        assert "`project-base`" in failed_field.value

        built_field = embed.fields[1]
        assert "Built" in built_field.name
        assert "`lab-1`" in built_field.value
        assert "`lab-2`" in built_field.value

        assert validate_notification(notification) == []


class TestDockerNotificationError:
    def test_docker_with_error(self):
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
            action_url="https://github.com/actions/runs/123",
        )
        message = notification.messages[0]
        embed = message.embeds[0]

        assert "failed" in embed.title.lower()
        assert "ValueError: bad image" in embed.description
        assert message.content is None

        assert validate_notification(notification) == []
