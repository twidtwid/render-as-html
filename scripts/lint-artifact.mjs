#!/usr/bin/env node
// lint-artifact.mjs — run the MECHANICAL subset of SKILL.md's pre-save checklist
// against a freshly generated artifact at an ARBITRARY path.
//
// review-contracts.mjs and perf_harness.py already encode these checks, but both
// only ever run against the repo's own examples/. This points the same detectors
// at one (or several) generated .html files so the agent can verify its own
// output before reporting "done" — turning the pre-save checklist from
// "enforced by me" into "enforced by a tool".
//
//   node scripts/lint-artifact.mjs ~/Reports/2026-06-10-my-thing.html
//   node scripts/lint-artifact.mjs --longform a.html b.html   # enforce 30KB floor
//   node scripts/lint-artifact.mjs --json out.html            # machine-readable
//
// Exit 0 = all hard checks pass. Exit 1 = at least one FAIL. Warnings never fail.
// stdlib only, no dependencies.

import fs from "node:fs";
import vm from "node:vm";

const argv = process.argv.slice(2);
const opts = { longform: false, json: false, published: false, files: [] };
for (const a of argv) {
  if (a === "--longform") opts.longform = true;
  else if (a === "--json") opts.json = true;
  else if (a === "--published") opts.published = true;
  else if (a === "-h" || a === "--help") { usage(); process.exit(0); }
  else opts.files.push(a);
}
if (!opts.files.length) { usage(); process.exit(2); }

const LONGFORM_FLOOR = 30_000;

const REQUIRED_META = [
  ["name", "description"],
  ["property", "og:title"],
  ["property", "og:description"],
  ["property", "og:type"],
  ["property", "og:site_name"],
  ["name", "twitter:card"],
];

// Same feature vocabulary as perf_harness.py's _HTML_NATIVE_FEATURES.
const FEATURES = {
  search: /type=["']search["']|\bsearch\b/i,
  inline_svg: /<svg\b/i,
  table: /<table\b/i,
  copy_as_prompt: /copy as prompt|copyPrompt|prompt-output/i,
  sorting: /\bsort(?:able|ing)?\b|data-sort/i,
  filtering: /\bfilter(?:ed|ing)?\b|chip\b/i,
  local_storage: /localStorage/i,
  drag: /\bdraggable\b|dragstart|dragover|drop\(/i,
  toggle: /aria-pressed|type=["']checkbox["']|\btoggle\b/i,
  textarea: /<textarea\b/i,
  cross_highlight: /highlight|scrollIntoView|IntersectionObserver|scroll-spy|scrollspy/i,
};

// Resource-LOADING external refs only. Anchor href="https://" is navigation, allowed.
const EXTERNAL_RESOURCE = [
  /<script[^>]+src=['"]https?:/i,
  /<link[^>]+href=['"]https?:/i,
  /<img[^>]+src=['"]https?:/i,
  /<source[^>]+src=['"]https?:/i,
  /@import\s+['"]?https?:/i,
  /url\(\s*['"]?https?:/i,
  /fetch\(\s*['"]https?:/i,
];

function usage() {
  process.stderr.write(
    "usage: node scripts/lint-artifact.mjs [--longform] [--published] [--json] <file.html> [more.html ...]\n",
  );
}

function hasMeta(html, attr, value) {
  const rx = new RegExp(`<meta\\b[^>]*${attr}=["']${value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["'][^>]*>`, "i");
  return rx.test(html);
}

function attrValue(tag, attr) {
  return tag.match(new RegExp(`\\b${attr}=["']([^"']*)["']`, "i"))?.[1] || "";
}

function hasAccessibleName(html, tag) {
  if (/\baria-label=|\baria-labelledby=|\btitle=/.test(tag)) return true;
  const id = attrValue(tag, "id");
  if (!id) return false;
  const forRx = new RegExp(`<label\\b[^>]*\\bfor=["']${id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["'][^>]*>`, "i");
  return forRx.test(html);
}

function lintOne(file) {
  const fails = [];
  const warns = [];
  let html;
  try {
    html = fs.readFileSync(file, "utf8");
  } catch (e) {
    return { file, ok: false, fails: [`cannot read file: ${e.message}`], warns: [], features: [], bytes: 0 };
  }
  const bytes = Buffer.byteLength(html, "utf8");

  // --- self-containment (publish + file:// invariant) ---
  for (const rx of EXTERNAL_RESOURCE) {
    const m = html.match(rx);
    if (m) fails.push(`loads an external resource (no CDN/fonts/analytics by default): ${m[0].slice(0, 60)}`);
  }

  // --- head hygiene ---
  if (!/<html\b[^>]*\blang=["'][a-z-]+["']/i.test(html)) fails.push('missing <html lang="…">');
  if (!hasMeta(html, "name", "viewport")) fails.push("missing viewport meta (mobile is a hard requirement)");
  if (!/<link\b[^>]*\brel=["']icon["'][^>]*\bhref=["']data:,["'][^>]*>/i.test(html))
    fails.push('missing blank data favicon <link rel="icon" href="data:,">');
  for (const [attr, value] of REQUIRED_META) {
    if (!hasMeta(html, attr, value)) fails.push(`missing social-card meta: ${value}`);
  }
  // image-card metadata. When --published, og:image is REQUIRED (the sibling
  // og-card IS hosted at the slug URL — generate it with bin/og-card.mjs).
  // Otherwise it's optional but flagged (a bare file:// has no hosted sibling).
  const hasImageCard = /\bog:image\b|\btwitter:image\b|summary_large_image/i.test(html);
  if (opts.published) {
    if (!/property=["']og:image["']/i.test(html))
      fails.push("published artifact missing og:image — run bin/og-card.mjs <file> --inject to make the social card (+twitter:image, twitter:card=summary_large_image)");
  } else if (hasImageCard) {
    warns.push("image-card metadata present — valid only if a sibling og-card image is hosted (publish path); breaks file:// self-containment otherwise. Lint with --published once hosted.");
  }

  // --- HTML-native feature floor (the load-bearing 'is this an artifact' test) ---
  const features = Object.entries(FEATURES).filter(([, rx]) => rx.test(html)).map(([k]) => k);
  if (features.length < 3)
    fails.push(`only ${features.length} HTML-native feature(s) detected (${features.join(", ") || "none"}); need ≥3 — this reads as styled prose, not an artifact`);

  // --- copy-as-prompt contract ---
  const hasCopyPrompt = /(copyAsPrompt|copyPrompt|copyRecommendation|generateStuckPrompt|prompt-output|copy as prompt)/i.test(html);
  if (/<artifact\.html>/.test(html))
    fails.push("copy-as-prompt names the placeholder <artifact.html> instead of the real file path");
  if (hasCopyPrompt && !/BEGIN ARTIFACT STATE DATA/.test(html))
    fails.push("copy-as-prompt output must delimit collected state with BEGIN/END ARTIFACT STATE DATA");

  // --- clipboard guard ---
  if (/navigator\.clipboard\.writeText/.test(html)) {
    const guarded = /navigator\.clipboard\s*&&\s*navigator\.clipboard\.writeText|navigator\.clipboard\?\.writeText/.test(html);
    if (!guarded) fails.push("navigator.clipboard.writeText called without guarding navigator.clipboard first");
  }

  // --- content-discipline / format smells ---
  if (/<(?:button|a)\b[^>]*>[^<]*copy as markdown/i.test(html))
    fails.push('"copy as markdown" control implies another canonical format — prefer copy-as-prompt / copy-section');
  for (const m of html.matchAll(/<svg\b[^>]*\b(?:height|width)=["']auto["'][^>]*>/gi))
    fails.push(`SVG has width/height="auto" (invalid attribute value); size responsively via CSS — ${m[0].slice(0, 50)}`);

  // --- accessible names on interactive controls ---
  for (const m of html.matchAll(/<input\b[^>]*\btype=["']search["'][^>]*>/gi))
    if (!hasAccessibleName(html, m[0])) warns.push("a search input has no accessible label (aria-label or <label for>)");
  for (const m of html.matchAll(/<textarea\b[^>]*readonly[^>]*>/gi))
    if (!hasAccessibleName(html, m[0])) warns.push("a readonly textarea has no accessible label");

  // --- dead-script guard: every inline <script> must PARSE ---
  // A single stray brace is a SyntaxError → the WHOLE script never runs →
  // every toggle/search/copy button is silently dead. (2026-07-04: shipped 3×.)
  const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
    .filter(m => !/\bsrc=/i.test(m[1]) && !/type\s*=\s*["']application\/(json|ld\+json)["']/i.test(m[1]))
    .map(m => m[2]);
  let scriptSrc = "";
  scripts.forEach((src, i) => {
    if (!src.trim()) return;
    scriptSrc += "\n" + src;
    try {
      vm.compileFunction(src, [], { filename: `script-${i}.js` }); // parses, does not execute
    } catch (e) {
      fails.push(`inline <script> #${i + 1} has a JS syntax error → the whole script is dead (all interactivity fails): ${e.message}`);
    }
  });

  // --- dead-control guard: every getElementById/querySelector('#id') must resolve ---
  const idAttrs = new Set([...html.matchAll(/\bid\s*=\s*["']([^"']+)["']/g)].map(m => m[1]));
  const referenced = new Set();
  for (const m of scriptSrc.matchAll(/getElementById\(\s*['"]([^'"]+)['"]\s*\)/g)) referenced.add(m[1]);
  for (const m of scriptSrc.matchAll(/querySelector\(\s*['"]#([A-Za-z][\w-]*)['"]\s*\)/g)) referenced.add(m[1]);
  for (const id of referenced)
    if (!idAttrs.has(id)) fails.push(`JS references #${id} but no element has id="${id}" → that control is wired to nothing (dead)`);

  // --- size floor (only when caller asserts this is long-form) ---
  if (opts.longform && bytes < LONGFORM_FLOOR)
    fails.push(`${bytes} bytes < ${LONGFORM_FLOOR}B long-form floor — likely rendered off a summary / skipped features`);

  return { file, ok: fails.length === 0, fails, warns, features, bytes };
}

const results = opts.files.map(lintOne);

if (opts.json) {
  console.log(JSON.stringify({ results, ok: results.every((r) => r.ok) }, null, 2));
  process.exit(results.every((r) => r.ok) ? 0 : 1);
}

let anyFail = false;
for (const r of results) {
  const tag = r.ok ? "PASS" : "FAIL";
  console.log(`\n${tag}  ${r.file}  (${(r.bytes / 1024).toFixed(1)} KB · ${r.features.length} HTML-native: ${r.features.join(", ") || "none"})`);
  for (const f of r.fails) console.log(`  ✗ ${f}`);
  for (const w of r.warns) console.log(`  ⚠ ${w}`);
  if (!r.ok) anyFail = true;
}
console.log(
  `\n${results.length} file(s) · ${results.filter((r) => r.ok).length} pass · ${results.filter((r) => !r.ok).length} fail`,
);
process.exit(anyFail ? 1 : 0);
