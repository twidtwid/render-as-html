# Comparison matrix — items as columns

Load before implementing or changing the comparison-matrix primitive. The compact picker + stub live in `SKILL.md` §Canonical primitives; reference implementation is `examples/primitives/07-table-comparison.html`.

- **Pick when:** "X vs Y vs Z" decision matrix with shared criteria; you want the reader to tune weights and see who wins live; 2–5 items, 3–10 criteria.
- **Required:** items as columns (entities-as-rows would be a dashboard, not this — the axis flip *is* the shape); weight column on the far left with a full-height +/− stepper flanking the input (no native browser spinners); aggregate row normalized to 0–100 (so total-weight changes don't mask relative position); explicit `↑ better` / `↓ better` per-criterion direction; per-row star + ochre tint marks row winner; overall winner in the footer goes terracotta; round-trip `copy as prompt` with visible textarea fallback.
- **Interaction:** step or type any weight 0–5; per-row and overall winners recompute on every change.
- **Avoid:** entities-as-rows layout; tiny native spinner buttons; weights without bounds; copy buttons that imply another canonical format (use `copy as recommendation` / `copy as prompt`, not `copy as markdown`).
