// Groups blog posts into month buckets for the archive listing + TOC.
// Anchor ids use English month names so they stay stable and URL-clean
// regardless of the page locale; the visible label uses the localized name.
import { STRINGS } from "./i18n.js";

const MONTHS_EN = [
  "january", "february", "march", "april", "may", "june",
  "july", "august", "september", "october", "november", "december",
];

/**
 * Group `updated_at`-sorted posts by year+month, preserving reverse-chronological
 * order (posts arrive sorted DESC, so first-seen order is already newest-first).
 *
 * @param {Array<{updated_at: string|Date}>} posts
 * @param {string} lang - "pt-BR" | "en"
 * @returns {Array<{year:number, monthIndex:number, anchorId:string, label:string, posts:Array}>}
 */
export function groupPostsByMonth(posts, lang) {
  const months = STRINGS[lang].months;
  const byKey = new Map();
  const groups = [];
  for (const p of posts) {
    const d = new Date(p.updated_at);
    const year = d.getFullYear();
    const monthIndex = d.getMonth(); // 0–11
    const key = `${year}-${monthIndex}`;
    let group = byKey.get(key);
    if (!group) {
      // year+month is unique per group by construction, so anchorId can't collide.
      const anchorId = `${year}---${MONTHS_EN[monthIndex]}`;
      group = { year, monthIndex, anchorId, label: `${year} - ${months[monthIndex]}`, posts: [] };
      byKey.set(key, group);
      groups.push(group);
    }
    group.posts.push(p);
  }
  return groups;
}
