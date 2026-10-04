#!/usr/bin/env node
// check-contracts.mjs — fail when SKILL.md, references/, examples/, or the
// harness disagree with contracts/shapes.json and contracts/primitives.json.
//
//   node scripts/check-contracts.mjs
//   node scripts/check-contracts.mjs --root /path/to/tree
//
// stdlib only. Exit 0 on a matching tree. Exit 1 on drift.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const FEATURE_KEYS = new Set([
  "search",
  "inline_svg",
  "table",
  "copy_as_prompt",
  "sorting",
  "filtering",
  "local_storage",
  "drag",
  "toggle",
  "textarea",
  "cross_highlight",
]);
const NOT_SHAPES = new Set(["checklist", "podcast-transcript"]);
const STALE_COUNTS = [
  "Nine page shapes",
  "nine chart and table primitives",
  "All eleven shape examples",
];

const argv = process.argv.slice(2);
let root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const rootIdx = argv.indexOf("--root");
if (rootIdx >= 0) {
  if (!argv[rootIdx + 1]) {
    console.error("check-contracts: --root needs a directory");
    process.exit(2);
  }
  root = path.resolve(argv[rootIdx + 1]);
}

const read = (rel) => fs.readFileSync(path.join(root, rel), "utf8");
const exists = (rel) => fs.existsSync(path.join(root, rel));

const fails = [];
const note = (msg) => fails.push(msg);

let shapesDoc;
let primitivesDoc;
try {
  shapesDoc = JSON.parse(read("contracts/shapes.json"));
  primitivesDoc = JSON.parse(read("contracts/primitives.json"));
} catch (err) {
  console.error(`check-contracts: cannot read registry JSON (${err.message})`);
  process.exit(2);
}

const shapes = shapesDoc.shapes;
const primitives = primitivesDoc.primitives;
if (!Array.isArray(shapes) || !Array.isArray(primitives)) {
  console.error("check-contracts: registry JSON must have shapes[] and primitives[]");
  process.exit(2);
}

console.log(`${shapes.length} shapes · ${primitives.length} primitives`);

if (shapes.length !== 12) note(`expected 12 shapes, found ${shapes.length}`);
if (primitives.length !== 10) note(`expected 10 primitives, found ${primitives.length}`);

const shapeIds = new Set();
for (const shape of shapes) {
  if (!shape.id) {
    note("a shapes.json entry is missing id");
    continue;
  }
  if (NOT_SHAPES.has(shape.id)) note(`${shape.id} must stay out of the shape list`);
  if (shapeIds.has(shape.id)) note(`duplicate shape id ${shape.id}`);
  shapeIds.add(shape.id);
  if (!shape.pickWhen) note(`${shape.id}: missing pickWhen`);
  if (!shape.register) note(`${shape.id}: missing register`);
  if (!Array.isArray(shape.requiredFeatures)) note(`${shape.id}: missing requiredFeatures`);
  else {
    for (const key of shape.requiredFeatures) {
      if (!FEATURE_KEYS.has(key)) note(`${shape.id}: unknown required feature ${key}`);
    }
  }
  if (!shape.example) note(`${shape.id}: missing example`);
  else if (!exists(shape.example)) note(`${shape.id}: missing ${shape.example}`);
  if (!shape.reference) note(`${shape.id}: missing reference`);
  else if (!exists(shape.reference)) note(`${shape.id}: missing ${shape.reference}`);
}

const primitiveIds = new Set();
for (const primitive of primitives) {
  if (!primitive.id) {
    note("a primitives.json entry is missing id");
    continue;
  }
  if (primitiveIds.has(primitive.id)) note(`duplicate primitive id ${primitive.id}`);
  primitiveIds.add(primitive.id);
  if (!primitive.pickWhen) note(`${primitive.id}: missing pickWhen`);
  if (!primitive.register) note(`${primitive.id}: missing register`);
  if (!Array.isArray(primitive.requiredFeatures)) note(`${primitive.id}: missing requiredFeatures`);
  else {
    for (const key of primitive.requiredFeatures) {
      if (!FEATURE_KEYS.has(key)) note(`${primitive.id}: unknown required feature ${key}`);
    }
  }
  if (!primitive.example) note(`${primitive.id}: missing example`);
  else if (!exists(primitive.example)) note(`${primitive.id}: missing ${primitive.example}`);
  if (!primitive.reference) note(`${primitive.id}: missing reference`);
  else if (!exists(primitive.reference)) note(`${primitive.id}: missing ${primitive.reference}`);
}

let skill = "";
let gallery = "";
let primGallery = "";
let harness = "";
try {
  skill = read("SKILL.md");
  gallery = read("examples/index.html");
  primGallery = read("examples/primitives.html");
  harness = read("scripts/perf_harness.py");
} catch (err) {
  note(`cannot read a compared file (${err.message})`);
}

for (const shape of shapes) {
  if (!shape.id) continue;
  if (!skill.includes(shape.id)) note(`${shape.id}: SKILL.md does not name this id`);
  if (shape.href && !gallery.includes(shape.href)) {
    note(`${shape.id}: gallery missing link ${shape.href}`);
  }
  const heading = new RegExp(`#### \`${shape.id}\``);
  if (skill && !heading.test(skill)) note(`${shape.id}: SKILL.md missing compact contract`);
}

for (const primitive of primitives) {
  if (!primitive.id) continue;
  if (!skill.includes(primitive.id)) note(`${primitive.id}: SKILL.md does not name this id`);
  if (primitive.href && !primGallery.includes(primitive.href)) {
    note(`${primitive.id}: primitives gallery missing link ${primitive.href}`);
  }
  if (primitive.skillHeading) {
    const heading = new RegExp(primitive.skillHeading, "i");
    if (skill && !heading.test(skill)) {
      note(`${primitive.id}: SKILL.md missing contract ${primitive.skillHeading}`);
    }
  }
}

if (harness) {
  if (!harness.includes("contracts/shapes.json")) {
    note("scripts/perf_harness.py does not load contracts/shapes.json");
  }
  if (!harness.includes("contracts/primitives.json")) {
    note("scripts/perf_harness.py does not load contracts/primitives.json");
  }
  if (/^SHAPE_REFERENCES = \{/m.test(harness)) {
    note("scripts/perf_harness.py still hardcodes SHAPE_REFERENCES");
  }
  if (/^PRIMITIVE_FILES = \{/m.test(harness)) {
    note("scripts/perf_harness.py still hardcodes PRIMITIVE_FILES");
  }
}

if (exists("references/shapes")) {
  for (const name of fs.readdirSync(path.join(root, "references/shapes"))) {
    if (!name.endsWith(".md")) continue;
    const id = name.slice(0, -3);
    if (!shapeIds.has(id)) note(`references/shapes/${name} is not in contracts/shapes.json`);
  }
}

if (exists("examples/podcast.html")) {
  const podcast = read("examples/podcast.html");
  for (const stale of STALE_COUNTS) {
    if (podcast.includes(stale)) note(`examples/podcast.html still says ${stale}`);
  }
}

if (fails.length) {
  console.error("check-contracts: drift detected");
  for (const line of fails) console.error(`  ${line}`);
  process.exit(1);
}

console.log("check-contracts: 12 shapes and 10 primitives match the tree.");
process.exit(0);
