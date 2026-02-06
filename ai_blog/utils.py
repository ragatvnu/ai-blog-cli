import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from slugify import slugify as _slugify


@dataclass
class ParsedOutput:
    title: str
    meta_description: str
    body: str


def slugify_topic(topic: str) -> str:
    return _slugify(topic, lowercase=True, separator="-")


def ensure_out_dir(out_dir: str | Path) -> Path:
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def build_frontmatter(
    title: str,
    slug: str,
    meta_description: str,
    topic: str,
    word_count_target: int,
    date_str: str | None = None,
    dry_run: bool = False,
) -> str:
    if date_str is None:
        date_str = date.today().isoformat()
    lines = [
        "---",
        f"title: {_yaml_quote(title)}",
        f"slug: {_yaml_quote(slug)}",
        f"meta_description: {_yaml_quote(meta_description)}",
        f"date: {_yaml_quote(date_str)}",
        f"topic: {_yaml_quote(topic)}",
        f"word_count_target: {word_count_target}",
    ]
    if dry_run:
        lines.append("dry_run: true")
    lines.append("---")
    return "\n".join(lines)


def trim_meta(meta: str, max_len: int = 155) -> str:
    clean = " ".join(meta.split())
    if len(clean) <= max_len:
        return clean
    trimmed = clean[:max_len]
    if " " in trimmed:
        trimmed = trimmed.rsplit(" ", 1)[0]
    trimmed = trimmed.rstrip(" -:;,.\n\t")
    if not trimmed:
        return clean[:max_len].rstrip()
    return trimmed


def parse_model_output(text: str) -> ParsedOutput:
    title = None
    meta = None
    body = None

    lines = text.splitlines()
    for i, line in enumerate(lines):
        if title is None and line.startswith("TITLE:"):
            title = line[len("TITLE:") :].strip()
            continue
        if meta is None and line.startswith("META:"):
            meta = line[len("META:") :].strip()
            continue
        if line.startswith("BODY:"):
            remainder = line[len("BODY:") :].lstrip()
            body_lines = []
            if remainder:
                body_lines.append(remainder)
            body_lines.extend(lines[i + 1 :])
            body = "\n".join(body_lines).lstrip("\n")
            break

    if not title or not meta or body is None:
        raise ValueError("Model output missing TITLE, META, or BODY sections.")

    return ParsedOutput(title=title, meta_description=meta, body=body)


def count_h1(body: str) -> int:
    return sum(1 for line in body.splitlines() if line.startswith("# "))


def count_h2(body: str) -> int:
    return sum(1 for line in body.splitlines() if line.startswith("## "))


def count_faqs(body: str) -> int:
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("## faq"):
            start = i + 1
            break
    if start is None:
        return 0

    count = 0
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if re.match(r"^\s*Q:\s+", line, re.IGNORECASE):
            count += 1
    return count


def validate_body(body: str) -> list[str]:
    issues: list[str] = []
    if count_h1(body) < 1:
        issues.append("Missing H1 title")
    if count_h2(body) < 5:
        issues.append("Needs at least 5 H2 headings")
    if count_faqs(body) < 5:
        issues.append("FAQs must include at least 5 Q/A pairs")
    return issues


def write_markdown(path: Path, frontmatter: str, body: str) -> None:
    content = f"{frontmatter}\n\n{body.strip()}\n"
    path.write_text(content, encoding="utf-8")
