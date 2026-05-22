---
name: render-as-html
version: 2.1.1
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
- **Social card (always, in `<head>`)** so a hosted artifact unfurls as a titled preview:
  - **Required tags:** `<meta name="description">`, `og:title`, `og:description`, `og:type`, `og:site_name`, `twitter:card`.
  - **Sourcing:** `og:title` = the artifact `<title>`. `og:description` = one plain sentence (≤155 chars) describing *what the artifact is*, derived from the subtitle/thesis — not a production count, not "an HTML artifact about X". `og:type` = `article` for content, `website` for an index/gallery. `twitter:card` = `summary`.
  - **Omit `og:url`** (final URL unknown at generation time; scrapers fall back to the request URL).
  - **`og:image` is conditional.** Omit by default — it would need a hosted image file and breaks self-containment for `file://` artifacts. BUT when the artifact is shipped to a portal that hosts a sibling thumbnail (e.g. an `og-card.png` next to the entry), emit `og:image` + `twitter:image` as a relative path and upgrade `twitter:card` to `summary_large_image`. Generate the thumbnail from a 1200×630 HTML+inline-SVG template using the artifact's own design tokens, rendered via `chrome --headless --window-size=1200,630 --screenshot=…`.
  - Inert on `file://`, ~6 lines, costs nothing — unconditional, not publish-gated.
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

**Content discipline:**

- **Content vs. metadata.** Surface the thing, not the fact that the thing exists. Counts of the *subject* orient the reader and are good ("23 restaurants on file, 2021–2026"; "4 open ports"). Counts of the *artifact's own production* are slop ("Found 6 claims", "12 sections", transcript word count as a hero stat). Live UI state ("9 starred · unsaved changes") is feedback, not a hero stat — fine. Stat tiles in `dashboard`/`comparison` are content only when the metric *is* the subject; never when they count the artifact.
- **Headlines that argue, not category labels.** Section and item titles take a position ("Why the market may stay concentrated") not a noun phrase ("Market structure"). If a 4–10 word position-establishing headline can't be written, the argument isn't understood yet.
- **Bodies add information beyond their headline.** A body that paraphrases its headline in more words is visibly lazy. The body delivers the mechanism/evidence/consequence the headline promised.

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
| **`editorial`** | Argument-driven long-form where the reader absorbs a sustained position — deep essays, research synthesis, analytical memos, argument-driven briefings |

**Auto-pick rules:**
- Source has >5 tables of similar shape → `dashboard`
- Source is mostly headings + paragraphs navigated as reference (spec/plan/notes) → `document`
- Source has dates as primary structure → `timeline`
- Source is procedural (ordered steps with commands) → `runbook`
- Source is a sustained argument read front-to-back with named entities worth a reference rail → `editorial`
- Ambiguous? Ask.

Explicit user override always wins.

### Shape contracts

#### `dashboard`
- **Register:** Instrument (sans display + sans body; see Density).
- **Layout:** max-width 1280px, 1.4fr/1fr two-column dashboard grid, sticky controls row at top
- **First viewport:** hero with stats tiles + search + chip filters + TL;DR
- **Required primitives:** search input, toggleable category chips, dense table with mono first column, stats tiles, donut chart inline SVG, status pills, one inline-SVG topology/diagram
- **Density:** instrument defaults; 4-8px table padding acceptable for the compact variant.
- **HTML-native ≥3:** live filter, clickable cross-highlights, inline charts, toggles, sortable headers, copy buttons
- **Avoid:** narrow column, generous whitespace, single-column scroll, generic h2/p/table layout

#### `document`
- **Register:** Reading (serif display + serif body, cream paper, terracotta accent; see Density).
- **Layout:** max-width 880px, single column, sticky TOC sidebar on desktop
- **First viewport:** title, byline, TL;DR (required), TOC visible
- **Required primitives:** TL;DR block, sticky TOC sidebar with scroll-spy, footnote pattern, inline dense tables, callouts (note/warn), per-section copy button (hover-revealed on each h2)
- **Density:** reading defaults.
- **HTML-native ≥3:** TOC scroll-spy, per-section copy buttons, collapsible appendix, click-to-expand footnotes
- **Avoid:** dashboard-style multi-column grid, 60+ char line length, corporate "executive summary card" headers

#### `editorial`
- **Register:** Reading (serif display + serif body, cream paper, terracotta accent; see Density).
- **Layout:** studio max-width ~1320px. Three zones, narrow–wide–narrow so the reading column dominates:
  - Left rail ~18rem, sticky: kicker + title hero + "context/about" card.
  - Center: prose, measure capped at `50rem` (~75ch); stays anchored left-of-center on wide screens.
  - Right inspector ~18rem: entity list grouped by category with canonical links, then a "read next" link list.
  - Collapse: inspector drops below center under ~1180px; single column under ~820px.
  - Both rails follow the **sticky-rail, footer, and scrollbox invariants** in §Layout principles. Skip them and the rails overlap the prose at narrow widths and paint over the footer at scroll-bottom.
- **First viewport:** kicker + title + italic thesis/bottom-line + start of body. No stat tiles.
- **Required primitives:**
  - Italic serif thesis/bottom-line pull-quote, left-aligned (never centered). No left-handle bar.
  - Stacked numbered takeaways — single column with mono numerals, never a tile grid.
  - Claim/section cards: arguing headline + 1–3 sentence mechanism body + small `Evidence:` line.
  - **Evidence lines hyperlink their sources.** Every source token in a claim's `Evidence:` line (and every inline entity mention with a primary source) must be an `<a href>`. When the upstream data is structured (e.g. a research engine's JSON with a `url` per item), the link target MUST come from that data — never synthesized, inferred, or left as a bare publication name. If an item genuinely has no URL, render plain text and say why ("primary source not in feed"). Hard self-check before saving: every Evidence `href` is a substring of the source data you were given, and every claim section has ≥1 evidence link.
  - Right-rail entity inspector grouped by category (people, companies, orgs, concepts, …), each row a colored category dot + name (canonical link if present, `↗` for external) + one-line note. Follows the scrollbox invariant in §Layout principles.
  - "Read next" list of source links.
  - Per-section copy-as-prompt button (hover-revealed on each section heading), targeting the current `.html` artifact path.
- **HTML-native ≥3:** in-text `<mark>` search **with prev/next nav**; click-entity-to-open / cross-highlight; per-section copy-as-prompt; section scroll-spy if a section rail is present.
- **Search nav (load-bearing — a match counter without stepping is a footgun):** any search that reports a match count MUST let the reader step through matches. Required: `↑`/`↓` buttons by the input; counter shows "N of M" (current position, not just total); the current match gets a distinct style (e.g. `mark.current` filled with `--accent`) so it stands out from the others; Enter advances, Shift+Enter goes back; buttons auto-disable at 0–1 matches. "3 matches" with no way to reach matches 2 and 3 is broken UX.
- **Narrative-data sections use cards, not wide tables.** When an editorial section has 3–8 items each carrying several prose fields (e.g. artifact / recipient / outcome), render them as stacked cards — mono header (number + key + tag pill) → prose body → outcome line — not a dense ops table. The editorial stage caps prose at 50rem; a 6-column table of prose data clips on wide screens with the inspector rail open, and `overflow-x: auto` inside an editorial column is a cop-out (horizontal scroll is undiscoverable). The dense ops table primitive belongs in `dashboard`/`comparison`/`developer` shapes where the stage isn't capped.
- **Cross-link scroll semantics (load-bearing — get the direction wrong and clicking a link hurls the reader away from what they clicked):**
  - *Prose mention → entity card:* highlight both, then reveal the card by scrolling **the inspector's own scrollbox only** — `card.scrollIntoView({ block: 'nearest' })` (with the inspector as the nearest scroll container) or set `inspector.scrollTop` directly. Never call a scroll that moves the document/prose, and skip the scroll entirely if the card is already within the inspector's visible box. Clicking a prose link must not move the prose.
  - *Entity card → prose mention:* scroll the **document** to the first `<mark>` with `block: 'center'`; make it a no-op if that mention is already in the viewport (no yank).
  - The rule of thumb: a click scrolls *the other panel*, never the panel you clicked in.
- **External links** open `target="_blank" rel="noopener noreferrer"`; internal anchors stay same-window.
- **Avoid:** artifact-counting stat tiles; left-handle accent bars; category-label section titles; identical-tile card grids; prose measure wider than ~75ch; dashboard-style multi-column-of-tiles; **prose `Evidence:` lines that name sources ("per Bloomberg", "X @HPCwire (score 69)") without linking them** — a plain-text Evidence line when the URLs were available in the source data is a hard miss; it makes the artifact strictly worse than a raw source dump, which links everything for free.

#### `timeline`
- **Register:** Reading (serif display + serif body; see Density). Mono small-caps for date/kicker lines.
- **Layout:** vertical spine on the left (~140px column for date markers + dots), event cards on the right (~720px). Max-width ~1000px.
- **First viewport:** title + date-range scrubber + search input + most recent N events
- **Required primitives:** vertical spine line, date-marker dots on the spine, event cards (timestamp/title/body/tags), sticky year/month group headers, jump-to-date picker, per-event copy button
- **Density:** reading defaults; dense event cards (8-10px padding), 12px gap between events.
- **HTML-native ≥3:** live text search across events with highlight, date-range filter pills, cluster-collapse (month/year → count), tag-chip filter, per-event "copy as quote"
- **Avoid:** decorative-CV-style animations, wall of dates with no spine, event cards too wide (reads as document paragraphs)

#### `runbook`
- **Register:** Instrument (sans display + sans body; see Density).
- **Layout:** sticky header with "Step X of N" + progress bar; max-width 960px single column; step cards stacked vertically
- **First viewport:** title + scope/danger callout + progress bar + step 1 visible
- **Required primitives:** step card with `[number] [checkbox] [title]` + expandable body, code block with per-block copy button (load-bearing), "expected output" collapsible callouts, branch markers ("if X, jump to step Y"), sticky progress bar, "I'm stuck" copy-as-prompt
- **Density:** instrument defaults; prominent mono code blocks.
- **HTML-native ≥3:** per-code-block copy button, live progress tracking, "stuck" prompt generator, conditional step visibility
- **Avoid:** plain numbered list with code blocks, making it look like `document`-shape (this is an *instrument*, not just reading material)

#### `comparison`
- **Register:** Instrument (sans display + sans body; see Density).
- **Layout:** items as **columns** (the axis flip vs dashboard), criteria as **rows**. Sticky header row with item names. Max-width 1280px.
- **First viewport:** title + TL;DR + matrix with weight column on left, aggregate-winner row on bottom
- **Required primitives:** column-header item cards, criterion rows with per-item values, winner highlighting per row (background tint + ★), weight inputs per criterion, aggregate-score footer that live-recomputes, color-coded value scale (red→amber→green) for numerics
- **Density:** instrument defaults; dense cells (6-10px padding).
- **HTML-native ≥3:** live weight tuning recomputes winners, column sort by aggregate, "must-have" criterion toggle, "copy as recommendation" prompt
- **Avoid:** dashboard-style layout (entities as rows). The axis flip *is* the shape.

#### `network-map`
- **Register:** Instrument (sans display + sans body; see Density).
- **Layout:** big graph canvas center (60-70% width), entity-detail right rail (~280px), filter chips top
- **First viewport:** the graph fitted to viewport, filter chips above, "click for details" hint
- **Required primitives:** SVG canvas with positioned nodes (hand-positioned or small vanilla force-directed sim), edges, node sizing by importance, cluster color-coding, right-rail entity card updating on click, top filter chips, search to focus, click-node-to-focus (dim others, highlight direct edges)
- **Density:** instrument defaults; packed node labels and edge metadata.
- **HTML-native ≥3:** click-to-focus, hover-edge-highlight, search-to-focus, cluster toggle, shortest-path finder
- **Avoid:** rendering as a table of names with "connections: X, Y, Z" — that's a dashboard. The graph IS the primary view.

#### `triage-board`
- **Register:** Instrument (sans display + sans body; see Density).
- **Layout:** title + brief instruction + 3-5 column boards horizontally (e.g. Now / Next / Later / Cut). Cards inside columns. Sticky export bar at bottom.
- **Required primitives:** column headers with live count, draggable cards (HTML5 DnD, vanilla — no React-DnD), per-card one-line rationale text input, pre-sorted suggested distribution at load, sticky copy/export + "copy as prompt" bar, undo
- **Density:** instrument defaults; cards 80-120px tall, columns 240-320px wide.
- **HTML-native ≥3:** drag-between-columns, live column counts, copy-as-prompt exporting final assignments, undo, filter/search across all cards
- **Avoid:** vertical lists with status badges (that's a dashboard). The horizontal layout WITH drag IS the shape.

#### `developer`
- **Register:** Instrument (sans display + sans body; see Density).
- **Layout:** title + PR/commit metadata strip + risk callouts at top + annotated diff body + summary footer. Max-width 1280px. Optional left rail with "files changed" nav.
- **First viewport:** PR summary, severity-coded findings count (critical / warning / nit), top risk callout
- **Required primitives:** syntax-highlighted code with local CSS classes, per-file diffs with `+`/`−` line gutters in green/red soft tints, inline margin annotations on specific lines, severity-coded finding cards, files-changed navigator, copy-link-to-finding buttons
- **Density:** instrument defaults; mono at 13px for code.
- **HTML-native ≥3:** syntax-highlighted code without relying on an external renderer, severity-color findings, jump-to-file, click-to-copy individual findings, side-by-side before/after
- **Avoid:** generic document with code blocks (that's `document`). The annotated diff + severity findings IS the shape.

## Sub-patterns (within shapes, not standalone shapes)

Interaction patterns that show up across multiple shapes — use where they fit:

- **Exploration grid:** generate N variants of a design/option and lay them out in a CSS grid for side-by-side comparison. *"Generate 6 distinctly different approaches and lay them out as a grid so I can compare them side by side."*
- **Config editor:** form-based editing of structured config with grouped sections, dependency warnings, "copy diff" button
- **Prompt tuner:** side-by-side editor with the prompt on the left (variable slots highlighted) and 2-3 sample inputs on the right rendering the filled template live + token counter + copy button
- **Annotation overlay:** marks on top of a document/diff/transcript with copy-out-the-annotations button
- **Checklist:** an unordered list where each item carries a state control plus an optional freeform note, with a sticky batch-export bar.
  - *Use for:* review collection, decision shortlists, audit/packing lists, "which of these should we do", approval passes, curation with annotations.
  - *vs `runbook`:* runbook checkboxes track execution of an ordered procedure; checklist items are an unordered set being selected/annotated.
  - *vs `triage-board`:* no columns, no drag — one list, per-item state + note + batch export.
  - *Primitives:* item rows (title + mono metadata line + state control (checkbox, star, or small rating) + note `<textarea>`); sticky footer bar (live count + batch copy-as-prompt with visible textarea fallback); per-item state persists in the DOM and is read by the batch exporter.
  - *Round-trip:* batch action emits a prompt naming the current `.html` artifact and the per-item state/notes as explicit instructions — same copy-as-prompt contract described above.
  - *Register:* inherits the host shape's register. Reads well in the Reading register but is layout-agnostic; usable inside `editorial`, `timeline`, or standalone.

## Canonical primitives (charts and tables)

Nine primitives that show up across the page shapes. Same one-truth palette as every shape, with locked interaction contracts so a `dashboard` donut, a `comparison` matrix, and a `developer` diff all feel like one system. The reference implementations live at [`examples/primitives.html`](examples/primitives.html) (one file per primitive under `examples/primitives/`); the gallery itself is also a render-as-html artifact (`document` shape).

These are primitives, not shapes. They compose **inside** a shape's contract; pick the shape first, then reach for the primitives the content calls for.

### Charts

#### Donut — categorical status mix
- **Pick when:** 2–5 mutually-exclusive categories where the proportion is more useful at a glance than the absolute counts.
- **Required:** subject-count in the center (never a category count, never an artifact count); ring track in `--rule-soft` so partial fills don't read as missing data; legend in CSS subgrid so counts and percents align in columns across rows.
- **Interaction:** click a legend row to isolate that segment (others dim); visible `× clear` appears while a filter is active.
- **Avoid:** 6+ slivers (use a stacked bar instead); donut-on-its-own as a hero — pair it with the data beneath.

#### Bar — ranked top-N
- **Pick when:** ≤12 items where order matters and a single magnitude per item is the signal.
- **Required:** name in its own subgrid column to the left of the bar (never on the bar with a text-shadow); ochre marks the current leader, terracotta the rest; bar / name / value / Δ subgrid aligns across rows; secondary dimension (Δ, age, score) gets its own right-edge column.
- **Interaction:** sort dropdown at minimum offers value, alpha, and the secondary dimension; bars re-scale to the new leader when sort changes.
- **Avoid:** text-shadow / outline glow on labels (illegible); per-bar rainbow coloring; bars without a max-width cap.

#### Sparkline — stat-tile cluster
- **Pick when:** 2–4 hero metrics where each metric IS the subject (not an artifact count), current value + recent-trend shape is the one-glance read.
- **Required:** single accent color for the spark line across all tiles; delta carries direction-of-good (ok / accent / muted); latest-point dot is hollow (paper fill, accent stroke) so it reads as a marker, not a glitch; faint area fill (`opacity ~0.08`) is optional weight, not a true area chart.
- **Interaction:** hover the spark drops a vertical guide + value/time tooltip at the nearest data point.
- **Avoid:** 4+ tiles (cross into dashboard territory); stat tiles that count the artifact itself; axis tick marks per data point (tooltip carries precision).

#### Stacked bar — composition over time
- **Pick when:** categories sum to a meaningful whole each period (success/fail buckets, traffic mix, deal stages); 7–30 periods on the x-axis.
- **Required:** y-axis recomputes when categories toggle off; severity-ascending bottom-up stack order; per-column tooltip with the day's breakdown + total; chip legend doubles as the filter (clicking removes that category from the stack).
- **Interaction:** hover any column for the full breakdown tooltip; click chips to remove/add categories.
- **Avoid:** categories that don't sum cleanly (use grouped bars); fixed y-axis when categories can toggle off.

#### Topology — inline service graph
- **Pick when:** connections are the point and node count is ≤30 (≤10 sits comfortably inline; 10–30 still works hand-positioned).
- **Required:** hand-positioned coordinates (force-directed wiggle earns its place at 30+); mono-uppercase node labels; paper-card node fill with a cluster-colored dot (never fill the node with category color — doesn't scale when clusters grow); edges meet rect boundaries (clip via center-offset math); right-rail inspector matching the editorial-shape entity pattern.
- **Interaction:** click a node to focus its neighborhood (dim others, light direct edges, update inspector); search ochre-highlights matches independently of focus; `× clear focus` resets.
- **Avoid:** force-directed simulations on small graphs; edges drawn center-to-center poking through node rects; SVG with no surrounding tile chrome.

### Tables

#### Dense ops table
- **Pick when:** flat list of records keyed by an identifier; ≥6 rows; filtering / sorting is the central interaction. The instrument-register workhorse.
- **Required:** mono first column (the identifier); sans middle (the labels); mono right-aligned numerics with `tabular-nums`; status pills carry outline + colored dot + text (color is never the sole signal); footer reports true row count (not the filtered count).
- **Interaction:** column-header click cycles sort asc → desc → none (always-escapable); pill-filter in toolbar inverts (ink fill, paper text) when active; search across identifier + label fields.
- **Avoid:** color-only status; footers that lie about dataset size when filtered; sorts with no neutral state.

#### Comparison matrix — items as columns
- **Pick when:** "X vs Y vs Z" decision matrix with shared criteria; you want the reader to tune weights and see who wins live; 2–5 items, 3–10 criteria.
- **Required:** items as columns (entities-as-rows would be a dashboard, not this — the axis flip *is* the shape); weight column on the far left with a full-height +/− stepper flanking the input (no native browser spinners); aggregate row normalized to 0–100 (so total-weight changes don't mask relative position); explicit `↑ better` / `↓ better` per-criterion direction; per-row star + ochre tint marks row winner; overall winner in the footer goes terracotta; round-trip `copy as prompt` with visible textarea fallback.
- **Interaction:** step or type any weight 0–5; per-row and overall winners recompute on every change.
- **Avoid:** entities-as-rows layout; tiny native spinner buttons; weights without bounds; copy buttons that imply another canonical format (use `copy as recommendation` / `copy as prompt`, not `copy as markdown`).

#### Annotated diff — code review primitive
- **Pick when:** reviewing code changes, security findings, or any line-anchored critique where adjacency to the source matters more than a side panel.
- **Required:** findings sit IN the diff, anchored to the line they touch; severity carried three ways (strip count at the top + left bar on the finding card + colored badge fill — color is never alone); explicit `L<n> · new` / `L<n> · removed` line labels so reviewers know which side they're commenting on; `+`/`−` gutter chars in their own column AND row background tint (two cues); syntax highlighting via local CSS classes only (no Prism, no CDN, no runtime tokenizer); per-finding `copy as prompt` quoting the line context.
- **Interaction:** click any line number to copy a `file:line` reference (gutter flashes); per-finding copy button round-trips back as a paste-able instruction; `show nits` toggle hides low-priority findings.
- **Avoid:** findings in a sidebar separated from the lines they discuss; color-only severity; runtime syntax highlighters or CDN dependencies.

#### Log stream — chronological event table
- **Pick when:** the data is a tail of timestamped events with a categorical level; newest-first reading is the default; payloads have structure worth expanding.
- **Required:** three live-state cues (pulsing dot + LIVE/PAUSED label + button mode-flip) so state reads without sound and survives a screenshot; ochre flash on new rows (~1.2s fade) for peripheral-glance detection; FATAL fills its pill background, other levels are outline-only (visual weight matches operational weight); counts are against full event set (never the filtered view); expanded payload uses the same syntax-token palette as the diff primitive (keys terracotta, strings ochre, numbers note-blue).
- **Interaction:** multi-select level chips; search across messages; click any row to expand the payload; `⏸ pause tail` freezes scroll and tail state so investigation doesn't lose the spot.
- **Avoid:** live-only state cues (must read when muted or in screenshots); identical pill styling for FATAL vs ERROR; expanding a row that destroys scroll position.

### Cross-cutting rules (primitives only)

- **Subgrid for cross-row column alignment.** Where multiple rows have parallel structure (legend, ranked list, comparison matrix), the outer container is the grid and rows are `display: grid; grid-template-columns: subgrid; grid-column: 1 / -1;` — so columns line up without per-row width hacks.
- **Counts reflect the underlying data, not the filtered view.** Filters hide events; they never lie about how many exist.

(Three more rules apply to every primitive but live elsewhere: one palette per §Color, visible filter clears per §Interactivity, color-is-never-the-only-signal per §Color.)

## Design system

One palette, two registers, determined entirely by shape. The **reading register** (documents, editorials, timelines) uses serif display and body, warm cream paper, and terracotta accent — long-form comfortable, iA-Writer-adjacent in rhythm but wider and more structured. The **instrument register** (dashboards, comparisons, developer tools, runbooks) uses dense sans, tighter metrics, and the same palette — Linear/Stripe in feel. Both are information-rich; neither wastes wide screens on a narrow centered column.

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
- **Mobile is a hard requirement, not an afterthought.** Test by resizing browser to ~375px before saving — and also test the *intermediate* widths (~1100px, ~950px), where multi-zone layouts break worst. Cards stack to single column under ~700px, sticky nav collapses gracefully, touch targets ≥32px, horizontal scroll forbidden on body (tables in scroll containers OK), font sizes adjust down 1-2px.
- **Sticky-rail collapse invariant (any multi-zone shape — editorial, dashboard, document, network-map):** a `position: sticky` rail with a viewport-tall `height` is only safe while it owns a grid column. A sticky element keeps its own scroll box and paint layer even after the grid collapses, so if it stays sticky once its column is gone it renders *on top of* the prose. **Default to mobile-first:** rail is plain in-flow at base; attach `position: sticky` + the grid column together inside the wide `@media (min-width: …)` rule, so the failure state is unreachable by construction. Only if you went desktop-first must you reset to `position: static; height: auto` at every breakpoint the column is lost. A sticky *top/bottom bar* (full-width, no fixed height) is always safe — the hazard is exclusively a tall sticky *side rail* in a collapsing grid. **Footer corollary:** keep the page footer *outside* the grid that contains a sticky rail (a sibling after the grid container, not a `grid-column: 1/-1` child) — the rail's containing block is the grid, so an in-grid footer gets painted over by the still-pinned rail at scroll-bottom. **Scrollbox corollary:** any sticky side rail whose content can exceed the viewport MUST be a bounded scrollbox (`max-height: calc(100dvh - <top>); overflow-y: auto; overscroll-behavior: contain`) added in the same rule that makes it sticky — otherwise content past the fold is unreachable and any programmatic scroll-to-item is forced to drag the whole document. A click that cross-links between panels scrolls *the other* panel (minimally, `block:'nearest'`/no-op-if-visible), never the panel that was clicked. Verify at the breakpoint boundaries *and* at the very bottom of a long page, not just the extremes.

### Density

- **Reading register:** 17–18px serif body, line-height 1.6, prose measure capped at `46rem` (~70ch) even when chrome is wider. Section gap ~2.5rem. Real horizontal rules between sections, not boxed borders.
- **Instrument register:** 14–15px sans body, line-height 1.5, table cell padding `8px 10px`, packed. Stat tiles allowed *only* when the metric is the subject (see Content discipline, in "The bar").
- Headlines line-height 1.2 in both.

### Typography

Three faces, defined once:

```
--font-serif:   "Charter", "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, "Source Serif Pro", serif;
--font-sans:    ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
--font-mono:    ui-monospace, "SF Mono", Menlo, Consolas, monospace;
```

Application is determined by the shape's register, never chosen by the user or skill ad hoc:

| Register | Shapes | Display | Body | Size / line-height | Mono usage |
|---|---|---|---|---|---|
| **Reading** | `document`, `editorial`, `timeline` | serif, 700, tight tracking | serif | 17–18px / 1.6 | metadata, timestamps, numerals |
| **Instrument** | `dashboard`, `comparison`, `developer`, `runbook`, `triage-board`, `network-map` | sans, 700 | sans | 14–15px / 1.5 | numerics, code, IDs |

- Mono is metadata/numerics/code in both registers. `font-variant-numeric: tabular-nums` on all tables and numeric columns.
- Reading register may use mono small-caps for kicker/eyebrow lines (e.g. `SAN FRANCISCO · 14 MAY 2021`).
- Instrument register uses serif sparingly or not at all (e.g. a single pull-quote), never for dense tabular content.

### Color

```
Light:
--paper       #faf6ef   warm cream — page background
--paper-tint  #f3ede1   recessed surfaces, hover fills
--paper-card  #fbf7f0   raised cards
--ink         #1a1815   warm near-black — body text
--ink-soft    #4a443c   secondary text
--muted       #736d62   metadata, captions (AA: 4.76:1 on --paper)
--rule        #d9d1c2   dividers, borders
--rule-soft   #ece5d6   hairline dividers inside cards
--accent      #8a3a1a   terracotta — THE single accent (links, active state, emphasis)
--accent-2    #c2901a   ochre/gold — affirmative actions only (primary button, star/select on)
--ok          #2f7d44
--warn        #9b641d
--note        #2f6fb3

Dark (via prefers-color-scheme):
--paper       #1a1815
--paper-tint  #221f1a
--paper-card  #211e19
--ink         #f0eee8
--ink-soft    #c9c3b6
--muted       #9a948a   (AA: 5.89:1 on dark --paper)
--rule        #38332b
--rule-soft   #2c2820
--accent      #e0794f   terracotta, lifted for dark bg
--accent-2    #d8a73a
--ok          #5cae6f
--warn        #c79a4a
--note        #6f9fd0
```

- One primary accent. One affirmative-action color. No third accent, no corporate blue.
- **All text must meet WCAG AA on its background** (≥4.5:1 normal, ≥3:1 large/UI). This includes `--muted` — the lightest text token — not just the semantic colors. The values above are AA-verified against `--paper` in their respective modes; if you retune a text token, re-check the ratio rather than eyeballing it.
- **`--accent-2` (ochre) is a fill, not a text color on `--paper`.** Ochre text/glyphs on cream are ~2.7:1 (fail). Affirmative elements put `--accent-2` in the *background* and use `--ink` (not white) as the foreground — white-on-ochre is ~2.9:1 (fail), ink-on-ochre is ~6:1 (pass). A toggled glyph (e.g. a filled ★) may use ochre only when its state is also carried by shape/`aria-pressed`, never by color alone.
- High contrast; no gray-on-gray. Color is never the only signal — pair it with text, icon, or shape so the artifact survives colorblind viewing.

### Interactivity

**Every filter needs a visible clear path.** If clicking activates a filter, clicking again has to deactivate it (toggle), and a visible "× clear" affordance has to appear while the filter is active. Never rely on double-click, escape, or "click outside" to reset. Those gestures are undiscoverable.

**Use real controls for real actions.** When something needs to be toggleable, editable, pickable, or clickable, use a control that looks like one: `<input type="checkbox">`, `<input type="range">`, `<select>`, `<button>`. Don't invent gestures on decorative elements ("click this pill", "shift-click this badge", "double-tap this card"). Pills and badges and stat tiles read as static information; making them interactive is invisible and inscrutable. If a pill needs editing, put a real checkbox or button next to it. The pill stays read-only.

**Every copy button needs a fallback.** `navigator.clipboard.writeText()` can fail in local files, hardened browsers, iframes, and permission-restricted contexts. If copy fails, place the exact text in a visible `<textarea>`, focus it, and select it.

**In-text `<mark>` search.** When search filters content, mark the actual occurrences with `<mark>` and scroll to the first match. Never highlight an entire block because the term appears somewhere inside it; the visible part of a long block often does not contain the term. Cache original text (e.g. `data-original`) so clearing search restores cleanly.

### Anti-patterns

- Still exactly three faces (serif, sans, mono); no fourth
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
- No left-handle accent bars. A 3–4px accent-colored vertical line on the left edge of a card or quote is the visual fingerprint of AI-generated layouts. Convey emphasis through type, whitespace, horizontal rules, color, and position. A horizontal rule (top border) between sections is fine; a pull-quote may use larger italic type without a bar.
- Identical-tile grids read as SaaS dashboards; cards stack as columns by default. Only lay out as a grid of equal tiles when the data is genuinely parallel and comparison across tiles is the point.

## Rendering process

1. **Read the request and any existing HTML artifact**
2. **Pick the page shape** from content signals (or ask if ambiguous)
3. **Plan the instrument:**
   - What's the central interaction? (filter? compare? execute? explore?)
   - What features require HTML? Pick at least 3 — write them down before writing HTML.
   - Where does a diagram, chart, or spatial layout add information?
   - Which of the 8 dimensions am I using? (Aim for ≥4)
4. **Write the HTML** — single self-contained file, all CSS inline, all JS (vanilla, ~100-200 lines) inline, no external fonts or CDN assets by default; include the Open Graph / Twitter summary card in `<head>` (see Output)
5. **Validate against the bar:** name the HTML-native features. If <3, redesign before saving. Also scan the rendered HTML for content-discipline anti-patterns — artifact-counting hero stats, left-handle accent bars, category-label section titles, whole-block search highlighting; fix any before saving. This is a self-review instruction, not an automated harness.
6. **Write to `~/Reports/<YYYY-MM-DD>-<slug>.html`**
7. **`open` the file** so it pops in browser when the environment allows it
8. **Report back:** path, size, list of HTML-native features

## Credits

- HTML-artifact framing and copy-as-prompt: [@trq212's "Unreasonable Effectiveness of HTML"](https://x.com/trq212/status/2052809885763747935)
- Content-matched-shapes idea: [`clockless-org/html-anything`](https://github.com/clockless-org/html-anything)
