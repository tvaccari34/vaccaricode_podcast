## Context

Topic selection today is score-only: `scoring.py` computes `base_score` (recency × engagement
× source_weight) then multiplies by a corroboration factor; the scheduler/jobs pick the
top-scored topics to generate. Sources (`sources/registry.py`) are Hacker News, GitHub
Trending, and RSS — all developer-centric. Topics carry no category. The content strategy
defines four editorial lanes, and the generation *voice* already reflects them (done on
`feat/content-strategy`); this change makes *selection* lane-aware so the published mix
matches the strategy. The end goal is authority + newsletter-list growth, so we also want to
measure which lanes convert subscribers.

## Goals / Non-Goals

**Goals:**
- Classify every topic into exactly one of four lanes and persist it.
- Add sources that feed the business and Big Tech lanes.
- Select topics with lane balance over a rolling window (not pure global score).
- Tag off-site CTA links with the lane so subscriber growth is attributable per lane.

**Non-Goals:**
- Generation voice/framing and the fixed intro/outro (already done).
- TTS/voice changes; any web/UI changes.
- A full analytics dashboard — this change only *emits* the per-lane tag; reading it is via
  existing analytics.

## Decisions

### Lane as a first-class field on the topic
Add a `lane` column (enum-like string: `business-story` | `business-problem` | `tech-deepdive`
| `bigtech-news`) via a DB migration, set during ingestion/scoring. A first-class field (vs.
inferring at selection time) lets selection, CTA tagging, and later reporting all read one
value, and keeps classification cost paid once per topic.

### LLM classification with a deterministic fallback
Classify with a cheap single call through the existing `boosternews.llm` provider (prompt:
"return exactly one of these four lanes for this title+summary"). Fall back to a
source-hint + keyword heuristic when the model is unavailable or returns garbage, so ingestion
never blocks and every topic always gets exactly one lane. Alternative — pure keyword rules —
was rejected as too brittle for the business/tech boundary; LLM-first with a safety net is more
accurate and still deterministic on failure.

### Per-source default lane hint (cheap prior)
Let a source declare a default lane in its config (e.g. a startup-lessons feed → `business-story`).
This is the fallback classifier's prior and reduces LLM calls for obviously-single-lane sources.
The LLM can still override per item when a source is mixed.

### Balanced selection: quota over a rolling window
Selection picks per-lane by a configurable quota over a rolling window (default: even split
across the four lanes), taking the highest-scored unused topic within each allotted lane —
score still ranks *within* a lane. If a lane is empty for the window, its slot is reallocated
to lanes with candidates and the shortfall is recorded so later windows can rebalance.
Alternative — a global score with per-lane penalty — was rejected as harder to reason about
and to guarantee "no lane dominates." Quota makes the balance explicit and tunable.

### Lane in the CTA campaign tag (reuse utm.py)
Extend the existing UTM/campaign tagging (`utm.py` + `subscribe_cta(..., utm=...)`) so off-site
CTA links include the lane in the campaign value (e.g. `campaign=episode-<id>-<lane>` or a
dedicated `content_lane` param). On-site links stay untagged, as today. No new analytics
system — the tag flows into the analytics already in place.

## Risks / Trade-offs

- Misclassification → a topic lands in the wrong lane. Mitigation: LLM-first + source-hint
  prior; lane is visible in the review dashboard so a human can catch/relabel before publish.
- LLM cost/latency per topic → mitigate with the per-source prior (skip the call when a source
  is single-lane) and by classifying only topics that survive dedup/scoring.
- Starved lanes (business feeds thin at first) → slot reallocation keeps throughput up; the
  recorded shortfall lets balance recover as more business sources are added. Log when a lane
  is empty so it is visible, not silent.
- Over-balancing could bury a genuinely dominant story → the window is configurable; a strong
  topic still wins within its lane and lanes can be weighted, not forced to a hard even split.

## Open Questions

- Rolling-window size and the per-lane quota (even 25/25/25/25 vs. weighted, e.g. heavier on
  tech)? Default: even split, tunable in config.
- Should the review dashboard allow a human to override a topic's lane before publish? Default:
  yes, surface it as an editable field (small follow-up if not trivial here).
- Exact tag shape: fold lane into `campaign` vs. a separate `content_lane` UTM key? Default: a
  dedicated key so lane and episode id stay independent for reporting.
