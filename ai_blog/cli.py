import os
from enum import Enum
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

from .generator import generate_article, generate_outline, resolve_model, expand_section
from .errors import OpenAIAuthError, OpenAIRateLimitError, MockDryRunRegressionError
from .outline_parse import OutlineParseError, get_section, parse_outline_file
from .utils import slugify_topic

app = typer.Typer(help="Generate SEO-friendly Markdown blog posts.")
console = Console()
_DOTENV_LOADED = False


class Provider(str, Enum):
    openai = "openai"
    mock = "mock"


def _load_dotenv() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    project_root = Path(__file__).resolve().parents[1]
    cwd = Path.cwd()
    candidates = [project_root / ".env"]
    if cwd != project_root:
        candidates.append(cwd / ".env")
    for env_path in candidates:
        if env_path.exists():
            load_dotenv(env_path, override=False)
    _DOTENV_LOADED = True


def _require_api_key() -> None:
    _load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        console.print(
            "[red]OPENAI_API_KEY is not set. Please export your OpenAI API key.[/red]"
        )
        raise typer.Exit(code=2)


@app.command()
def generate(
    topic: str = typer.Option(..., help="Topic or keyword for the post."),
    words: int = typer.Option(1200, help="Target word count."),
    tone: str = typer.Option("friendly", help="Tone of voice."),
    audience: str = typer.Option("beginners", help="Target audience."),
    country: str = typer.Option("India", help="Target country/context."),
    out: Path = typer.Option("./out", help="Output directory."),
    model: str = typer.Option(None, help="OpenAI model (overrides env)."),
    provider: Provider = typer.Option(
        Provider.openai, help="Content provider: openai or mock."
    ),
    dry_run: bool = typer.Option(False, help="Skip OpenAI calls and use sample output."),
):
    if not dry_run and provider == Provider.openai:
        _require_api_key()
    selected_model = resolve_model(model)
    try:
        article = generate_article(
            topic=topic,
            words=words,
            tone=tone,
            audience=audience,
            country=country,
            out_dir=str(out),
            model=selected_model,
            provider=provider.value,
            dry_run=dry_run,
        )
        console.print(f"[green]Saved:[/green] {article.path}")
    except MockDryRunRegressionError:
        console.print("[red]Mock/Dry-run generator regression[/red]")
        raise typer.Exit(code=4)
    except OpenAIAuthError:
        console.print(
            "[red]Authentication failed. Please check OPENAI_API_KEY and try again.[/red]"
        )
        raise typer.Exit(code=2)
    except OpenAIRateLimitError:
        console.print(
            "[red]Rate limit or quota exceeded. To fix:[/red]\n"
            "- Check your OpenAI billing status and add a payment method\n"
            "- Review usage and limits for your account\n"
            "- Wait a few minutes and retry if you're rate-limited"
        )
        raise typer.Exit(code=3)


@app.command()
def batch(
    topics: Path = typer.Option(..., help="Path to topics file (one per line)."),
    words: int = typer.Option(1200, help="Target word count."),
    tone: str = typer.Option("friendly", help="Tone of voice."),
    audience: str = typer.Option("beginners", help="Target audience."),
    country: str = typer.Option("India", help="Target country/context."),
    out: Path = typer.Option("./out", help="Output directory."),
    model: str = typer.Option(None, help="OpenAI model (overrides env)."),
    provider: Provider = typer.Option(
        Provider.openai, help="Content provider: openai or mock."
    ),
    dry_run: bool = typer.Option(False, help="Skip OpenAI calls and use sample output."),
):
    if not dry_run and provider == Provider.openai:
        _require_api_key()
    selected_model = resolve_model(model)
    if not topics.exists():
        console.print(f"[red]Topics file not found:[/red] {topics}")
        raise typer.Exit(code=1)

    lines = [line.strip() for line in topics.read_text(encoding="utf-8").splitlines()]
    topic_list = [line for line in lines if line and not line.startswith("#")]
    if not topic_list:
        console.print("[red]No topics found in file.[/red]")
        raise typer.Exit(code=1)

    for t in topic_list:
        try:
            article = generate_article(
                topic=t,
                words=words,
                tone=tone,
                audience=audience,
                country=country,
                out_dir=str(out),
                model=selected_model,
                provider=provider.value,
                dry_run=dry_run,
            )
            console.print(f"[green]Saved:[/green] {article.path}")
        except MockDryRunRegressionError:
            console.print("[red]Mock/Dry-run generator regression[/red]")
            raise typer.Exit(code=4)
        except OpenAIAuthError:
            console.print(
                "[red]Authentication failed. Please check OPENAI_API_KEY and try again.[/red]"
            )
            raise typer.Exit(code=2)
        except OpenAIRateLimitError:
            console.print(
                "[red]Rate limit or quota exceeded. To fix:[/red]\n"
                "- Check your OpenAI billing status and add a payment method\n"
                "- Review usage and limits for your account\n"
                "- Wait a few minutes and retry if you're rate-limited"
            )
            raise typer.Exit(code=3)
        except Exception as exc:
            console.print(f"[red]Failed:[/red] {t} ({exc})")


@app.command()
def outline(
    topic: str = typer.Option(..., help="Topic or keyword for the outline."),
    tone: str = typer.Option("friendly", help="Tone of voice."),
    audience: str = typer.Option("beginners", help="Target audience."),
    country: str = typer.Option("India", help="Target country/context."),
    out: Path = typer.Option("./out", help="Output directory."),
    model: str = typer.Option(None, help="OpenAI model (overrides env)."),
    provider: Provider = typer.Option(
        Provider.openai, help="Content provider: openai or mock."
    ),
    dry_run: bool = typer.Option(False, help="Skip OpenAI calls and use sample output."),
):
    if not dry_run and provider == Provider.openai:
        _require_api_key()
    selected_model = resolve_model(model)
    try:
        article = generate_outline(
            topic=topic,
            tone=tone,
            audience=audience,
            country=country,
            out_dir=str(out),
            model=selected_model,
            provider=provider.value,
            dry_run=dry_run,
        )
        console.print(f"[green]Saved:[/green] {article.path}")
    except MockDryRunRegressionError:
        console.print("[red]Mock/Dry-run generator regression[/red]")
        raise typer.Exit(code=4)
    except OpenAIAuthError:
        console.print(
            "[red]Authentication failed. Please check OPENAI_API_KEY and try again.[/red]"
        )
        raise typer.Exit(code=2)
    except OpenAIRateLimitError:
        console.print(
            "[red]Rate limit or quota exceeded. To fix:[/red]\n"
            "- Check your OpenAI billing status and add a payment method\n"
            "- Review usage and limits for your account\n"
            "- Wait a few minutes and retry if you're rate-limited"
        )
        raise typer.Exit(code=3)


@app.command()
def expand(
    outline: Path = typer.Option(..., help="Path to outline markdown file."),
    section: int = typer.Option(..., help="1-based index of the H2 section to expand."),
    out: Path = typer.Option("./out", help="Output directory or file path."),
    model: str = typer.Option(None, help="OpenAI model (overrides env)."),
    provider: Provider = typer.Option(
        Provider.openai, help="Content provider: openai or mock."
    ),
    dry_run: bool = typer.Option(False, help="Print to stdout and skip file output."),
    tone: str = typer.Option("friendly", help="Tone of voice."),
    audience: str = typer.Option("beginners", help="Target audience."),
    country: str = typer.Option("India", help="Target country/context."),
):
    if not dry_run and provider == Provider.openai:
        _require_api_key()
    selected_model = resolve_model(model)

    try:
        doc = parse_outline_file(outline)
        section_obj = get_section(doc, section)
    except OutlineParseError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    topic = None
    if "topic" in doc.frontmatter:
        topic = str(doc.frontmatter["topic"])
    elif doc.title:
        topic = doc.title

    try:
        content = expand_section(
            section_heading=section_obj.heading,
            section_body_lines=section_obj.body_lines,
            topic=topic,
            tone=tone,
            audience=audience,
            country=country,
            model=selected_model,
            provider=provider.value,
            dry_run=dry_run,
        )
    except OpenAIAuthError:
        console.print(
            "[red]Authentication failed. Please check OPENAI_API_KEY and try again.[/red]"
        )
        raise typer.Exit(code=2)
    except OpenAIRateLimitError:
        console.print(
            "[red]Rate limit or quota exceeded. To fix:[/red]\n"
            "- Check your OpenAI billing status and add a payment method\n"
            "- Review usage and limits for your account\n"
            "- Wait a few minutes and retry if you're rate-limited"
        )
        raise typer.Exit(code=3)

    if dry_run:
        print(content)
        return

    out_path = out
    if out_path.suffix != ".md" and not (out_path.exists() and out_path.is_file()):
        out_path.mkdir(parents=True, exist_ok=True)
        slug = slugify_topic(section_obj.heading)
        out_path = out_path / f"{section:02d}-{slug}.md"
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)

    out_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    console.print(f"[green]Saved:[/green] {out_path}")
