import { marked } from "marked";
import sanitizeHtml from "sanitize-html";

// Allowlist for rendered post/episode content. marked passes raw HTML through unchanged, so we
// sanitize its output before it is injected with set:html — this strips <script>, event handlers,
// javascript:/data: URLs, etc., preventing stored XSS from a published post or show notes.
const OPTIONS = {
  allowedTags: [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "a", "ul", "ol", "li", "blockquote", "code", "pre",
    "strong", "em", "b", "i", "del", "hr", "br", "img",
    "table", "thead", "tbody", "tr", "th", "td", "span",
  ],
  allowedAttributes: {
    a: ["href", "title", "rel", "target"],
    img: ["src", "alt", "title", "width", "height", "loading"],
    code: ["class"],
    span: ["class"],
    pre: ["class"],
  },
  allowedSchemes: ["http", "https", "mailto"],
  allowProtocolRelative: false,
  transformTags: {
    // Harden outbound links.
    a: sanitizeHtml.simpleTransform("a", { rel: "noopener noreferrer" }, true),
  },
};

/** Render Markdown to sanitized HTML (safe for set:html). */
export function renderMarkdown(md) {
  return sanitizeHtml(marked.parse(md || ""), OPTIONS);
}
