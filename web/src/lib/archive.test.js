import { test } from "node:test";
import assert from "node:assert/strict";
import { groupPostsByMonth } from "./archive.js";

// Posts as they arrive from getPublishedPosts(): sorted updated_at DESC.
// Dates are kept mid-month at midday UTC so the local-time bucketing in
// groupPostsByMonth() lands in the same month under any host timezone.
const POSTS = [
  { topic_id: "e", title: "E", body: "e", updated_at: "2026-07-20T12:00:00Z" },
  { topic_id: "d", title: "D", body: "d", updated_at: "2026-07-15T12:00:00Z" },
  { topic_id: "c", title: "C", body: "c", updated_at: "2026-06-15T12:00:00Z" },
  { topic_id: "b", title: "B", body: "b", updated_at: "2026-04-15T12:00:00Z" },
  { topic_id: "a", title: "A", body: "a", updated_at: "2025-12-15T12:00:00Z" },
];

test("groups posts into one bucket per year+month", () => {
  const groups = groupPostsByMonth(POSTS, "en");
  assert.equal(groups.length, 4); // Jul, Jun, Apr 2026 + Dec 2025
  assert.deepEqual(
    groups.map((g) => g.posts.length),
    [2, 1, 1, 1]
  );
});

test("preserves reverse-chronological order across groups", () => {
  const groups = groupPostsByMonth(POSTS, "en");
  assert.deepEqual(
    groups.map((g) => `${g.year}-${g.monthIndex}`),
    ["2026-6", "2026-5", "2026-3", "2025-11"]
  );
});

test("preserves post order within a group (newest first)", () => {
  const [july] = groupPostsByMonth(POSTS, "en");
  assert.deepEqual(july.posts.map((p) => p.topic_id), ["e", "d"]);
});

test("merges same-month posts even when not contiguous in input", () => {
  const scrambled = [
    { updated_at: "2026-07-20T12:00:00Z" },
    { updated_at: "2026-06-15T12:00:00Z" },
    { updated_at: "2026-07-15T12:00:00Z" }, // same month as the first, later in the list
  ];
  const groups = groupPostsByMonth(scrambled, "en");
  assert.equal(groups.length, 2);
  assert.equal(groups[0].posts.length, 2); // both July posts in one bucket
});

test("anchor ids use English month names and are stable regardless of locale", () => {
  const en = groupPostsByMonth(POSTS, "en").map((g) => g.anchorId);
  const pt = groupPostsByMonth(POSTS, "pt-BR").map((g) => g.anchorId);
  assert.deepEqual(en, ["2026---july", "2026---june", "2026---april", "2025---december"]);
  assert.deepEqual(pt, en); // ids identical across locales
});

test("anchor ids are unique across groups", () => {
  const ids = groupPostsByMonth(POSTS, "en").map((g) => g.anchorId);
  assert.equal(new Set(ids).size, ids.length);
});

test("labels are localized per locale", () => {
  const en = groupPostsByMonth(POSTS, "en").map((g) => g.label);
  const pt = groupPostsByMonth(POSTS, "pt-BR").map((g) => g.label);
  assert.equal(en[0], "2026 - July");
  assert.equal(pt[0], "2026 - Julho");
  assert.equal(pt[3], "2025 - Dezembro");
});

test("lists only months that contain posts", () => {
  // April and June are absent from this input — they must not appear.
  const groups = groupPostsByMonth(
    [{ updated_at: "2026-07-15T12:00:00Z" }, { updated_at: "2025-12-15T12:00:00Z" }],
    "en"
  );
  assert.deepEqual(groups.map((g) => g.anchorId), ["2026---july", "2025---december"]);
});

test("returns an empty array for empty input", () => {
  assert.deepEqual(groupPostsByMonth([], "en"), []);
});
