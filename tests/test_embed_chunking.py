from notifications.discord_limits import (
    EMBED_CHAR_LIMIT,
    FIELDS_PER_EMBED,
    EmbedBuilder,
    calc_embed_size,
)
from notifications.resources import Author, Embed, Field, Footer


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

    def test_spacer_fields(self):
        embed = Embed(
            title="",
            description="",
            color=0,
            fields=[Field(name="\u200b", value="\u200b")],
            timestamp="",
        )
        assert calc_embed_size(embed) == 2


class TestEmbedBuilderLimits:
    def test_builder_never_exceeds_embed_char_limit(self):
        b = EmbedBuilder(
            title="Title",
            description="Description text",
            color=0,
            timestamp="",
            author=Author(name="Bot"),
            footer=Footer(text="Footer"),
        )
        added = 0
        for i in range(100):
            if not b.add_field(f"field-{i}", "x" * 500):
                break
            added += 1
        embed = b.build()
        assert calc_embed_size(embed) <= EMBED_CHAR_LIMIT
        assert added > 0

    def test_builder_respects_field_count_limit(self):
        b = EmbedBuilder(title="T", description="D", color=0, timestamp="")
        for i in range(30):
            b.add_field(f"f{i}", "v")
        embed = b.build()
        assert len(embed.fields) <= FIELDS_PER_EMBED

    def test_all_fields_preserved_when_within_limits(self):
        b = EmbedBuilder(title="T", description="D", color=0, timestamp="")
        for i in range(10):
            b.add_field(f"f{i}", f"v{i}")
        embed = b.build()
        assert len(embed.fields) == 10

    def test_typical_pypi_embed_stays_small(self):
        b = EmbedBuilder(
            title="PyPI Update",
            description="A new version has been published.",
            color=0x3B82F6,
            timestamp="2025-01-01T00:00:00Z",
            author=Author(name="PyPI Bot"),
            footer=Footer(text="BeanLab Dev Utils"),
        )
        b.add_field("Package", "my-package")
        b.add_field("Version", "1.2.3")
        b.add_field("Status", "Published")
        embed = b.build()
        assert calc_embed_size(embed) < EMBED_CHAR_LIMIT
