"""Content generation: turn one topic into a blog post, podcast script, and newsletter blurb.

All three formats are generated from the SAME source material (the topic's extracted article text
+ summary + source URLs) and persisted as drafts linked to the originating topic, so one news item
fans out into a blog post, a podcast episode, and a newsletter section that reference each other.
Output is grounded in the sources and attributes them (blog frontmatter + a Sources section).
"""

from __future__ import annotations

import logging
import re
from datetime import date

from . import repository as repo
from .config import get_settings
from .db import get_conn
from .llm import generate as llm_generate
from .utm import with_utm
from .prompts import (
    DEFAULT_BRAND_VOICE,
    FORMAT_INSTRUCTION,
    FORMAT_SPECS,
    GROUNDING_RULE,
)

log = logging.getLogger("boosternews.generate")

MAX_SOURCE_CHARS = 6000
PREVIEW_CHARS = 280

_FENCE_RE = re.compile(r"^```[a-zA-Z]*\n(.*)\n```$", re.DOTALL)


# ── Pure helpers (unit-tested, no network/DB) ───────────────────────────────
def brand_voice() -> str:
    s = get_settings()
    if s.brand_voice:
        return s.brand_voice
    return DEFAULT_BRAND_VOICE.format(
        author=s.author_name, site=s.site_domain, language=s.content_language
    )


def _truncate(text: str, limit: int = MAX_SOURCE_CHARS) -> str:
    return text if len(text) <= limit else text[:limit] + "\n…[truncated]"


def source_block(topic: dict) -> str:
    """Assemble the SOURCE MATERIAL block passed to the model."""
    parts = [f"TITLE: {topic['title']}"]
    if topic.get("summary"):
        parts.append(f"SUMMARY: {topic['summary']}")
    text = topic.get("extracted_text")
    if text:
        parts.append("ARTICLE:\n" + _truncate(text))
    urls = topic.get("urls") or []
    if urls:
        parts.append("SOURCE URLS:\n" + "\n".join(urls))
    return "\n\n".join(parts)


def build_prompt(topic: dict, fmt: str) -> str:
    s = get_settings()
    spec = FORMAT_SPECS[fmt].format(author=s.author_name)
    return (
        f"LANGUAGE: Write the entire {fmt} in {s.content_language}. Do not answer in English.\n\n"
        f"{GROUNDING_RULE}\n\n"
        f"Constraints for this {fmt}: {spec}\n\n"
        f"=== SOURCE MATERIAL ===\n{source_block(topic)}\n=== END SOURCE MATERIAL ===\n\n"
        f"{FORMAT_INSTRUCTION[fmt]}"
    )


def strip_code_fences(text: str) -> str:
    """Remove a wrapping ```lang ... ``` fence if the model added one."""
    text = text.strip()
    m = _FENCE_RE.match(text)
    return m.group(1).strip() if m else text


def _yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def assemble_blog_markdown(
    title: str,
    body: str,
    sources: list[str],
    topic_id: str,
    *,
    tags: list[str] | None = None,
    today: date | None = None,
    sources_heading: str = "Sources",
) -> str:
    """Wrap a generated blog body in frontmatter and guarantee a sources section."""
    today = today or date.today()
    tags = tags or []
    body = strip_code_fences(body)

    fm = [
        "---",
        f'title: "{_yaml_escape(title)}"',
        f"date: {today.isoformat()}",
        "draft: false",
    ]
    fm.append("tags: [" + ", ".join(f'"{_yaml_escape(t)}"' for t in tags) + "]")
    fm.append("sources:")
    fm.extend(f'  - "{_yaml_escape(u)}"' for u in sources)
    fm.append(f'topic_id: "{topic_id}"')
    fm.append("---")

    # Guarantee attribution even if the model omitted the sources section. Check by URL presence
    # (not heading text) so a localized heading the model wrote isn't duplicated.
    if sources and not any(u in body for u in sources):
        links = "\n".join(f"- [{u}]({u})" for u in sources)
        body = f"{body}\n\n## {sources_heading}\n{links}"

    return "\n".join(fm) + "\n\n" + body + "\n"


def _show_notes(blurb: str, sources: list[str], heading: str = "Sources") -> str:
    notes = strip_code_fences(blurb)
    if sources:
        notes += f"\n\n{heading}:\n" + "\n".join(f"- {u}" for u in sources)
    return notes


def subscribe_url(language_code: str, *, utm: dict | None = None) -> str:
    """Absolute URL of the subscribe page for a language (pt-BR at root, others under /<code>).

    Pass ``utm`` (source/medium/campaign) only for links delivered off-site (podcast/newsletter).
    """
    s = get_settings()
    root = s.public_site_url.rstrip("/")
    base = "" if language_code == s.primary_language_code else f"/{language_code}"
    url = f"{root}{base}{s.subscribe_path}"
    return with_utm(url, **utm) if utm else url


def subscribe_cta(language_code: str, *, utm: dict | None = None) -> str:
    """Localized subscribe/referral block for a language ("" when disabled)."""
    s = get_settings()
    if not s.subscribe_cta_enabled:
        return ""
    template = s.subscribe_cta if language_code == s.primary_language_code else s.subscribe_cta_en
    return template.format(url=subscribe_url(language_code, utm=utm)).strip()


def append_subscribe_cta(text: str, cta: str) -> str:
    """Append a CTA block to markdown/show notes, separated by a horizontal rule."""
    if not cta:
        return text
    return f"{text.rstrip()}\n\n---\n\n{cta}\n"


# ── Orchestration (DB + model) ──────────────────────────────────────────────
def localized_title(source_title: str, *, gen=llm_generate) -> str:
    """Rewrite a source headline into a concise title in the configured content language."""
    s = get_settings()
    prompt = (
        f"Rewrite this article headline as a concise, natural title in {s.content_language}, "
        f"faithful to its meaning. Return ONLY the title text — no quotes, no explanation.\n\n"
        f"Headline: {source_title}"
    )
    out = (gen(prompt) or "").strip().strip('"').splitlines()
    return (out[0].strip() if out else "") or source_title


def translate(text: str, target_language: str, *, gen=llm_generate) -> str:
    """Translate text into ``target_language``, preserving Markdown, code, URLs, and tech terms."""
    if not text:
        return text
    prompt = (
        f"Translate the following into {target_language}. Preserve the meaning, tone, and any "
        f"Markdown formatting. Keep code, URLs, and established technical terms intact. Return "
        f"ONLY the translation, nothing else.\n\n{text}"
    )
    out = gen(prompt)
    return strip_code_fences(out) if out else text


def _persist_language(
    conn,
    *,
    topic_id: str,
    language: str,
    title: str,
    blog_md: str,
    blurb: str,
    script: str,
    show_notes: str,
    meta: dict,
    voice_id: str | None,
    narrate: bool,
) -> dict:
    """Persist one language's drafts + episode; optionally queue narration (primary language)."""
    blog_id = repo.upsert_draft(conn, topic_id, "blog", title, blog_md, meta, language)
    news_id = repo.upsert_draft(conn, topic_id, "newsletter", title, blurb, meta, language)
    pod_id = repo.upsert_draft(conn, topic_id, "podcast", title, script, meta, language)
    episode_id = repo.upsert_episode(
        conn, topic_id, pod_id, title, script, show_notes, language, voice_id
    )
    if narrate:
        repo.enqueue_narration(conn, episode_id, voice_id or "tiago", script)
    return {"blog": blog_id, "newsletter": news_id, "podcast": pod_id, "episode": episode_id}


def generate_for_topic(topic_id: str, *, gen=llm_generate) -> dict:
    """Generate all formats for a topic (primary + secondary language), persist, mark 'drafted'.

    Primary language (pt-BR) is auto-narrated. The secondary language (English) mirror gets a
    generated script but NO narration job — its audio is uploaded manually via the dashboard.
    """
    s = get_settings()
    topic = repo.get_topic(topic_id)
    if not topic:
        raise ValueError(f"topic {topic_id} not found")

    system = brand_voice()
    sources = topic.get("urls") or []
    title = localized_title(topic["title"], gen=gen)
    meta = {"sources": sources}

    log.info("generating content for topic %s (%s)", topic_id, title)
    blog_body = gen(build_prompt(topic, "blog"), system=system)
    raw_script = strip_code_fences(gen(build_prompt(topic, "podcast"), system=system))
    blurb = strip_code_fences(gen(build_prompt(topic, "newsletter"), system=system))

    pt_cta = subscribe_cta(s.primary_language_code)  # on-site blog CTA — untagged
    pod_utm = {"source": "podcast", "medium": "podcast", "campaign": f"episode-{topic_id}"}
    pt_pod_cta = subscribe_cta(s.primary_language_code, utm=pod_utm)  # off-site show notes — tagged
    pt_script = f"{s.podcast_intro}\n\n{raw_script}" if s.podcast_intro else raw_script
    pt_blog = append_subscribe_cta(
        assemble_blog_markdown(
            title, blog_body, sources, topic_id, sources_heading=s.sources_heading
        ),
        pt_cta,
    )
    pt_show_notes = append_subscribe_cta(_show_notes(blurb, sources, s.sources_heading), pt_pod_cta)

    # Secondary-language (English) mirror via translation — no narration.
    en = None
    if s.secondary_language:
        log.info("translating topic %s to %s", topic_id, s.secondary_language)
        en_title = translate(title, s.secondary_language, gen=gen)
        en_blog_body = translate(blog_body, s.secondary_language, gen=gen)
        en_raw_script = translate(raw_script, s.secondary_language, gen=gen)
        en_blurb = translate(blurb, s.secondary_language, gen=gen)
        en_script = (
            f"{s.podcast_intro_en}\n\n{en_raw_script}" if s.podcast_intro_en else en_raw_script
        )
        en_cta = subscribe_cta(s.secondary_language_code)  # on-site blog CTA — untagged
        en_pod_cta = subscribe_cta(s.secondary_language_code, utm=pod_utm)  # show notes — tagged
        en_blog = append_subscribe_cta(
            assemble_blog_markdown(
                en_title, en_blog_body, sources, topic_id,
                sources_heading=s.secondary_sources_heading,
            ),
            en_cta,
        )
        en = {
            "title": en_title,
            "blog_md": en_blog,
            "blurb": en_blurb,
            "script": en_script,
            "show_notes": append_subscribe_cta(
                _show_notes(en_blurb, sources, s.secondary_sources_heading), en_pod_cta
            ),
        }

    with get_conn() as conn:
        primary = _persist_language(
            conn,
            topic_id=topic_id,
            language=s.primary_language_code,
            title=title,
            blog_md=pt_blog,
            blurb=blurb,
            script=pt_script,
            show_notes=pt_show_notes,
            meta=meta,
            voice_id=s.voice_id,
            narrate=True,
        )
        if en:
            _persist_language(
                conn,
                topic_id=topic_id,
                language=s.secondary_language_code,
                title=en["title"],
                blog_md=en["blog_md"],
                blurb=en["blurb"],
                script=en["script"],
                show_notes=en["show_notes"],
                meta=meta,
                voice_id=None,
                # Secondary language is manual-audio by default; a cloud provider can auto-narrate it.
                narrate=s.narration_secondary_enabled,
            )
        repo.set_topic_status(conn, topic_id, "drafted")
        conn.commit()

    return {
        "topic_id": topic_id,
        "title": title,
        "episode_id": primary["episode"],
        "languages": [s.primary_language_code] + ([s.secondary_language_code] if en else []),
        "previews": {
            "blog": pt_blog[:PREVIEW_CHARS],
            "podcast": pt_script[:PREVIEW_CHARS],
            "newsletter": blurb[:PREVIEW_CHARS],
        },
    }


def generate_top(*, gen=llm_generate) -> dict | None:
    """Generate for the highest-scoring 'new' topic that has extracted text."""
    topic_id = repo.pick_top_new_topic()
    if not topic_id:
        return None
    return generate_for_topic(topic_id, gen=gen)
