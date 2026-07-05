---
# DESIGN.md — the one-truth design tokens, in the google-labs-code/design.md format.
#
# This file is the CANONICAL source for the render-as-html palette and type system.
# SKILL.md's §Design system color block and the CSS custom properties in index.html
# are derived from these values; scripts/check-tokens.mjs asserts they have not
# drifted. design.md was adopted for the *format* only — render-as-html deliberately
# does NOT expose design tokens as a user-tunable knob (the fixed taste IS the
# product). This is an internal build input, not a configuration surface.
#
# Format: github.com/google-labs-code/design.md  ·  spec: docs/spec.md
overview:
  personality: Warm, editorial, non-corporate. Two registers — a serif "reading"
    voice for long-form and a dense sans "instrument" voice for data — sharing one
    palette so a dashboard and an essay feel like the same system.
  modes: [light, dark]

colors:
  light:
    paper:        "#faf6ef"   # warm cream — page background
    paper-tint:   "#f3ede1"   # recessed surfaces, hover fills
    paper-card:   "#fbf7f0"   # raised cards
    ink:          "#1a1815"   # warm near-black — body text
    ink-soft:     "#4a443c"   # secondary text
    muted:        "#736d62"   # metadata, captions (AA 4.76:1 on paper)
    rule:         "#d9d1c2"   # dividers, borders
    rule-soft:    "#ece5d6"   # hairline dividers inside cards
    accent:       "#8a3a1a"   # terracotta — THE single accent
    accent-2:     "#c2901a"   # ochre/gold — affirmative actions only (fill, never text on paper)
    ok:           "#2f7d44"
    warn:         "#9b641d"
    note:         "#2f6fb3"
  dark:
    paper:        "#1a1815"
    paper-tint:   "#221f1a"
    paper-card:   "#211e19"
    ink:          "#f0eee8"
    ink-soft:     "#c9c3b6"
    muted:        "#9a948a"   # AA 5.89:1 on dark paper
    rule:         "#38332b"
    rule-soft:    "#2c2820"
    accent:       "#e0794f"   # terracotta, lifted for dark bg
    accent-2:     "#d8a73a"
    ok:           "#5cae6f"
    warn:         "#c79a4a"
    note:         "#6f9fd0"

typography:
  families:
    serif: '"Charter", "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, "Source Serif Pro", serif'
    sans:  'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif'
    mono:  'ui-monospace, "SF Mono", Menlo, Consolas, monospace'
  registers:
    reading:    { shapes: [document, editorial, timeline], display: serif, body: serif, size: 17-18px, line-height: 1.6, measure: 46rem }
    instrument: { shapes: [dashboard, comparison, developer, runbook, triage-board, network-map], display: sans, body: sans, size: 14-15px, line-height: 1.5, cell-padding: "8px 10px" }
  numerics: tabular-nums on every table and numeric column

rounded:
  sm: 3px      # inputs, chips
  md: 6px      # cards, tiles
  lg: 10px     # frames, gallery panels

spacing:
  section-gap-reading: 2.5rem
  table-cell: "8px 10px"
  touch-target-min: 32px
---

# Design tokens

This is the single source of truth for render-as-html's palette and type system, written in the [design.md](https://github.com/google-labs-code/design.md) format. The frontmatter above is machine-readable; this prose is the rationale.

## Why design.md format, but not design.md philosophy

design.md exists to make a design system a *portable, configurable* thing — many tools and agents read the same tokens and render consistently, and the design is a variable. render-as-html's entire thesis is the opposite: **the design is not a variable.** One palette, two registers, application determined by the page shape, never chosen ad hoc. The fixed taste is the product.

So we adopt the *format* (a clean, machine-readable token file) without the *configurability*. `DESIGN.md` is an internal build input — the canonical place the palette lives — not a knob the user turns. Generated artifacts never read it at runtime; they inline their own copy of these values.

## What derives from this file

- **`SKILL.md` §Design system / Color** — the light + dark hex block. Must match this file exactly. `scripts/check-tokens.mjs` hard-fails on any divergence.
- **`index.html`** — the live design-system gallery uses its own CSS custom-property *names* but the same *values*. The checker reports (as drift warnings) any canonical value missing from `index.html`, since index.html legitimately also carries extra category/chart swatches not part of the core palette.
- **Every generated artifact** — inlines these values as `:root` custom properties (self-contained, zero external requests).

## Color rules (carried from SKILL.md, normative)

- One primary accent (terracotta), one affirmative-action color (ochre). No third accent, no corporate blue.
- All text meets WCAG AA on its background (≥4.5:1 normal, ≥3:1 large/UI), including `--muted`.
- `--accent-2` (ochre) is a **fill, not a text color on paper** — ochre-on-cream is ~2.7:1 (fail). Affirmative elements put ochre in the background with `--ink` (not white) as foreground (~6:1, pass).
- Color is never the only signal — pair with text, icon, or shape.

## Maintenance

When the palette changes: edit this file, then run `node scripts/check-tokens.mjs` and update `SKILL.md` + `index.html` until it passes clean. This file changes first; the others follow.
