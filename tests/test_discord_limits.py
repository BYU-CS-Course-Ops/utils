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
        message = mb.build()
        assert len(message.embeds) == 1
        assert message.embeds[0].title == "Title"

    def test_new_embed_creates_continuation(self):
        mb = MessageBuilder(color=0xFF0000, timestamp="2025-01-01T00:00:00Z")
        mb.new_embed(title="First", description="Desc")
        mb.new_embed(title="Second", description="")
        message = mb.build()
        assert len(message.embeds) == 2

    def test_set_content(self):
        mb = MessageBuilder(color=0, timestamp="")
        mb.set_content("hello world")
        mb.new_embed(title="T", description="D")
        message = mb.build()
        assert message.content == "hello world"

    def test_current_embed_returns_active_builder(self):
        mb = MessageBuilder(color=0, timestamp="")
        eb = mb.new_embed(title="T", description="D")
        assert mb.current_embed is eb


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
