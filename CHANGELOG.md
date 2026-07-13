# Changelog

Newest first. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

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
