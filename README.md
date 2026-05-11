# render-as-html

> A Claude Code skill for creating HTML artifacts as the source of truth: filters, charts, drag-and-drop boards, and buttons that turn browser edits back into prompts for Claude.
>
> Inspired by [@trq212's "Unreasonable Effectiveness of HTML"](https://x.com/trq212/status/2052809885763747935).

**Live design system:** https://twidtwid.github.io/render-as-html/

---

## Why this exists

This repo is an implementation of [@trq212's HTML-artifact philosophy](https://x.com/trq212/status/2052809885763747935), not my attempt to rebrand it. The claim I am borrowing is: HTML can be the file you keep, not an export, preview, or PDF-like rendering of another canonical document. The browser artifact becomes the working surface and the source of truth.

Thariq's key move is that HTML lets the artifact control layout, styling, state, interaction, and round-trip edits directly. Use the browser for the parts where it is clearly better: live filters, sortable headers, SVG charts, cross-highlighting, drag-and-drop, sliders, checkboxes, and copy-as-prompt buttons. You mutate state in the browser, copy a precise instruction, paste it into Claude Code, update the `.html` file, and keep going.

My contribution here is the opinionated design system and page-shape contracts around that idea. The goal is not to make a prettier document. The goal is to make a local, inspectable, editable HTML artifact that can carry enough structure and interaction to stay useful after the first read.

## Scope

`render-as-html` is a design system and Claude Code skill for writing and updating standalone HTML artifacts. It does not fetch URLs, parse arbitrary exports, crawl repos, or provide a standalone CLI.

## What's in here

- `SKILL.md` — read this first. Page shapes, design system, copy-as-prompt, the "would this die outside HTML?" bar.
- `index.html` — the design system as a single file. Live link above.
- `LICENSE` — MIT.

## Page shapes

Pick the shape from content signals before designing. Eight shapes, each with a contract (layout, required primitives, density, what to avoid):

| Shape | For | Distinct because |
|---|---|---|
| `dashboard` | Network scans, ops data, device explorers | Multi-column, filter bar, dense tables, charts |
| `document` | Plans, specs, briefings, essays | Single column, sticky TOC, per-section copy |
| `timeline` | Diaries, logs, retros, project histories | Vertical spine + date markers + event cards |
| `runbook` | DR, deploy guides, machine rebuilds | Sticky progress bar, per-step checkboxes, code-block copy buttons |
| `comparison` | "X vs Y vs Z" decision matrices | Items as **columns**, criteria as **rows**, weight sliders |
| <code>network&#8209;map</code> | People graphs, brain backlinks, dependencies | Big SVG canvas, click-to-focus, edge highlights |
| <code>triage&#8209;board</code> | GTD reorg, inbox triage | Drag cards between Now/Next/Later/Cut columns |
| `developer` | PR writeups, code review | Annotated diffs, severity findings, file nav |

## The bar

Ask what would disappear if this were flattened into a static text document. If only the SVG diagram disappears, it is styled prose, not a real HTML artifact. Try again. Aim for at least three HTML-native features: live filter, click-to-cross-highlight, inline charts, toggles, copy-as-prompt, drag-and-drop, you get the idea.

## Install (Claude Code)

```bash
git clone https://github.com/twidtwid/render-as-html ~/.claude/skills/render-as-html
```

Restart Claude Code. Then say `make an HTML artifact for this`, `turn this into an interactive HTML file`, `update this HTML artifact`, or `/render-as-html`.

Output lands at `~/Reports/<YYYY-MM-DD>-<slug>.html` by default and opens in your browser. That `.html` file is the artifact to edit, share, revisit, and improve.

To update later:

```bash
git -C ~/.claude/skills/render-as-html pull
```

## Install (Codex)

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
git clone https://github.com/twidtwid/render-as-html "${CODEX_HOME:-$HOME/.codex}/skills/render-as-html"
```

Restart Codex so it loads the skill.

## Sharing the output

The skill emits a vanilla `.html` file. Serve it however you want — locally, Tailscale Serve, Tailscale Funnel, GitHub Pages, S3, `python3 -m http.server`, whatever. By default, generated artifacts should be self-contained and make no external network requests.

Treat generated HTML as sensitive. It can embed private report text, file paths, internal hostnames, local IPs, account names, or other details that were included while building the artifact. `SKILL.md` sketches a private-by-default, publish-on-explicit-trigger pattern if you want one.

## Credits

- HTML-artifact framing and copy-as-prompt pattern: [@trq212](https://x.com/trq212), ["The Unreasonable Effectiveness of HTML"](https://x.com/trq212/status/2052809885763747935)
- Content-matched-shapes idea: [clockless-org/html-anything](https://github.com/clockless-org/html-anything)

## License

MIT
