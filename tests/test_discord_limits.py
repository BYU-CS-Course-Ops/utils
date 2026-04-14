from notifications.discord_limits import (
    TITLE_LIMIT,
    DESCRIPTION_LIMIT,
    FIELD_NAME_LIMIT,
    FIELD_VALUE_LIMIT,
    FIELDS_PER_EMBED,
    FOOTER_LIMIT,
    AUTHOR_NAME_LIMIT,
    EMBED_CHAR_LIMIT,
    MAX_EMBEDS_PER_MESSAGE,
    CONTENT_LIMIT,
    calc_embed_size,
    split_content,
    EmbedBuilder,
    MessageBuilder,
    validate_notification,
)
from notifications.resources import Author, Embed, Field, Footer, Notification, WebhookMessage


class TestConstants:
    def test_embed_char_limit(self):
        assert EMBED_CHAR_LIMIT == 6000

    def test_field_value_limit(self):
        assert FIELD_VALUE_LIMIT == 1024

    def test_fields_per_embed(self):
        assert FIELDS_PER_EMBED == 25

    def test_content_limit(self):
        assert CONTENT_LIMIT == 2000

    def test_max_embeds_per_message(self):
        assert MAX_EMBEDS_PER_MESSAGE == 10


class TestCalcEmbedSize:
    def test_basic_size(self):
        embed = Embed(
            title="Hello",
            description="World",
            color=0xFF0000,
            fields=[Field(name="key", value="val")],
            timestamp="2025-01-01T00:00:00Z",
        )
        assert calc_embed_size(embed) == len("Hello") + len("World") + len("key") + len("val")

    def test_includes_footer_and_author(self):
        embed = Embed(
            title="T",
            description="D",
            color=0,
            fields=[],
            timestamp="",
            author=Author(name="AuthorName"),
            footer=Footer(text="FooterText"),
        )
        assert calc_embed_size(embed) == len("T") + len("D") + len("AuthorName") + len("FooterText")

    def test_empty_embed(self):
        embed = Embed(
            title="",
            description="",
            color=0,
            fields=[],
            timestamp="",
        )
        assert calc_embed_size(embed) == 0


class TestSplitContent:
    def test_short_content_unchanged(self):
        result = split_content("hello", 2000)
        assert result == ["hello"]

    def test_long_content_splits_on_paragraphs(self):
        paragraphs = ["paragraph " + str(i) for i in range(200)]
        content = "\n\n".join(paragraphs)
        result = split_content(content, 100)
        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= 100


class TestEmbedBuilder:
    def test_build_produces_embed(self):
        b = EmbedBuilder(
            title="Title",
            description="Desc",
            color=0xFF0000,
            timestamp="2025-01-01T00:00:00Z",
            author=Author(name="Bot"),
            footer=Footer(text="Footer"),
        )
        embed = b.build()
        assert embed.title == "Title"
        assert embed.description == "Desc"
        assert embed.color == 0xFF0000
        assert embed.author.name == "Bot"
        assert embed.footer.text == "Footer"
        assert embed.fields == []

    def test_add_field_success(self):
        b = EmbedBuilder(
            title="T", description="D", color=0, timestamp="",
        )
        result = b.add_field("Name", "Value", inline=False)
        assert result is True
        embed = b.build()
        assert len(embed.fields) == 1
        assert embed.fields[0].name == "Name"
        assert embed.fields[0].value == "Value"

    def test_can_add_field_checks_char_limit(self):
        b = EmbedBuilder(
            title="x" * 5000, description="", color=0, timestamp="",
        )
        assert b.can_add_field("name", "x" * 1500) is False

    def test_can_add_field_checks_field_count(self):
        b = EmbedBuilder(
            title="T", description="D", color=0, timestamp="",
        )
        for i in range(25):
            b.add_field(f"f{i}", "v")
        assert b.can_add_field("f25", "v") is False

    def test_add_field_returns_false_when_full(self):
        b = EmbedBuilder(
            title="x" * 5900, description="", color=0, timestamp="",
        )
        result = b.add_field("name", "x" * 500)
        assert result is False
        assert len(b.build().fields) == 0

    def test_remaining_chars_decreases(self):
        b = EmbedBuilder(
            title="Hello", description="World", color=0, timestamp="",
        )
        initial = b.remaining_chars()
        b.add_field("Key", "Value")
        assert b.remaining_chars() == initial - len("Key") - len("Value")


class TestMessageBuilder:
    def test_build_single_embed_message(self):
        mb = MessageBuilder(color=0xFF0000, timestamp="2025-01-01T00:00:00Z")
        eb = mb.new_embed(title="Title", description="Desc")
        eb.add_field("Key", "Value")
        messages = mb.build()
        assert len(messages) == 1
        assert len(messages[0].embeds) == 1
        assert messages[0].embeds[0].title == "Title"

    def test_new_embed_creates_continuation(self):
        mb = MessageBuilder(color=0xFF0000, timestamp="2025-01-01T00:00:00Z")
        mb.new_embed(title="First", description="Desc")
        mb.new_embed(title="Second", description="")
        messages = mb.build()
        # Both small embeds should fit in one message
        total_embeds = sum(len(m.embeds) for m in messages)
        assert total_embeds == 2

    def test_set_content(self):
        mb = MessageBuilder(color=0, timestamp="")
        mb.set_content("hello world")
        mb.new_embed(title="T", description="D")
        messages = mb.build()
        assert messages[0].content == "hello world"

    def test_content_only_on_first_message(self):
        mb = MessageBuilder(color=0, timestamp="")
        mb.set_content("hello world")
        # Create two embeds that together exceed 6000 chars
        mb.new_embed(title="T", description="x" * 5000)
        mb.new_embed(title="T", description="x" * 5000)
        messages = mb.build()
        assert len(messages) == 2
        assert messages[0].content == "hello world"
        assert messages[1].content is None

    def test_current_embed_returns_active_builder(self):
        mb = MessageBuilder(color=0, timestamp="")
        eb = mb.new_embed(title="T", description="D")
        assert mb.current_embed is eb

    def test_large_embeds_split_across_messages(self):
        mb = MessageBuilder(color=0, timestamp="")
        # Create 3 embeds each ~3000 chars — can't fit 2 in one message
        for i in range(3):
            mb.new_embed(title=f"E{i}", description="x" * 2990)
        messages = mb.build()
        assert len(messages) >= 2
        for msg in messages:
            combined = sum(
                len(e.title or "") + len(e.description or "")
                for e in msg.embeds
            )
            assert combined <= 6000


class TestValidateNotification:
    def test_valid_notification_returns_empty(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    content=None,
                    embeds=[
                        Embed(
                            title="Title",
                            description="Desc",
                            color=0,
                            fields=[Field(name="k", value="v")],
                            timestamp="",
                        )
                    ],
                )
            ],
        )
        assert validate_notification(notification) == []

    def test_title_too_long(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    embeds=[
                        Embed(
                            title="x" * 257,
                            description="",
                            color=0,
                            fields=[],
                            timestamp="",
                        )
                    ],
                )
            ],
        )
        violations = validate_notification(notification)
        assert any("title" in v.lower() for v in violations)

    def test_field_value_too_long(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    embeds=[
                        Embed(
                            title="T",
                            description="",
                            color=0,
                            fields=[Field(name="k", value="x" * 1025)],
                            timestamp="",
                        )
                    ],
                )
            ],
        )
        violations = validate_notification(notification)
        assert any("field value" in v.lower() for v in violations)

    def test_too_many_fields(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    embeds=[
                        Embed(
                            title="T",
                            description="",
                            color=0,
                            fields=[Field(name="k", value="v") for _ in range(26)],
                            timestamp="",
                        )
                    ],
                )
            ],
        )
        violations = validate_notification(notification)
        assert any("field count" in v.lower() for v in violations)

    def test_embed_total_chars_too_large(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    embeds=[
                        Embed(
                            title="x" * 256,
                            description="x" * 4096,
                            color=0,
                            fields=[Field(name="k", value="x" * 1024) for _ in range(3)],
                            timestamp="",
                        )
                    ],
                )
            ],
        )
        violations = validate_notification(notification)
        assert any("embed char" in v.lower() for v in violations)

    def test_content_too_long(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    content="x" * 2001,
                    embeds=[],
                )
            ],
        )
        violations = validate_notification(notification)
        assert any("content" in v.lower() for v in violations)

    def test_too_many_embeds(self):
        notification = Notification(
            username="Bot",
            messages=[
                WebhookMessage(
                    embeds=[
                        Embed(title="T", description="", color=0, fields=[], timestamp="")
                        for _ in range(11)
                    ],
                )
            ],
        )
        violations = validate_notification(notification)
        assert any("embed count" in v.lower() for v in violations)


import json
from pathlib import Path

from notifications.formatting.canvas_format import format_notification


class TestIntegrationWithRealPayload:
    @staticmethod
    def _load_payload():
        path = Path(__file__).parent / "test-mdxcanvas-payload.json"
        with open(path) as f:
            return json.load(f)

    def test_success_case_passes_all_limits(self):
        data = self._load_payload()
        notification = format_notification(
            data=data,
            course_id="110",
            course_name="CS 110 Course Updates",
            course_url="https://byu.instructure.com/courses/20736",
            author="robbykap",
            author_icon="https://github.com/robbykap.png",
            branch="main",
            action_url="https://github.com/actions/runs/1",
        )
        violations = validate_notification(notification)
        assert violations == [], f"Limit violations: {violations}"

    def test_review_case_passes_all_limits(self):
        data = self._load_payload()
        data["content_to_review"] = [
            ("assignment", "lab-notebook-week1", "https://byu.instructure.com/courses/20736/assignments/1332409"),
            ("assignment", "group-presentation", "https://byu.instructure.com/courses/20736/assignments/1332413"),
        ]
        notification = format_notification(
            data=data,
            course_id="110",
            course_name="CS 110 Course Updates",
            course_url="https://byu.instructure.com/courses/20736",
            author="robbykap",
            author_icon="https://github.com/robbykap.png",
            branch="main",
            action_url="https://github.com/actions/runs/1",
            cicd_role_id="999888777",
        )
        violations = validate_notification(notification)
        assert violations == [], f"Limit violations: {violations}"

    def test_error_case_passes_all_limits(self):
        data = {
            "deployed_content": [],
            "content_to_review": [],
            "error": "SONDecodeError: Expecting value: line 1 column 1 (char 0)",
        }
        notification = format_notification(
            data=data,
            course_id="110",
            course_name="CS 110 Course Updates",
            course_url="https://byu.instructure.com/courses/20736",
            author="robbykap",
            author_icon="",
            branch="main",
            action_url="https://github.com/actions/runs/1",
            cicd_role_id="999888777",
        )
        violations = validate_notification(notification)
        assert violations == [], f"Limit violations: {violations}"

    def test_overview_table_has_correct_type_count(self):
        data = self._load_payload()
        notification = format_notification(
            data=data,
            course_id="110",
            course_name="CS 110 Course Updates",
            course_url="https://byu.instructure.com/courses/20736",
            author="robbykap",
            author_icon="",
            branch="main",
            action_url="https://github.com/actions/runs/1",
        )
        overview_field = notification.messages[0].embeds[0].fields[0]
        for resource_type in ["module", "assignment", "quiz", "page"]:
            assert resource_type in overview_field.value

    def test_massive_payload_passes_all_limits(self):
        data = {
            "deployed_content": [
                ("page", f"page-{i}", f"https://example.com/pages/{i}")
                for i in range(500)
            ],
            "content_to_review": [],
            "error": "",
        }
        notification = format_notification(
            data=data,
            course_id="110",
            course_name="CS 110 Course Updates",
            course_url="https://byu.instructure.com/courses/20736",
            author="robbykap",
            author_icon="",
            branch="main",
            action_url="https://github.com/actions/runs/1",
        )
        violations = validate_notification(notification)
        assert violations == [], f"Limit violations: {violations}"

    def test_empty_payload_has_no_content(self):
        from notifications.formatting.canvas_format import has_content
        data = {
            "deployed_content": [],
            "content_to_review": [],
            "error": "",
        }
        assert has_content(data) is False
