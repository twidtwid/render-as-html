#!/usr/bin/env node
// og-card.mjs — generate a 1200×630 social card PNG for a render-as-html artifact,
// using the artifact's OWN title / og:description / design tokens, then (optionally)
// inject og:image + twitter:image into the artifact <head> so a hosted artifact
// unfurls with a real preview. Fixes the "published post lacked an og image" gap.
//
// Usage:
//   node bin/og-card.mjs <artifact.html> [--inject]
// Writes <artifact-dir>/og-card.png (report-portal auto-detects this sibling).
// With --inject, also rewrites the artifact <head>: adds og:image=og-card.png,
// twitter:image=og-card.png, and upgrades twitter:card to summary_large_image.
//
// Browser discovery: set OG_CARD_CHROME to a browser binary to override the
// built-in candidate probe (useful off macOS or in CI).
//
// --no-screenshot: for tests/CI — skips browser resolution and the screenshot
// entirely but still performs --inject. Not part of the publish contract.

import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import os from 'node:os';

const file = process.argv[2];
const inject = process.argv.includes('--inject');
const noScreenshot = process.argv.includes('--no-screenshot');
if (!file) { console.error('usage: og-card.mjs <artifact.html> [--inject]'); process.exit(2); }
let html = fs.readFileSync(file, 'utf8');
const pick = (rx, d = '') => (html.match(rx)?.[1] ?? d).trim();
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const title = pick(/<title>([\s\S]*?)<\/title>/i, 'Untitled');
const desc  = pick(/property=["']og:description["']\s+content=["']([^"']*)["']/i)
           || pick(/name=["']description["']\s+content=["']([^"']*)["']/i);
const kicker = pick(/property=["']og:site_name["']\s+content=["']([^"']*)["']/i, 'render-as-html');
// tokens from :root (fall back to house reading-register values)
const tok = (name, d) => pick(new RegExp('--' + name + ':\\s*(#[0-9a-fA-F]{3,8})'), d);
const paper = tok('paper', '#faf6ef'), ink = tok('ink', '#1a1815'),
      accent = tok('accent', '#8a3a1a'), muted = tok('muted', '#736d62'), rule = tok('rule', '#d9d1c2');

const card = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;box-sizing:border-box}
html,body{width:1200px;height:630px}
body{background:${paper};color:${ink};font-family:"Charter","Iowan Old Style",Palatino,Georgia,serif;padding:76px 84px;display:flex;flex-direction:column;justify-content:space-between}
.kick{font-family:ui-monospace,Menlo,monospace;font-size:20px;letter-spacing:.16em;text-transform:uppercase;color:${accent}}
h1{font-size:${title.length > 78 ? 54 : title.length > 52 ? 64 : 76}px;line-height:1.08;font-weight:700;letter-spacing:-.01em;max-width:1020px}
p{font-size:30px;line-height:1.4;color:${muted};max-width:1000px}
.rule{height:6px;width:120px;background:${accent};border-radius:3px;margin-bottom:30px}
.foot{font-family:ui-monospace,Menlo,monospace;font-size:19px;color:${muted};border-top:1px solid ${rule};padding-top:18px}
</style></head><body>
<div><div class="kick">${esc(kicker)}</div></div>
<div><div class="rule"></div><h1>${esc(title)}</h1></div>
<div class="foot">${esc(desc).slice(0, 120)}</div>
</body></html>`;

// Per-artifact name so a shared reports dir doesn't collide (report-portal
// copies this to og-card.png inside each published slug dir).
const stem = path.basename(file).replace(/\.html?$/i, '');
const out = path.join(path.dirname(path.resolve(file)), `${stem}.og.png`);

function findChrome() {
  if (process.env.OG_CARD_CHROME) return process.env.OG_CARD_CHROME;
  const candidates = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  const pathDirs = (process.env.PATH || '').split(path.delimiter);
  for (const bin of ['google-chrome', 'chromium', 'chromium-browser']) {
    for (const dir of pathDirs) {
      const full = path.join(dir, bin);
      if (fs.existsSync(full)) return full;
    }
  }
  return null;
}

if (!noScreenshot) {
  const chrome = findChrome();
  if (!chrome) {
    console.error('og-card: no Chrome/Chromium found — set OG_CARD_CHROME to a browser binary');
    process.exit(1);
  }
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'og-card-'));
  const tmp = path.join(tmpDir, path.basename(file) + '.html');
  fs.writeFileSync(tmp, card);
  try {
    execFileSync(chrome, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
      '--window-size=1200,630', `--screenshot=${out}`, `file://${tmp}`], { stdio: 'ignore' });
    console.log('wrote ' + out);
  } catch (e) {
    console.error('og-card: screenshot failed: ' + e.message);
    process.exitCode = 1;
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
  if (process.exitCode === 1) process.exit(1);
}

if (inject) {
  if (!/property=["']og:image["']/i.test(html)) {
    const tags = `<meta property="og:image" content="og-card.png">\n<meta name="twitter:image" content="og-card.png">\n`;
    const before = html;
    // upgrade twitter:card to large image
    html = html.replace(/<meta\s+name=["']twitter:card["']\s+content=["'][^"']*["']\s*>/i,
      '<meta name="twitter:card" content="summary_large_image">');
    html = html.replace(/(<meta\s+name=["']twitter:card["'][^>]*>)/i, `$1\n${tags.trim()}`);
    if (html === before) {
      // No twitter:card tag existed, so both replaces were no-ops. Fall back
      // to inserting a fresh twitter:card plus the image tags right after
      // </title> (or after <head…> if no <title> is present).
      const fallback = `<meta name="twitter:card" content="summary_large_image">\n${tags.trim()}`;
      if (/<\/title>/i.test(html)) {
        html = html.replace(/<\/title>/i, `</title>\n${fallback}`);
      } else if (/<head[^>]*>/i.test(html)) {
        html = html.replace(/<head[^>]*>/i, `$&\n${fallback}`);
      } else {
        console.error('og-card: could not find </title> or <head> to inject into — aborting');
        process.exit(1);
      }
    }
    fs.writeFileSync(file, html);
    console.log('injected og:image + twitter:image into ' + path.basename(file) + '; twitter:card → summary_large_image');
  } else {
    console.log('og:image already present — not re-injecting');
  }
}
