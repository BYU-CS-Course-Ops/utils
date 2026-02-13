import pytest

from notifications.resources import Embed, Field, Author, Footer
from notifications.send_notification import _calc_embed_size, _chunk_embed, MAX_EMBED_CHARS


class TestCalcEmbedSize:
    def test_basic_size(self):
        embed = Embed(
            title="Hello",
            description="World",
            color=0xFF0000,
            fields=[Field(name="key", value="val")],
            timestamp="2025-01-01T00:00:00Z",
        )
        assert _calc_embed_size(embed) == len("Hello") + len("World") + len("key") + len("val")

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
        assert _calc_embed_size(embed) == len("T") + len("D") + len("AuthorName") + len("FooterText")

    def test_empty_embed(self):
        embed = Embed(
            title="",
            description="",
            color=0,
            fields=[],
            timestamp="",
        )
        assert _calc_embed_size(embed) == 0

    def test_spacer_fields(self):
        embed = Embed(
            title="",
            description="",
            color=0,
            fields=[Field(name="\u200b", value="\u200b")],
            timestamp="",
        )
        # Zero-width spaces are 1 char each
        assert _calc_embed_size(embed) == 2


class TestChunkEmbed:
    def test_small_embed_passthrough(self):
        embed = Embed(
            title="Small",
            description="Desc",
            color=0x00FF00,
            fields=[Field(name="f1", value="v1")],
            timestamp="2025-01-01T00:00:00Z",
            author=Author(name="Bot"),
            footer=Footer(text="Footer"),
        )
        chunks = _chunk_embed(embed)
        assert len(chunks) == 1
        assert chunks[0] is embed

    def test_large_embed_splits(self):
        # Create fields that will exceed the limit
        fields = [Field(name=f"field-{i}", value="x" * 500) for i in range(20)]
        embed = Embed(
            title="Big Embed",
            description="Description",
            color=0xFF0000,
            fields=fields,
            timestamp="2025-01-01T00:00:00Z",
            author=Author(name="Bot"),
            footer=Footer(text="Footer"),
        )
        chunks = _chunk_embed(embed)
        assert len(chunks) > 1

    def test_first_chunk_has_original_metadata(self):
        fields = [Field(name=f"f{i}", value="x" * 500) for i in range(20)]
        embed = Embed(
            title="Original Title",
            description="Original Desc",
            color=0xABCDEF,
            fields=fields,
            timestamp="2025-06-01T00:00:00Z",
            author=Author(name="TestBot"),
            footer=Footer(text="TestFooter"),
        )
        chunks = _chunk_embed(embed)
        first = chunks[0]
        assert first.title == "Original Title"
        assert first.description == "Original Desc"
        assert first.author is not None
        assert first.author.name == "TestBot"
        assert first.color == 0xABCDEF

    def test_continuation_chunks_have_continued_title_and_no_author(self):
        fields = [Field(name=f"f{i}", value="x" * 500) for i in range(20)]
        embed = Embed(
            title="My Title",
            description="Desc",
            color=0x123456,
            fields=fields,
            timestamp="2025-01-01T00:00:00Z",
            author=Author(name="Bot"),
            footer=Footer(text="Footer"),
        )
        chunks = _chunk_embed(embed)
        for chunk in chunks[1:]:
            assert chunk.title == "My Title (continued)"
            assert chunk.author is None
            assert chunk.description == ""

    def test_all_chunks_same_color(self):
        fields = [Field(name=f"f{i}", value="x" * 500) for i in range(20)]
        embed = Embed(
            title="Title",
            description="Desc",
            color=0xDEADBE,
            fields=fields,
            timestamp="",
        )
        chunks = _chunk_embed(embed)
        for chunk in chunks:
            assert chunk.color == 0xDEADBE

    def test_all_chunks_have_footer(self):
        fields = [Field(name=f"f{i}", value="x" * 500) for i in range(20)]
        embed = Embed(
            title="Title",
            description="Desc",
            color=0,
            fields=fields,
            timestamp="",
            footer=Footer(text="BeanLab"),
        )
        chunks = _chunk_embed(embed)
        for chunk in chunks:
            assert chunk.footer is not None
            assert chunk.footer.text == "BeanLab"

    def test_each_chunk_under_limit(self):
        fields = [Field(name=f"field-{i}", value="x" * 500) for i in range(20)]
        embed = Embed(
            title="Title",
            description="Desc",
            color=0,
            fields=fields,
            timestamp="",
            author=Author(name="Bot"),
            footer=Footer(text="Footer"),
        )
        chunks = _chunk_embed(embed)
        for chunk in chunks:
            assert _calc_embed_size(chunk) <= MAX_EMBED_CHARS

    def test_total_field_count_preserved(self):
        fields = [Field(name=f"f{i}", value="x" * 500) for i in range(15)]
        embed = Embed(
            title="Title",
            description="Desc",
            color=0,
            fields=fields,
            timestamp="",
        )
        chunks = _chunk_embed(embed)
        total_fields = sum(len(c.fields) for c in chunks)
        assert total_fields == 15

    def test_no_footer_case(self):
        fields = [Field(name=f"f{i}", value="x" * 500) for i in range(20)]
        embed = Embed(
            title="Title",
            description="Desc",
            color=0,
            fields=fields,
            timestamp="",
            footer=None,
        )
        chunks = _chunk_embed(embed)
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.footer is None

    def test_typical_pypi_embed_stays_single(self):
        # A typical pypi notification is small enough to fit in one embed
        fields = [
            Field(name="Package", value="my-package"),
            Field(name="Version", value="1.2.3"),
            Field(name="Status", value="Published"),
        ]
        embed = Embed(
            title="PyPI Update",
            description="A new version has been published.",
            color=0x3B82F6,
            fields=fields,
            timestamp="2025-01-01T00:00:00Z",
            author=Author(name="PyPI Bot"),
            footer=Footer(text="BeanLab Dev Utils"),
        )
        chunks = _chunk_embed(embed)
        assert len(chunks) == 1
