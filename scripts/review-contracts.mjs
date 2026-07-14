import fs from "node:fs";
import path from "node:path";
import { REQUIRED_META, hasMeta, attrValue, hasAccessibleName } from "./lib/html-checks.mjs";

const root = process.cwd();
const htmlFiles = [
  "index.html",
  ...fs.readdirSync("examples")
    .filter((name) => name.endsWith(".html"))
    .map((name) => `examples/${name}`),
  ...fs.readdirSync("examples/primitives")
    .filter((name) => name.endsWith(".html"))
    .map((name) => `examples/primitives/${name}`),
].sort();

const failures = [];

function read(file) {
  return fs.readFileSync(path.join(root, file), "utf8");
}

function fail(file, message) {
  failures.push(`${file}: ${message}`);
}

function lineNumber(text, index) {
  return text.slice(0, index).split("\n").length;
}

for (const file of htmlFiles) {
  const html = read(file);

  if (!/<html\b[^>]*\blang=["']en["']/i.test(html)) {
    fail(file, "missing <html lang=\"en\">");
  }
  if (!hasMeta(html, "name", "viewport")) {
    fail(file, "missing viewport meta");
  }
  for (const [attr, value] of REQUIRED_META) {
    if (!hasMeta(html, attr, value)) {
      fail(file, `missing ${value} meta`);
    }
  }
  if (!/<link\b[^>]*\brel=["']icon["'][^>]*\bhref=["']data:,["'][^>]*>/i.test(html)) {
    fail(file, "missing blank data favicon link");
  }

  const ids = new Set([...html.matchAll(/\bid=["']([^"']+)["']/g)].map((m) => m[1]));
  for (const match of html.matchAll(/<a\b[^>]*\bhref=["']([^"']+)["'][^>]*>/gi)) {
    const [tag, href] = match;
    if (href.startsWith("#") && href !== "#" && !ids.has(href.slice(1))) {
      fail(file, `local anchor ${href} has no target`);
    }
    if (/^https?:\/\//.test(href)) {
      if (!/\btarget=["']_blank["']/.test(tag)) {
        fail(file, `external link ${href} missing target="_blank"`);
      }
      if (!/\brel=["']noopener noreferrer["']/.test(tag)) {
        fail(file, `external link ${href} missing rel="noopener noreferrer"`);
      }
    }
  }

  for (const match of html.matchAll(/\.dataset\.original\s*=\s*[^;\n]*\.innerHTML/g)) {
    fail(file, `line ${lineNumber(html, match.index)} stores serialized innerHTML for later regex rewriting`);
  }
  for (const match of html.matchAll(/\.innerHTML\s*=\s*[^;\n]*\.replace\s*\(\s*(rx|re)\b/g)) {
    fail(file, `line ${lineNumber(html, match.index)} rewrites serialized HTML with regex`);
  }
  if (/\b(match|matches|no matches)\b/.test(html) && /\bid=["']ed-fcount["']/.test(html)) {
    if (!/id=["']search-prev["']/.test(html) || !/id=["']search-next["']/.test(html)) {
      fail(file, "search match counts require previous/next navigation controls");
    }
  }
  if (/JSON\.parse\s*\(\s*sessionStorage\.getItem/.test(html) && !/function safeSessionJson/.test(html)) {
    fail(file, "sessionStorage JSON.parse must be guarded by safeSessionJson");
  }
  for (const match of html.matchAll(/<textarea\b[^>]*\bclass=["'][^"']*\bcopy-fallback-textarea\b[^"']*["'][^>]*>/gi)) {
    if (!hasAccessibleName(html, match[0])) {
      fail(file, `line ${lineNumber(html, match.index)} copy fallback textarea needs an accessible label`);
    }
  }
  for (const match of html.matchAll(/<input\b[^>]*\bclass=["'][^"']*\bweight-input\b[^"']*["'][^>]*>/gi)) {
    if (!hasAccessibleName(html, match[0])) {
      fail(file, `line ${lineNumber(html, match.index)} weight input needs an accessible label`);
    }
  }
  for (const match of html.matchAll(/<input\b[^>]*\btype=["']search["'][^>]*>/gi)) {
    if (!hasAccessibleName(html, match[0])) {
      fail(file, `line ${lineNumber(html, match.index)} search input needs an accessible label`);
    }
  }
  for (const match of html.matchAll(/<textarea\b[^>]*\bclass=["'][^"']*\b(?:cap-output|cl-note)\b[^"']*["'][^>]*>/gi)) {
    if (!hasAccessibleName(html, match[0])) {
      fail(file, `line ${lineNumber(html, match.index)} textarea needs an accessible label`);
    }
  }
  for (const match of html.matchAll(/<textarea\b[^>]*readonly[^>]*>/gi)) {
    if (!hasAccessibleName(html, match[0])) {
      fail(file, `line ${lineNumber(html, match.index)} readonly textarea needs an accessible label`);
    }
  }
  for (const match of html.matchAll(/<svg\b[^>]*\b(?:height|width)=["']auto["'][^>]*>/gi)) {
    fail(file, `line ${lineNumber(html, match.index)} SVG width/height attributes cannot be "auto"; use CSS for responsive sizing`);
  }
  if (/<artifact\.html>/.test(html)) {
    fail(file, "copy-as-prompt must name the concrete HTML file, not <artifact.html>");
  }
  // Trigger on the JS identifiers of a real control, or on "copy as prompt"
  // inside a SINGLE <button> element. The old `<button[\s\S]*?copy as prompt`
  // form spanned unrelated elements, so a prose mention anywhere after any
  // button on the page falsely demanded the state delimiter. Matches
  // lint-artifact.mjs's per-button scan.
  const buttonSaysCopyPrompt = [...html.matchAll(/<button\b[^>]*>([\s\S]*?)<\/button>/gi)]
    .some((m) => /copy as prompt/i.test(m[1]));
  const hasCopyPrompt =
    /(copyAsPrompt|copyPrompt|copyRecommendation|generateStuckPrompt|copyBtn|promptOut)/.test(html) ||
    buttonSaysCopyPrompt;
  if (hasCopyPrompt && !/BEGIN ARTIFACT STATE DATA/.test(html)) {
    fail(file, "copy-as-prompt output must delimit artifact state as data");
  }
}

const clipboardFiles = ["SKILL.md", ...htmlFiles];
for (const file of clipboardFiles) {
  const text = read(file);
  // Accept either guard form: legacy `&&` or optional chaining `?.`.
  // Artifacts use a `writeClipboard` helper that wraps `?.writeText`, so
  // any file with that helper (or a direct `?.writeText` callsite) passes.
  if (/navigator\.clipboard\.writeText/.test(text)) {
    const hasGuard = /navigator\.clipboard\s*&&\s*navigator\.clipboard\.writeText|navigator\.clipboard\?\.writeText/.test(text);
    if (!hasGuard) fail(file, "clipboard writes must guard navigator.clipboard before calling writeText");
  }
}

const runbook = read("examples/runbook.html");
for (const match of runbook.matchAll(/<div class=["']step-header["'][^>]*>/g)) {
  const tag = match[0];
  if (!/\btabindex=["']0["']/.test(tag)) {
    fail("examples/runbook.html", "step header missing tabindex=\"0\"");
    break;
  }
}
if (!/function handleStepHeaderKey/.test(runbook)) {
  fail("examples/runbook.html", "step headers missing keyboard handler");
}
if (/position:fixed;left:-9999px;top:0;opacity:0/.test(runbook)) {
  fail("examples/runbook.html", "copy-code fallback is hidden offscreen instead of visible");
}

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log(`review contracts passed for ${htmlFiles.length} HTML files`);
