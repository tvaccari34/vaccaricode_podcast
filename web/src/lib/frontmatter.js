import matter from "gray-matter";

/**
 * Parse frontmatter but never throw. A hand-authored post can contain malformed YAML frontmatter
 * (e.g. a Markdown bullet list under `tags:`), which would otherwise crash the whole static build
 * and take the site down. On any parse error we fall back to treating the entire body as content.
 */
export function safeMatter(body) {
  try {
    return matter(body || "");
  } catch {
    return { content: body || "", data: {} };
  }
}
