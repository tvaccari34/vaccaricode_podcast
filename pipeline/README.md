# pipeline

The Python service that runs on the **VPS**: trend discovery, AI content generation, episode
audio assembly, and publishing. Talks to PostgreSQL and S3-compatible object storage, and
enqueues narration jobs for the home GPU sound-worker.

## Layout

```
src/boosternews/
  config.py     Fail-fast settings (pydantic-settings)
  db.py         PostgreSQL connection helpers (psycopg 3)
  storage.py    S3/MinIO client helper
  migrate.py    Forward-only SQL migration runner
  models.py     Shared dataclasses (SourceRow, SourceItem)
  sources/      Trend fetchers: rss, hackernews, github + registry
  extract.py    Article text extraction (trafilatura)
  dedup.py      Normalized-title dedup key (merge same story)
  scoring.py    Relevance scoring (recency + engagement + corroboration)
  repository.py DB access for sources + topics (upsert/merge)
  seed.py       Default trend sources
  ingest.py     Ingestion + extraction passes
  cli.py        CLI dispatch
  __main__.py   Entry point
tests/          pytest
```

## CLI

```bash
python -m boosternews check            # config + Postgres/storage connectivity
python -m boosternews seed-sources     # insert default trend sources (idempotent)
python -m boosternews ingest --all     # one trend-discovery pass (omit --all to honor intervals)
python -m boosternews ingest --source "Lobsters" --extract   # one source + inline extraction
python -m boosternews extract --limit 10   # backfill article text for top topics missing it
python -m boosternews list-topics          # ranked candidate queue

python -m boosternews generate             # generate blog+script+newsletter for the top topic
python -m boosternews generate --topic <id># generate for a specific topic
python -m boosternews list-drafts          # generated drafts (channel, status, size)
python -m boosternews show-draft <id> blog # print a draft body (blog|podcast|newsletter)

python -m boosternews publish --all        # publish approved drafts (gate-enforced) → then web-build
python -m boosternews publish --topic <id> # publish one topic's approved channels
python -m boosternews list-publications     # what has been published
```

Publishing (task group 8): only **approved** drafts publish — `repository.publish_draft` enforces
the gate via `review.assert_publishable`. Blog/podcast flip to `published` (the Astro `web-build`
then renders them and regenerates the RSS + iTunes feeds); the newsletter becomes a Listmonk
campaign (`boosternews.llm`/`listmonk.py`, sending wired in task group 7). `make publish` runs
publish + web-build together.

Content generation (Gemini): from one topic's source material it produces a blog post (markdown
+ frontmatter with `sources`), a podcast script (spoken, in the author's voice), and a
newsletter blurb — persisted as `drafts` (pending_review) plus an `episodes` row, all linked to
the same topic. Output is grounded in the extracted article and attributes the source URLs. The
LLM lives behind `boosternews.llm`; brand voice + per-format specs are in `prompts.py`.

Trend discovery: each enabled source is fetched (failures isolated per source), items are
scored (recency + engagement + cross-source corroboration), deduplicated by normalized title,
and merged into the `topics` queue. Extraction (trafilatura) stores clean article text used
later to ground generation.

## Local development

```bash
python -m venv .venv && . .venv/Scripts/activate   # PowerShell: .venv\Scripts\Activate.ps1
pip install -e .[dev]
# Provide env (copy ../.env.example to ../.env or export the vars), then:
python -m boosternews            # validates config + checks Postgres/storage
boosternews-migrate              # apply db migrations
pytest
ruff check . && black --check .
```

## What's next

Subsequent task groups add modules here: `sources/` + `ingest.py` (trend-discovery),
`generate.py` (content-generation), `assemble.py` (episode audio), `publish.py`, and a
`narration` job API for the home worker.
