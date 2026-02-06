from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class OutlineParseError(Exception):
    """Raised when an outline file cannot be parsed."""


@dataclass
class OutlineSection:
    heading: str
    body_lines: list[str]


@dataclass
class OutlineDoc:
    path: Path
    frontmatter: dict[str, str]
    title: str | None
    sections: list[OutlineSection]


def _parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], int]:
    if not lines or lines[0].strip() != "---":
        return {}, 0
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise OutlineParseError("Frontmatter started but not closed")

    fm: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            try:
                value = json.loads(value)
            except Exception:
                pass
        fm[key] = value
    return fm, end + 1


def parse_outline_file(path: str | Path) -> OutlineDoc:
    file_path = Path(path)
    if not file_path.exists():
        raise OutlineParseError(f"File not found: {file_path}")

    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    frontmatter, start_idx = _parse_frontmatter(lines)

    title = None
    sections: list[OutlineSection] = []
    current_heading = None
    current_body: list[str] = []

    for line in lines[start_idx:]:
        if line.startswith("# "):
            if title is None:
                title = line[2:].strip()
            continue
        if line.startswith("## "):
            if current_heading is not None:
                sections.append(
                    OutlineSection(heading=current_heading, body_lines=current_body)
                )
            current_heading = line[3:].strip()
            current_body = []
            continue
        if current_heading is not None:
            current_body.append(line)

    if current_heading is not None:
        sections.append(OutlineSection(heading=current_heading, body_lines=current_body))

    if not sections:
        raise OutlineParseError("No H2 sections found")

    return OutlineDoc(
        path=file_path,
        frontmatter=frontmatter,
        title=title,
        sections=sections,
    )


def get_section(doc: OutlineDoc, idx: int) -> OutlineSection:
    if idx < 1 or idx > len(doc.sections):
        raise OutlineParseError(
            f"Section out of range: {idx} (1-{len(doc.sections)})"
        )
    return doc.sections[idx - 1]
