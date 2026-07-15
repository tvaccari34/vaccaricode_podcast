## Why

The content strategy defines four editorial lanes — business stories with a lesson,
business problems solved, technical deep-dives (AI/automation/data), and Big Tech news — to
build Tiago's authority and grow the newsletter list. The generation *voice* now reflects
those lanes, but *selection* does not: topics are chosen by score alone, from dev-heavy
sources (Hacker News, GitHub, RSS). So the published mix skews technical and the business
lanes are starved. To make the mix match the strategy, selection itself must be lane-aware.

## What Changes

- Introduce a **lane taxonomy** and classify every topic into exactly one of the four lanes;
  persist the lane on the topic.
- Add **business/leadership/startup-oriented sources** (curated feeds) so the business and
  Big Tech lanes actually have candidate topics.
- Make topic selection **lane-balanced**: pick topics to generate by balancing across the
  four lanes over a rolling window (quota / round-robin), still honoring score *within* a
  lane — instead of pure global score.
- Add **per-lane campaign tagging** to the newsletter CTA links so subscriber growth can be
  attributed by lane, feeding later marketing campaigns.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `trend-discovery`: ingestion gains lane-oriented sources; topics gain a lane
  classification; the ranked selection becomes lane-balanced rather than pure-score.
- `content-generation`: the subscribe/CTA links carry a per-lane campaign tag so list growth
  is measurable per lane.

## Impact

- `pipeline/src/boosternews/models.py` — add a `lane` field to the topic model.
- `pipeline/src/boosternews/scoring.py` (or a new `lanes.py`) — lane classification
  (LLM-based via `boosternews.llm`, with a source-hint/keyword fallback) and lane-balanced
  selection.
- `pipeline/src/boosternews/sources/` + source config/seed — add curated business/Big Tech
  RSS sources; optionally a per-source default-lane hint.
- `pipeline/src/boosternews/scheduler.py` / `jobs.py` — use lane-balanced selection when
  choosing topics to generate.
- `pipeline/src/boosternews/utm.py` + `generate.py` (`subscribe_cta`) — include the lane in
  the CTA campaign/UTM tag.
- DB: a migration for the new `lane` column.
- Out of scope: generation voice/framing and the fixed intro/outro (already done), TTS/voice,
  and any web/UI changes.
