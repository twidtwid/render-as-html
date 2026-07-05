#!/usr/bin/env node
// check-tokens.mjs — assert the design tokens have not drifted across surfaces.
//
// DESIGN.md (google-labs-code/design.md format) is the canonical source. This
// checker enforces:
//   HARD  — SKILL.md's §Design system color block matches DESIGN.md exactly
//           (same set of hex values). These two are both token specs; they must
//           agree or one is stale.
//   SOFT  — every canonical value also appears literally in index.html. index.html
//           uses its own CSS var NAMES (only values/roles must match) and carries
//           extra category/chart swatches, so a miss here is reported as drift to
//           investigate, not a hard failure.
//
//   node scripts/check-tokens.mjs            # report; exit 1 on HARD drift
//   node scripts/check-tokens.mjs --strict   # also exit 1 on index.html drift
//
// stdlib only, no dependencies.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const strict = process.argv.includes("--strict");

const read = (rel) => fs.readFileSync(path.join(REPO, rel), "utf8");
const hexes = (text) => new Set((text.match(/#[0-9a-fA-F]{6}\b/g) || []).map((h) => h.toLowerCase()));

// --- canonical: hexes inside DESIGN.md's frontmatter (between the first two ---) ---
const design = read("DESIGN.md");
const fm = design.match(/^---\n([\s\S]*?)\n---/);
if (!fm) {
  console.error("check-tokens: DESIGN.md has no YAML frontmatter block");
  process.exit(2);
}
const canonical = hexes(fm[1]);

// --- SKILL.md: hexes inside the §Design system "### Color" fenced block(s) ---
const skill = read("SKILL.md");
const colorSection = skill.split(/\n### Color\b/)[1]?.split(/\n### /)[0] ?? "";
const skillHexes = hexes(colorSection);

// --- index.html: all hexes (superset — has category swatches beyond core palette) ---
const indexHexes = hexes(read("index.html"));

const fmt = (set) => [...set].sort().join(" ");

const missingFromSkill = [...canonical].filter((h) => !skillHexes.has(h)).sort();
const extraInSkill = [...skillHexes].filter((h) => !canonical.has(h)).sort();
const missingFromIndex = [...canonical].filter((h) => !indexHexes.has(h)).sort();

let hard = false;

console.log(`DESIGN.md canonical tokens: ${canonical.size}`);
console.log(`SKILL.md §Color tokens:     ${skillHexes.size}`);
console.log(`index.html distinct hexes:   ${indexHexes.size} (superset OK — includes chart/category swatches)\n`);

if (missingFromSkill.length || extraInSkill.length) {
  hard = true;
  console.log("HARD DRIFT — SKILL.md §Color does not match DESIGN.md:");
  if (missingFromSkill.length) console.log(`  in DESIGN.md but missing from SKILL.md: ${missingFromSkill.join(" ")}`);
  if (extraInSkill.length) console.log(`  in SKILL.md but not in DESIGN.md:        ${extraInSkill.join(" ")}`);
  console.log("  → reconcile: DESIGN.md leads, SKILL.md follows.\n");
} else {
  console.log("OK — SKILL.md §Color matches DESIGN.md exactly.\n");
}

if (missingFromIndex.length) {
  console.log(`${strict ? "DRIFT" : "WARN"} — canonical values absent from index.html (uses its own var names; investigate):`);
  console.log(`  ${missingFromIndex.join(" ")}`);
  console.log("  (e.g. a token index.html expresses via rgba(), a different name, or genuinely dropped.)\n");
} else {
  console.log("OK — every canonical value also appears in index.html.\n");
}

if (hard || (strict && missingFromIndex.length)) {
  console.error("check-tokens: drift detected — failing.");
  process.exit(1);
}
console.log("check-tokens: clean.");
