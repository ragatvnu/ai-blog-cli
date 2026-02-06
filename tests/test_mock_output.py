import json
import re

from ai_blog.generator import generate_article
from ai_blog.utils import count_faqs, count_h2


def _parse_frontmatter(content: str) -> dict:
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


def test_mock_output_structure(tmp_path):
    topic = "best earbuds under 5000 in india"
    article = generate_article(
        topic=topic,
        words=1200,
        tone="friendly",
        audience="beginners",
        country="India",
        out_dir=str(tmp_path),
        model="gpt-4o-mini",
        provider="mock",
        dry_run=False,
    )

    content = tmp_path.joinpath(f"{article.slug}.md").read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(content)

    for key in ["title", "slug", "meta_description", "date", "topic"]:
        assert key in fm

    meta = json.loads(fm["meta_description"])
    assert len(meta) <= 155

    assert re.search(r"^#\s+", body, re.MULTILINE)
    assert count_h2(body) >= 5
    assert count_faqs(body) >= 5
