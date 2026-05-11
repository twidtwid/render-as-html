# render-as-html

> A Claude Code skill that turns markdown into dense, Apple-style HTML reports
> with real interactivity — filters, drag-and-drop, copy-as-prompt round-trips.
>
> Inspired by [@trq212's "Unreasonable Effectiveness of HTML"](https://x.com/trq212/status/2052809885763747935).

**Live design system:** https://twidtwid.github.io/render-as-html/

---

## Why this exists

Markdown's main historical benefit was that humans could hand-edit it. That benefit
has collapsed: most of us aren't hand-editing files anymore — we're prompting
Claude Code to edit them for us. Once that flips, markdown stops being the right
medium for anything we actually want to *read*. It's just the source format.

HTML carries information markdown can't: real tables, color, SVG, code highlighting,
sliders, draggable cards, side-by-side diffs, copy-as-prompt buttons. The medium
becomes an *instrument* — not a long scroll you skim, but a thing you can poke at,
filter, drag, and push state back through.

The killer pattern from Thariq's post: a button that takes whatever state you've
mutated in the browser and emits a paste-able prompt for Claude Code. The artifact
becomes an editing surface that round-trips back to the canonical source.

This skill is one opinionated take on that. Different aesthetic from
[clockless-org/html-anything](https://github.com/clockless-org/html-anything) (the
other public project in this space) — denser, more opinionated about visuals, fewer
named styles. Same content-matched-page-shapes framing.

## What's in here

- **`SKILL.md`** — the actual skill. Read it. Page shapes, design system, the
  copy-as-prompt pattern, the "would this die in markdown?" bar.
- **`index.html`** — the design system. Open it in a browser (or visit the live
  link above). Color tokens, typography, every primitive shown live, an interactive
  copy-as-prompt slider demo, and shape-card previews for all 8 shapes.
- **`LICENSE`** — MIT.

## Page shapes

Pick the shape from content signals before designing. Eight shapes, each with a
contract (layout, required primitives, density, what to avoid):

| Shape | For | Distinct because |
|---|---|---|
| `dashboard` | Network scans, ops data, device explorers | Multi-column, filter bar, dense tables, charts |
| `document` | Plans, specs, briefings, essays | Single column, sticky TOC, per-section copy-as-MD |
| `timeline` | Diaries, logs, retros, project histories | Vertical spine + date markers + event cards |
| `runbook` | DR, deploy guides, machine rebuilds | Sticky progress bar, per-step checkboxes, code-block copy buttons |
| `comparison` | "X vs Y vs Z" decision matrices | Items as **columns**, criteria as **rows**, weight sliders |
| `network-map` | People graphs, brain backlinks, dependencies | Big SVG canvas, click-to-focus, edge highlights |
| `triage-board` | GTD reorg, inbox triage | Drag cards between Now/Next/Later/Cut columns |
| `developer` | PR writeups, code review | Annotated diffs, severity findings, file nav |

## The bar

If you converted the artifact back to markdown, what would be impossible to preserve?
If the only answer is "the SVG diagram," it's styled markdown — not a real HTML
artifact. Aim for **at least 3 features that physically cannot exist in MD**: live
filter, click-to-cross-highlight, inline charts, toggle controls, copy-as-prompt,
drag-and-drop, etc.

## Install (Claude Code)

```bash
git clone https://github.com/twidtwid/render-as-html ~/.claude/skills/render-as-html
```

Restart Claude Code. Then say `render <file>.md as html` or `make me a pretty
version of <file>` or `/render-as-html`.

The skill emits a single self-contained HTML file at
`~/Reports/<YYYY-MM-DD>-<slug>.html` by default and opens it in your browser.
The MD source stays the canonical version; the HTML is a rendering, like a PDF.

## Sharing the output

The skill emits a vanilla `.html` file. Serve it however you like:

- Open locally (`open <file>.html`)
- Tailscale Serve for tailnet-only viewing
- Tailscale Funnel / GitHub Pages / Cloudflare Pages / S3 for public sharing
- `python3 -m http.server` for ad-hoc LAN sharing

If you want a publish-on-explicit-trigger pattern (private by default, public only
when the user says "make this public" or "publish this"), the SKILL.md has a
sketch of how to wire it up.

## Credits

- Concept and copy-as-prompt pattern: [@trq212](https://x.com/trq212), ["The Unreasonable Effectiveness of HTML"](https://x.com/trq212/status/2052809885763747935)
- Content-matched-shapes framework: [clockless-org/html-anything](https://github.com/clockless-org/html-anything)
- Built by [@twidtwid](https://github.com/twidtwid) with Claude Code

## License

MIT
