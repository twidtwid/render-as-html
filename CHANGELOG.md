# Changelog

Newest first. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## 2.7.0 — 2026-07-13

Eight audit-driven improvement plans, executed and reviewed. Nothing in the artifact contract changed; the quality gates around it got materially stricter, and the always-loaded context got smaller.

**Quality gates**

- **CI, at last.** `.github/workflows/ci.yml` runs `make check` on every push to `main` and every PR. `make check` is the single answer to "does the repo pass?" — pytest, the perf harness, and the four Node linters, in one command.
- **The feature floor now measures markup, not prose.** The "≥3 HTML-native features" gate was matching the *words* "search", "filter", "toggle", "sort", and "highlight" anywhere on the page — including in prose and CSS. The five detectors are now anchored to real markup and behavior (`type="search"`, `data-sort`, `aria-pressed`, `scrollIntoView`, `classList.add/toggle(`, …). Consequence, and it's the honest one: `examples/index.html` and `examples/primitives.html` were clearing the artifact floor on phantom matches — they have no interactive markup at all — and are now linted as reference surfaces (`--reference`) rather than artifacts. The 13 shape examples all still clear the floor on real features.
- **Dead-control scan widened** to `querySelectorAll` and compound selectors (`querySelector('#chart .bar')` was silently unchecked). **Token drift check** now sees 3-, 4-, and 8-digit hex, not only 6-digit.
- **copy-as-prompt delimiter check** no longer fires on a prose mention of the phrase — only on a real control.
- **One vocabulary, machine-enforced.** The shared HTML-invariant rules (required meta, feature table, external-resource patterns) live in `scripts/lib/html-checks.mjs`, imported by both Node linters. `scripts/perf_harness.py` keeps a deliberate Python mirror (the harness must run without Node) and a new parity test fails the suite if the two ever drift.
- **Version drift** is gated by `scripts/check-versions.mjs` (added in 2.6.3): SKILL.md frontmatter is canonical and every release surface must match.

**Correctness**

- `bin/render-podcast`: URLs from the episode package are scheme-checked before becoming live `href`s (a `javascript:`/`data:` URL in scraped show-notes was previously rendered as a clickable anchor). Malformed or `episode`-less packages now exit 1 with a one-line message instead of a traceback.
- `bin/render-podcast` ↔ canonical-example parity is now tested: every id and styled class the examples wire up must appear in real rendered output. The dark-mode `@media`→`body.dark` rewrite was **dead code** — the example stopped using `prefers-color-scheme` some releases ago — so it's deleted and replaced with an assertion that fails loudly if the example's palette block drifts.
- `bin/og-card.mjs`: discovers Chrome/Chromium (env override + candidate probe) instead of hardcoding one macOS path; uses a unique temp dir and cleans it up on failure; and `--inject` no longer reports success while injecting nothing when the artifact has no `twitter:card` tag.

**Context load**

- `SKILL.md` §Design system's deep contract (sticky-rail collapse invariant, density metrics, interactivity rules) moved to `references/design.md`, loaded on demand via the preflight `READ:`. SKILL.md drops ~1,000 tokens (12,621 → 11,617) off every invocation.
- The perf harness stopped lying about deferral: it was counting SKILL.md-internal sections as "on-demand reference" (a claimed 34% that loads every time). It now measures `references/` as the real deferred load, and `perf/baseline.json` carries only the fields the gates actually check.

## 2.6.3 — 2026-07-12

- Added `scripts/check-versions.mjs` — version-drift checker: SKILL.md frontmatter is the canonical version; every release surface (README, index.html, gallery/primitives/podcast example footers, `bin/render-podcast`) must carry the same string. Gated by a new test in `tests/test_linters.py`.
- Introduced this CHANGELOG.
- Corrected the example-gallery primitives card: ten canonical primitives (scatter was missing from the count and the list).
- README "What's in here" now documents `bin/og-card.mjs`.
- This version also stamps the previously-unversioned feature set shipped in `e0278cb` past the v2.6.2 tag: artifact lint gate (dead-script + dead-control + og:image checks in `scripts/lint-artifact.mjs`), `bin/og-card.mjs` social-card generator, scatter primitive (10th), per-shape reference contracts (`references/shapes/*.md`), and `DESIGN.md` canonical tokens + `scripts/check-tokens.mjs`.

## 2.6.2 — 2026-05-31

- Added Architecture diagram to README.

## 2.6.1 — 2026-05-30

- Progressive disclosure of primitive + editorial contracts (compact inline stubs in SKILL.md; full contracts load on demand from `references/`).

## 2.6.0 — 2026-05-30

- Podcast contract split + harness audits.

## 2.5.0 — 2026-05-30

- Contract/QA hardening + perf harness (`scripts/perf_harness.py` with committed baseline).

Older history lives in git tags (`git tag -l` / `git log v2.0.0..v2.5.0 --oneline`).
