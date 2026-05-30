# Annotated diff — code review primitive

Load before implementing or changing the annotated-diff primitive. The compact picker + stub live in `SKILL.md` §Canonical primitives; reference implementation is `examples/primitives/08-diff.html`.

- **Pick when:** reviewing code changes, security findings, or any line-anchored critique where adjacency to the source matters more than a side panel.
- **Required:** findings sit IN the diff, anchored to the line they touch; severity carried three ways (strip count at the top + left bar on the finding card + colored badge fill — color is never alone); explicit `L<n> · new` / `L<n> · removed` line labels so reviewers know which side they're commenting on; `+`/`−` gutter chars in their own column AND row background tint (two cues); syntax highlighting via local CSS classes only (no Prism, no CDN, no runtime tokenizer); per-finding `copy as prompt` quoting the line context.
- **Interaction:** click any line number to copy a `file:line` reference (gutter flashes); per-finding copy button round-trips back as a paste-able instruction; `show nits` toggle hides low-priority findings.
- **Avoid:** findings in a sidebar separated from the lines they discuss; color-only severity; runtime syntax highlighters or CDN dependencies.
