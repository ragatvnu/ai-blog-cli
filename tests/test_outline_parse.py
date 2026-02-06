import pytest

from ai_blog.outline_parse import OutlineParseError, get_section, parse_outline_file


def test_parse_outline_with_frontmatter(tmp_path):
    content = """---\ntitle: \"Test Outline\"\ntopic: \"test topic\"\n---\n# Test Outline\n\n## First Section\n- one\n- two\n\n## Second Section\n- three\n"""
    path = tmp_path / "outline.md"
    path.write_text(content, encoding="utf-8")

    doc = parse_outline_file(path)
    assert doc.title == "Test Outline"
    assert doc.frontmatter["topic"] == "test topic"
    assert len(doc.sections) == 2
    assert doc.sections[0].heading == "First Section"
    assert "- one" in doc.sections[0].body_lines


def test_parse_outline_no_h2(tmp_path):
    path = tmp_path / "outline.md"
    path.write_text("# Title\n\nNo sections here.\n", encoding="utf-8")

    with pytest.raises(OutlineParseError, match="No H2 sections found"):
        parse_outline_file(path)


def test_parse_outline_frontmatter_not_closed(tmp_path):
    path = tmp_path / "outline.md"
    path.write_text("---\ntitle: \"Test\"\n# Title\n", encoding="utf-8")

    with pytest.raises(OutlineParseError, match="Frontmatter started but not closed"):
        parse_outline_file(path)


def test_get_section_out_of_range(tmp_path):
    content = "# Title\n\n## Only Section\n- one\n"
    path = tmp_path / "outline.md"
    path.write_text(content, encoding="utf-8")
    doc = parse_outline_file(path)

    with pytest.raises(OutlineParseError, match="Section out of range"):
        get_section(doc, 2)
