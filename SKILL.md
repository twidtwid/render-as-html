---
name: render-as-html
description: Create or update a designed, self-contained HTML artifact as the source of truth. Use when the user says "make an HTML artifact", "render this as html", "make me a pretty version", "I want to read this carefully", "make it interactive/readable", "update this HTML", or "/render-as-html". Output is an editable HTML file, not a conversion preview of another canonical document.
---

# render-as-html

Create designed HTML artifacts that are the files of record. The HTML is not an export layer over another canonical document; it is the thing the user reads, edits, shares, and revisits.

## When to invoke

- User says "render this as html", "make me a pretty version", "render <file>", "/render-as-html"
- User wants to actually read a long report carefully, share with a non-CLI human, or hand off to a colleague
- After producing a long plan/spec/report when the user says "I want to read it"

## Artifact forms

| Input | Handling |
|---|---|
| Existing `.html` artifact | Read it and update the HTML file directly |
| New artifact brief in conversation | Write a new `.html` artifact |
| Supporting local files | Read only what is needed as context, then write the HTML artifact |
| URL | Out of scope — explain that this skill writes local HTML artifacts and does not fetch URLs |

If multiple inputs possible, ask which.

## Output

- Default path: `~/Reports/<YYYY-MM-DD>-<slug>.html`. Configurable.
- Slug: kebab-case from the artifact title.
- Auto-`open` the file at the end when the environment allows it. The browser is where this thing lives.
- Footer shows the artifact path and generated/updated timestamp.
- Generated artifacts should be self-contained and make no external network requests by default.
- If metadata mentions supporting context, label it as context/provenance. Do not present another file as canonical.
- Any copy-as-prompt action must target the current `.html` artifact path, not a notes file, source file, or parallel document.

### Sharing (optional)

The skill emits a self-contained `.html` file. Serve it however you want: locally, `python3 -m http.server`, Tailscale Serve, Tailscale Funnel, GitHub Pages, S3.

A common pattern is two tiers: a `private/` subdir for tailnet-only viewing and a `public/` subdir explicitly synced to a public host only when the user uses a trigger phrase like "publish this" or "make it public".

### Sensitivity check (when publishing publicly)

Before pushing an artifact to public hosting, scan the rendered HTML for:
- Credential strings (`password`, `token`, `secret`, `key`, base64-like blobs)
- Private LAN IPs (192.168.*, 10.*, 172.16-31.*) — usually OK in moderation but flag clusters
- MAC addresses
- File paths starting with `/Users/`, `/home/`, `~/`
- Internal hostnames (`.local`, `.tailXXXX.ts.net`)
- Personal info (phone numbers, addresses, account numbers)
- External asset URLs that would leak document opens or private context to a third party

If anything matches, list it to the user before publishing. They decide what to redact.

## The bar (read this every time)

**Flatten it to static text. What disappears?**

If only the SVG diagram disappears, it's styled prose, not an HTML artifact. Try again.

A real HTML artifact has 3+ HTML-native features:

- Live filter / search input that hides rows as you type
- Clickable elements that highlight related content elsewhere on the page
- Inline SVG charts (donut, bar, sparkline) generated from data
- Spatial layouts (floor plans, zone maps, topology with positional meaning)
- Color swatches showing actual colors when colors are part of the content
- Toggle controls (show/hide columns, dark/light, units)
- Side-by-side visual diffs (old vs new, before vs after)
- Hover-for-detail tooltips on dense data
- Click-to-copy buttons on individual rows / values
- Sortable table headers
- **Copy-as-prompt buttons that round-trip state back to the HTML file** ← the load-bearing one

The HTML file is the *report* and the *instrument*. Build the thing directly.

## The 8 information dimensions HTML can carry

Framing from [Thariq's "Unreasonable Effectiveness of HTML"](https://x.com/trq212/status/2052809885763747935) — every artifact should leverage ≥4:

| Dimension | What it means |
|---|---|
| **Tables** | Real rows & columns |
| **Design** | Color, type, spacing as information |
| **Illustrations** | Inline SVG diagrams |
| **Code** | Highlighted snippets with local CSS classes; no CDN by default |
| **Interaction** | Sliders, toggles, JS-driven UI |
| **Workflows** | Boxes / arrows / flow / sequence / state |
| **Spatial** | Canvas + coordinates — actual positional meaning |
| **Images** | Embedded figures via data URI or local relative assets |

**Self-check before saving:** which 4+ dimensions did I use? If I can only name 2, the artifact is under-leveraging the medium.

## Copy-as-prompt

Tune values in the browser, hit a button, get a paste-able prompt for Claude Code that applies those changes back to the `.html` artifact. The artifact becomes an editing surface instead of a viewer.

**Examples:**
- Action-items panel → toggle items, click "copy as prompt" → returns `"In <artifact.html>, mark these items resolved: …"`
- Design tuner → sliders for accent color, font-size → `"In <artifact.html>, update --accent to hsl(…)"`
- Plan editor → drag-reorder workstreams → `"In <artifact.html>, re-prioritize the plan to this order: 1) X, 2) Y, 3) Z"`
- Triage editor → bucket items into Now/Next/Later/Cut → `"In <artifact.html>, re-bucket these items: Now=[…] …"`

**Implementation pattern:**
```html
<textarea id="prompt-output" readonly></textarea>
<button class="copy-prompt-btn" onclick="copyPrompt()">copy as prompt</button>
<script>
function copyPrompt() {
  const changes = collectChanges();   // read mutated state
  const prompt = `In ${ARTIFACT_PATH}, apply these changes:\n${formatAsInstructions(changes)}`;
  const out = document.querySelector('#prompt-output');
  out.value = prompt;
  navigator.clipboard.writeText(prompt).catch(() => {
    out.focus();
    out.select(); // visible fallback when clipboard permission is blocked
  });
}
</script>
```

The prompt should:
- **Name the HTML artifact file** (so Claude knows what to edit)
- Be **specific and actionable** — not "the user changed some things" but "set X to Y"
- Be **minimal** — only the deltas, not the full HTML restated
- Read naturally when pasted as a user message
- Have a **visible fallback** when clipboard access is blocked

Cost: ~20 lines of JS. The artifact gains a real edit loop.

## Page shapes (pick before designing)

Different content wants different bones. Pick the shape first from content signals, then design inside it. The content-matched-shapes idea comes from [`clockless-org/html-anything`](https://github.com/clockless-org/html-anything); the visual treatment here is mine.

### Shape selection

| Shape | Pick when the artifact is… |
|---|---|
| **`dashboard`** | Network scans, system reports, device lists, ops data — anything tabular with categories that benefit from filtering |
| **`document`** | Plans, specs, briefings, essays, brainstorms, meeting notes — prose-heavy where you'd read paragraph-to-paragraph |
| **`timeline`** | Dated logs, diaries, retrospectives, project histories, trip journals |
| **`runbook`** | Disaster recovery, deploy guides, machine rebuilds — sequential procedure being *executed* not read |
| **`comparison`** | "X vs Y vs Z" decision matrices, model comparisons, vendor pickers |
| **`network-map`** | People/relationships, brain backlinks, dependencies — connections matter |
| **`triage-board`** | Bucketing items into 3-5 columns (Now/Next/Later/Cut), inbox triage, GTD reorg |
| **`developer`** | PR writeups, code review, "explain this code" — annotated diff with severity findings |

**Auto-pick rules:**
- Source has >5 tables of similar shape → `dashboard`
- Source is mostly headings + paragraphs → `document`
- Source has dates as primary structure → `timeline`
- Source is procedural (ordered steps with commands) → `runbook`
- Ambiguous? Ask.

Explicit user override always wins.

### Shape contracts

#### `dashboard`
- **Layout:** max-width 1280px, 1.4fr/1fr two-column dashboard grid, sticky controls row at top
- **First viewport:** hero with stats tiles + search + chip filters + TL;DR
- **Required primitives:** search input, toggleable category chips, dense table with mono first column, stats tiles, donut chart inline SVG, status pills, one inline-SVG topology/diagram
- **Density:** 14px body, 4-8px table padding, packed
- **HTML-native ≥3:** live filter, clickable cross-highlights, inline charts, toggles, sortable headers, copy buttons
- **Avoid:** narrow column, generous whitespace, single-column scroll, generic h2/p/table layout

#### `document`
- **Layout:** max-width 880px, single column, sticky TOC sidebar on desktop
- **First viewport:** title, byline, TL;DR (required), TOC visible
- **Required primitives:** TL;DR block, sticky TOC sidebar with scroll-spy, footnote pattern, inline dense tables, callouts (note/warn), per-section copy button (hover-revealed on each h2)
- **Density:** 16px body, 1.55 line-height
- **HTML-native ≥3:** TOC scroll-spy, per-section copy buttons, collapsible appendix, click-to-expand footnotes
- **Avoid:** dashboard-style multi-column grid, 60+ char line length, corporate "executive summary card" headers

#### `timeline`
- **Layout:** vertical spine on the left (~140px column for date markers + dots), event cards on the right (~720px). Max-width ~1000px.
- **First viewport:** title + date-range scrubber + search input + most recent N events
- **Required primitives:** vertical spine line, date-marker dots on the spine, event cards (timestamp/title/body/tags), sticky year/month group headers, jump-to-date picker, per-event copy button
- **Density:** 15px body, dense event cards (8-10px padding), 12px gap between events
- **HTML-native ≥3:** live text search across events with highlight, date-range filter pills, cluster-collapse (month/year → count), tag-chip filter, per-event "copy as quote"
- **Avoid:** decorative-CV-style animations, wall of dates with no spine, event cards too wide (reads as document paragraphs)

#### `runbook`
- **Layout:** sticky header with "Step X of N" + progress bar; max-width 960px single column; step cards stacked vertically
- **First viewport:** title + scope/danger callout + progress bar + step 1 visible
- **Required primitives:** step card with `[number] [checkbox] [title]` + expandable body, code block with per-block copy button (load-bearing), "expected output" collapsible callouts, branch markers ("if X, jump to step Y"), sticky progress bar, "I'm stuck" copy-as-prompt
- **Density:** 15px body, prominent code blocks
- **HTML-native ≥3:** per-code-block copy button, live progress tracking, "stuck" prompt generator, conditional step visibility
- **Avoid:** plain numbered list with code blocks, making it look like `document`-shape (this is an *instrument*, not just reading material)

#### `comparison`
- **Layout:** items as **columns** (the axis flip vs dashboard), criteria as **rows**. Sticky header row with item names. Max-width 1280px.
- **First viewport:** title + TL;DR + matrix with weight column on left, aggregate-winner row on bottom
- **Required primitives:** column-header item cards, criterion rows with per-item values, winner highlighting per row (background tint + ★), weight inputs per criterion, aggregate-score footer that live-recomputes, color-coded value scale (red→amber→green) for numerics
- **Density:** 14px body, dense cells (6-10px padding)
- **HTML-native ≥3:** live weight tuning recomputes winners, column sort by aggregate, "must-have" criterion toggle, "copy as recommendation" prompt
- **Avoid:** dashboard-style layout (entities as rows). The axis flip *is* the shape.

#### `network-map`
- **Layout:** big graph canvas center (60-70% width), entity-detail right rail (~280px), filter chips top
- **First viewport:** the graph fitted to viewport, filter chips above, "click for details" hint
- **Required primitives:** SVG canvas with positioned nodes (hand-positioned or small vanilla force-directed sim), edges, node sizing by importance, cluster color-coding, right-rail entity card updating on click, top filter chips, search to focus, click-node-to-focus (dim others, highlight direct edges)
- **HTML-native ≥3:** click-to-focus, hover-edge-highlight, search-to-focus, cluster toggle, shortest-path finder
- **Avoid:** rendering as a table of names with "connections: X, Y, Z" — that's a dashboard. The graph IS the primary view.

#### `triage-board`
- **Layout:** title + brief instruction + 3-5 column boards horizontally (e.g. Now / Next / Later / Cut). Cards inside columns. Sticky export bar at bottom.
- **Required primitives:** column headers with live count, draggable cards (HTML5 DnD, vanilla — no React-DnD), per-card one-line rationale text input, pre-sorted suggested distribution at load, sticky copy/export + "copy as prompt" bar, undo
- **Density:** 14px body. Cards 80-120px tall. Columns 240-320px wide.
- **HTML-native ≥3:** drag-between-columns, live column counts, copy-as-prompt exporting final assignments, undo, filter/search across all cards
- **Avoid:** vertical lists with status badges (that's a dashboard). The horizontal layout WITH drag IS the shape.

#### `developer`
- **Layout:** title + PR/commit metadata strip + risk callouts at top + annotated diff body + summary footer. Max-width 1280px. Optional left rail with "files changed" nav.
- **First viewport:** PR summary, severity-coded findings count (critical / warning / nit), top risk callout
- **Required primitives:** syntax-highlighted code with local CSS classes, per-file diffs with `+`/`−` line gutters in green/red soft tints, inline margin annotations on specific lines, severity-coded finding cards, files-changed navigator, copy-link-to-finding buttons
- **Density:** 14px body, 13px code
- **HTML-native ≥3:** syntax-highlighted code without relying on an external renderer, severity-color findings, jump-to-file, click-to-copy individual findings, side-by-side before/after
- **Avoid:** generic document with code blocks (that's `document`). The annotated diff + severity findings IS the shape.

## Sub-patterns (within shapes, not standalone shapes)

Interaction patterns that show up across multiple shapes — use where they fit:

- **Exploration grid:** generate N variants of a design/option and lay them out in a CSS grid for side-by-side comparison. *"Generate 6 distinctly different approaches and lay them out as a grid so I can compare them side by side."*
- **Config editor:** form-based editing of structured config with grouped sections, dependency warnings, "copy diff" button
- **Prompt tuner:** side-by-side editor with the prompt on the left (variable slots highlighted) and 2-3 sample inputs on the right rendering the filled template live + token counter + copy button
- **Annotation overlay:** marks on top of a document/diff/transcript with copy-out-the-annotations button

## Design system

System typography and Apple-level color discipline, Linear / Stripe density. Beautiful and information-rich. Wide screens exist; narrow centered columns waste them. Think `apple.com/mac` or Stripe docs or Linear's app, not iA Writer.

Slightly warm and non-corporate, but keep public artifacts professional by default.

`index.html` is the canonical component gallery for maintaining the design system, but do **not** read the whole gallery during normal renders. For ordinary artifact generation, use the compact shape contracts and tokens in this skill. Open `index.html` only when the user asks to inspect the design system, when changing the design system, or when a visual/detail decision is genuinely blocked.

### Performance defaults

- Pick the shape quickly. If the artifact is procedural, choose `runbook` without a long comparison pass.
- Reuse the shape contract instead of inventing a new CSS system for each artifact.
- Keep normal artifacts to the primitives the shape needs. A runbook usually needs progress, checkboxes, copy-code buttons, collapsible troubleshooting, and stuck-copy-as-prompt. It does not need swatches, charts, topology, tables, and every shared component unless the artifact calls for them.
- For private/internal artifacts where speed matters more than portability, ask before using a shared local CSS/JS runtime instead of inlining all boilerplate. Self-contained remains the default for public or shareable artifacts.

### Layout principles

- **Max-width 1280px** on dashboards, 880px on documents, fluid below
- **Multi-column grids** for parallel content, NOT sequential h2 sections
- **Sticky top nav** with section anchors for docs >5 sections
- **Filter bar** when content is filterable — vanilla JS, no framework
- **Mobile is a hard requirement, not an afterthought.** Test by resizing browser to ~375px before saving. Cards stack to single column under ~700px, sticky nav collapses gracefully, touch targets ≥32px, horizontal scroll forbidden on body (tables in scroll containers OK), font sizes adjust down 1-2px.

### Density

- Line-height **1.5** body (dashboard) / **1.55** (document), **1.2** headlines
- Table cell padding **8px 10px** (was 12px 16px — too generous)
- Section gap 2.5rem between h2 sections
- Don't be afraid of 0.8rem text for metadata — big text is for hierarchy, not everything

### Typography

- One display, one body, one mono. **No more.**
- Body: `-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif`
- Display: same system stack, heavier weight (700/800), tight letter-spacing (`-0.022em`)
- Mono: `'JetBrains Mono', 'SF Mono', ui-monospace, monospace`
- Body 15-16px desktop, 14-15px mobile
- `font-variant-numeric: tabular-nums` on tables

### Color

- Light mode: bg `#fafaf7` (warm white), text `#1a1a1a`, muted `#6b6b6b`, border `#e8e5dd`
- Dark mode (via `prefers-color-scheme`): bg `#1a1a1a`, text `#f0eee8`, muted `#a8a6a0`, border `#2e2e2a`
- Single accent: warm coral `#c74438` / `#ff7066`. No corporate blue.
- Semantic text colors: `ok=#2f7d44`, `warn=#9b641d`, `note=#2f6fb3`
- High contrast — no gray-on-gray. Text-use colors should meet WCAG AA.

### Interactivity

**Every filter needs a visible clear path.** If clicking activates a filter, clicking again has to deactivate it (toggle), and a visible "× clear" affordance has to appear while the filter is active. Never rely on double-click, escape, or "click outside" to reset. Those gestures are undiscoverable.

**Use real controls for real actions.** When something needs to be toggleable, editable, pickable, or clickable, use a control that looks like one: `<input type="checkbox">`, `<input type="range">`, `<select>`, `<button>`. Don't invent gestures on decorative elements ("click this pill", "shift-click this badge", "double-tap this card"). Pills and badges and stat tiles read as static information; making them interactive is invisible and inscrutable. If a pill needs editing, put a real checkbox or button next to it. The pill stays read-only.

**Every copy button needs a fallback.** `navigator.clipboard.writeText()` can fail in local files, hardened browsers, iframes, and permission-restricted contexts. If copy fails, place the exact text in a visible `<textarea>`, focus it, and select it.

### Anti-patterns

- Multiple fonts beyond the three above
- Drop shadows on everything; gradients for their own sake
- Emoji explosion (1-3 across the whole doc, not one per heading)
- Generic AI-report decoration: redundant boxes, ornamental "Key Insights" headers
- Centered body text outside of titles
- Tailwind utility-class soup (hand-written CSS reads better)
- Narrow centered columns on data-heavy content
- Excessive whitespace as a stand-in for design taste
- Running a generic document converter and calling it done
- Pulling in a JS framework. Single file, vanilla JS.
- External fonts, analytics, or CDN assets in private artifacts unless the user explicitly approves them.
- Copy/export buttons that imply another canonical format. Prefer "copy section", "copy recommendation", "copy board state", or "copy as prompt"; avoid "copy as markdown" unless the user explicitly wants a one-off export.

## Rendering process

1. **Read the request and any existing HTML artifact**
2. **Pick the page shape** from content signals (or ask if ambiguous)
3. **Plan the instrument:**
   - What's the central interaction? (filter? compare? execute? explore?)
   - What features require HTML? Pick at least 3 — write them down before writing HTML.
   - Where does a diagram, chart, or spatial layout add information?
   - Which of the 8 dimensions am I using? (Aim for ≥4)
4. **Write the HTML** — single self-contained file, all CSS inline, all JS (vanilla, ~100-200 lines) inline, no external fonts or CDN assets by default
5. **Validate against the bar:** name the HTML-native features. If <3, redesign before saving.
6. **Write to `~/Reports/<YYYY-MM-DD>-<slug>.html`**
7. **`open` the file** so it pops in browser when the environment allows it
8. **Report back:** path, size, list of HTML-native features

## Credits

- HTML-artifact framing and copy-as-prompt: [@trq212's "Unreasonable Effectiveness of HTML"](https://x.com/trq212/status/2052809885763747935)
- Content-matched-shapes idea: [`clockless-org/html-anything`](https://github.com/clockless-org/html-anything)
