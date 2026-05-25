import fs from "node:fs";
import path from "node:path";

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

function hasMeta(html, attr, value) {
  const rx = new RegExp(`<meta\\b[^>]*${attr}=["']${value}["'][^>]*>`, "i");
  return rx.test(html);
}

for (const file of htmlFiles) {
  const html = read(file);

  if (!/<html\b[^>]*\blang=["']en["']/i.test(html)) {
    fail(file, "missing <html lang=\"en\">");
  }
  if (!hasMeta(html, "name", "viewport")) {
    fail(file, "missing viewport meta");
  }
  if (!hasMeta(html, "name", "description")) {
    fail(file, "missing description meta");
  }
  for (const property of ["og:title", "og:description", "og:type", "og:site_name"]) {
    if (!hasMeta(html, "property", property)) {
      fail(file, `missing ${property} meta`);
    }
  }
  if (!hasMeta(html, "name", "twitter:card")) {
    fail(file, "missing twitter:card meta");
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
}

const clipboardFiles = ["SKILL.md", ...htmlFiles];
for (const file of clipboardFiles) {
  const text = read(file);
  if (/navigator\.clipboard\.writeText/.test(text) && !/navigator\.clipboard\s*&&\s*navigator\.clipboard\.writeText/.test(text)) {
    fail(file, "clipboard writes must guard navigator.clipboard before calling writeText");
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
