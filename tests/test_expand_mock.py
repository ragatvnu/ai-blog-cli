from ai_blog.generator import expand_section
from ai_blog.outline_parse import get_section, parse_outline_file
from ai_blog.utils import slugify_topic


def test_expand_mock_deterministic(tmp_path):
    content = """---\ntitle: \"Test Outline\"\ntopic: \"test topic\"\n---\n# Test Outline\n\n## First Section\n- bullet one\n- bullet two\n\n## FAQs\n- Q1?\n- Q2?\n- Q3?\n- Q4?\n- Q5?\n"""
    path = tmp_path / "outline.md"
    path.write_text(content, encoding="utf-8")

    doc = parse_outline_file(path)
    section = get_section(doc, 1)
    expected_slug = slugify_topic(section.heading)

    first = expand_section(
        section_heading=section.heading,
        section_body_lines=section.body_lines,
        topic=doc.frontmatter.get("topic"),
        tone="friendly",
        audience="beginners",
        country="India",
        model="gpt-4o-mini",
        provider="mock",
        dry_run=False,
    )
    second = expand_section(
        section_heading=section.heading,
        section_body_lines=section.body_lines,
        topic=doc.frontmatter.get("topic"),
        tone="friendly",
        audience="beginners",
        country="India",
        model="gpt-4o-mini",
        provider="mock",
        dry_run=False,
    )

    assert first.startswith("## ")
    assert first == second
    assert expected_slug == "first-section"


def test_expand_output_filename(tmp_path):
    content = """---\ntitle: \"Test Outline\"\ntopic: \"test topic\"\n---\n# Test Outline\n\n## First Section\n- bullet one\n- bullet two\n"""
    outline_path = tmp_path / "outline.md"
    outline_path.write_text(content, encoding="utf-8")

    doc = parse_outline_file(outline_path)
    section = get_section(doc, 1)
    expected_filename = f"01-{slugify_topic(section.heading)}.md"

    # Simulate CLI naming logic
    out_dir = tmp_path / "expanded"
    out_dir.mkdir()
    out_path = out_dir / expected_filename

    out_path.write_text(
        expand_section(
            section_heading=section.heading,
            section_body_lines=section.body_lines,
            topic=doc.frontmatter.get("topic"),
            tone="friendly",
            audience="beginners",
            country="India",
            model="gpt-4o-mini",
            provider="mock",
            dry_run=False,
        ),
        encoding="utf-8",
    )

    assert out_path.exists()
