// html-checks.mjs — single source for the HTML-invariant vocabulary shared by
// lint-artifact.mjs and review-contracts.mjs. scripts/perf_harness.py carries
// a deliberate Python mirror (the harness must run without Node); the two are
// held in lockstep by tests/test_linters.py::test_js_python_vocabulary_parity,
// which fails the suite the moment they drift.

export const REQUIRED_META = [
  ["name", "description"],
  ["property", "og:title"],
  ["property", "og:description"],
  ["property", "og:type"],
  ["property", "og:site_name"],
  ["name", "twitter:card"],
];

// Same feature vocabulary as perf_harness.py's _HTML_NATIVE_FEATURES.
export const FEATURES = {
  search: /type=["']search["']/i,
  inline_svg: /<svg\b/i,
  table: /<table\b/i,
  copy_as_prompt: /copy as prompt|copyPrompt|prompt-output/i,
  sorting: /data-sort|aria-sort=/i,
  filtering: /data-filter|class=["'][^"']*\bchip\b/i,
  local_storage: /localStorage/i,
  drag: /\bdraggable\b|dragstart|dragover|drop\(/i,
  toggle: /aria-pressed|type=["']checkbox["']/i,
  textarea: /<textarea\b/i,
  cross_highlight: /scrollIntoView|IntersectionObserver|classList\.(?:add|toggle)\(/i,
};

// Resource-LOADING external refs only. Anchor href="https://" is navigation, allowed.
export const EXTERNAL_RESOURCE = [
  /<script[^>]+src=['"]https?:/i,
  /<link[^>]+href=['"]https?:/i,
  /<img[^>]+src=['"]https?:/i,
  /<source[^>]+src=['"]https?:/i,
  /@import\s+['"]?https?:/i,
  /url\(\s*['"]?https?:/i,
  /fetch\(\s*['"]https?:/i,
];

export function hasMeta(html, attr, value) {
  const rx = new RegExp(`<meta\\b[^>]*${attr}=["']${value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["'][^>]*>`, "i");
  return rx.test(html);
}

export function attrValue(tag, attr) {
  return tag.match(new RegExp(`\\b${attr}=["']([^"']*)["']`, "i"))?.[1] || "";
}

export function hasAccessibleName(html, tag) {
  if (/\baria-label=|\baria-labelledby=|\btitle=/.test(tag)) return true;
  const id = attrValue(tag, "id");
  if (!id) return false;
  const forRx = new RegExp(`<label\\b[^>]*\\bfor=["']${id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["'][^>]*>`, "i");
  return forRx.test(html);
}
