## 1. Lane taxonomy + data model

- [ ] 1.1 Define the four lanes as a shared constant/enum (`business-story`, `business-problem`, `tech-deepdive`, `bigtech-news`) in the pipeline (e.g. `lanes.py`).
- [ ] 1.2 Add a `lane` field to the topic model (`models.py`) and a DB migration adding the `lane` column (nullable until backfilled, then always set at ingestion).

## 2. Classification

- [ ] 2.1 Implement lane classification: a cheap LLM call via `boosternews.llm` returning exactly one lane from a title + summary.
- [ ] 2.2 Implement a deterministic fallback (per-source default-lane hint + keyword heuristic) used when the LLM is unavailable or returns an invalid lane; guarantee exactly one lane always.
- [ ] 2.3 Wire classification into the ingestion/scoring path so every surviving candidate gets a persisted lane; unit-test both LLM and fallback paths (mock the LLM).

## 3. Lane-oriented sources

- [ ] 3.1 Add a per-source optional `default_lane` hint to source config/seed.
- [ ] 3.2 Add curated business/leadership/startup + Big Tech RSS sources (seed data) feeding the `business-story`, `business-problem`, and `bigtech-news` lanes.

## 4. Lane-balanced selection

- [ ] 4.1 Implement lane-balanced selection: over a rolling window, allot slots per lane by a configurable quota (default even), choosing the highest-scored unused topic within each allotted lane.
- [ ] 4.2 Handle empty lanes: reallocate the slot to lanes with candidates and record the shortfall so later windows rebalance; log empty lanes (no silent skew).
- [ ] 4.3 Use lane-balanced selection in `scheduler.py`/`jobs.py` where top-scored topics are currently picked for generation.
- [ ] 4.4 Unit-test selection: balanced distribution, score-within-lane, empty-lane reallocation, and shortfall recovery.

## 5. Per-lane subscribe attribution

- [ ] 5.1 Extend `utm.py` + `subscribe_cta(..., utm=...)` so off-site CTA links carry the topic's lane in the campaign/UTM tag; keep on-site links untagged.
- [ ] 5.2 Unit-test that off-site CTA links include the lane and on-site links do not.

## 6. Verification

- [ ] 6.1 Run the pipeline test suite (`pytest`) green, including the new classification/selection/UTM tests.
- [ ] 6.2 Dry-run selection over a seeded candidate set and confirm the output distributes across the four lanes per the configured quota, degrading gracefully when a lane is empty.
- [ ] 6.3 Generate a topic end-to-end and confirm the persisted `lane` and the lane-tagged off-site CTA link are correct.
