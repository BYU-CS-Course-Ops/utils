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
)
from notifications.resources import Author, Embed, Field, Footer


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
