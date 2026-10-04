#!/usr/bin/env node
// Throwaway spike: replay named historical failures against today's lint-artifact.
// Not production code. Decision instrument only.

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SPIKE = path.dirname(fileURLToPath(import.meta.url));
const REPO = process.env.REPO || "/workspace";
const FIX = path.join(SPIKE, "fixtures");
fs.mkdirSync(FIX, { recursive: true });

const HEAD = `
<!doctype html><html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>Spike</title>
<meta name="description" content="spike fixture">
<meta property="og:title" content="Spike">
<meta property="og:description" content="spike fixture">
<meta property="og:type" content="article">
<meta property="og:site_name" content="render-as-html">
<meta name="twitter:card" content="summary">
</head><body>
`;

function write(name, html) {
  const p = path.join(FIX, name);
  fs.writeFileSync(p, html);
  return p;
}

const cases = [];

// Magnifica-style: styled prose, TOC + quotes + CTA, no HTML-native features, small.
cases.push({
  id: "magnifica-styled-prose",
  incident: "2026-05-25 Magnifica Humanitas / PR #5",
  expectFail: true,
  flags: [],
  path: write(
    "magnifica.html",
    `${HEAD}<h1>Encyclical</h1><p>TOC</p><blockquote>quote</blockquote>
<a href="https://example.com">read full article</a></body></html>`,
  ),
});

// Magnifica long-form size floor: 20KB prose, still no features, --longform
const pad = "word ".repeat(4000);
cases.push({
  id: "magnifica-longform-floor",
  incident: "2026-05-25 Magnifica size smell / PR #5",
  expectFail: true,
  flags: ["--longform"],
  path: write(
    "magnifica-longform.html",
    `${HEAD}<h1>Encyclical</h1><p>${pad}</p></body></html>`,
  ),
});

// Feature-floor false positive: prose mentions search/filter/toggle, no markup
cases.push({
  id: "gallery-prose-features",
  incident: "v2.7.0 CHANGELOG: feature floor matched words in prose",
  expectFail: true,
  flags: [],
  path: write(
    "prose-features.html",
    `${HEAD}<p>This page has search, filter, toggle, sort, and highlight in the prose.</p></body></html>`,
  ),
});

// Dead script: stray brace, otherwise looks like a real artifact
cases.push({
  id: "dead-script-stray-brace",
  incident: "2026-07-04 dead-script shipped 3x / lint-artifact.mjs:121",
  expectFail: true,
  flags: [],
  path: write(
    "dead-script.html",
    `${HEAD}
<input type="search" aria-label="q">
<button type="button">copy as prompt</button>
<textarea id="prompt-output"></textarea>
<svg></svg>
<script>
function copyPrompt() {
  const x = {;
}
</script>
</body></html>`,
  ),
});

// Dead control: getElementById missing
cases.push({
  id: "dead-control-missing-id",
  incident: "dead-control scan / e0278cb + 4b65691 compound selectors",
  expectFail: true,
  flags: [],
  path: write(
    "dead-control.html",
    `${HEAD}
<input type="search" aria-label="q">
<button type="button" id="go">copy as prompt</button>
<textarea id="prompt-output"></textarea>
<svg></svg>
<script>
document.getElementById('missing-chart');
</script>
</body></html>`,
  ),
});

// Unguarded clipboard
cases.push({
  id: "unguarded-clipboard",
  incident: "cbcaf99 clipboard guard",
  expectFail: true,
  flags: [],
  path: write(
    "clipboard.html",
    `${HEAD}
<input type="search" aria-label="q">
<button type="button">copy as prompt</button>
<textarea id="prompt-output"></textarea>
<svg></svg>
<script>
navigator.clipboard.writeText('x');
</script>
</body></html>`,
  ),
});

// Placeholder path
cases.push({
  id: "artifact-html-placeholder",
  incident: "SKILL.md lint step: no <artifact.html> placeholder",
  expectFail: true,
  flags: [],
  path: write(
    "placeholder.html",
    `${HEAD}
<input type="search" aria-label="q">
<button type="button">copy as prompt</button>
<textarea id="prompt-output"></textarea>
<svg></svg>
<p>In <artifact.html>, apply these changes.</p>
</body></html>`,
  ),
});

// Copy as markdown
cases.push({
  id: "copy-as-markdown",
  incident: "SKILL anti-pattern + lint-artifact copy-as-markdown fail",
  expectFail: true,
  flags: [],
  path: write(
    "markdown.html",
    `${HEAD}
<input type="search" aria-label="q">
<button type="button">copy as markdown</button>
<textarea></textarea>
<svg></svg>
</body></html>`,
  ),
});

// Missing copy-as-prompt delimiter when a real control exists
cases.push({
  id: "copy-prompt-no-delimiter",
  incident: "copy-as-prompt contract / review-contracts false positive fix v2.7.1",
  expectFail: true,
  flags: [],
  path: write(
    "no-delim.html",
    `${HEAD}
<input type="search" aria-label="q">
<button type="button">copy as prompt</button>
<textarea id="prompt-output"></textarea>
<svg></svg>
</body></html>`,
  ),
});

// Prose mention of copy as prompt should NOT demand delimiter if no button
cases.push({
  id: "copy-prompt-prose-mention",
  incident: "v2.7.1 review-contracts regex spanned unrelated elements",
  expectFail: false,
  flags: [],
  path: write(
    "copy-prose.html",
    `${HEAD}
<input type="search" aria-label="q">
<table></table>
<svg></svg>
<p>Use copy as prompt when the user mutates state.</p>
</body></html>`,
  ),
});

// External CDN
cases.push({
  id: "cdn-script",
  incident: "self-containment / EXTERNAL_RESOURCE",
  expectFail: true,
  flags: [],
  path: write(
    "cdn.html",
    `${HEAD}
<input type="search" aria-label="q"><table></table><svg></svg>
<script src="https://cdn.example.com/app.js"></script>
</body></html>`,
  ),
});

// SVG width=auto
cases.push({
  id: "svg-width-auto",
  incident: "lint-artifact SVG auto size",
  expectFail: true,
  flags: [],
  path: write(
    "svg-auto.html",
    `${HEAD}
<input type="search" aria-label="q"><table></table>
<svg width="auto" height="auto"></svg>
</body></html>`,
  ),
});

// Judgment: wrong shape (editorial chrome on a table) — lint cannot know
cases.push({
  id: "wrong-shape-editorial-on-table",
  incident: "2026-05-25 omega-3 editorial draft on tabular data / PR #6",
  expectFail: false,
  flags: [],
  judgment: "lint cannot detect wrong shape",
  path: write(
    "wrong-shape.html",
    `${HEAD}
<input type="search" aria-label="q">
<button type="button">copy as prompt</button>
<textarea id="prompt-output">BEGIN ARTIFACT STATE DATA
x
END ARTIFACT STATE DATA</textarea>
<svg></svg>
<table><tr><td>EPA</td><td>1860</td></tr></table>
<article class="editorial"><p>An essay about supplements.</p></article>
</body></html>`,
  ),
});

// Judgment: scatter for 8 clustered points — lint cannot know
cases.push({
  id: "wrong-primitive-scatter",
  incident: "2026-05-25 omega-3 scatter for 8 clustered points / PR #6",
  expectFail: false,
  flags: [],
  judgment: "lint cannot detect wrong chart primitive",
  path: write(
    "wrong-scatter.html",
    `${HEAD}
<input type="search" aria-label="q">
<button type="button">copy as prompt</button>
<textarea id="prompt-output">BEGIN ARTIFACT STATE DATA
x
END ARTIFACT STATE DATA</textarea>
<svg class="scatter"><circle cx="1" cy="1"></circle></svg>
</body></html>`,
  ),
});

const results = [];
for (const c of cases) {
  const r = spawnSync(
    "node",
    [path.join(REPO, "scripts/lint-artifact.mjs"), "--json", ...c.flags, c.path],
    { encoding: "utf8" },
  );
  let parsed;
  try {
    parsed = JSON.parse(r.stdout);
  } catch {
    parsed = { raw: r.stdout, stderr: r.stderr, status: r.status };
  }
  const ok = parsed.ok === true;
  const caught = c.expectFail ? !ok : ok;
  results.push({
    id: c.id,
    incident: c.incident,
    expectFail: c.expectFail,
    judgment: c.judgment || null,
    lintOk: ok,
    exit: r.status,
    caught,
    fails: parsed.results?.[0]?.fails || [],
    features: parsed.results?.[0]?.features || [],
    bytes: parsed.results?.[0]?.bytes || 0,
  });
}

const out = {
  repo: REPO,
  lint: "scripts/lint-artifact.mjs",
  cases: results,
  summary: {
    total: results.length,
    caught: results.filter((x) => x.caught).length,
    missedMechanical: results.filter((x) => !x.caught && x.expectFail).length,
    judgmentGaps: results.filter((x) => x.judgment).map((x) => x.id),
  },
};
fs.writeFileSync(path.join(SPIKE, "replay-results.json"), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2));
