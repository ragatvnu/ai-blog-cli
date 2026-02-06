## 💰 Pro Version

Get the paid version (includes full source, mock & dry-run modes):

👉 Buy here: https://ragatvnu.gumroad.com/l/ai-blog-cli


# AI Blog CLI

Generate SEO-friendly Markdown blog posts from a keyword/topic with a predictable structure and clean output files.

## Install

```bash
cd ai-blog-cli
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export OPENAI_API_KEY="your_key"
```

Optional model override:

```bash
export AI_BLOG_MODEL="gpt-4o-mini"
```

Or create a `.env` file in the project root or current working directory:

```env
OPENAI_API_KEY=sk-your-key-here
AI_BLOG_MODEL=gpt-4o-mini
```

## Usage

Single topic:

```bash
python -m ai_blog generate --topic "best earbuds under 5000 in india" --words 1200 --tone "friendly" --audience "beginners" --out ./out
```

Mock provider (no API calls):

```bash
python -m ai_blog generate --topic "best earbuds under 5000 in india" --out ./out --provider mock
```

Batch mode (one topic per line):

```bash
python -m ai_blog batch --topics topics.txt --words 1200 --out ./out
```

Outline only:

```bash
python -m ai_blog outline --topic "best laptops for writers" --out ./out
```

Dry run (no API calls, uses bundled sample output):

```bash
python -m ai_blog generate --topic "best earbuds under 5000 in india" --out ./out --dry-run
```

## What It Produces

Each `.md` file includes:

- YAML frontmatter (`title`, `slug`, `meta_description`, `date`, `topic`, `word_count_target`)
- H1 title, intro, quick answer, 5-8 H2 sections, decision checklist, FAQs, and conclusion + CTA

## Exit Codes

- `0` success
- `2` missing or invalid `OPENAI_API_KEY`
- `3` rate limit or quota exceeded
- `4` mock/dry-run generator regression

## Pro Version Roadmap

- WordPress publishing
- Image generation and placement
- Internal link suggestions
- Multi-language support

## License

MIT (add your preferred license if different).
