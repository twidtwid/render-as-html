# Developer Shape Reference

Load before authoring or changing a `developer`-shape artifact, or `examples/developer.html`. The compact stub in `SKILL.md` §Page shapes is enough to pick the shape and scaffold; this file holds the build detail. **The annotated diff + severity findings are the shape** — a generic document with code blocks is `document`.

- **Register:** Instrument (sans display + sans body; see §Design system / Density); mono at 13px for code.
- **Use for:** PR writeups, code review, "explain this code" — line-anchored critique where adjacency to the source beats a side panel.
- **Layout:** title + a PR/commit metadata strip + risk callouts at top + the annotated diff body + a summary footer. Max-width 1280px. Optional left rail with a "files changed" navigator.
- **First viewport:** PR summary, a severity-coded findings count (critical / warning / nit), and the top risk callout.
- **Required primitives:** syntax-highlighted code using a tiny set of **local CSS classes** (no Prism, no CDN tokenizer); per-file diffs with `+`/`−` line gutters in soft green/red tints; inline margin annotations anchored to specific lines (not a sidebar); severity-coded finding cards; a files-changed navigator; copy-link-to-finding buttons. See `references/primitives/annotated-diff.md`.
- **Severity travels three ways** (left bar + badge fill + a strip count) so it survives colorblind viewing and greyscale screenshots — never color alone.
- **HTML-native ≥3:** local-CSS syntax highlighting (no external renderer); severity-color findings with a "show nits" toggle; jump-to-file; click-to-copy an individual finding (or `file:line`); optional side-by-side before/after.
- **Avoid:** a generic document with code blocks (that's `document`); findings in a sidebar divorced from the lines they discuss; color-only severity; runtime tokenizers / CDN syntax highlighters.
