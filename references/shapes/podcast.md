# Podcast Shape Reference

Load this reference before changing `bin/render-podcast`, changing the canonical podcast examples, or generating a podcast artifact by hand. Normal artifact renders should use the compact `podcast` contract in `SKILL.md`.

## Input Contract

The renderer consumes `episode.package.json` from the podcastify/podcast-transformer pipeline.

Required fields read by the current renderer:

- `episode.{title,short_title,podcast_title,episode_number,episode_url,description,published_at,duration_seconds,hosts,guests}`
- `bottom_line`
- `built_for`
- `takeaways[]`
- `claims[]{topic,claim,evidence}`
- `terms[]{term,name,category,confidence,notes,url}`
- `chapters[]{anchor_id,timestamp,title,turn_index,turn_id}`
- `turns[]{speaker,text,id,timestamp,word_count}`
- `links[]` or `read_next[]` with `{url,label,note}`
- `outputs.{summary_html,annotated_transcript_html}`

Unknown future fields must be ignored. They must never break rendering.

## Output Contract

The podcast shape always produces two sibling files in the same directory:

- `podcast-at-a-glance.html` or `outputs.summary_html`
- `annotated-transcript.html` or `outputs.annotated_transcript_html`

Both files must be standalone source documents:

- They link each other through topbar folder tabs.
- They include `<link rel="icon" href="data:,">`.
- They emit the required summary-card metadata from the global Output contract.
- They do not emit `og:image`, `twitter:image`, or `summary_large_image` unless a real hosted sibling thumbnail exists.
- They embed the same package JSON as `<script type="application/json" id="episode-data">...</script>`, escaping `<`, `>`, and `&` so `</script>` cannot terminate the data island.
- The colophon footer is outside the main grid container.

## Briefing Layout

The briefing is a three-zone studio at `min-width: 1181px`:

- Left rail: episode hero, host profile card, guest profile card.
- Center: thesis card, takeaways, claim cards.
- Right inspector: terms grouped by category, then read-next links.

Collapse behavior:

- Under `1181px`, the inspector drops below the center content.
- Under `821px`, the layout becomes a single column.
- The inspector toggle is hidden at `max-width: 1180px` because the inspector is no longer a collapsible sibling.

Required briefing primitives:

- Topbar with brand, folder tabs, hide-sidebar toggle, and theme toggle.
- Episode hero: kicker, serif `h1`, one-sentence summary, meta row.
- Host and guest cards when data exists.
- Thesis pull-quote from `bottom_line`, italic serif, left-aligned, no left accent bar.
- Numbered takeaways, single column, no tile grid.
- Claim cards with topic, claim body, and Evidence line.
- Term inspector grouped by People / Organizations / Concepts / Tools / Books and articles.
- Read-next list.

Density is intentionally compact: card gap around `0.6rem`, card padding around `0.9rem 1.05rem 1rem`, no tall whitespace between thesis and takeaways.

## Transcript Layout

The transcript view is an instrument-style browser:

- Chapter rail left, speaker-turn list right at `min-width: 821px`.
- Single column below `821px`, with the in-flow chapter rail capped to an internal scroll area.
- Search should bind to the turn corpus only when implemented.
- Speaker labels are hidden on consecutive turns by the same speaker so monologues read continuously.

Chapter rail rows must use flex layout:

- Row: `display: flex; align-items: flex-start`.
- `<time>`: `flex: 0 0 auto; min-width: 4.2rem`.
- Title wrapper: `<span class="ch-title">` with `flex: 1 1 auto; min-width: 0`.

This prevents wrapped chapter titles from falling underneath the timestamp column.

## Topbar Parity

The briefing and transcript topbars must keep folder tabs in the same on-screen X position.

Rules:

- Brand text is identical across views. Do not append "Transcript" or any view suffix to the transcript brand row.
- Both views keep the same toggle slot. The transcript hide-sidebar toggle hides the chapter rail; the briefing toggle hides the term inspector.
- The folder tabs are normal page navigation links: `<nav>` + `<a>` with `aria-current="page"` on the active link. Do not use `role="tablist"`, `role="tab"`, or `aria-selected`.

## Theme And A11y

- Light is the default. Do not use `@media (prefers-color-scheme: dark)` for generated podcast output.
- Dark mode is opt-in with `body.dark`, a topbar button, and `localStorage` key `render-as-html.theme`.
- Wrap localStorage access in `try/catch` for `file://` and sandboxed contexts.
- Use inline SVG moon/sun glyphs; small Unicode moon/sun glyphs rendered poorly on iOS Safari in the 2026-05-24 audit.
- All tab links, buttons, and body links need visible `:focus-visible`.
- Transcript must include `<h1 class="sr-only">` inside `<main>`.
- Inactive folder-tab text uses `--ink-soft`, not `--muted`, to preserve contrast.

## Scroll And Footer Invariants

- The right inspector is sticky only on the wide layout where it has a column.
- The inspector is a bounded independent scrollbox: `max-height: calc(100dvh - <topbar>)`, `overflow-y: auto`, `overscroll-behavior: contain`.
- The left rail follows the same sticky + max-height + overflow pattern at the two-column breakpoint.
- The footer is a sibling after the `.studio` grid. Never put it inside the grid with `grid-column: 1 / -1`; sticky rails can paint over it at scroll-bottom.

## Avoid

- One mega-scroll containing briefing and transcript together.
- Hero stat tiles that count words, turns, or production artifacts.
- External fonts, scripts, or image resources.
- Fabricated term URLs. If `terms[].url` is missing, render plain text.
- Copy/export controls that imply another canonical format.
