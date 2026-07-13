#!/usr/bin/env node
// check-versions.mjs — assert every release surface carries the canonical version.
//
// SKILL.md's frontmatter `version:` field is the canonical source. This
// checker enforces that the canonical version string appears (as `X.Y.Z` or
// `vX.Y.Z`) in every release-surface file, and that no OTHER render-as-html
// version number (a stale leftover from a previous bump) remains anywhere in
// those files.
//
//   node scripts/check-versions.mjs   # report; exit 1 on drift, 2 on structural error
//
// stdlib only, no dependencies.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const read = (rel) => fs.readFileSync(path.join(REPO, rel), "utf8");

// --- canonical: SKILL.md frontmatter `version:` line ---
const skill = read("SKILL.md");
const versionMatch = skill.match(/^version:\s*(\d+\.\d+\.\d+)\s*$/m);
if (!versionMatch) {
  console.error("check-versions: SKILL.md has no frontmatter `version: X.Y.Z` line");
  process.exit(2);
}
const canonical = versionMatch[1];

const FILES = [
  "SKILL.md",
  "README.md",
  "index.html",
  "examples/index.html",
  "examples/primitives.html",
  "examples/podcast.html",
  "examples/podcast-transcript.html",
  "bin/render-podcast",
];

// Stale-version detection is scoped to actual version-stamp contexts, not a
// bare `\bv?\d+\.\d+\.\d+\b` scan across the whole file: these files also
// contain unrelated dotted numbers that look like versions but aren't —
// WCAG success-criteria numbers ("WCAG 2.4.7"), and prose/comments that
// reference a *past* render-as-html version by name ("same v2.1.2 editorial
// pattern"). Both would false-positive a naive scan. Real version stamps in
// this repo always sit next to a middot (`v2.6.2 · ...` / `... · v2.6.2`),
// or use the literal word "Version"/"version" (README's "**Version 2.6.2**",
// SKILL.md frontmatter's "version: 2.6.2").
const STAMP_PATTERNS = [
  /·\s*v?(\d+\.\d+\.\d+)/g, // "· v2.6.2" or "· 2.6.2"
  /v?(\d+\.\d+\.\d+)\s*·/g, // "v2.6.2 ·" or "2.6.2 ·"
  /[Vv]ersion:?\s+(\d+\.\d+\.\d+)/g, // "**Version 2.6.2**" / "version: 2.6.2"
];

let anyFail = false;
const lines = [];

for (const rel of FILES) {
  let content;
  try {
    content = read(rel);
  } catch (err) {
    anyFail = true;
    lines.push(`STALE ${rel} — could not read file (${err.message})`);
    continue;
  }

  const hasCanonical = content.includes(canonical);

  const stale = new Set();
  for (const re of STAMP_PATTERNS) {
    re.lastIndex = 0;
    let m;
    while ((m = re.exec(content)) !== null) {
      const found = m[1];
      // Only the "2." major line is render-as-html's version scheme; this
      // also excludes incidental dotted-number matches (e.g. an IP address
      // octet run like "192.168.1.225" adjacent to a middot in example
      // markup) that aren't render-as-html versions at all.
      if (found !== canonical && found.startsWith("2.")) stale.add(found);
    }
  }

  if (!hasCanonical) {
    anyFail = true;
    lines.push(`STALE ${rel} — missing canonical version ${canonical}`);
  } else if (stale.size) {
    anyFail = true;
    lines.push(`STALE ${rel} — stale version-stamp string(s) found: ${[...stale].sort().join(", ")}`);
  } else {
    lines.push(`OK    ${rel}`);
  }
}

console.log(`canonical version (SKILL.md): ${canonical}\n`);
for (const line of lines) console.log(line);
console.log();

if (anyFail) {
  console.error("check-versions: drift detected — failing.");
  process.exit(1);
}
console.log("check-versions: clean.");
