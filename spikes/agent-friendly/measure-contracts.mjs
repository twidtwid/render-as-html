#!/usr/bin/env node
// Throwaway spike: measure SKILL vs reference vs example sizes and overlap.
// Decision instrument only.

import fs from "node:fs";
import path from "node:path";

const REPO = process.env.REPO || "/workspace";
const words = (s) => s.trim().split(/\s+/).filter(Boolean).length;
const tokensApprox = (s) => Math.round(s.length / 4);

function read(rel) {
  return fs.readFileSync(path.join(REPO, rel), "utf8");
}

const skill = read("SKILL.md");
const shapes = fs.readdirSync(path.join(REPO, "references/shapes")).filter((f) => f.endsWith(".md"));
const prims = fs.readdirSync(path.join(REPO, "references/primitives")).filter((f) => f.endsWith(".md"));

function sectionBetween(src, startRe, endRe) {
  const start = src.search(startRe);
  if (start < 0) return "";
  const rest = src.slice(start);
  const end = rest.slice(1).search(endRe);
  return end < 0 ? rest : rest.slice(0, end + 1);
}

const rows = [];
for (const f of shapes) {
  const name = f.replace(/\.md$/, "");
  const ref = read(`references/shapes/${f}`);
  const examplePath = `examples/${name}.html`;
  const example = fs.existsSync(path.join(REPO, examplePath)) ? read(examplePath) : "";
  const stubRe = new RegExp(`#### \`${name}\`[\\s\\S]*?(?=\\n#### |\n## )`);
  const stub = skill.match(stubRe)?.[0] || "";
  rows.push({
    kind: "shape",
    name,
    skillStubLines: stub ? stub.split("\n").length : 0,
    skillStubWords: words(stub),
    refLines: ref.split("\n").length,
    refWords: words(ref),
    refIsStub: ref.split("\n").length <= 20,
    exampleBytes: Buffer.byteLength(example, "utf8"),
    exampleHasScript: /<script\b/i.test(example),
    skillThickerThanRef: words(stub) > words(ref),
  });
}

for (const f of prims) {
  const name = f.replace(/\.md$/, "");
  const ref = read(`references/primitives/${f}`);
  const exampleFiles = fs.readdirSync(path.join(REPO, "examples/primitives")).filter((x) => x.endsWith(".html"));
  rows.push({
    kind: "primitive",
    name,
    refLines: ref.split("\n").length,
    refWords: words(ref),
    refIsStub: ref.split("\n").length <= 16,
    exampleCount: exampleFiles.length,
  });
}

const versionFiles = [
  "SKILL.md",
  "README.md",
  "index.html",
  "examples/index.html",
  "examples/primitives.html",
  "examples/podcast.html",
  "examples/podcast-transcript.html",
  "bin/render-podcast",
];
const extraStampFiles = [];
for (const rel of [
  "examples/dashboard.html",
  "examples/document.html",
  "examples/editorial.html",
  "examples/timeline.html",
  "examples/runbook.html",
  "examples/comparison.html",
  "examples/network-map.html",
  "examples/triage-board.html",
  "examples/developer.html",
  "examples/execution-log.html",
  "examples/deck-review.html",
  "examples/checklist.html",
]) {
  const t = read(rel);
  if (/·\s*v?2\.\d+\.\d+|v2\.\d+\.\d+\s*·|[Vv]ersion:?\s+2\.\d+\.\d+/.test(t)) extraStampFiles.push(rel);
}

const writeClipboardFiles = [];
const walk = (dir) => {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name);
    if (fs.statSync(p).isDirectory()) walk(p);
    else if (name.endsWith(".html") || name === "SKILL.md") {
      const t = fs.readFileSync(p, "utf8");
      if (/function writeClipboard|navigator\.clipboard/.test(t)) writeClipboardFiles.push(path.relative(REPO, p));
    }
  }
};
walk(path.join(REPO, "examples"));
if (/function writeClipboard/.test(skill)) writeClipboardFiles.push("SKILL.md");

const out = {
  skill: {
    bytes: Buffer.byteLength(skill, "utf8"),
    lines: skill.split("\n").length,
    words: words(skill),
    tokensApprox: tokensApprox(skill),
    baselineTokens: 12241,
  },
  referencesDir: {
    shapes: shapes.length,
    primitives: prims.length,
    designWords: words(read("references/design.md")),
  },
  rows,
  stubShapes: rows.filter((r) => r.kind === "shape" && r.refIsStub).map((r) => r.name),
  thickShapes: rows.filter((r) => r.kind === "shape" && !r.refIsStub).map((r) => r.name),
  skillThickerThanRef: rows.filter((r) => r.skillThickerThanRef).map((r) => r.name),
  versionCheckerFiles: versionFiles,
  extraExampleStampsNotInChecker: extraStampFiles.filter((f) => !versionFiles.includes(f)),
  clipboardSites: writeClipboardFiles,
  plan009Shipped: fs.existsSync(path.join(REPO, "scripts/lib/html-checks.mjs")),
};
fs.writeFileSync("/tmp/rah-spikes/contract-measure.json", JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2));
