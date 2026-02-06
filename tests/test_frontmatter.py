import re

from ai_blog.utils import build_frontmatter


def test_frontmatter_fields():
    fm = build_frontmatter(
        title="Test Title",
        slug="test-title",
        meta_description="Short meta",
        topic="Test Topic",
        word_count_target=1200,
        date_str="2026-02-05",
    )

    assert fm.startswith("---\n")
    assert "title:" in fm
    assert "slug:" in fm
    assert "meta_description:" in fm
    assert "date:" in fm
    assert "topic:" in fm
    assert "word_count_target:" in fm

    match = re.search(r"date: \"(\d{4}-\d{2}-\d{2})\"", fm)
    assert match
