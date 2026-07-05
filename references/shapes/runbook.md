# Runbook Shape Reference

Load before authoring or changing a `runbook`-shape artifact, or `examples/runbook.html`. The compact stub in `SKILL.md` §Page shapes is enough to pick the shape and scaffold; this file holds the build detail. A runbook is an *instrument being executed*, not reading material — that distinction drives every choice below.

- **Register:** Instrument (sans display + sans body; see §Design system / Density), with prominent mono code blocks.
- **Use for:** disaster recovery, deploy guides, machine rebuilds — a sequential procedure being *run*, step by step, while something is on fire.
- **Layout:** a sticky header with "Step X of N" + a progress bar; max-width 960px single column; step cards stacked vertically. The sticky progress bar is a full-width top bar (always safe per §Layout principles).
- **First viewport:** title + a scope/danger callout + the progress bar + step 1 visible.
- **Required primitives:** step card with `[number] [checkbox] [title]` + an expandable body; a code block with a per-block copy button (load-bearing — running a runbook means copying commands); "expected output" collapsible callouts; branch markers ("if X, jump to step Y"); the sticky progress bar; an "I'm stuck" copy-as-prompt that names the current `.html` path and the current step.
- **Step headers must be keyboard-operable:** `tabindex="0"` + a keydown handler (Enter/Space toggles the body), not click-only.
- **HTML-native ≥3:** per-code-block copy button (with a *visible* fallback, never an offscreen textarea); live progress tracking as checkboxes are ticked; the "stuck" prompt generator; conditional/collapsible step bodies.
- **Avoid:** a plain numbered list with code blocks; making it look like `document` shape (this is an instrument); hiding the copy-code fallback offscreen.
