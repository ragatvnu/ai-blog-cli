import json
import re

from ai_blog.generator import generate_outline
from ai_blog.utils import count_h2


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    assert content.startswith("---\n")
    parts = content.split("\n---\n", 1)
    assert len(parts) == 2
    fm_block = parts[0].splitlines()[1:]
    fm = {}
    for line in fm_block:
        if not line.strip():
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = value.strip()
    return fm, parts[1]


def _section_bullet_counts(body: str) -> dict[str, int]:
    lines = body.splitlines()
    indices = [i for i, line in enumerate(lines) if line.startswith("## ")]
    counts: dict[str, int] = {}
    for idx, start in enumerate(indices):
        end = indices[idx + 1] if idx + 1 < len(indices) else len(lines)
        heading = lines[start][3:].strip()
        count = 0
        for line in lines[start + 1 : end]:
            if re.match(r"^\\s*-\\s+", line):
                count += 1
        counts[heading] = count
    return counts


def test_outline_mock_output(tmp_path):
    topic = "test topic"
    generate_outline(
        topic=topic,
        tone="friendly",
        audience="beginners",
        country="India",
        out_dir=str(tmp_path),
        model="gpt-4o-mini",
        provider="mock",
        dry_run=False,
    )

    content = tmp_path.joinpath("test-topic-outline.md").read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(content)

    for key in [
        "title",
        "slug",
        "meta_description",
        "date",
        "topic",
        "kind",
        "provider",
        "dry_run",
    ]:
        assert key in fm

    meta = json.loads(fm["meta_description"])
    assert len(meta) <= 155

    assert re.search(r"^#\\s+", body, re.MULTILINE)
    assert count_h2(body) >= 8

    counts = _section_bullet_counts(body)
    assert "FAQs" in counts
    assert counts["FAQs"] >= 5

    for heading, count in counts.items():
        if heading != "FAQs":
            assert 3 <= count <= 6


def test_outline_deterministic(tmp_path):
    topic = "test topic"
    generate_outline(
        topic=topic,
        tone="friendly",
        audience="beginners",
        country="India",
        out_dir=str(tmp_path),
        model="gpt-4o-mini",
        provider="mock",
        dry_run=False,
    )
    first = tmp_path.joinpath("test-topic-outline.md").read_text(encoding="utf-8")

    generate_outline(
        topic=topic,
        tone="friendly",
        audience="beginners",
        country="India",
        out_dir=str(tmp_path),
        model="gpt-4o-mini",
        provider="mock",
        dry_run=False,
    )
    second = tmp_path.joinpath("test-topic-outline.md").read_text(encoding="utf-8")

    assert first == second
