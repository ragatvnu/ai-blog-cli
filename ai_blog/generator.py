from __future__ import annotations

import hashlib
import os
import random
import re
from dataclasses import dataclass

from . import prompts
from .errors import OpenAIAuthError, OpenAIRateLimitError, MockDryRunRegressionError
from .utils import (
    ParsedOutput,
    build_frontmatter,
    ensure_out_dir,
    parse_model_output,
    slugify_topic,
    trim_meta,
    validate_body,
    write_markdown,
)


@dataclass
class Article:
    title: str
    meta_description: str
    body: str
    slug: str
    path: str


def _openai_error_classes():
    try:
        from openai import AuthenticationError as OAAuthError
        from openai import RateLimitError as OARateLimitError
    except Exception as exc:
        raise RuntimeError("OpenAI SDK not available. Install openai.") from exc
    return OAAuthError, OARateLimitError


def _openai_client():
    try:
        from openai import OpenAI
    except Exception as exc:
        raise RuntimeError("OpenAI SDK not available. Install openai.") from exc
    return OpenAI()


def _call_openai(
    client,
    auth_error_cls,
    rate_error_cls,
    model: str,
    system: str,
    user: str,
) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    try:
        response = client.responses.create(model=model, input=messages)
        return response.output_text
    except auth_error_cls as exc:
        raise OpenAIAuthError(str(exc)) from exc
    except rate_error_cls as exc:
        raise OpenAIRateLimitError(str(exc)) from exc
    except Exception:
        try:
            response = client.chat.completions.create(model=model, messages=messages)
            return response.choices[0].message.content
        except auth_error_cls as exc:
            raise OpenAIAuthError(str(exc)) from exc
        except rate_error_cls as exc:
            raise OpenAIRateLimitError(str(exc)) from exc


def _topic_words(topic: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+", topic.lower())
    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "for",
        "to",
        "of",
        "in",
        "on",
        "under",
        "over",
        "with",
        "without",
        "best",
        "top",
        "vs",
        "vs.",
        "guide",
        "buy",
        "buying",
    }
    filtered = [w for w in words if w not in stopwords]
    if not filtered:
        return ["quality", "budget", "features"]
    seen: set[str] = set()
    unique = []
    for w in filtered:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique


def _title_case(text: str) -> str:
    return " ".join(part.capitalize() for part in text.split())


def _build_dry_run_output(
    topic: str,
    words: int,
    tone: str,
    audience: str,
    country: str,
    banner: str,
    mode_label: str,
) -> ParsedOutput:
    seed_base = f"{topic}|{country}|{tone}|{audience}"
    seed = int(hashlib.sha256(seed_base.encode("utf-8")).hexdigest()[:16], 16)
    rnd = random.Random(seed)

    topic_title = _title_case(topic)
    title = f"{topic_title} in {country}: A {audience.title()} Guide"

    meta = (
        f"Learn how to choose {topic} in {country} with a quick checklist, "
        f"key features, and FAQs for {audience}."
    )

    words_list = _topic_words(topic)
    num_sections = 5 + (seed % 2)
    templates = [
        "Key {word} features for {topic}",
        "How {word} affects day-to-day use",
        "Comparing {word} options in {country}",
        "Balancing {word} with budget",
        "Common mistakes with {word} and how to avoid them",
        "Choosing {word} for long-term value",
    ]
    rnd.shuffle(templates)

    headings = []
    for i in range(num_sections):
        word = words_list[i % len(words_list)]
        template = templates[i % len(templates)]
        headings.append(
            template.format(word=word, topic=topic, country=country).replace(
                "  ", " "
            )
        )

    intro_variants = [
        banner,
        (
            f"This article demonstrates the required structure for a post "
            f"about {topic} in {country}."
        ),
        (
            f"It is written for {audience} in a {tone} tone and uses deterministic "
            f"placeholders for stable tests."
        ),
        (
            "Use it as a scaffold before generating a real article with live data."
        ),
    ]
    intro_paragraphs = intro_variants[: 2 + (seed % 2)]

    india_label = "India"

    def intro_sentence(section_label: str) -> str:
        if country.strip().lower() != "india":
            region = f"{india_label} and {country}"
        else:
            region = india_label
        return (
            f"For {audience} in {region}, {topic} choices around "
            f"{section_label.lower()} should stay practical and value-focused."
        )

    def pick_bullets(templates: list[str]) -> list[str]:
        options = templates[:]
        rnd.shuffle(options)
        count = 3 + rnd.randint(0, 2)
        bullets = []
        for i in range(count):
            word = words_list[i % len(words_list)]
            bullets.append(
                options[i % len(options)].format(
                    topic=topic,
                    audience=audience,
                    country=country,
                    india=india_label,
                    word=word,
                )
            )
        return bullets

    tip_templates = [
        "If two options look similar, choose the one with better comfort and service support in India.",
        "Compare real reviews for call quality and durability before you decide.",
        "Prioritize everyday usability over flashy marketing specs.",
        "Keep your top two picks and check warranty terms in India.",
    ]

    quick_templates = [
        "Set a clear budget before comparing {topic} in {india}.",
        "Focus on comfort and {word} performance for {audience}.",
        "Prioritize reliable calls and day-to-day usability.",
        "Choose brands with proven service support in {india}.",
        "Shortlist 2-3 options and compare real-world reviews.",
    ]

    main_templates = [
        "Define a budget cap before comparing {topic} in {india}.",
        "Prioritize {word} comfort and fit for {audience}.",
        "Check battery life claims against real-world use.",
        "Compare mic clarity and call quality for daily use.",
        "Look for dependable warranty and service coverage in {india}.",
        "Avoid overpaying for features you won't use.",
        "Shortlist 2-3 options and compare value per feature.",
    ]

    checklist_templates = [
        "Budget fits your range and value expectations",
        "Comfortable fit for {audience} daily use",
        "Balanced performance for {topic}",
        "Warranty and service coverage in {india}",
        "Return or replacement policy you trust",
    ]

    faq_templates = [
        "What should I prioritize when choosing {topic} in {country}?",
        "How do I compare {topic} options fairly?",
        "Is it okay to choose the cheapest {topic} available?",
        "What features matter most for {audience}?",
        "How long should I expect {topic} to last?",
        "Are warranties important for {topic} in {country}?",
    ]
    rnd.shuffle(faq_templates)
    faqs = []
    for i in range(5):
        q = faq_templates[i].format(topic=topic, country=country, audience=audience)
        a = (
            f"For {topic} in {country}, focus on the basics first: comfort, "
            f"reliability, and value for your budget."
        )
        faqs.append((q, a))

    body_lines = [f"# {title}", ""]
    for p in intro_paragraphs:
        body_lines.append(p)
        body_lines.append("")

    body_lines.extend(["## Quick answer", ""])
    body_lines.append(intro_sentence("Quick answer"))
    body_lines.append("")
    for bullet in pick_bullets(quick_templates):
        body_lines.append(f"- {bullet}")
    body_lines.append("")
    body_lines.append(f"Tip: {rnd.choice(tip_templates)}")
    body_lines.append("")

    for heading in headings:
        body_lines.append(f"## {heading}")
        body_lines.append("")
        body_lines.append(intro_sentence(heading))
        body_lines.append("")
        for bullet in pick_bullets(main_templates):
            body_lines.append(f"- {bullet}")
        body_lines.append("")
        body_lines.append(f"Tip: {rnd.choice(tip_templates)}")
        body_lines.append("")

    body_lines.extend(["## Decision checklist", ""])
    body_lines.append(intro_sentence("Decision checklist"))
    body_lines.append("")
    for item in pick_bullets(checklist_templates):
        body_lines.append(f"- {item}")
    body_lines.append("")
    body_lines.append(f"Tip: {rnd.choice(tip_templates)}")
    body_lines.append("")

    body_lines.extend(["## FAQs", ""])
    body_lines.append(intro_sentence("FAQs"))
    body_lines.append("")
    for bullet in pick_bullets(main_templates):
        body_lines.append(f"- {bullet}")
    body_lines.append("")
    body_lines.append(f"Tip: {rnd.choice(tip_templates)}")
    body_lines.append("")
    for q, a in faqs:
        body_lines.append(f"Q: {q}")
        body_lines.append(f"A: {a}")
        body_lines.append("")

    body_lines.extend(
        [
            "## Conclusion",
            "",
            intro_sentence("Conclusion"),
            "",
        ]
    )
    for bullet in pick_bullets(main_templates):
        body_lines.append(f"- {bullet}")
    body_lines.extend(
        [
            "",
            f"Tip: {rnd.choice(tip_templates)}",
            "",
            f"This {mode_label.lower()} output shows the full structure for {topic} in {country}.",
            (
                f"If you want a tailored recommendation for {topic}, "
                f"share your budget and priorities and we can refine the shortlist."
            ),
        ]
    )

    body = "\n".join(body_lines).strip()
    return ParsedOutput(title=title, meta_description=meta, body=body)


def _build_dry_run_outline(
    topic: str,
    tone: str,
    audience: str,
    country: str,
) -> ParsedOutput:
    seed_base = f"{topic}|{country}|{tone}|{audience}|outline"
    seed = int(hashlib.sha256(seed_base.encode("utf-8")).hexdigest()[:16], 16)
    rnd = random.Random(seed)

    topic_title = _title_case(topic)
    title = f"{topic_title} in {country}: Outline"
    meta = (
        f"Outline for {topic} in {country}, covering key sections, checklist, and FAQs."
    )

    words_list = _topic_words(topic)
    templates = [
        "Overview: {topic}",
        "{word} priorities for {audience}",
        "Budget and value factors in {country}",
        "Common mistakes to avoid",
        "How to compare options",
        "Final decision checklist",
    ]
    rnd.shuffle(templates)
    headings = []
    for i in range(5):
        word = words_list[i % len(words_list)]
        headings.append(
            templates[i].format(
                topic=topic, word=word, audience=audience, country=country
            )
        )

    faq_questions = [
        f"What should I look for when choosing {topic} in {country}?",
        f"How do I compare {topic} options quickly?",
        f"Which {topic} features matter most for {audience}?",
        f"Is the cheapest {topic} a good idea?",
        f"How long should {topic} typically last?",
    ]

    body_lines = [f"# {title}", ""]
    for heading in headings:
        body_lines.append(f"## {heading}")
    body_lines.append("")
    body_lines.append("## FAQs")
    body_lines.append("")
    for q in faq_questions:
        body_lines.append(f"- {q}")

    body = "\n".join(body_lines).strip()
    return ParsedOutput(title=title, meta_description=meta, body=body)


def _repair_body(
    client,
    auth_error_cls,
    rate_error_cls,
    model: str,
    topic: str,
    words: int,
    tone: str,
    audience: str,
    country: str,
    issues: list[str],
    body: str,
) -> str:
    user = prompts.repair_user_prompt(
        topic=topic,
        words=words,
        tone=tone,
        audience=audience,
        country=country,
        issues=issues,
        body=body,
    )
    return _call_openai(
        client, auth_error_cls, rate_error_cls, model, prompts.SYSTEM_MESSAGE, user
    )


def generate_article(
    topic: str,
    words: int,
    tone: str,
    audience: str,
    country: str,
    out_dir: str,
    model: str,
    provider: str = "openai",
    dry_run: bool = False,
    client: object | None = None,
) -> Article:
    if provider not in {"openai", "mock"}:
        raise ValueError(f"Unknown provider: {provider}")

    if dry_run or provider == "mock":
        mode_label = "DRY RUN" if dry_run else "MOCK"
        banner = (
            f"{mode_label} OUTPUT: Deterministic placeholder content for "
            f"\"{topic}\" in {country}."
        )
        parsed = _build_dry_run_output(
            topic, words, tone, audience, country, banner, mode_label
        )
    else:
        if client is None:
            client = _openai_client()
        auth_error_cls, rate_error_cls = _openai_error_classes()
        user = prompts.blog_user_prompt(
            topic=topic,
            words=words,
            tone=tone,
            audience=audience,
            country=country,
        )
        raw = _call_openai(
            client, auth_error_cls, rate_error_cls, model, prompts.SYSTEM_MESSAGE, user
        )
        parsed = parse_model_output(raw)

    meta = trim_meta(parsed.meta_description, 155)
    body = parsed.body

    issues = validate_body(body)
    if issues:
        if provider == "openai" and not dry_run:
            repaired = _repair_body(
                client=client,
                auth_error_cls=auth_error_cls,
                rate_error_cls=rate_error_cls,
                model=model,
                topic=topic,
                words=words,
                tone=tone,
                audience=audience,
                country=country,
                issues=issues,
                body=body,
            )
            body = repaired.strip()
            issues = validate_body(body)
            if issues:
                raise ValueError(f"Validation failed after repair: {issues}")
        else:
            raise MockDryRunRegressionError("Mock/Dry-run generator regression")

    slug = slugify_topic(topic)
    frontmatter = build_frontmatter(
        title=parsed.title,
        slug=slug,
        meta_description=meta,
        topic=topic,
        word_count_target=words,
        dry_run=dry_run,
    )

    out_path = ensure_out_dir(out_dir) / f"{slug}.md"
    write_markdown(out_path, frontmatter, body)

    return Article(
        title=parsed.title,
        meta_description=meta,
        body=body,
        slug=slug,
        path=str(out_path),
    )


def generate_outline(
    topic: str,
    tone: str,
    audience: str,
    country: str,
    out_dir: str,
    model: str,
    provider: str = "openai",
    dry_run: bool = False,
    client: object | None = None,
) -> Article:
    if provider not in {"openai", "mock"}:
        raise ValueError(f"Unknown provider: {provider}")

    if dry_run or provider == "mock":
        parsed = _build_dry_run_outline(topic, tone, audience, country)
    else:
        if client is None:
            client = _openai_client()
        auth_error_cls, rate_error_cls = _openai_error_classes()
        user = prompts.outline_user_prompt(
            topic=topic,
            tone=tone,
            audience=audience,
            country=country,
        )
        raw = _call_openai(
            client, auth_error_cls, rate_error_cls, model, prompts.SYSTEM_MESSAGE, user
        )
        parsed = parse_model_output(raw)

    meta = trim_meta(parsed.meta_description, 155)
    body = parsed.body

    slug = slugify_topic(topic) + "-outline"
    frontmatter = build_frontmatter(
        title=parsed.title,
        slug=slug,
        meta_description=meta,
        topic=topic,
        word_count_target=0,
        dry_run=dry_run,
    )

    out_path = ensure_out_dir(out_dir) / f"{slug}.md"
    write_markdown(out_path, frontmatter, body)

    return Article(
        title=parsed.title,
        meta_description=meta,
        body=body,
        slug=slug,
        path=str(out_path),
    )


def resolve_model(cli_model: str | None) -> str:
    return (
        cli_model
        or os.getenv("AI_BLOG_MODEL")
        or os.getenv("OPENAI_MODEL")
        or "gpt-4o-mini"
    )
