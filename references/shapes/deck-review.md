# Deck Review Shape Reference

Load before authoring a `deck-review` artifact or changing `examples/deck-review.html`. The compact stub in `SKILL.md` is enough to pick the shape; this file holds the build detail. **The review workflow is the shape** — status context, slide preview, per-slide notes, and send-back export.

## Pick This Shape

Use `deck-review` when the user needs a browser page for reviewing a slide deck or presentation package:

- A Keynote/PPT/PDF deck plus speaker notes, presenter script, or revision memo.
- A reviewer needs to leave comments slide by slide.
- A deck owner needs structured feedback sent back without a collaboration platform.
- The payload may be sensitive enough to encrypt inside the HTML file.

If the source is only a prose memo about a deck, use `document` or `editorial`. If the task is to create the actual slide deck, use the presentation tooling instead of this shape.

## Layout

Use a Hybrid register:

- Status view: Reading register, serif headline and paragraphs, bounded measure.
- Slides view: Instrument frame around a large slide preview, nav, talk track, and notes textarea.
- Send-back view: Instrument controls around a readable export textarea.

Required topbar:

- Deck/project title.
- Three view controls: Status, Slides, Send it back.
- Notes-count badge (`no notes yet`, `1 slide noted`, `n slides noted`).
- View counter on the right (`Status`, `Slide 3 / 15`, `Send it back`).

Tabs are real buttons when they switch views inside one file. Carry state with `aria-pressed` or `aria-current`; do not use ARIA tab roles unless the whole tab keyboard contract is implemented.

## Required Data

Normalize the deck into this shape before rendering:

```js
const DATA = {
  deck: {
    title: "Client deck review",
    subtitle: "Draft v4 · 15 slides",
    recipient: "Lee",
    ownerEmail: "todd@example.com"
  },
  statusHtml: "<p>What changed and what needs review.</p>",
  slides: [
    {
      n: 1,
      title: "Cover — A national services agreement",
      time: "19s",
      img: "data:image/png;base64,...", // or inline SVG produced locally
      lines: [{ say: "What the presenter says here." }],
      video: null,
      videoBox: null
    }
  ]
};
```

For public repo examples, use synthetic data. For private artifacts, make an explicit sensitivity call before deciding whether slide data can sit unencrypted in the file.

## Optional Encrypted Payload

Use WebCrypto for private/sensitive deck payloads:

- Encrypt the payload JSON with AES-GCM 256.
- Derive the key with PBKDF2 + SHA-256. Use a high iteration count (current examples use 200,000).
- Embed only `{ salt, iv, ct, iters }` in the HTML.
- Keep the passphrase in `sessionStorage` at most; never `localStorage`.
- Store reviewer notes in `localStorage` under a deck-specific key. Notes are user-authored browser state, not the encrypted deck payload.
- Decrypt in the browser. The passphrase must not be sent to a server.
- Show a clear locked state, an explicit passphrase form, and an error that does not reveal which part failed.

The ciphertext is not a publishing permission slip. If the deck cannot safely be shared with anyone who has the passphrase, do not ship it as a standalone HTML file. Do not commit real encrypted client payloads to public repositories; examples must be synthetic.

## Required Views

### Status

The status view explains what changed, what the reviewer should focus on, and any known constraints. It is prose-first, not a dashboard. Avoid artifact-counting hero stats. A small callout is fine for "what this took", "since last review", or "known issue".

### Slides

Required components:

- Large slide image/SVG preview with useful `alt`.
- Previous/next controls with stable dimensions.
- Dots or list navigation; note-bearing slides get a non-color-only marker.
- Slide title, number, and optional spoken duration.
- Presenter script/talk track under the slide.
- Per-slide reviewer textarea, persisted locally.
- Keyboard navigation with left/right arrows except while typing.

The slide, talk track, and textarea must stay synchronized. When a reviewer navigates, update the title, preview, script, notes value, note markers, and counter in one state transition.

### Send It Back

Required components:

- Export textarea containing a structured, human-readable notes package.
- Email/mailto action when an owner email exists.
- Copy action with clipboard guard and visible fallback.
- Clear-notes action with confirmation.
- Warning when a generated mailto URL is likely too long for common mail clients.

Export format:

```text
<Deck title>
<Deck subtitle>
Notes on <n> of <total> slides

Slide 03 — <title>
<reviewer note>
```

The export is not copy-as-markdown. It is the browser-collected review state. If the artifact is also meant to round-trip back into the HTML source, add a separate copy-as-prompt control that wraps state with `BEGIN ARTIFACT STATE DATA` / `END ARTIFACT STATE DATA`.

## Visual Rules

- The deck/project name is visible in the first viewport.
- The slide preview should be inspectable; do not blur, crop, or shrink it into a decorative card.
- Use restrained buttons and stable controls. Icon-only arrows are fine when the label is provided with `aria-label`.
- Notes textareas need enough height for real comments and must not resize the page unpredictably.
- On mobile, stack preview, script, and notes; keep nav controls reachable and avoid horizontal page overflow.

## Avoid

- Unencrypted confidential slide data in shared/public HTML.
- Sending notes automatically or using a remote endpoint unless the user explicitly asked for that workflow.
- Screenshot-only review with no per-slide note binding.
- A status page that only says "please review"; it must name what changed and what kind of feedback is needed.
- Mailto export without copy fallback.
- Storing passphrases or decrypted payloads in `localStorage`.
