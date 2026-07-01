"""Brand voice and per-format generation specs.

The brand voice can be overridden at runtime via the BRAND_VOICE env var (see config); otherwise
this default is used. Per-format specs encode the length / tone / structure constraints applied
to each channel.
"""

from __future__ import annotations

DEFAULT_BRAND_VOICE = (
    "You write for {author}'s site at {site} — covering trends in software development, AI, and "
    "engineering practice, in the spirit of akitaonrails.com. Voice: a pragmatic, experienced "
    "senior engineer; curious and opinionated but grounded; clear and concise with light wit; no "
    "hype, no marketing fluff. Audience: working software developers. "
    "Write EVERYTHING in {language}; established technical terms may stay in English where that is "
    "the norm among developers."
)

GROUNDING_RULE = (
    "Ground everything strictly in the SOURCE MATERIAL provided below. Do not invent facts, "
    "quotes, numbers, benchmarks, or features. If the source is thin, stay high-level rather than "
    "fabricating specifics."
)

FORMAT_SPECS: dict[str, str] = {
    "blog": (
        "600-900 words. Markdown body with 2-4 '##' sections. Open with a hook, deliver substance, "
        "and end with a short 'why it matters' takeaway. Do NOT include an H1 title (it is added "
        "separately). End with a sources section (heading in the target language) listing the "
        "source URLs as markdown links."
    ),
    "podcast": (
        "A spoken monologue script for a single host named {author}. ~500-700 words. Natural and "
        "conversational, short sentences, easy to read aloud. Do NOT write an opening greeting or "
        "introduce yourself/the show (a fixed intro is added before your text) — start directly "
        "with the subject. End with a short sign-off. No stage directions, no speaker labels, no "
        "markdown — only the words to be spoken."
    ),
    "newsletter": (
        "80-130 words. One punchy, skimmable paragraph followed by a single 'Why it matters:' line. "
        "No markdown headings."
    ),
}

FORMAT_INSTRUCTION: dict[str, str] = {
    "blog": "Write the blog post body now.",
    "podcast": "Write the podcast narration script now.",
    "newsletter": "Write the newsletter blurb now.",
}
