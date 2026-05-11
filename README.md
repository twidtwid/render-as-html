# render-as-html

> A Claude Code skill. Renders markdown as actual HTML — filters, drag-and-drop, and a button that reads your edits back as a prompt for Claude.
>
> Inspired by [@trq212's "Unreasonable Effectiveness of HTML"](https://x.com/trq212/status/2052809885763747935).

**Live design system:** https://twidtwid.github.io/render-as-html/

---

## Why this exists

Markdown won when humans were hand-editing files. We're mostly not anymore. We ask Claude to edit them. Once you make that switch, markdown's main job (being easy for humans to type) goes away. It's just the format you and Claude both happen to speak.

HTML can carry information markdown literally cannot. Tables. Color as data. SVG. Code highlighting. Live filters. Drag-and-drop. Sortable headers. The killer move is a button that takes whatever you mutated in the browser (a slider position, a checkbox state, a column re-order) and writes a paste-able instruction. You paste it into Claude Code, the markdown gets updated, you re-render. The HTML stops being a thing you read and becomes a thing you use.

## What's in here

- `SKILL.md` — read this first. Page shapes, design system, copy-as-prompt, the "would this die in markdown?" bar.
- `index.html` — the design system as a single file. Live link above.
- `LICENSE` — MIT.

## Page shapes

Pick the shape from content signals before designing. Eight shapes, each with a contract (layout, required primitives, density, what to avoid):

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

Convert the artifact back to markdown. What disappears? If only the SVG diagram, it's styled markdown, not a real HTML artifact. Try again. Aim for at least three things that physically cannot exist in MD: live filter, click-to-cross-highlight, inline charts, toggles, copy-as-prompt, drag-and-drop, you get the idea.

## Install (Claude Code)

```bash
git clone https://github.com/twidtwid/render-as-html ~/.claude/skills/render-as-html
```

Restart Claude Code. Then say `render <file>.md as html` or `make me a pretty version of <file>` or `/render-as-html`.

Output lands at `~/Reports/<YYYY-MM-DD>-<slug>.html` by default and opens in your browser. Markdown stays canonical. The HTML is a rendering, like a PDF.

## Sharing the output

The skill emits a vanilla `.html` file. Serve it however you want — locally, Tailscale Serve, Tailscale Funnel, GitHub Pages, S3, `python3 -m http.server`, whatever. SKILL.md sketches a private-by-default, publish-on-explicit-trigger pattern if you want one.

## Credits

- Concept and copy-as-prompt pattern: [@trq212](https://x.com/trq212), ["The Unreasonable Effectiveness of HTML"](https://x.com/trq212/status/2052809885763747935)
- Content-matched-shapes idea: [clockless-org/html-anything](https://github.com/clockless-org/html-anything)

## License

MIT
