#!/usr/bin/env node
// Throwaway spike: lint --against prior.html for dropped ids / copy-as-prompt / scripts.
// Decision instrument for plans/README direction A (update contract).

import fs from "node:fs";

const priorPath = process.argv[2];
const nextPath = process.argv[3];
if (!priorPath || !nextPath) {
  console.error("usage: node lint-against.mjs <prior.html> <next.html>");
  process.exit(2);
}

const ids = (html) => new Set([...html.matchAll(/\bid=["']([^"']+)["']/g)].map((m) => m[1]));
const scripts = (html) =>
  [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].filter((m) => !/\bsrc=/i.test(m[1])).length;
const copyPrompt = (html) => /copy as prompt|copyPrompt|prompt-output/i.test(html);
const features = (html) => {
  const rx = {
    search: /type=["']search["']/i,
    svg: /<svg\b/i,
    table: /<table\b/i,
    textarea: /<textarea\b/i,
    toggle: /aria-pressed|type=["']checkbox["']/i,
  };
  return Object.keys(rx).filter((k) => rx[k].test(html));
};

const prior = fs.readFileSync(priorPath, "utf8");
const next = fs.readFileSync(nextPath, "utf8");
const droppedIds = [...ids(prior)].filter((id) => !ids(next).has(id)).sort();
const addedIds = [...ids(next)].filter((id) => !ids(prior).has(id)).sort();
const report = {
  prior: priorPath,
  next: nextPath,
  droppedIds,
  addedIds,
  scriptCount: { prior: scripts(prior), next: scripts(next) },
  copyPrompt: { prior: copyPrompt(prior), next: copyPrompt(next) },
  features: { prior: features(prior), next: features(next) },
  fails: [],
};
if (droppedIds.length) report.fails.push(`dropped ids: ${droppedIds.join(", ")}`);
if (scripts(prior) > 0 && scripts(next) === 0) report.fails.push("update deleted every inline script");
if (copyPrompt(prior) && !copyPrompt(next)) report.fails.push("update dropped copy-as-prompt");
const lost = features(prior).filter((f) => !features(next).includes(f));
if (lost.length) report.fails.push(`lost feature detectors: ${lost.join(", ")}`);
report.ok = report.fails.length === 0;
console.log(JSON.stringify(report, null, 2));
process.exit(report.ok ? 0 : 1);
