SYSTEM_MESSAGE = (
    "You are an expert SEO writer and editor. "
    "You write clear, factual, and helpful blog posts in Markdown. "
    "Follow structure requirements exactly."
)


def blog_user_prompt(topic, words, tone, audience, country):
    return f"""
Write a complete SEO-friendly blog post in Markdown.

Topic: {topic}
Target words: {words}
Tone: {tone}
Audience: {audience}
Country: {country}

OUTPUT REQUIREMENTS (STRICT ORDER):
1) H1 title
2) Short intro (2-4 paragraphs)
3) H2 section titled "Quick answer" with bullet points
4) 5-8 H2 sections, each with useful content
5) H2 section titled "Decision checklist" with bullet points
6) H2 section titled "FAQs" with 5-8 Q/A pairs in this format:
   Q: ...
   A: ...
7) H2 section titled "Conclusion" with a CTA in the last paragraph

Return EXACTLY in this format:
TITLE: <title>
META: <meta description, 155 chars max>
BODY:
<markdown body>

Ensure the body contains at least 5 H2 headings and FAQs have at least 5 Q/A pairs.
""".strip()


def outline_user_prompt(topic, tone, audience, country):
    return f"""
Create a concise blog outline in Markdown for the topic below.

Topic: {topic}
Tone: {tone}
Audience: {audience}
Country: {country}

Output a Markdown outline with:
- H1 title
- 5-8 H2 headings
- A short list of FAQ questions (5-8) under an H2 "FAQs"

Return EXACTLY in this format:
TITLE: <title>
META: <meta description, 155 chars max>
BODY:
<markdown outline>
""".strip()


def repair_user_prompt(topic, words, tone, audience, country, issues, body):
    issues_str = "\n".join(f"- {i}" for i in issues)
    return f"""
Fix the Markdown body to resolve the formatting issues below.

Topic: {topic}
Target words: {words}
Tone: {tone}
Audience: {audience}
Country: {country}

Issues:
{issues_str}

Rules:
- Keep existing content where possible.
- Ensure at least 5 H2 headings.
- Ensure the FAQs section has 5-8 Q/A pairs in Q:/A: format.
- Do not include frontmatter, title line, or meta description.

Return ONLY the corrected Markdown body (no extra labels).

BODY TO FIX:
{body}
""".strip()
