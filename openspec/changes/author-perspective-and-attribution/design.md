## Context

`generate.generate_for_topic` sends three prompts (blog, podcast, newsletter) to Gemini:
- The system instruction is `brand_voice()`: `DEFAULT_BRAND_VOICE`, or `BRAND_VOICE` when set.
- The user prompt is `build_prompt()`: a language line, `GROUNDING_RULE`, the format spec and
  the SOURCE MATERIAL block (title, summary, article text, URLs).

The podcast spec frames the script as "a spoken monologue for a single host named {author}".
Nothing tells the model that the source's first-person voice belongs to someone else, and the
model is never told who published the source. The English versions are translations of the
pt-BR output, so they inherit whatever perspective the pt-BR text has.

## Goals / Non-Goals

**Goals:**
- Experiences from the source are credited to the source, in every format and both languages.
- The host's voice is commentary: opinion, analysis, practical takeaway.
- The host's personal experiences come only from facts the author has written down.
- Editing the profile needs no rebuild or redeploy.

**Non-Goals:**
- A per-topic "my take" input or regenerating from the dashboard (planned as a follow-up change).
- Extracting article bylines or author metadata during extraction. The topic has no author
  field yet, so the URL domain is the attribution handle for now.
- Rewriting existing drafts.

## Decisions

1. **The perspective rule goes in the per-format user prompt, next to `GROUNDING_RULE`, not in
   the brand voice.** `BRAND_VOICE` can replace the whole system instruction, so a rule placed
   only there could be lost. `build_prompt` is used for every format, so one constant covers
   blog, podcast and newsletter. The rule is formatted with `{author}` so it names the host.

2. **Publishers come from the source URL domains.** `source_block` adds a
   `PUBLISHED BY: example.com, news.ycombinator.com` line: unique hosts, without `www.`, in URL
   order. The rule tells the model to credit the article's named author when the text names one,
   and the publisher otherwise. It also notes that link aggregators and discussion sites
   (Hacker News, Reddit) host discussions rather than authoring them. This is cheap, and it needs
   no schema change.

3. **The author profile is a mounted file, with env text as a fallback.**
   - The `author_profile_file` setting defaults to `/app/config/author_profile.md`; the
     `author_profile` setting holds inline text. If the file exists and is non-empty it wins;
     otherwise the env text is used; otherwise there is no profile.
   - The file is read on each `generate_for_topic` call (it is small, and generation runs at
     most a few times an hour), so edits take effect on the next generation.
   - Multi-line text in `.env` is awkward with Swarm env interpolation, which is why a file is
     the main path.
   - The profile is capped at 6000 characters: it is truncated with a logged warning, so the
     prompt can't grow without bound.

4. **The profile goes in the system instruction.** A new `system_instruction()` returns
   `brand_voice()` plus an "AUTHOR PROFILE" block when a profile exists. The block says it is the
   only allowed source of the host's own experiences, background and recurring opinions, and
   that it must not be quoted verbatim or overused (use it only when relevant to the topic).
   `generate_for_topic` uses `system_instruction()` instead of `brand_voice()`.

5. **`config/` is mounted read-only into the generating services.**
   - Swarm: `/root/vaccaricode_podcast/config:/app/config:ro` on `scheduler` and `dashboard`.
     The dashboard doesn't generate today, but the planned "my take" regeneration will run there.
   - Local compose: `../config:/app/config:ro` on `pipeline`, `scheduler` and `dashboard`.
   - The directory is tracked (it holds `author_profile.example.md`), so the bind source always
     exists after checkout. A missing bind source would otherwise make the Swarm task fail to
     start.
   - `config/author_profile.md` is gitignored, so personal content doesn't land in either repo
     (including the public mirror).

## Risks / Trade-offs

- **The model may still slip into the first person for source events.** → The rule is explicit
  and gives concrete phrasings. Human review stays the backstop. Tests assert the rule is
  present in every format's prompt.
- **Credit to a domain is less personal than credit to the author.** → The model is told to
  prefer the author named in the article text. Byline extraction is a possible follow-up.
- **Profile anecdotes could be repeated in every episode.** → The block tells the model to use a
  profile fact only when it is genuinely relevant, and at most once or twice per piece.
- **A forgotten profile file.** → Generation keeps working without one. The rule then forbids
  invented personal anecdotes, so the failure mode is "less personal", not "false".

## Migration Plan

1. Deploy as usual (`bash deploy/redeploy.sh`). No DB migration is needed.
2. Optionally create `config/author_profile.md` on the VPS from the example; it takes effect on
   the next generation.
3. Rollback: redeploy the previous commit. A leftover profile file does no harm.
